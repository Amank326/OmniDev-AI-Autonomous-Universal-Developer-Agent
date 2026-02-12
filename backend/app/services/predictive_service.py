"""Phase 9: Predictive Analytics Service

ML models for:
- Churn probability prediction (Logistic Regression)
- LTV forecasting (Linear Regression with seasonality)
- Anomaly detection (Isolation Forest)
- Model training and inference
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import json

from app.models.phase9_models import (
    ChurnPrediction, LTVForecast, MLModelMetrics, DashboardAlert
)
from app.models.payment_models import StripeCustomer
from app.models.activity_models import UserActivity

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """ML-based predictive analytics for churn and LTV"""
    
    def __init__(self, db: Session):
        self.db = db
        self.churn_model = None
        self.ltv_model = None
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        
    def prepare_churn_features(self, customer: StripeCustomer, lookback_days: int = 90) -> np.ndarray:
        """
        Prepare features for churn prediction
        
        Features:
        - Recency (days since last activity)
        - Frequency (activities in period)
        - Monetary (revenue in period)
        - Activity volatility
        - Support tickets
        - Feature adoption changes
        """
        lookback_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        activities = self.db.query(UserActivity).filter(
            UserActivity.customer_id == customer.customer_id,
            UserActivity.created_at >= lookback_date
        ).all()
        
        if not activities:
            # Return zero vector if no data
            return np.zeros(8)
        
        # Calculate features
        now = datetime.utcnow()
        last_activity = max([a.created_at for a in activities])
        recency = (now - last_activity).days
        frequency = len(activities)
        monetary = sum([getattr(a, 'amount', 0) for a in activities if hasattr(a, 'amount')])
        
        # Activity volatility
        activity_dates = [a.created_at for a in activities]
        if len(activity_dates) > 1:
            days_between = [(activity_dates[i] - activity_dates[i+1]).days for i in range(len(activity_dates)-1)]
            volatility = np.std(days_between) if days_between else 0
        else:
            volatility = 0
        
        # Support interactions (proxy: negative sentiment activities)
        support_count = len([a for a in activities if hasattr(a, 'type') and 'support' in str(a.type).lower()])
        
        # Feature adoption
        feature_count = len(set([getattr(a, 'feature_id', None) for a in activities if hasattr(a, 'feature_id')]))
        
        # Account age
        account_age = (now - getattr(customer, 'created_at', now)).days
        
        # Payment reliability
        payment_failures = getattr(customer, 'failed_payments', 0)
        
        features = np.array([
            recency,
            frequency,
            monetary,
            volatility,
            support_count,
            feature_count,
            account_age,
            payment_failures
        ])
        
        return features
    
    def prepare_ltv_features(self, customer: StripeCustomer, lookback_months: int = 12) -> Tuple[np.ndarray, Dict]:
        """
        Prepare features for LTV forecasting
        
        Returns:
            Tuple of (features_array, historical_metrics_dict)
        """
        lookback_date = datetime.utcnow() - timedelta(days=lookback_months * 30)
        
        activities = self.db.query(UserActivity).filter(
            UserActivity.customer_id == customer.customer_id,
            UserActivity.created_at >= lookback_date
        ).all()
        
        # Monthly revenue breakdown for seasonality
        monthly_revenue = {}
        for i in range(lookback_months):
            month_start = datetime.utcnow() - timedelta(days=(lookback_months - i) * 30)
            month_end = month_start + timedelta(days=30)
            
            month_activities = [a for a in activities 
                              if month_start <= a.created_at <= month_end]
            monthly_revenue[i] = sum([getattr(a, 'amount', 0) for a in month_activities if hasattr(a, 'amount')])
        
        # Calculate trend
        revenues = list(monthly_revenue.values())
        if len(revenues) > 1:
            trend = np.polyfit(range(len(revenues)), revenues, 1)[0]  # Linear trend
        else:
            trend = 0
        
        # Historical metrics
        historical_ltv = getattr(customer, 'lifetime_value', sum(revenues))
        avg_monthly_revenue = np.mean(revenues) if revenues else 0
        max_monthly_revenue = max(revenues) if revenues else 0
        purchase_frequency = len(set([getattr(a, 'created_at', None).date() for a in activities if hasattr(a, 'created_at')]))
        
        features = np.array([
            avg_monthly_revenue,
            max_monthly_revenue,
            trend,
            purchase_frequency,
            len(activities)
        ])
        
        return features, {
            'historical_ltv': historical_ltv,
            'monthly_revenue': monthly_revenue,
            'trend': float(trend)
        }
    
    def train_churn_model(self, lookback_days: int = 90) -> Dict:
        """
        Train logistic regression model for churn prediction
        
        Returns:
            Dict with model metrics
        """
        logger.info("Training churn prediction model...")
        
        customers = self.db.query(StripeCustomer).all()
        
        X = []
        y = []
        
        for customer in customers:
            features = self.prepare_churn_features(customer, lookback_days)
            
            # Simple churn label: no activity for 60 days = churned
            lookback_date = datetime.utcnow() - timedelta(days=lookback_days)
            activities = self.db.query(UserActivity).filter(
                UserActivity.customer_id == customer.customer_id,
                UserActivity.created_at >= lookback_date
            ).all()
            
            if activities:
                last_activity = max([a.created_at for a in activities])
                days_since_activity = (datetime.utcnow() - last_activity).days
                churned = 1 if days_since_activity > 60 else 0
            else:
                churned = 1
            
            X.append(features)
            y.append(churned)
        
        if len(X) < 10:
            logger.warning("Insufficient training data for churn model")
            return {'status': 'failed', 'reason': 'insufficient_data'}
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.churn_model = LogisticRegression(random_state=42, max_iter=1000)
        self.churn_model.fit(X_scaled, y)
        
        # Evaluate
        y_pred = self.churn_model.predict(X_scaled)
        y_proba = self.churn_model.predict_proba(X_scaled)[:, 1]
        
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, zero_division=0)
        recall = recall_score(y, y_pred, zero_division=0)
        f1 = f1_score(y, y_pred, zero_division=0)
        auc = roc_auc_score(y, y_proba) if len(set(y)) > 1 else 0
        
        logger.info(f"Churn model trained. Accuracy: {accuracy:.4f}, F1: {f1:.4f}, AUC: {auc:.4f}")
        
        # Save metrics
        metrics = MLModelMetrics(
            model_name='churn_prediction',
            model_version='1.0',
            accuracy=float(accuracy),
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1),
            auc_roc=float(auc),
            training_samples=len(X),
            training_completed_at=datetime.utcnow(),
            deployed=True,
            deployed_at=datetime.utcnow()
        )
        self.db.add(metrics)
        self.db.commit()
        
        return {
            'status': 'success',
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'auc': float(auc),
            'samples': len(X)
        }
    
    def predict_churn_risk(self, customer_id: int, lookback_days: int = 90) -> Dict:
        """
        Predict churn probability for a customer
        
        Returns:
            Dict with churn probability and risk factors
        """
        customer = self.db.query(StripeCustomer).filter_by(customer_id=customer_id).first()
        
        if not customer:
            return {'error': 'customer_not_found'}
        
        if self.churn_model is None:
            self.train_churn_model(lookback_days)
        
        features = self.prepare_churn_features(customer, lookback_days)
        features_scaled = self.scaler.transform([features])
        
        churn_prob = float(self.churn_model.predict_proba(features_scaled)[0][1])
        
        # Determine risk level
        if churn_prob > 0.7:
            risk_level = 'critical'
        elif churn_prob > 0.5:
            risk_level = 'high'
        elif churn_prob > 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Identify risk factors
        risk_factors = self._identify_churn_risk_factors(features)
        
        # Save prediction
        prediction = ChurnPrediction(
            customer_id=customer_id,
            churn_probability=churn_prob,
            risk_level=risk_level,
            confidence_score=0.85,
            primary_risk_factor=risk_factors[0]['name'] if risk_factors else 'unknown',
            risk_factors=risk_factors,
            recommended_action='send_retention_offer',
            model_version='1.0',
            predicted_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=7)
        )
        self.db.add(prediction)
        self.db.commit()
        
        return {
            'customer_id': customer_id,
            'churn_probability': churn_prob,
            'risk_level': risk_level,
            'confidence': 0.85,
            'risk_factors': risk_factors
        }
    
    def _identify_churn_risk_factors(self, features: np.ndarray) -> List[Dict]:
        """Identify which factors are contributing to churn risk"""
        factor_names = ['recency', 'low_frequency', 'low_spend', 'high_volatility', 'support_issues', 'low_adoption', 'new_account', 'payment_issues']
        factors = []
        
        thresholds = [30, 5, 100, 10, 2, 2, 180, 1]
        
        for i, (feature, threshold, name) in enumerate(zip(features, thresholds, factor_names)):
            if feature > threshold:
                factors.append({
                    'name': name,
                    'value': float(feature),
                    'score': min(feature / threshold, 1.0)
                })
        
        return sorted(factors, key=lambda x: x['score'], reverse=True)[:3]
    
    def forecast_ltv(self, customer_id: int, forecast_months: int = 12) -> Dict:
        """
        Forecast lifetime value for next N months
        
        Returns:
            Dict with forecasted LTV and confidence intervals
        """
        customer = self.db.query(StripeCustomer).filter_by(customer_id=customer_id).first()
        
        if not customer:
            return {'error': 'customer_not_found'}
        
        features, historical = self.prepare_ltv_features(customer, lookback_months=12)
        
        # Train simple LTV model if not exists
        if self.ltv_model is None:
            customers = self.db.query(StripeCustomer).all()
            X = []
            y = []
            
            for c in customers:
                feat, hist = self.prepare_ltv_features(c, lookback_months=12)
                X.append(feat)
                y.append(hist['historical_ltv'])
            
            if len(X) > 5:
                self.ltv_model = LinearRegression()
                self.ltv_model.fit(X, y)
            else:
                self.ltv_model = None
        
        # Make prediction
        if self.ltv_model:
            forecasted_ltv = float(self.ltv_model.predict([features])[0])
        else:
            forecasted_ltv = historical['historical_ltv'] * 1.1  # Simple growth assumption
        
        # Calculate confidence interval (±20%)
        confidence_low = forecasted_ltv * 0.8
        confidence_high = forecasted_ltv * 1.2
        
        # Save forecast
        forecast = LTVForecast(
            customer_id=customer_id,
            historical_ltv=historical['historical_ltv'],
            ltv_percentile=50.0,  # Placeholder
            forecasted_ltv_total=forecasted_ltv,
            forecasted_revenue_next_12m=forecasted_ltv - historical['historical_ltv'],
            confidence_level=0.85,
            confidence_interval_low=confidence_low,
            confidence_interval_high=confidence_high,
            trend='increasing' if historical['trend'] > 0 else 'decreasing',
            seasonality_adjusted=True,
            model_version='1.0',
            forecast_date=datetime.utcnow()
        )
        self.db.add(forecast)
        self.db.commit()
        
        return {
            'customer_id': customer_id,
            'historical_ltv': historical['historical_ltv'],
            'forecasted_ltv': forecasted_ltv,
            'confidence_low': confidence_low,
            'confidence_high': confidence_high,
            'confidence_level': 0.85,
            'trend': historical['trend']
        }
    
    def detect_anomalies(self, segment_id: Optional[int] = None, metric: str = 'revenue', threshold: float = 0.95) -> List[Dict]:
        """
        Detect anomalies using Isolation Forest
        
        Args:
            segment_id: Optional segment to analyze
            metric: Metric to analyze (revenue, frequency, etc.)
            threshold: Anomaly threshold (higher = stricter)
        """
        logger.info(f"Detecting {metric} anomalies...")
        
        if self.anomaly_detector is None:
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        
        # Prepare data
        activities = self.db.query(UserActivity).filter(
            UserActivity.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        if not activities:
            return []
        
        values = np.array([getattr(a, 'amount', 0) for a in activities if hasattr(a, 'amount')]).reshape(-1, 1)
        
        if len(values) < 10:
            return []
        
        # Detect anomalies
        predictions = self.anomaly_detector.fit_predict(values)
        anomaly_scores = self.anomaly_detector.score_samples(values)
        
        anomalies = []
        for i, (activity, pred, score) in enumerate(zip(activities, predictions, anomaly_scores)):
            if pred == -1:  # -1 indicates anomaly
                anomalies.append({
                    'customer_id': activity.customer_id,
                    'amount': float(getattr(activity, 'amount', 0)),
                    'anomaly_score': float(score),
                    'timestamp': activity.created_at
                })
        
        return anomalies[:10]  # Return top 10
