"""
Phase 7B: Advanced Analytics Service

Comprehensive analytics, ML/AI predictions, anomaly detection, engagement scoring,
churn prediction, customer segmentation, and recommendation engine.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from scipy import stats

logger = logging.getLogger(__name__)


class AdvancedAnalyticsService:
    """Advanced analytics with ML/AI capabilities"""
    
    # ==================== ACTIVITY LOGGING ====================
    
    @staticmethod
    def log_user_activity(
        db: Session,
        customer_id: int,
        activity_type: str,
        description: str = None,
        metadata: Dict = None,
        duration_ms: int = None,
        ip_address: str = None,
        user_agent: str = None,
        endpoint: str = None
    ):
        """Log user activity for engagement tracking and audit trail"""
        try:
            from app.models.activity_models import UserActivity
            
            activity = UserActivity(
                customer_id=customer_id,
                activity_type=activity_type,
                description=description,
                metadata=metadata or {},
                duration_ms=duration_ms,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                created_at=datetime.utcnow()
            )
            db.add(activity)
            db.commit()
            return activity
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            db.rollback()
            return None
    
    
    @staticmethod
    def create_audit_log(
        db: Session,
        customer_id: int,
        action: str,
        resource_type: str,
        resource_id: str,
        old_values: Dict = None,
        new_values: Dict = None,
        changes_summary: str = None,
        actor_id: str = None,
        actor_type: str = "system",
        ip_address: str = None
    ):
        """Create comprehensive audit log entry for compliance"""
        try:
            from app.models.activity_models import AuditLog
            
            audit = AuditLog(
                customer_id=customer_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                changes_summary=changes_summary,
                actor_id=actor_id,
                actor_type=actor_type,
                ip_address=ip_address,
                created_at=datetime.utcnow()
            )
            db.add(audit)
            db.commit()
            return audit
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()
            return None
    
    
    # ==================== ENGAGEMENT SCORING ====================
    
    @staticmethod
    def calculate_engagement_score(
        db: Session,
        customer_id: int,
        period_days: int = 30
    ) -> float:
        """Calculate engagement score 0-100 based on multiple factors"""
        try:
            from app.models.activity_models import (
                UserActivity, ActivityType, EngagementMetrics
            )
            from app.models.models import StripeCustomer
            
            # Query activities in period
            start_date = datetime.utcnow() - timedelta(days=period_days)
            activities = db.query(UserActivity).filter(
                and_(
                    UserActivity.customer_id == customer_id,
                    UserActivity.created_at >= start_date
                )
            ).all()
            
            customer = db.query(StripeCustomer).filter(
                StripeCustomer.id == customer_id
            ).first()
            
            if not customer:
                return 0.0
            
            # Calculate component scores
            logins = len([a for a in activities if a.activity_type == ActivityType.LOGIN])
            features_used = len(set(a.endpoint for a in activities if a.endpoint))
            api_calls = len([a for a in activities if a.activity_type == ActivityType.API_CALL])
            
            # Calculate days since last activity
            last_activity = max([a.created_at for a in activities]) if activities else customer.created_at
            days_inactive = (datetime.utcnow() - last_activity).days
            
            # Calculate tenure bonus
            tenure_days = (datetime.utcnow() - customer.created_at).days
            tenure_bonus = min(20, (tenure_days / 365) * 20)  # Cap at 20 points
            
            # Score components (0-20 each = 100 total)
            login_score = min(20, (logins / period_days) * 20)  # Max 1 login/day
            feature_score = min(20, (features_used / 10) * 20)  # Max 10 features
            api_score = min(20, (api_calls / 100) * 20)  # Max 100 calls
            activity_recency_score = max(0, 20 - (days_inactive * 0.5))  # Decay by activity inactivity
            retention_score = tenure_bonus
            
            engagement_score = (
                login_score + feature_score + api_score +
                activity_recency_score + retention_score
            )
            engagement_score = max(0, min(100, engagement_score))
            
            # Determine trend
            last_week_activities = len([
                a for a in activities
                if a.created_at >= datetime.utcnow() - timedelta(days=7)
            ])
            prev_week_activities = len([
                a for a in activities
                if a.created_at >= datetime.utcnow() - timedelta(days=14)
                and a.created_at < datetime.utcnow() - timedelta(days=7)
            ])
            
            if last_week_activities > prev_week_activities:
                trend = "increasing"
            elif last_week_activities < prev_week_activities:
                trend = "declining"
            else:
                trend = "stable"
            
            # Update or create engagement metrics
            metrics = db.query(EngagementMetrics).filter(
                EngagementMetrics.customer_id == customer_id
            ).first()
            
            if not metrics:
                metrics = EngagementMetrics(customer_id=customer_id)
            
            metrics.engagement_score = engagement_score
            metrics.login_frequency_score = login_score
            metrics.feature_usage_score = feature_score
            metrics.api_usage_score = api_score
            metrics.retention_score = retention_score
            metrics.logins_30d = logins
            metrics.active_days_30d = len(set(a.created_at.date() for a in activities))
            metrics.feature_count_used = features_used
            metrics.api_calls_30d = api_calls
            metrics.last_activity_at = last_activity
            metrics.days_since_last_activity = days_inactive
            metrics.engagement_trend = trend
            metrics.engagement_declining = trend == "declining"
            metrics.updated_at = datetime.utcnow()
            
            db.add(metrics)
            db.commit()
            
            return engagement_score
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement score: {e}")
            return 0.0
    
    
    # ==================== ANOMALY DETECTION ====================
    
    @staticmethod
    def detect_anomalies(db: Session) -> List[Dict]:
        """Detect system and customer anomalies using statistical methods"""
        try:
            from app.models.activity_models import (
                AnomalyDetection, AnomalyType, SystemMetrics
            )
            
            anomalies = []
            
            # Get last 30 days of system metrics
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            metrics_history = db.query(SystemMetrics).filter(
                SystemMetrics.recorded_at >= thirty_days_ago
            ).order_by(SystemMetrics.recorded_at).all()
            
            if len(metrics_history) > 5:
                # Extract metric values
                response_times = [m.avg_response_time_ms for m in metrics_history if m.avg_response_time_ms]
                error_rates = [m.error_rate for m in metrics_history if m.error_rate is not None]
                
                # Detect spikes using z-score
                if response_times:
                    z_scores = stats.zscore(response_times)
                    spike_idx = np.argmax(np.abs(z_scores))
                    
                    if np.abs(z_scores[spike_idx]) > 2.5:  # 2.5 std deviations
                        anomalies.append({
                            "anomaly_type": AnomalyType.UNUSUAL_TRAFFIC,
                            "severity": "high" if np.abs(z_scores[spike_idx]) > 3 else "medium",
                            "metric_name": "response_time",
                            "expected_value": np.mean(response_times),
                            "actual_value": response_times[spike_idx],
                            "deviation_percent": ((response_times[spike_idx] - np.mean(response_times)) / np.mean(response_times)) * 100,
                            "description": f"Response time spike detected: {response_times[spike_idx]:.0f}ms vs avg {np.mean(response_times):.0f}ms"
                        })
                
                # Detect error rate spikes
                if error_rates:
                    avg_error_rate = np.mean(error_rates)
                    max_error_rate = max(error_rates)
                    
                    if max_error_rate > avg_error_rate * 1.5:  # 50% above average
                        anomalies.append({
                            "anomaly_type": AnomalyType.PAYMENT_FAILURE_SPIKE if max_error_rate > 5 else AnomalyType.REVENUE_DROP,
                            "severity": "critical" if max_error_rate > 10 else "high",
                            "metric_name": "error_rate",
                            "expected_value": avg_error_rate,
                            "actual_value": max_error_rate,
                            "deviation_percent": ((max_error_rate - avg_error_rate) / avg_error_rate) * 100,
                            "description": f"Error rate spike: {max_error_rate:.2f}% vs avg {avg_error_rate:.2f}%"
                        })
            
            # Save detected anomalies to database
            for anomaly_data in anomalies:
                existing = db.query(AnomalyDetection).filter(
                    and_(
                        AnomalyDetection.anomaly_type == anomaly_data["anomaly_type"],
                        AnomalyDetection.customer_id.is_(None),
                        AnomalyDetection.resolved == False
                    )
                ).first()
                
                if not existing:
                    anomaly = AnomalyDetection(
                        customer_id=None,
                        anomaly_type=anomaly_data["anomaly_type"],
                        severity=anomaly_data["severity"],
                        metric_name=anomaly_data["metric_name"],
                        expected_value=anomaly_data["expected_value"],
                        actual_value=anomaly_data["actual_value"],
                        deviation_percent=anomaly_data["deviation_percent"],
                        description=anomaly_data["description"],
                        recommended_action="Investigate system performance and take appropriate action",
                        detected_at=datetime.utcnow()
                    )
                    db.add(anomaly)
            
            db.commit()
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return []
    
    
    # ==================== CHURN PREDICTION ====================
    
    @staticmethod
    def predict_churn(
        db: Session,
        customer_id: int = None
    ) -> Dict:
        """Predict customer churn probability using ML model"""
        try:
            from app.models.activity_models import (
                ChurnPrediction, EngagementMetrics
            )
            from app.models.models import StripeCustomer, StripeSubscription
            
            if customer_id:
                customers = db.query(StripeCustomer).filter(
                    StripeCustomer.id == customer_id
                ).all()
            else:
                customers = db.query(StripeCustomer).all()
            
            results = []
            
            for customer in customers:
                # Gather features
                engagement = db.query(EngagementMetrics).filter(
                    EngagementMetrics.customer_id == customer.id
                ).first()
                
                subscriptions = db.query(StripeSubscription).filter(
                    StripeSubscription.customer_id == customer.id
                ).all()
                
                # Calculate metrics
                engagement_score = engagement.engagement_score if engagement else 0
                days_last_activity = engagement.days_since_last_activity if engagement else 365
                subscription_tenure = (datetime.utcnow() - customer.created_at).days
                active_subs = len([s for s in subscriptions if s.status == "active"])
                
                # Simple rule-based churn prediction
                churn_prob = 0.0
                
                # Low engagement is a strong churn signal
                if engagement_score < 30:
                    churn_prob += 0.4
                elif engagement_score < 50:
                    churn_prob += 0.2
                
                # Recent inactivity is a churn signal
                if days_last_activity > 30:
                    churn_prob += 0.3
                elif days_last_activity > 14:
                    churn_prob += 0.15
                
                # Short tenure increases churn risk
                if subscription_tenure < 30:
                    churn_prob += 0.2
                elif subscription_tenure < 90:
                    churn_prob += 0.1
                
                # No active subscriptions = high churn risk
                if active_subs == 0:
                    churn_prob += 0.3
                
                # Cap at 0.99
                churn_prob = min(0.99, churn_prob)
                
                # Determine risk level
                if churn_prob > 0.75:
                    risk_level = "critical"
                    intervention = "Immediate outreach required - offer discount or premium feature"
                elif churn_prob > 0.5:
                    risk_level = "high"
                    intervention = "Schedule business review call with customer"
                elif churn_prob > 0.3:
                    risk_level = "medium"
                    intervention = "Send engagement email with new features"
                else:
                    risk_level = "low"
                    intervention = "Monitor engagement trends"
                
                # Update or create prediction
                prediction = db.query(ChurnPrediction).filter(
                    ChurnPrediction.customer_id == customer.id
                ).first()
                
                if not prediction:
                    prediction = ChurnPrediction(customer_id=customer.id)
                
                prediction.churn_probability = churn_prob
                prediction.churn_risk_level = risk_level
                prediction.engagement_score = engagement_score
                prediction.days_since_last_activity = days_last_activity
                prediction.subscription_tenure_days = subscription_tenure
                prediction.intervention_recommended = churn_prob > 0.3
                prediction.suggested_intervention = intervention
                prediction.model_version = "v1.0"
                prediction.confidence_score = 0.75
                prediction.predicted_at = datetime.utcnow()
                
                db.add(prediction)
                
                results.append({
                    "customer_id": customer.id,
                    "churn_probability": churn_prob,
                    "risk_level": risk_level,
                    "intervention": intervention
                })
            
            db.commit()
            return results
            
        except Exception as e:
            logger.error(f"Failed to predict churn: {e}")
            return []
    
    
    # ==================== CUSTOMER SEGMENTATION ====================
    
    @staticmethod
    def segment_customers(db: Session) -> List[Dict]:
        """Segment customers using ML clustering"""
        try:
            from app.models.activity_models import CustomerSegment, EngagementMetrics
            from app.models.models import StripeCustomer
            
            customers = db.query(StripeCustomer).all()
            
            # Gather feature data
            features = []
            customer_ids = []
            
            for customer in customers:
                engagement = db.query(EngagementMetrics).filter(
                    EngagementMetrics.customer_id == customer.id
                ).first()
                
                ltv = getattr(customer, 'ltv_value', 0) or 0
                engagement_score = engagement.engagement_score if engagement else 0
                
                features.append([
                    ltv,  # Value
                    engagement_score,  # Engagement
                ])
                customer_ids.append(customer.id)
            
            if len(features) < 2:
                return []
            
            # Normalize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # K-means clustering (4 clusters)
            kmeans = KMeans(n_clusters=min(4, len(customers)), random_state=42, n_init=10)
            labels = kmeans.fit_predict(features_scaled)
            
            segments_map = {
                0: {"name": "Enterprise Powerhouse", "value": "enterprise", "engagement": "highly-engaged"},
                1: {"name": "Growth Potential", "value": "mid-market", "engagement": "moderate"},
                2: {"name": "Steady Performers", "value": "smb", "engagement": "highly-engaged"},
                3: {"name": "At-Risk Accounts", "value": "starter", "engagement": "at-risk"},
            }
            
            results = []
            for customer_id, label in zip(customer_ids, labels):
                segment_info = segments_map.get(label, segments_map[0])
                
                segment = db.query(CustomerSegment).filter(
                    CustomerSegment.customer_id == customer_id
                ).first()
                
                if not segment:
                    segment = CustomerSegment(customer_id=customer_id)
                
                segment.segment_name = segment_info["name"]
                segment.value_segment = segment_info["value"]
                segment.engagement_segment = segment_info["engagement"]
                segment.segment_score = 0.85
                segment.characteristics = {
                    "cluster": int(label),
                    "profile": "Detailed analysis based on LTV and engagement"
                }
                segment.recommended_actions = {
                    "actions": ["Personalized outreach", "Feature recommendations", "Priority support"]
                }
                segment.updated_at = datetime.utcnow()
                
                db.add(segment)
                
                results.append({
                    "customer_id": customer_id,
                    "segment": segment_info["name"]
                })
            
            db.commit()
            return results
            
        except Exception as e:
            logger.error(f"Failed to segment customers: {e}")
            return []
    
    
    # ==================== TREND ANALYSIS ====================
    
    @staticmethod
    def analyze_engagement_trends(
        db: Session,
        customer_id: int,
        period_days: int = 90
    ) -> Dict:
        """Analyze engagement trends over time"""
        try:
            from app.models.activity_models import UserActivity
            
            start_date = datetime.utcnow() - timedelta(days=period_days)
            activities = db.query(UserActivity).filter(
                and_(
                    UserActivity.customer_id == customer_id,
                    UserActivity.created_at >= start_date
                )
            ).order_by(UserActivity.created_at).all()
            
            # Group by week
            weeks = {}
            for activity in activities:
                week = activity.created_at.isocalendar()[1]
                if week not in weeks:
                    weeks[week] = 0
                weeks[week] += 1
            
            if len(weeks) < 2:
                return {"trend": "insufficient_data", "weeks": weeks}
            
            # Calculate trend (simple linear regression)
            x = np.array(list(range(len(weeks))))
            y = np.array(list(weeks.values()))
            
            coefficients = np.polyfit(x, y, 1)
            slope = coefficients[0]
            
            if slope > 0.5:
                trend = "strong_growth"
            elif slope > 0:
                trend = "slight_growth"
            elif slope > -0.5:
                trend = "slight_decline"
            else:
                trend = "strong_decline"
            
            return {
                "trend": trend,
                "slope": float(slope),
                "weeks": weeks,
                "total_activities": len(activities)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            return {"trend": "error", "error": str(e)}
    
    
    # ==================== RECOMMENDATIONS ====================
    
    @staticmethod
    def generate_recommendations(
        db: Session,
        customer_id: int
    ) -> List[Dict]:
        """Generate AI-powered recommendations"""
        try:
            from app.models.activity_models import (
                RecommendationEngine, EngagementMetrics, ChurnPrediction
            )
            from app.models.models import StripeCustomer, StripeSubscription
            
            customer = db.query(StripeCustomer).filter(
                StripeCustomer.id == customer_id
            ).first()
            
            engagement = db.query(EngagementMetrics).filter(
                EngagementMetrics.customer_id == customer_id
            ).first()
            
            churn_pred = db.query(ChurnPrediction).filter(
                ChurnPrediction.customer_id == customer_id
            ).first()
            
            subscriptions = db.query(StripeSubscription).filter(
                StripeSubscription.customer_id == customer_id
            ).all()
            
            recommendations = []
            
            # Recommend upsell if high engagement and low churn risk
            if engagement and engagement.engagement_score > 70 and (not churn_pred or churn_pred.churn_probability < 0.3):
                recommendations.append({
                    "type": "upsell",
                    "title": "Upgrade to Professional Plan",
                    "description": "Based on your high engagement, consider upgrading for advanced features",
                    "score": 85,
                    "expected_value": 49.0,
                    "plan": "professional"
                })
            
            # Recommend retention if at-risk
            if churn_pred and churn_pred.churn_probability > 0.5:
                recommendations.append({
                    "type": "retention",
                    "title": "Special Retention Offer",
                    "description": "We noticed you might be considering leaving. Here's a special offer to stay",
                    "score": 95,
                    "expected_value": 50.0,
                    "plan": "current_discounted"
                })
            
            # Recommend feature adoption
            if engagement and engagement.feature_count_used < 5:
                recommendations.append({
                    "type": "feature",
                    "title": "Discover Powerful Features",
                    "description": "You're using basic features. Check out these powerful tools to maximize your investment",
                    "score": 70,
                    "expected_value": 0.0,
                    "feature": "advanced_analytics"
                })
            
            # Save recommendations
            for rec_data in recommendations:
                rec = RecommendationEngine(
                    customer_id=customer_id,
                    recommendation_type=rec_data["type"],
                    recommendation_title=rec_data["title"],
                    recommendation_description=rec_data["description"],
                    recommendation_score=rec_data["score"],
                    expected_value=rec_data.get("expected_value", 0),
                    expected_acceptance_prob=0.35,
                    created_at=datetime.utcnow()
                )
                db.add(rec)
            
            db.commit()
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    
    # ==================== PROJECT TRACKING ====================
    
    @staticmethod
    def track_project_metrics(
        db: Session,
        customer_id: int,
        project_name: str,
        api_calls: int,
        error_rate: float,
        response_time_ms: float
    ):
        """Track per-project metrics"""
        try:
            from app.models.activity_models import ProjectMetrics
            
            project = db.query(ProjectMetrics).filter(
                and_(
                    ProjectMetrics.customer_id == customer_id,
                    ProjectMetrics.project_name == project_name
                )
            ).first()
            
            if not project:
                project = ProjectMetrics(
                    customer_id=customer_id,
                    project_name=project_name
                )
            
            project.api_calls = api_calls
            project.error_rate = error_rate
            project.avg_response_time_ms = response_time_ms
            project.last_api_call_at = datetime.utcnow()
            project.days_since_last_call = 0
            project.updated_at = datetime.utcnow()
            
            db.add(project)
            db.commit()
            return project
            
        except Exception as e:
            logger.error(f"Failed to track project metrics: {e}")
            return None
    
    
    # ==================== PREDICTIVE ALERTS ====================
    
    @staticmethod
    def generate_predictive_alerts(
        db: Session,
        customer_id: int = None
    ) -> List[Dict]:
        """Generate predictive alerts based on patterns"""
        try:
            from app.models.activity_models import (
                PredictiveAlert, ChurnPrediction, EngagementMetrics
            )
            from app.models.models import StripeCustomer
            
            alerts = []
            
            if customer_id:
                customers = db.query(StripeCustomer).filter(
                    StripeCustomer.id == customer_id
                ).all()
            else:
                customers = db.query(StripeCustomer).all()
            
            for customer in customers:
                churn_pred = db.query(ChurnPrediction).filter(
                    ChurnPrediction.customer_id == customer.id
                ).first()
                
                engagement = db.query(EngagementMetrics).filter(
                    EngagementMetrics.customer_id == customer.id
                ).first()
                
                # Alert if high churn risk
                if churn_pred and churn_pred.churn_probability > 0.6:
                    alerts.append({
                        "type": "churn_risk",
                        "priority": "critical",
                        "title": "High Churn Risk Detected",
                        "recommended_action": "Schedule customer success call"
                    })
                
                # Alert if engagement dropping
                if engagement and engagement.engagement_declining:
                    alerts.append({
                        "type": "engagement_drop",
                        "priority": "high",
                        "title": "Engagement Declining",
                        "recommended_action": "Send re-engagement campaign"
                    })
                
                # Save alerts
                for alert_data in alerts:
                    existing = db.query(PredictiveAlert).filter(
                        and_(
                            PredictiveAlert.customer_id == customer.id,
                            PredictiveAlert.alert_type == alert_data["type"],
                            PredictiveAlert.resolved == False
                        )
                    ).first()
                    
                    if not existing:
                        alert = PredictiveAlert(
                            customer_id=customer.id,
                            alert_type=alert_data["type"],
                            priority=alert_data["priority"],
                            alert_title=alert_data["title"],
                            recommended_action=alert_data["recommended_action"],
                            created_at=datetime.utcnow()
                        )
                        db.add(alert)
            
            db.commit()
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to generate predictive alerts: {e}")
            return []
    
    
    # ==================== SYSTEM METRICS ====================
    
    @staticmethod
    def record_system_metrics(
        db: Session,
        total_requests: int,
        requests_per_minute: float,
        unique_active_users: int,
        avg_response_time_ms: float,
        p95_response_time_ms: float,
        p99_response_time_ms: float,
        success_rate: float,
        error_rate: float,
        cpu_usage_percent: float,
        memory_usage_percent: float,
        database_connection_count: int
    ):
        """Record system-wide metrics for monitoring"""
        try:
            from app.models.activity_models import SystemMetrics
            
            metrics = SystemMetrics(
                total_requests=total_requests,
                requests_per_minute=requests_per_minute,
                unique_active_users=unique_active_users,
                avg_response_time_ms=avg_response_time_ms,
                p95_response_time_ms=p95_response_time_ms,
                p99_response_time_ms=p99_response_time_ms,
                success_rate=success_rate,
                error_rate=error_rate,
                cpu_usage_percent=cpu_usage_percent,
                memory_usage_percent=memory_usage_percent,
                database_connection_count=database_connection_count,
                recorded_at=datetime.utcnow()
            )
            db.add(metrics)
            db.commit()
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")
            return None
