"""
Phase 11: Anomaly Detector
Detect unusual patterns and behaviors in workflow executions
"""

import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in workflow execution patterns
    Uses statistical methods to identify unusual behaviors
    """

    def __init__(self):
        self.execution_history = []
        self.baseline_metrics = {}
        self.anomalies = []
        self.anomaly_thresholds = {
            "duration_zscore": 2.5,  # 2.5 standard deviations
            "error_rate_increase": 1.5,  # 50% increase
            "frequency_deviation": 2.0,  # 2x expected frequency
        }

    def record_execution(self, execution: Dict) -> None:
        """Record an execution for anomaly detection"""
        self.execution_history.append({
            **execution,
            "timestamp": datetime.utcnow(),
        })

    def detect_anomalies(self, workflow_id: str) -> List[Dict]:
        """
        Detect anomalies in a workflow's execution history
        Returns list of detected anomalies with details
        """
        logger.info(f"Detecting anomalies for workflow {workflow_id}")

        workflow_executions = [
            e for e in self.execution_history
            if e.get("workflow_id") == workflow_id
        ]

        if len(workflow_executions) < 5:
            logger.warning(f"Insufficient data for anomaly detection: {len(workflow_executions)} executions")
            return []

        anomalies = []

        # Check for duration anomalies
        duration_anomalies = self._detect_duration_anomalies(workflow_executions)
        anomalies.extend(duration_anomalies)

        # Check for error rate anomalies
        error_anomalies = self._detect_error_rate_anomalies(workflow_executions)
        anomalies.extend(error_anomalies)

        # Check for pattern anomalies
        pattern_anomalies = self._detect_pattern_anomalies(workflow_executions)
        anomalies.extend(pattern_anomalies)

        # Check for resource anomalies
        resource_anomalies = self._detect_resource_anomalies(workflow_executions)
        anomalies.extend(resource_anomalies)

        self.anomalies.extend(anomalies)
        return anomalies

    def _detect_duration_anomalies(self, executions: List[Dict]) -> List[Dict]:
        """Detect executions with unusual durations"""
        anomalies = []

        durations = [e.get("duration", 0) for e in executions]
        if not durations or len(durations) < 3:
            return anomalies

        mean_duration = np.mean(durations)
        std_duration = np.std(durations)

        # Z-score test
        for i, execution in enumerate(executions[-10:]):  # Check recent executions
            duration = execution.get("duration", 0)
            if std_duration > 0:
                zscore = abs((duration - mean_duration) / std_duration)
                if zscore > self.anomaly_thresholds["duration_zscore"]:
                    anomalies.append({
                        "type": "duration_anomaly",
                        "execution_id": execution.get("id"),
                        "workflow_id": execution.get("workflow_id"),
                        "observed_duration": round(duration, 2),
                        "expected_duration": round(mean_duration, 2),
                        "deviation": round(zscore, 2),
                        "severity": "high" if zscore > 3.5 else "medium",
                        "description": f"Execution took {duration/mean_duration:.1f}x expected time",
                        "timestamp": execution.get("timestamp"),
                    })

        return anomalies

    def _detect_error_rate_anomalies(self, executions: List[Dict]) -> List[Dict]:
        """Detect unusual error rates"""
        anomalies = []

        # Split into recent and historical
        recent_count = min(10, len(executions))
        recent_executions = executions[-recent_count:]
        historical_executions = executions[:-recent_count] if len(executions) > recent_count else executions

        if not historical_executions:
            return anomalies

        # Calculate error rates
        historical_error_rate = len(
            [e for e in historical_executions if e.get("status") == "error"]
        ) / len(historical_executions)

        recent_error_rate = len(
            [e for e in recent_executions if e.get("status") == "error"]
        ) / len(recent_executions) if recent_executions else 0

        # Check for significant increase
        if historical_error_rate > 0:
            increase_factor = recent_error_rate / historical_error_rate
            if increase_factor > self.anomaly_thresholds["error_rate_increase"]:
                anomalies.append({
                    "type": "error_rate_anomaly",
                    "workflow_id": executions[0].get("workflow_id"),
                    "historical_error_rate": round(historical_error_rate, 2),
                    "recent_error_rate": round(recent_error_rate, 2),
                    "increase_factor": round(increase_factor, 2),
                    "severity": "critical" if increase_factor > 5 else "high",
                    "description": f"Error rate increased {increase_factor:.1f}x",
                })

        return anomalies

    def _detect_pattern_anomalies(self, executions: List[Dict]) -> List[Dict]:
        """Detect unusual action sequences or patterns"""
        anomalies = []

        # Get action sequences
        action_sequences = []
        for execution in executions:
            sequence = tuple(
                n.get("action_type") for n in execution.get("nodes", [])
            )
            action_sequences.append(sequence)

        # Find most common sequence
        from collections import Counter
        sequence_counts = Counter(action_sequences)
        most_common = sequence_counts.most_common(1)

        if most_common:
            common_sequence, common_count = most_common[0]
            common_percentage = common_count / len(action_sequences)

            # Find rare sequences
            for execution in executions[-5:]:
                sequence = tuple(
                    n.get("action_type") for n in execution.get("nodes", [])
                )
                if sequence != common_sequence and sequence_counts[sequence] == 1:
                    anomalies.append({
                        "type": "pattern_anomaly",
                        "execution_id": execution.get("id"),
                        "workflow_id": execution.get("workflow_id"),
                        "anomalous_sequence": sequence,
                        "common_sequence": common_sequence,
                        "common_percentage": round(common_percentage * 100, 1),
                        "severity": "low",
                        "description": "Unusual action sequence detected",
                    })

        return anomalies

    def _detect_resource_anomalies(self, executions: List[Dict]) -> List[Dict]:
        """Detect unusual resource consumption"""
        anomalies = []

        # Check memory usage if available
        memory_usages = [
            e.get("memory_usage_mb", 0)
            for e in executions if e.get("memory_usage_mb")
        ]

        if len(memory_usages) > 3:
            mean_memory = np.mean(memory_usages)
            std_memory = np.std(memory_usages)

            for execution in executions[-5:]:
                memory = execution.get("memory_usage_mb")
                if memory and std_memory > 0:
                    zscore = abs((memory - mean_memory) / std_memory)
                    if zscore > 2.5:
                        anomalies.append({
                            "type": "resource_anomaly",
                            "execution_id": execution.get("id"),
                            "workflow_id": execution.get("workflow_id"),
                            "resource": "memory",
                            "observed": round(memory, 2),
                            "expected": round(mean_memory, 2),
                            "deviation": round(zscore, 2),
                            "severity": "medium",
                            "description": f"Memory usage {memory/mean_memory:.1f}x expected",
                        })

        return anomalies

    def classify_anomaly(self, anomaly: Dict) -> str:
        """Classify anomaly severity and type"""
        severity = anomaly.get("severity", "low")
        anomaly_type = anomaly.get("type")

        classification = {
            "type": anomaly_type,
            "severity": severity,
            "action_required": severity in ["critical", "high"],
            "alert_message": self._generate_alert_message(anomaly),
        }

        return classification

    def _generate_alert_message(self, anomaly: Dict) -> str:
        """Generate actionable alert message"""
        anomaly_type = anomaly.get("type")

        if anomaly_type == "duration_anomaly":
            return f"Workflow execution took {anomaly['deviation']:.1f} standard deviations longer than expected"

        elif anomaly_type == "error_rate_anomaly":
            return f"Error rate increased by {anomaly['increase_factor']:.1f}x - investigate recent changes"

        elif anomaly_type == "pattern_anomaly":
            return f"Unusual action sequence detected - verify workflow logic"

        elif anomaly_type == "resource_anomaly":
            return f"{anomaly['resource']} usage {anomaly['deviation']:.1f} standard deviations above expected"

        return "Anomaly detected"

    def get_workflow_health_score(self, workflow_id: str) -> float:
        """
        Calculate overall health score for a workflow (0-100)
        Based on absence of anomalies
        """
        recent_anomalies = [
            a for a in self.anomalies
            if a.get("workflow_id") == workflow_id and
            (datetime.utcnow() - a.get("timestamp", datetime.utcnow())).days <= 7
        ]

        if not recent_anomalies:
            return 100.0

        # Deduct points based on anomaly severity
        score = 100.0
        for anomaly in recent_anomalies:
            severity = anomaly.get("severity")
            if severity == "critical":
                score -= 20
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            elif severity == "low":
                score -= 2

        return max(score, 0.0)

    def correlate_anomalies(self, anomaly1: Dict, anomaly2: Dict) -> float:
        """
        Calculate correlation between two anomalies
        Returns score 0-1 indicating how related they are
        """
        correlation = 0.0

        # Same workflow
        if anomaly1.get("workflow_id") == anomaly2.get("workflow_id"):
            correlation += 0.3

        # Same type
        if anomaly1.get("type") == anomaly2.get("type"):
            correlation += 0.3

        # Similar timing
        time_diff = abs(
            (anomaly1.get("timestamp") - anomaly2.get("timestamp")).total_seconds()
            if anomaly1.get("timestamp") and anomaly2.get("timestamp") else 0
        )
        if time_diff < 3600:  # Within 1 hour
            correlation += 0.2

        # Similar severity
        if anomaly1.get("severity") == anomaly2.get("severity"):
            correlation += 0.2

        return min(correlation, 1.0)

    def find_root_cause(self, anomaly: Dict) -> List[Dict]:
        """
        Attempt to find root cause of an anomaly
        Returns list of potential causes with confidence scores
        """
        potential_causes = []

        anomaly_type = anomaly.get("type")

        if anomaly_type == "duration_anomaly":
            potential_causes = [
                {"cause": "Slow network connectivity", "confidence": 0.4},
                {"cause": "External API latency", "confidence": 0.3},
                {"cause": "Database query performance", "confidence": 0.25},
                {"cause": "System resource contention", "confidence": 0.05},
            ]

        elif anomaly_type == "error_rate_anomaly":
            potential_causes = [
                {"cause": "Recent code deployment", "confidence": 0.5},
                {"cause": "External service outage", "confidence": 0.3},
                {"cause": "Data quality issues", "confidence": 0.15},
                {"cause": "Configuration change", "confidence": 0.05},
            ]

        elif anomaly_type == "pattern_anomaly":
            potential_causes = [
                {"cause": "Conditional logic triggered differently", "confidence": 0.4},
                {"cause": "Input data variation", "confidence": 0.35},
                {"cause": "Edge case handling", "confidence": 0.25},
            ]

        # Sort by confidence
        potential_causes.sort(key=lambda x: x["confidence"], reverse=True)
        return potential_causes

    def clear_old_anomalies(self, days: int = 30) -> int:
        """Clear anomaly records older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        original_count = len(self.anomalies)

        self.anomalies = [
            a for a in self.anomalies
            if a.get("timestamp", datetime.utcnow()) > cutoff
        ]

        removed = original_count - len(self.anomalies)
        logger.info(f"Removed {removed} old anomaly records")
        return removed

    def get_anomaly_trends(self, workflow_id: str) -> Dict:
        """Get trends in anomalies over time"""
        workflow_anomalies = [
            a for a in self.anomalies
            if a.get("workflow_id") == workflow_id
        ]

        if not workflow_anomalies:
            return {"trend": "none", "anomaly_count": 0}

        # Group by day
        from collections import defaultdict
        anomalies_by_day = defaultdict(int)

        for anomaly in workflow_anomalies:
            timestamp = anomaly.get("timestamp", datetime.utcnow())
            day = timestamp.date()
            anomalies_by_day[day] += 1

        days = sorted(anomalies_by_day.keys())
        counts = [anomalies_by_day[day] for day in days]

        # Determine trend
        if len(counts) > 1:
            if counts[-1] > counts[0]:
                trend = "increasing"
            elif counts[-1] < counts[0]:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "total_anomalies": len(workflow_anomalies),
            "anomalies_this_week": len([a for a in workflow_anomalies if (datetime.utcnow() - a.get("timestamp", datetime.utcnow())).days <= 7]),
            "daily_breakdown": dict(anomalies_by_day),
        }
