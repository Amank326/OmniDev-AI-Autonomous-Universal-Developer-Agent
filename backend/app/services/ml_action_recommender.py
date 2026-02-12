"""
Phase 11: ML Action Recommender
Suggest optimal next actions based on execution history and context
"""

import logging
import json
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MLActionRecommender:
    """
    Machine learning based action recommender
    Learns from execution history to suggest optimal next actions
    """

    def __init__(self):
        self.action_history = defaultdict(list)
        self.transition_matrix = defaultdict(lambda: defaultdict(int))
        self.action_success_rates = defaultdict(float)
        self.action_avg_duration = defaultdict(float)
        self.context_features = defaultdict(list)

    def record_action_execution(self, workflow_id: str, action_type: str, 
                               execution_result: Dict) -> None:
        """Record action execution for learning"""
        timestamp = datetime.utcnow()

        # Store action execution
        self.action_history[action_type].append({
            "workflow_id": workflow_id,
            "timestamp": timestamp,
            "status": execution_result.get("status"),
            "duration": execution_result.get("duration", 0),
            "error": execution_result.get("error"),
            "context": execution_result.get("context", {}),
        })

        # Update success rates
        if execution_result.get("status") == "success":
            current_successes = len([
                h for h in self.action_history[action_type]
                if h.get("status") == "success"
            ])
            self.action_success_rates[action_type] = (
                current_successes / len(self.action_history[action_type])
            )

        # Update average duration
        durations = [h["duration"] for h in self.action_history[action_type]]
        if durations:
            self.action_avg_duration[action_type] = np.mean(durations)

    def record_action_transition(self, from_action: str, to_action: str) -> None:
        """Record transitions between actions for learning sequences"""
        self.transition_matrix[from_action][to_action] += 1

    def recommend_next_actions(self, current_action: str, workflow_context: Dict,
                               top_k: int = 5) -> List[Dict]:
        """
        Recommend next actions based on current action and context
        Returns top K recommended actions with confidence scores
        """
        recommendations = []

        # Get transition-based recommendations
        if current_action in self.transition_matrix:
            transitions = self.transition_matrix[current_action]
            total_transitions = sum(transitions.values())

            for next_action, count in transitions.items():
                transition_prob = count / total_transitions

                # Combine with success rate
                success_rate = self.action_success_rates.get(next_action, 0.5)
                combined_score = (0.6 * transition_prob) + (0.4 * success_rate)

                # Apply context-based adjustments
                adjusted_score = self._adjust_score_by_context(
                    next_action, workflow_context, combined_score
                )

                recommendations.append({
                    "action": next_action,
                    "confidence": adjusted_score,
                    "reason": self._generate_recommendation_reason(
                        next_action, transition_prob, success_rate
                    ),
                    "estimated_duration": self.action_avg_duration.get(next_action, 0),
                    "success_probability": success_rate,
                })

        # If no transition history, recommend based on general success rates
        if not recommendations:
            for action, success_rate in self.action_success_rates.items():
                if success_rate > 0.5:  # Only recommend high-success actions
                    recommendations.append({
                        "action": action,
                        "confidence": success_rate,
                        "reason": "High success rate from historical data",
                        "estimated_duration": self.action_avg_duration.get(action, 0),
                        "success_probability": success_rate,
                    })

        # Sort by confidence and return top K
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations[:top_k]

    def _adjust_score_by_context(self, action: str, context: Dict, base_score: float) -> float:
        """Adjust recommendation score based on workflow context"""
        adjusted_score = base_score

        # Check if action is compatible with workflow type
        workflow_type = context.get("workflow_type")
        if workflow_type:
            # Certain actions fit certain workflow types better
            type_compatibility = self._get_action_workflow_compatibility(action, workflow_type)
            adjusted_score *= (0.7 + 0.3 * type_compatibility)

        # Check if action requires parameters available in context
        required_params = self._get_action_required_params(action)
        available_params = set(context.get("available_variables", []))
        param_coverage = len(available_params & set(required_params)) / max(len(required_params), 1)
        adjusted_score *= (0.8 + 0.2 * param_coverage)

        # Consider time constraints
        if context.get("time_sensitive"):
            duration = self.action_avg_duration.get(action, 0)
            time_budget = context.get("time_budget", 300)  # 5 minutes default
            if duration <= time_budget:
                adjusted_score *= 1.2
            else:
                adjusted_score *= 0.7

        return min(adjusted_score, 1.0)  # Cap at 1.0

    def _get_action_workflow_compatibility(self, action: str, workflow_type: str) -> float:
        """Get compatibility score between action and workflow type"""
        compatibility_matrix = {
            "notification": {
                "send_email": 1.0,
                "send_slack": 1.0,
                "send_sms": 0.8,
                "query_data": 0.3,
            },
            "data_processing": {
                "query_data": 1.0,
                "create_record": 0.9,
                "update_record": 0.9,
                "export_data": 0.8,
            },
            "api_integration": {
                "call_api": 1.0,
                "query_data": 0.7,
                "create_record": 0.8,
            },
            "monitoring": {
                "query_data": 1.0,
                "create_alert": 0.95,
                "log_event": 0.9,
            },
        }

        return compatibility_matrix.get(workflow_type, {}).get(action, 0.5)

    def _get_action_required_params(self, action: str) -> List[str]:
        """Get required parameters for an action"""
        params_map = {
            "send_email": ["recipient", "subject", "body"],
            "send_slack": ["channel", "message"],
            "send_sms": ["phone", "message"],
            "create_record": ["table", "data"],
            "update_record": ["table", "id", "data"],
            "delete_record": ["table", "id"],
            "query_data": ["table", "filters"],
            "call_api": ["url", "method"],
            "log_event": ["message"],
        }

        return params_map.get(action, [])

    def _generate_recommendation_reason(self, action: str, transition_prob: float,
                                       success_rate: float) -> str:
        """Generate human-readable reason for recommendation"""
        if transition_prob > 0.7:
            return f"Commonly follows current action ({transition_prob*100:.0f}% of time)"
        elif success_rate > 0.9:
            return f"Very high success rate ({success_rate*100:.0f}%)"
        elif transition_prob > 0.3:
            return f"Frequently paired with current action"
        else:
            return "Recommended based on similar workflows"

    def batch_recommend(self, current_actions: List[str], context: Dict) -> Dict[str, List]:
        """Get recommendations for multiple current actions"""
        recommendations = {}
        for action in current_actions:
            recommendations[action] = self.recommend_next_actions(action, context)
        return recommendations

    def get_action_insights(self, action: str) -> Dict:
        """Get detailed insights about an action"""
        history = self.action_history.get(action, [])

        if not history:
            return {"status": "no_data"}

        recent_history = [
            h for h in history
            if (datetime.utcnow() - h["timestamp"]).days <= 30
        ]

        success_count = len([h for h in history if h["status"] == "success"])
        error_count = len([h for h in history if h["status"] == "error"])
        total = len(history)

        return {
            "action": action,
            "total_executions": total,
            "success_rate": success_count / total if total > 0 else 0,
            "error_rate": error_count / total if total > 0 else 0,
            "avg_duration": self.action_avg_duration.get(action, 0),
            "recent_success_rate": (
                len([h for h in recent_history if h["status"] == "success"]) /
                len(recent_history) if recent_history else None
            ),
            "common_next_actions": list(
                sorted(
                    self.transition_matrix.get(action, {}).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            ),
            "common_errors": self._get_common_errors(action),
        }

    def _get_common_errors(self, action: str) -> List[Tuple[str, int]]:
        """Get most common errors for an action"""
        errors = defaultdict(int)
        for h in self.action_history.get(action, []):
            if h.get("error"):
                error_type = h["error"].split(":")[0]  # Get error type
                errors[error_type] += 1

        return sorted(errors.items(), key=lambda x: x[1], reverse=True)[:5]

    def predict_action_success(self, action: str, context: Dict) -> Tuple[float, str]:
        """
        Predict success probability of an action given context
        Returns (probability, confidence_explanation)
        """
        base_success_rate = self.action_success_rates.get(action, 0.5)

        # Adjust based on context
        context_adjustment = self._adjust_score_by_context(action, context, 1.0)
        predicted_probability = base_success_rate * context_adjustment

        # Generate explanation
        if predicted_probability > 0.85:
            explanation = "Very likely to succeed based on historical performance"
        elif predicted_probability > 0.7:
            explanation = "Likely to succeed with current context"
        elif predicted_probability > 0.5:
            explanation = "Moderate chance of success"
        else:
            explanation = "High risk - consider alternative actions"

        return round(predicted_probability, 2), explanation

    def get_action_alternatives(self, action: str, reason: str = "high_risk") -> List[Dict]:
        """Get alternative actions to recommend instead"""
        alternatives = []

        if reason == "high_risk":
            # Find actions with similar purpose but higher success rate
            for alt_action, success_rate in self.action_success_rates.items():
                if alt_action != action and success_rate > self.action_success_rates.get(action, 0):
                    alternatives.append({
                        "action": alt_action,
                        "reason": f"Better success rate ({success_rate*100:.0f}%)",
                        "success_rate": success_rate,
                    })

        elif reason == "slow":
            # Find faster alternatives
            current_duration = self.action_avg_duration.get(action, float('inf'))
            for alt_action, duration in self.action_avg_duration.items():
                if alt_action != action and duration < current_duration * 0.8:
                    alternatives.append({
                        "action": alt_action,
                        "reason": f"Significantly faster ({duration:.1f}s vs {current_duration:.1f}s)",
                        "estimated_duration": duration,
                    })

        # Sort by relevance and return top 3
        alternatives.sort(
            key=lambda x: x.get("success_rate") or x.get("estimated_duration"),
            reverse=True
        )
        return alternatives[:3]

    def clear_old_history(self, days: int = 90) -> int:
        """Clear execution history older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        removed_count = 0

        for action in self.action_history:
            original_count = len(self.action_history[action])
            self.action_history[action] = [
                h for h in self.action_history[action]
                if h["timestamp"] > cutoff_date
            ]
            removed_count += original_count - len(self.action_history[action])

        return removed_count
