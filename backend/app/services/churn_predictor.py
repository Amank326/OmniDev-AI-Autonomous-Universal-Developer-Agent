"""
Phase 17: Churn Prediction & Prevention
- Random Forest classification for churn prediction
- At-risk customer identification
- Retention intervention recommendations
- Churn score tracking
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChurnPredictor:
    """ML-based churn prediction and prevention"""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize churn predictor"""
        self.db_session = db_session
        self.churn_model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.threshold = 0.5  # 50% churn probability threshold

    def train_churn_model(
        self,
        training_data: List[Dict[str, Any]],
        positive_class_weight: float = 2.0
    ) -> Dict[str, Any]:
        """
        Train Random Forest classifier for churn prediction
        
        Predicts: Will customer churn in next 30 days? (Binary classification)
        
        Args:
            training_data: Historical subscription data with churn labels
            positive_class_weight: Weight for churn class (handle imbalance)
        
        Returns:
            Model performance metrics
        """
        try:
            if len(training_data) < 50:
                return {"error": "Insufficient training data", "min_required": 50, "available": len(training_data)}
            
            df = pd.DataFrame(training_data)
            
            # Feature engineering
            X = df[[
                'subscription_age_days',
                'monthly_price',
                'usage_count_last_30d',
                'days_since_last_usage',
                'support_tickets_last_30d',
                'satisfaction_score',
                'payment_failures',
                'feature_adoption_rate',
                'agent_rating',
                'upgrade_attempts'
            ]].values
            
            y = df['churned'].values  # 1 = churned, 0 = retained
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Calculate class weights
            churn_count = np.sum(y)
            retention_count = len(y) - churn_count
            churn_weight = positive_class_weight
            retention_weight = 1.0
            
            # Train Random Forest
            self.churn_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=10,
                class_weight={0: retention_weight, 1: churn_weight},
                random_state=42,
                n_jobs=-1
            )
            self.churn_model.fit(X_scaled, y)
            
            # Store feature importance
            feature_names = [
                'subscription_age', 'monthly_price', 'usage_count', 'days_since_usage',
                'support_tickets', 'satisfaction', 'payment_failures', 'feature_adoption',
                'agent_rating', 'upgrade_attempts'
            ]
            self.feature_importance = dict(zip(feature_names, self.churn_model.feature_importances_))
            
            # Calculate performance metrics
            train_score = self.churn_model.score(X_scaled, y)
            
            return {
                "status": "trained",
                "accuracy": float(train_score),
                "feature_importance": {k: float(v) for k, v in self.feature_importance.items()},
                "training_samples": len(training_data),
                "churn_rate": float(churn_count / len(y)),
                "top_features": sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        except Exception as e:
            logger.error(f"Error training churn model: {str(e)}")
            return {"error": str(e)}

    def predict_churn_probability(
        self,
        user_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Predict churn probability for user in next 30 days
        
        Args:
            user_features: User subscription and engagement metrics
        
        Returns:
            Churn probability and risk level
        """
        try:
            if self.churn_model is None:
                return {"error": "Model not trained"}
            
            features = np.array([[
                user_features.get('subscription_age_days', 0),
                user_features.get('monthly_price', 0),
                user_features.get('usage_count_last_30d', 0),
                user_features.get('days_since_last_usage', 0),
                user_features.get('support_tickets_last_30d', 0),
                user_features.get('satisfaction_score', 5),
                user_features.get('payment_failures', 0),
                user_features.get('feature_adoption_rate', 0),
                user_features.get('agent_rating', 4),
                user_features.get('upgrade_attempts', 0)
            ]])
            
            features_scaled = self.scaler.transform(features)
            
            # Get prediction probabilities
            probabilities = self.churn_model.predict_proba(features_scaled)[0]
            churn_probability = probabilities[1]  # Probability of churn
            
            # Determine risk level
            if churn_probability > 0.7:
                risk_level = "critical"
            elif churn_probability > 0.5:
                risk_level = "high"
            elif churn_probability > 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "user_id": user_features.get('user_id'),
                "churn_probability": float(churn_probability),
                "risk_level": risk_level,
                "will_churn": churn_probability > self.threshold,
                "retention_probability": float(1 - churn_probability),
                "days_until_churn": self._estimate_days_to_churn(churn_probability)
            }
        
        except Exception as e:
            logger.error(f"Error predicting churn: {str(e)}")
            return {"error": str(e)}

    def identify_at_risk_users(
        self,
        users_data: List[Dict[str, Any]],
        risk_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Identify users at risk of churning
        
        Args:
            users_data: List of user subscription data
            risk_threshold: Probability threshold for at-risk classification
        
        Returns:
            At-risk users segmented by risk level
        """
        try:
            if self.churn_model is None:
                return {"error": "Model not trained"}
            
            at_risk_users = {"critical": [], "high": [], "medium": []}
            total_risk_score = 0
            
            for user_data in users_data:
                prediction = self.predict_churn_probability(user_data)
                
                if "error" in prediction:
                    continue
                
                if prediction["churn_probability"] > risk_threshold:
                    risk_info = {
                        "user_id": user_data.get("user_id"),
                        "churn_probability": prediction["churn_probability"],
                        "risk_level": prediction["risk_level"],
                        "retention_value": user_data.get("monthly_price", 0),
                        "key_risk_factors": self._identify_risk_factors(user_data)
                    }
                    
                    if prediction["risk_level"] == "critical":
                        at_risk_users["critical"].append(risk_info)
                    elif prediction["risk_level"] == "high":
                        at_risk_users["high"].append(risk_info)
                    else:
                        at_risk_users["medium"].append(risk_info)
                    
                    total_risk_score += prediction["churn_probability"]
            
            total_users = len(users_data)
            at_risk_count = len(at_risk_users["critical"]) + len(at_risk_users["high"]) + len(at_risk_users["medium"])
            
            return {
                "total_users": total_users,
                "at_risk_count": at_risk_count,
                "at_risk_percentage": (at_risk_count / total_users * 100) if total_users > 0 else 0,
                "avg_churn_probability": (total_risk_score / at_risk_count) if at_risk_count > 0 else 0,
                "risk_distribution": at_risk_users,
                "potential_mrr_at_risk": sum(u["retention_value"] for segment in at_risk_users.values() for u in segment)
            }
        
        except Exception as e:
            logger.error(f"Error identifying at-risk users: {str(e)}")
            return {"error": str(e)}

    def generate_retention_interventions(
        self,
        user_data: Dict[str, Any],
        churn_probability: float
    ) -> Dict[str, Any]:
        """
        Generate targeted retention interventions
        
        Args:
            user_data: User profile and subscription data
            churn_probability: Predicted churn probability
        
        Returns:
            Personalized retention recommendations
        """
        try:
            interventions = []
            urgency = "high" if churn_probability > 0.7 else "medium"
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(user_data)
            
            # Generate interventions based on risk factors
            if "low_usage" in risk_factors:
                interventions.append({
                    "type": "engagement",
                    "action": "Send usage tips email",
                    "content": "Help user maximize agent features",
                    "priority": "high"
                })
            
            if "payment_issues" in risk_factors:
                interventions.append({
                    "type": "payment",
                    "action": "Resolve payment method",
                    "content": "Update payment info or offer assistance",
                    "priority": "critical"
                })
            
            if "satisfaction_low" in risk_factors:
                interventions.append({
                    "type": "support",
                    "action": "Proactive support outreach",
                    "content": "Offer free support or consulting session",
                    "priority": "high"
                })
            
            if "agent_downgrade_candidate" in risk_factors:
                interventions.append({
                    "type": "pricing",
                    "action": "Offer tier downgrade",
                    "content": "Suggest lower-cost plan to retain customer",
                    "priority": "medium"
                })
            
            if not interventions:
                interventions.append({
                    "type": "general",
                    "action": "Check-in call",
                    "content": "Schedule brief call to understand needs",
                    "priority": "medium"
                })
            
            # Sort by priority
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            interventions.sort(key=lambda x: priority_order.get(x["priority"], 999))
            
            return {
                "user_id": user_data.get("user_id"),
                "churn_probability": churn_probability,
                "urgency": urgency,
                "risk_factors": risk_factors,
                "interventions": interventions,
                "recommended_discount": self._calculate_retention_discount(churn_probability),
                "intervention_window": "7 days"  # Act within 7 days
            }
        
        except Exception as e:
            logger.error(f"Error generating interventions: {str(e)}")
            return {"error": str(e)}

    def track_churn_metrics(
        self,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Track churn metrics over time period
        
        Args:
            time_period_days: Historical window
        
        Returns:
            Churn metrics and trends
        """
        try:
            # Would query actual data from database
            # Mock implementation
            
            total_subscriptions = 1000
            churned_subscriptions = 150
            churn_rate = churned_subscriptions / total_subscriptions
            
            # Cohort analysis (by signup month)
            cohorts = {
                "0-30_days": {"churn_rate": 0.15, "count": 200},
                "31-90_days": {"churn_rate": 0.10, "count": 300},
                "91-180_days": {"churn_rate": 0.08, "count": 250},
                "180+_days": {"churn_rate": 0.05, "count": 250}
            }
            
            # Risk distribution
            risk_dist = {
                "critical": 50,
                "high": 100,
                "medium": 150,
                "low": 700
            }
            
            return {
                "period_days": time_period_days,
                "total_subscriptions": total_subscriptions,
                "churned_count": churned_subscriptions,
                "churn_rate": float(churn_rate),
                "mrr_at_risk": 15000.0,  # Mock
                "cohort_analysis": cohorts,
                "risk_distribution": risk_dist,
                "trend": "improving"  # Compare to previous period
            }
        
        except Exception as e:
            logger.error(f"Error tracking churn metrics: {str(e)}")
            return {"error": str(e)}

    def get_churn_insights(
        self,
        organization_level: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive churn insights
        
        Args:
            organization_level: True for org-wide, False for agent-specific
        
        Returns:
            Actionable insights and recommendations
        """
        try:
            metrics = self.track_churn_metrics()
            
            insights = {
                "churn_rate": metrics.get("churn_rate", 0),
                "churn_rate_interpretation": self._interpret_churn_rate(metrics.get("churn_rate", 0)),
                "at_risk_value": metrics.get("mrr_at_risk", 0),
                "highest_risk_cohort": self._identify_highest_risk_cohort(metrics.get("cohort_analysis", {})),
                "feature_importance": self.feature_importance,
                "recommendations": self._generate_churn_recommendations(metrics)
            }
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generating churn insights: {str(e)}")
            return {"error": str(e)}

    # Helper methods
    
    def _identify_risk_factors(
        self,
        user_data: Dict[str, Any]
    ) -> List[str]:
        """Identify risk factors for user churn"""
        risk_factors = []
        
        if user_data.get("usage_count_last_30d", 0) < 5:
            risk_factors.append("low_usage")
        
        if user_data.get("payment_failures", 0) > 0:
            risk_factors.append("payment_issues")
        
        if user_data.get("satisfaction_score", 5) < 3:
            risk_factors.append("satisfaction_low")
        
        if user_data.get("support_tickets_last_30d", 0) > 5:
            risk_factors.append("high_support_load")
        
        if user_data.get("subscription_age_days", 0) < 30:
            risk_factors.append("new_customer")
        
        if user_data.get("monthly_price", 0) > 500:
            risk_factors.append("agent_downgrade_candidate")
        
        return risk_factors

    def _estimate_days_to_churn(
        self,
        churn_probability: float
    ) -> int:
        """Estimate days until churn if probability high"""
        if churn_probability < 0.3:
            return 999  # Very unlikely
        elif churn_probability < 0.5:
            return 30
        elif churn_probability < 0.7:
            return 15
        else:
            return 7  # Critical - act within 7 days

    def _calculate_retention_discount(
        self,
        churn_probability: float
    ) -> float:
        """Calculate optimal discount for retention"""
        if churn_probability > 0.7:
            return 0.25  # 25% discount
        elif churn_probability > 0.5:
            return 0.15  # 15% discount
        else:
            return 0.0  # No discount needed

    def _interpret_churn_rate(self, churn_rate: float) -> str:
        """Interpret churn rate"""
        if churn_rate < 0.05:
            return "Excellent retention"
        elif churn_rate < 0.10:
            return "Good retention"
        elif churn_rate < 0.15:
            return "Average retention"
        else:
            return "High churn - urgent action needed"

    def _identify_highest_risk_cohort(
        self,
        cohorts: Dict[str, Any]
    ) -> str:
        """Identify cohort with highest churn"""
        if not cohorts:
            return "unknown"
        
        return max(cohorts.items(), key=lambda x: x[1].get("churn_rate", 0))[0]

    def _generate_churn_recommendations(
        self,
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate churn reduction recommendations"""
        recommendations = []
        churn_rate = metrics.get("churn_rate", 0)
        
        if churn_rate > 0.15:
            recommendations.append("High churn rate detected. Launch retention campaign immediately.")
            recommendations.append("Analyze churned customers for common reasons.")
        
        highest_risk = metrics.get("highest_risk_cohort", "")
        if highest_risk and "0-30_days" in highest_risk:
            recommendations.append("Focus on onboarding experience for new customers.")
            recommendations.append("Implement 14-day check-in with new signups.")
        
        if metrics.get("mrr_at_risk", 0) > 10000:
            recommendations.append(f"${metrics['mrr_at_risk']:,.0f} MRR at risk. Prioritize retention efforts.")
        
        recommendations.append("Set up automated churn alerts for high-risk users.")
        recommendations.append("A/B test retention interventions.")
        
        return recommendations
