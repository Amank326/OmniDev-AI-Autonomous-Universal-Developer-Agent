"""Phase 9: Advanced Segmentation Service

Provides ML-powered customer segmentation using K-means clustering with:
- Behavioral segmentation
- RFM analysis
- Silhouette analysis for optimal clusters
- Dynamic segment reassignment
- Segment profiling
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, silhouette_samples
import json

from app.models.phase9_models import (
    CustomerSegment, SegmentProfile, SegmentAssignment, DashboardAlert
)
from app.models.payment_models import StripeCustomer
from app.models.activity_models import UserActivity

logger = logging.getLogger(__name__)


class AdvancedSegmentationService:
    """Advanced customer segmentation using K-means clustering"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scaler = StandardScaler()
        self.kmeans = None
        self.feature_names = None
        
    def prepare_customer_features(self, lookback_days: int = 90) -> Tuple[pd.DataFrame, List[str]]:
        """
        Prepare feature matrix for clustering
        
        Features:
        - RFM (Recency, Frequency, Monetary)
        - Engagement (feature usage, session frequency)
        - Lifetime value metrics
        - Activity patterns
        """
        lookback_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        customers = self.db.query(StripeCustomer).all()
        features_list = []
        
        for customer in customers:
            # Get activities
            activities = self.db.query(UserActivity).filter(
                UserActivity.user_id == customer.customer_id,
                UserActivity.created_at >= lookback_date
            ).all()
            
            if not activities:
                continue
            
            # RFM Metrics
            now = datetime.utcnow()
            last_activity = max([a.created_at for a in activities])
            recency = (now - last_activity).days
            frequency = len(activities)
            monetary = sum([getattr(a, 'amount', 0) for a in activities if hasattr(a, 'amount')])
            
            # Engagement metrics
            feature_usage_count = len(set([a.feature_id for a in activities if hasattr(a, 'feature_id')]))
            session_count = len(set([getattr(a, 'session_id', None) for a in activities if hasattr(a, 'session_id')]))
            
            # Value metrics
            ltv = getattr(customer, 'lifetime_value', monetary)
            
            features_list.append({
                'customer_id': customer.customer_id,
                'recency': recency,
                'frequency': frequency,
                'monetary': monetary,
                'feature_usage': feature_usage_count,
                'session_count': session_count,
                'ltv': ltv,
                'days_as_customer': (now - getattr(customer, 'created_at', now)).days
            })
        
        df = pd.DataFrame(features_list)
        
        if df.empty:
            return pd.DataFrame(), []
        
        feature_cols = ['recency', 'frequency', 'monetary', 'feature_usage', 'session_count', 'ltv', 'days_as_customer']
        self.feature_names = feature_cols
        
        return df, feature_cols
    
    def find_optimal_clusters(self, X: np.ndarray, max_clusters: int = 10) -> Tuple[int, List[float]]:
        """Find optimal number of clusters using silhouette analysis"""
        silhouette_scores = []
        
        for n_clusters in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            score = silhouette_score(X, labels)
            silhouette_scores.append(score)
            logger.info(f"Clusters: {n_clusters}, Silhouette Score: {score:.4f}")
        
        optimal_clusters = np.argmax(silhouette_scores) + 2
        return optimal_clusters, silhouette_scores
    
    def perform_behavioral_segmentation(self, n_clusters: Optional[int] = None, 
                                       lookback_days: int = 90) -> Dict:
        """
        Perform K-means clustering for behavioral segmentation
        
        Args:
            n_clusters: Number of clusters (auto-detect if None)
            lookback_days: Days of history to analyze
            
        Returns:
            Dict with segmentation results and metrics
        """
        logger.info("Starting behavioral segmentation...")
        
        # Prepare features
        df, feature_cols = self.prepare_customer_features(lookback_days)
        
        if df.empty:
            logger.warning("No customer data available for segmentation")
            return {'status': 'failed', 'reason': 'no_data'}
        
        X = df[feature_cols].values
        X_scaled = self.scaler.fit_transform(X)
        
        # Find optimal clusters if not specified
        if n_clusters is None:
            n_clusters, silhouette_scores = self.find_optimal_clusters(X_scaled)
            logger.info(f"Optimal cluster count: {n_clusters}")
        
        # Perform K-means clustering
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = self.kmeans.fit_predict(X_scaled)
        silhouette_avg = silhouette_score(X_scaled, labels)
        
        logger.info(f"Segmentation complete. Silhouette Score: {silhouette_avg:.4f}")
        
        df['segment'] = labels
        
        # Save segments to database
        self._save_segments(df, X_scaled, silhouette_avg)
        
        return {
            'status': 'success',
            'clusters': n_clusters,
            'silhouette_score': float(silhouette_avg),
            'customers_analyzed': len(df),
            'segment_distribution': df['segment'].value_counts().to_dict()
        }
    
    def _save_segments(self, df: pd.DataFrame, X_scaled: np.ndarray, silhouette_score: float):
        """Save segmentation results to database"""
        # Delete old segments
        self.db.query(CustomerSegment).delete()
        self.db.query(SegmentAssignment).delete()
        self.db.commit()
        
        # Create new segments
        for segment_id in range(self.kmeans.n_clusters):
            segment_data = df[df['segment'] == segment_id]
            
            segment_name = f"Segment_{segment_id}_{self._get_segment_label(segment_data)}"
            
            segment = CustomerSegment(
                segment_name=segment_name,
                segment_type='behavioral',
                customer_count=len(segment_data),
                avg_revenue=float(segment_data['monetary'].mean()),
                avg_ltv=float(segment_data['ltv'].mean()),
                avg_churn_risk=self._estimate_churn_risk(segment_data),
                engagement_score=self._calculate_engagement_score(segment_data),
                cluster_center=self.kmeans.cluster_centers_[segment_id].tolist(),
                silhouette_score=float(silhouette_score),
                feature_weights=self._compute_feature_weights(segment_data),
                is_active=True
            )
            
            self.db.add(segment)
            self.db.flush()
            
            # Create segment profile
            profile = SegmentProfile(
                segment_id=segment.segment_id,
                avg_purchase_frequency=float(segment_data['frequency'].mean()),
                avg_order_value=float(segment_data['monetary'].mean() / (segment_data['frequency'].mean() + 1)),
                feature_adoption_rate=float(segment_data['feature_usage'].mean() / 10),
                churn_risk_score=self._estimate_churn_risk(segment_data) * 100,
                recommended_actions=['offer_special_discount', 'personalized_email', 'product_recommendation']
            )
            
            self.db.add(profile)
            self.db.flush()
            
            # Create assignments
            for _, row in segment_data.iterrows():
                assignment = SegmentAssignment(
                    customer_id=int(row['customer_id']),
                    segment_id=segment.segment_id,
                    confidence_score=0.9,  # High confidence for K-means
                    distance_to_center=float(np.linalg.norm(X_scaled[row.name] - self.kmeans.cluster_centers_[segment_id])),
                    feature_vector=self._create_feature_vector(row),
                    assigned_at=datetime.utcnow(),
                    next_recompute=datetime.utcnow() + timedelta(days=7)
                )
                self.db.add(assignment)
        
        self.db.commit()
        logger.info(f"Saved {self.kmeans.n_clusters} segments to database")
    
    def _get_segment_label(self, segment_data: pd.DataFrame) -> str:
        """Generate human-readable segment label based on characteristics"""
        avg_recency = segment_data['recency'].mean()
        avg_frequency = segment_data['frequency'].mean()
        avg_monetary = segment_data['monetary'].mean()
        
        if avg_recency < 30 and avg_frequency > 5 and avg_monetary > 1000:
            return "VIP_Active"
        elif avg_recency > 90:
            return "Dormant"
        elif avg_frequency > 10:
            return "Loyal"
        elif avg_monetary > 500:
            return "Big_Spender"
        else:
            return "Emerging"
    
    def _estimate_churn_risk(self, segment_data: pd.DataFrame) -> float:
        """Estimate churn risk (0-1) based on recency"""
        avg_recency = segment_data['recency'].mean()
        # Higher recency = higher churn risk
        churn_risk = min(avg_recency / 180, 1.0)
        return float(churn_risk)
    
    def _calculate_engagement_score(self, segment_data: pd.DataFrame) -> float:
        """Calculate engagement score (0-100) based on activity"""
        frequency_score = min((segment_data['frequency'].mean() / 10) * 100, 100)
        session_score = min((segment_data['session_count'].mean() / 5) * 100, 100)
        return float((frequency_score + session_score) / 2)
    
    def _compute_feature_weights(self, segment_data: pd.DataFrame) -> Dict:
        """Compute feature importance for this segment"""
        weights = {}
        for col in self.feature_names:
            if col in segment_data.columns:
                weights[col] = float(segment_data[col].std())
        return weights
    
    def _create_feature_vector(self, row) -> Dict:
        """Create feature vector for a customer row"""
        return {col: float(row[col]) for col in self.feature_names if col in row.index}
    
    def predict_customer_segment(self, customer_features: Dict[str, float]) -> Tuple[int, float]:
        """
        Predict segment for a new customer
        
        Args:
            customer_features: Dict with feature values
            
        Returns:
            Tuple of (segment_id, confidence_score)
        """
        if self.kmeans is None:
            raise ValueError("Model not trained. Call perform_behavioral_segmentation first.")
        
        # Create feature array
        feature_array = np.array([[customer_features.get(col, 0) for col in self.feature_names]])
        feature_scaled = self.scaler.transform(feature_array)
        
        # Predict segment
        segment_id = self.kmeans.predict(feature_scaled)[0]
        
        # Calculate distance-based confidence
        distance = np.linalg.norm(feature_scaled[0] - self.kmeans.cluster_centers_[segment_id])
        confidence = 1 / (1 + distance)  # Sigmoid-like function
        
        return segment_id, float(confidence)
    
    def get_segment_recommendations(self, segment_id: int) -> List[Dict]:
        """Get recommended actions for a segment"""
        segment = self.db.query(CustomerSegment).filter_by(segment_id=segment_id).first()
        
        if not segment:
            return []
        
        recommendations = []
        
        if segment.avg_churn_risk > 0.5:
            recommendations.append({
                'type': 'retention',
                'action': 'send_special_offer',
                'priority': 'high',
                'expected_impact': '+15% retention'
            })
        
        if segment.engagement_score < 40:
            recommendations.append({
                'type': 'engagement',
                'action': 'launch_reengagement_campaign',
                'priority': 'medium',
                'expected_impact': '+25% engagement'
            })
        
        if segment.avg_ltv > 5000:
            recommendations.append({
                'type': 'vip',
                'action': 'assign_dedicated_account_manager',
                'priority': 'high',
                'expected_impact': '+30% retention'
            })
        
        return recommendations
    
    def detect_segment_shifts(self, customer_id: int, lookback_days: int = 30) -> Dict:
        """Detect if a customer has shifted segments recently"""
        assignments = self.db.query(SegmentAssignment).filter_by(
            customer_id=customer_id
        ).order_by(SegmentAssignment.assigned_at.desc()).limit(2).all()
        
        if len(assignments) < 2:
            return {'shifted': False, 'reason': 'insufficient_history'}
        
        current_segment = assignments[0].segment_id
        previous_segment = assignments[1].segment_id
        
        if current_segment != previous_segment:
            return {
                'shifted': True,
                'from_segment': previous_segment,
                'to_segment': current_segment,
                'shift_date': assignments[0].assigned_at,
                'requires_action': True
            }
        
        return {'shifted': False, 'reason': 'no_change'}
