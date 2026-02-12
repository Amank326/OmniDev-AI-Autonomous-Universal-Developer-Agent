"""
ML Dunning Service - Machine learning powered payment recovery optimization
Predicts recovery success, optimizes retry strategies, identifies patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

class RecoveryOutcome(str, Enum):
    """Recovery prediction outcomes"""
    HIGH_PROBABILITY = "high"      # >80% recovery chance
    MEDIUM_PROBABILITY = "medium"  # 50-80% recovery chance
    LOW_PROBABILITY = "low"        # <50% recovery chance


class MLDunningService:
    """
    Service for ML-powered payment recovery prediction and optimization.
    Uses historical data to optimize dunning strategies and recovery outcomes.
    """
    
    def __init__(self):
        """Initialize ML dunning service"""
        self.prediction_models = {}
        self.recovery_patterns = {}
        self.strategy_performance = {}
        self.feature_importance = {}
        self.historical_outcomes = {}
        
        # Initialize with default feature weights
        self._initialize_feature_weights()
    
    def _initialize_feature_weights(self):
        """Initialize default feature importance weights"""
        self.feature_importance = {
            "days_since_failure": 0.18,
            "customer_age": 0.15,
            "payment_history": 0.16,
            "previous_successful_recovery": 0.14,
            "subscription_tier": 0.12,
            "payment_method_reliability": 0.13,
            "customer_engagement": 0.12,
        }
    
    def predict_recovery_success(
        self,
        failure_data: Dict,
        customer_profile: Dict,
    ) -> Dict:
        """
        Predict likelihood of successful payment recovery.
        Uses ML features to score recovery probability.
        
        Args:
            failure_data: Payment failure details
            customer_profile: Customer history and characteristics
        
        Returns:
            Recovery probability and recommendation
        """
        # Extract features
        features = self._extract_features(failure_data, customer_profile)
        
        # Calculate recovery score (0-100)
        score = self._calculate_recovery_score(features)
        
        # Determine outcome probability
        if score >= 80:
            outcome = RecoveryOutcome.HIGH_PROBABILITY
            estimated_recovery_rate = 0.75  # 75% estimated recovery
        elif score >= 50:
            outcome = RecoveryOutcome.MEDIUM_PROBABILITY
            estimated_recovery_rate = 0.45  # 45% estimated recovery
        else:
            outcome = RecoveryOutcome.LOW_PROBABILITY
            estimated_recovery_rate = 0.15  # 15% estimated recovery
        
        # Recommend strategy
        strategy = self._recommend_strategy(score, customer_profile)
        
        # Estimate recovery amount
        failure_amount = failure_data.get("amount", 0)
        expected_recovery = failure_amount * estimated_recovery_rate
        
        prediction = {
            "failure_id": failure_data.get("failure_id", "unknown"),
            "recovery_score": score,
            "outcome_probability": outcome.value,
            "estimated_recovery_rate": round(estimated_recovery_rate, 2),
            "expected_recovery_amount": round(expected_recovery, 2),
            "recommended_strategy": strategy,
            "feature_scores": features,
            "confidence": self._calculate_confidence(score),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Store for training
        self.historical_outcomes[failure_data.get("failure_id", "")] = prediction
        
        return prediction
    
    def _extract_features(
        self,
        failure_data: Dict,
        customer_profile: Dict,
    ) -> Dict:
        """Extract features for ML model"""
        now = datetime.utcnow()
        
        # Time-based features
        failure_date = datetime.fromisoformat(failure_data.get("failure_date", now.isoformat()))
        days_since_failure = (now - failure_date).days
        
        # Customer features
        account_created = customer_profile.get("account_created", now.isoformat())
        account_age_days = (now - datetime.fromisoformat(account_created)).days
        
        # Payment history (0-1 score)
        successful_payments = customer_profile.get("successful_payments", 0)
        failed_payments = customer_profile.get("failed_payments", 0)
        total_payments = successful_payments + failed_payments
        payment_success_rate = (
            successful_payments / total_payments if total_payments > 0 else 0.5
        )
        
        # Previous recovery attempt (0-1 score)
        previous_recovery_success = 1.0 if customer_profile.get(
            "previous_recovery_success", False
        ) else 0.0
        
        # Subscription tier (0-1 scale)
        tier_scores = {
            "free": 0.2,
            "basic": 0.4,
            "pro": 0.7,
            "enterprise": 0.95,
        }
        tier = customer_profile.get("subscription_tier", "basic").lower()
        subscription_tier_score = tier_scores.get(tier, 0.5)
        
        # Payment method reliability (0-1 score)
        payment_method = failure_data.get("payment_method", "credit_card")
        method_reliability = {
            "credit_card": 0.85,
            "debit_card": 0.80,
            "bank_transfer": 0.92,
            "paypal": 0.88,
        }
        method_reliability_score = method_reliability.get(payment_method, 0.75)
        
        # Customer engagement (0-1 score)
        engagement = customer_profile.get("engagement_score", 0.5)
        
        features = {
            "days_since_failure": min(days_since_failure / 30, 1.0),  # Normalize to 0-1
            "customer_age": min(account_age_days / 365, 1.0),  # Normalize to 0-1
            "payment_history": payment_success_rate,
            "previous_successful_recovery": previous_recovery_success,
            "subscription_tier": subscription_tier_score,
            "payment_method_reliability": method_reliability_score,
            "customer_engagement": engagement,
        }
        
        return features
    
    def _calculate_recovery_score(self, features: Dict) -> float:
        """Calculate recovery probability score (0-100)"""
        score = 0.0
        
        for feature_name, weight in self.feature_importance.items():
            feature_value = features.get(feature_name, 0.5)
            score += (feature_value * weight) * 100
        
        return min(100, max(0, score))
    
    def _recommend_strategy(self, score: float, customer_profile: Dict) -> str:
        """Recommend optimal dunning strategy"""
        if score >= 85:
            return "aggressive"  # High recovery rate, can be aggressive
        elif score >= 70:
            return "moderate"  # Good recovery rate, balanced approach
        elif score >= 50:
            return "conservative"  # Lower recovery rate, gentle approach
        else:
            return "targeted"  # Very low rate, focus on highest value customers
    
    def _calculate_confidence(self, score: float) -> float:
        """Calculate model confidence (0-1)"""
        # Higher confidence near extremes
        distance_from_center = abs(score - 50)
        confidence = 0.5 + (distance_from_center / 100) * 0.5
        return round(confidence, 2)
    
    def optimize_retry_strategy(
        self,
        failure_data: Dict,
        customer_profile: Dict,
        current_strategy: str,
    ) -> Dict:
        """
        Optimize retry strategy based on customer and failure characteristics.
        Adjusts retry intervals and notification approach.
        
        Args:
            failure_data: Payment failure details
            customer_profile: Customer history
            current_strategy: Current dunning strategy
        
        Returns:
            Optimized retry strategy with parameters
        """
        # Get recovery prediction
        prediction = self.predict_recovery_success(failure_data, customer_profile)
        score = prediction["recovery_score"]
        
        # Optimize retry intervals based on score and customer
        if score >= 80:
            retry_intervals = [1, 2, 3, 5, 7]  # More frequent for high recovery
            escalation_aggressiveness = "aggressive"
        elif score >= 50:
            retry_intervals = [3, 7, 14, 21, 30]  # Moderate intervals
            escalation_aggressiveness = "moderate"
        else:
            retry_intervals = [7, 21, 60]  # Infrequent for low recovery
            escalation_aggressiveness = "gentle"
        
        # Notification strategy optimization
        notification_strategy = self._optimize_notifications(
            score, 
            customer_profile
        )
        
        # Email tone optimization
        email_tone = self._optimize_email_tone(score, customer_profile)
        
        optimization = {
            "failure_id": failure_data.get("failure_id"),
            "recommended_strategy": prediction["recommended_strategy"],
            "previous_strategy": current_strategy,
            "optimization_reason": f"Score: {score:.1f}",
            "retry_intervals": retry_intervals,
            "escalation_aggressiveness": escalation_aggressiveness,
            "notification_strategy": notification_strategy,
            "email_tone": email_tone,
            "expected_improvement": self._calculate_expected_improvement(
                current_strategy, 
                prediction["recommended_strategy"]
            ),
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        return optimization
    
    def _optimize_notifications(self, score: float, customer_profile: Dict) -> Dict:
        """Optimize notification approach"""
        if score >= 80:
            return {
                "frequency": "frequent",
                "channels": ["email", "sms", "in_app"],
                "urgency": "high",
            }
        elif score >= 50:
            return {
                "frequency": "moderate",
                "channels": ["email", "in_app"],
                "urgency": "medium",
            }
        else:
            return {
                "frequency": "infrequent",
                "channels": ["email"],
                "urgency": "low",
            }
    
    def _optimize_email_tone(self, score: float, customer_profile: Dict) -> str:
        """Optimize email tone based on recovery likelihood"""
        if score >= 80:
            return "urgent"  # "Payment is needed now"
        elif score >= 50:
            return "friendly"  # "We noticed a payment issue"
        else:
            return "supportive"  # "We're here to help"
    
    def _calculate_expected_improvement(
        self,
        current_strategy: str,
        recommended_strategy: str,
    ) -> float:
        """Calculate expected improvement in recovery rate"""
        current_recovery = {
            "aggressive": 0.65,
            "moderate": 0.50,
            "conservative": 0.35,
            "targeted": 0.55,
        }
        
        recommended_recovery = {
            "aggressive": 0.65,
            "moderate": 0.50,
            "conservative": 0.35,
            "targeted": 0.55,
        }
        
        current = current_recovery.get(current_strategy, 0.5)
        recommended = recommended_recovery.get(recommended_strategy, 0.5)
        
        improvement = (recommended - current) / current if current > 0 else 0
        return round(improvement * 100, 1)  # Return as percentage
    
    def identify_recovery_patterns(
        self,
        num_failures: int = 100,
    ) -> Dict:
        """
        Identify patterns in successful vs failed recovery attempts.
        Discovers what characteristics predict recovery success.
        
        Args:
            num_failures: Number of recent failures to analyze
        
        Returns:
            Pattern analysis and insights
        """
        # Analyze historical outcomes
        outcomes = list(self.historical_outcomes.values())[:num_failures]
        
        if not outcomes:
            return {"error": "No historical data available"}
        
        successful = [o for o in outcomes if o["outcome_probability"] == "high"]
        failed = [o for o in outcomes if o["outcome_probability"] == "low"]
        
        success_rate = len(successful) / len(outcomes) if outcomes else 0
        
        # Feature pattern analysis
        successful_features = [o.get("feature_scores", {}) for o in successful]
        failed_features = [o.get("feature_scores", {}) for o in failed]
        
        patterns = {
            "total_analyzed": len(outcomes),
            "successful_recoveries": len(successful),
            "failed_recoveries": len(failed),
            "overall_success_rate": round(success_rate, 2),
            "best_features": self._rank_features(successful_features),
            "worst_features": self._rank_features(failed_features),
            "strategy_performance": self._analyze_strategy_performance(),
            "temporal_patterns": self._identify_temporal_patterns(),
        }
        
        return patterns
    
    def _rank_features(self, feature_dicts: List[Dict]) -> Dict:
        """Rank features by average value"""
        if not feature_dicts:
            return {}
        
        feature_sums = {}
        for feature_dict in feature_dicts:
            for feature, value in feature_dict.items():
                feature_sums[feature] = feature_sums.get(feature, 0) + value
        
        feature_avgs = {
            feature: round(total / len(feature_dicts), 2)
            for feature, total in feature_sums.items()
        }
        
        # Sort by value descending
        return dict(sorted(feature_avgs.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_strategy_performance(self) -> Dict:
        """Analyze performance of different strategies"""
        strategy_outcomes = {
            "aggressive": {"success": 0, "total": 0},
            "moderate": {"success": 0, "total": 0},
            "conservative": {"success": 0, "total": 0},
            "targeted": {"success": 0, "total": 0},
        }
        
        for outcome in self.historical_outcomes.values():
            strategy = outcome.get("recommended_strategy", "moderate")
            if strategy in strategy_outcomes:
                strategy_outcomes[strategy]["total"] += 1
                if outcome["outcome_probability"] == "high":
                    strategy_outcomes[strategy]["success"] += 1
        
        # Calculate success rates
        performance = {}
        for strategy, data in strategy_outcomes.items():
            if data["total"] > 0:
                rate = data["success"] / data["total"]
                performance[strategy] = {
                    "success_rate": round(rate, 2),
                    "total_attempts": data["total"],
                    "successes": data["success"],
                }
        
        return performance
    
    def _identify_temporal_patterns(self) -> Dict:
        """Identify patterns by time of failure"""
        # Analyze by day of week, time of month, etc.
        weekday_performance = {}
        
        for outcome in self.historical_outcomes.values():
            timestamp = outcome.get("timestamp", "")
            if not timestamp:
                continue
            
            dt = datetime.fromisoformat(timestamp)
            weekday = dt.strftime("%A")
            
            if weekday not in weekday_performance:
                weekday_performance[weekday] = {"total": 0, "recovered": 0}
            
            weekday_performance[weekday]["total"] += 1
            if outcome["outcome_probability"] == "high":
                weekday_performance[weekday]["recovered"] += 1
        
        return {
            "by_weekday": weekday_performance,
            "best_recovery_day": max(
                weekday_performance.items(),
                key=lambda x: x[1]["recovered"] / x[1]["total"] if x[1]["total"] > 0 else 0,
                default=(None, {})
            )[0],
        }
    
    def calculate_recovery_roi(
        self,
        strategy: str,
        customer_segment: str = "all",
    ) -> Dict:
        """
        Calculate ROI of recovery attempts for strategy and segment.
        Helps prioritize resources on highest-yield recovery activities.
        
        Args:
            strategy: Dunning strategy name
            customer_segment: Customer segment (all, basic, pro, enterprise)
        
        Returns:
            ROI metrics and recommendations
        """
        # Get relevant outcomes
        relevant = [
            o for o in self.historical_outcomes.values()
            if o.get("recommended_strategy") == strategy
        ]
        
        if not relevant:
            return {"error": f"No data for strategy {strategy}"}
        
        # Calculate costs
        cost_per_attempt = 0.50  # Email + processing
        num_attempts = len(relevant)
        total_cost = cost_per_attempt * num_attempts
        
        # Calculate revenue recovered
        total_recovered = sum(
            o.get("expected_recovery_amount", 0) for o in relevant
        )
        
        # Calculate ROI
        roi = ((total_recovered - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "strategy": strategy,
            "customer_segment": customer_segment,
            "num_attempts": num_attempts,
            "total_cost": round(total_cost, 2),
            "total_recovered": round(total_recovered, 2),
            "average_recovery": round(total_recovered / num_attempts, 2),
            "roi_percentage": round(roi, 1),
            "roi_status": (
                "excellent" if roi > 200 else
                "good" if roi > 100 else
                "fair" if roi > 0 else
                "poor"
            ),
            "recommendation": self._roi_recommendation(roi),
        }
    
    def _roi_recommendation(self, roi: float) -> str:
        """Get recommendation based on ROI"""
        if roi > 200:
            return "Expand this strategy - excellent returns"
        elif roi > 100:
            return "Continue strategy - strong ROI"
        elif roi > 0:
            return "Monitor strategy - marginal returns"
        else:
            return "Consider alternative approaches"
