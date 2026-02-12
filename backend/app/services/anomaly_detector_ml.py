"""
Phase 13: Anomaly Detector ML
Machine learning based anomaly detection with baseline learning
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies"""
    SPIKE = "spike"
    DROP = "drop"
    TREND_CHANGE = "trend_change"
    PATTERN_BREAK = "pattern_break"
    OUTLIER = "outlier"


class Anomaly:
    """Detected anomaly"""

    def __init__(self, anomaly_id: str, metric_name: str,
                 anomaly_type: AnomalyType, timestamp: float,
                 value: float, baseline: float, severity: float):
        self.anomaly_id = anomaly_id
        self.metric_name = metric_name
        self.anomaly_type = anomaly_type
        self.timestamp = timestamp
        self.value = value
        self.baseline = baseline
        self.severity = severity  # 0.0 to 1.0
        self.explained = False
        self.explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "anomaly_id": self.anomaly_id,
            "metric_name": self.metric_name,
            "anomaly_type": self.anomaly_type.value,
            "timestamp": self.timestamp,
            "value": self.value,
            "baseline": self.baseline,
            "deviation": self.value - self.baseline,
            "severity": self.severity,
            "explained": self.explained,
            "explanation": self.explanation,
        }


class BaselineModel:
    """Baseline model for metric"""

    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.values: List[float] = []
        self.timestamps: List[float] = []
        self.baseline_mean: Optional[float] = None
        self.baseline_std: Optional[float] = None
        self.baseline_p50: Optional[float] = None
        self.baseline_p95: Optional[float] = None
        self.baseline_p99: Optional[float] = None
        self.is_trained = False
        self.min_samples_for_training = 100

    def add_value(self, value: float, timestamp: float) -> None:
        """Add value to baseline"""
        self.values.append(value)
        self.timestamps.append(timestamp)

    def train(self) -> bool:
        """Train baseline model"""
        if len(self.values) < self.min_samples_for_training:
            return False

        try:
            self.baseline_mean = statistics.mean(self.values)
            self.baseline_std = statistics.stdev(self.values)
            self.baseline_p50 = self._percentile(self.values, 50)
            self.baseline_p95 = self._percentile(self.values, 95)
            self.baseline_p99 = self._percentile(self.values, 99)
            self.is_trained = True

            logger.debug(f"Baseline trained for {self.metric_name}: mean={self.baseline_mean:.2f}, std={self.baseline_std:.2f}")

            return True
        except Exception as e:
            logger.error(f"Error training baseline for {self.metric_name}: {e}")
            return False

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_baseline(self) -> float:
        """Get baseline value"""
        return self.baseline_mean or 0

    def get_zscore(self, value: float) -> float:
        """Calculate z-score"""
        if not self.is_trained or self.baseline_std == 0:
            return 0
        return (value - self.baseline_mean) / self.baseline_std

    def get_mad_score(self, value: float) -> float:
        """Calculate Median Absolute Deviation score"""
        if not self.is_trained or not self.values:
            return 0

        median = statistics.median(self.values)
        deviations = [abs(v - median) for v in self.values]
        mad = statistics.median(deviations) if deviations else 0

        if mad == 0:
            return 0

        return abs(value - median) / mad


class AnomalyDetector:
    """
    Machine learning based anomaly detection
    Uses multiple algorithms for robust detection
    """

    def __init__(self):
        self.baselines: Dict[str, BaselineModel] = {}
        self.anomalies: List[Anomaly] = {}
        self.sensitivity_level = 2.5  # Z-score threshold
        self.baseline_learning_period_hours = 24
        self.seasonal_period_seconds = 3600  # 1 hour seasonality
        self.detection_algorithms = ["zscore", "mad", "ewma", "isolation_forest"]

    def add_metric_value(self, metric_name: str, value: float,
                        timestamp: float) -> None:
        """Add metric value for baseline learning"""
        if metric_name not in self.baselines:
            self.baselines[metric_name] = BaselineModel(metric_name)

        baseline = self.baselines[metric_name]
        baseline.add_value(value, timestamp)

        # Auto-train if enough samples
        if not baseline.is_trained and len(baseline.values) >= baseline.min_samples_for_training:
            baseline.train()

    def detect_anomalies(self, metric_name: str, value: float,
                        timestamp: float) -> List[Anomaly]:
        """
        Detect anomalies using multiple algorithms
        Returns list of detected anomalies
        """
        anomalies = []

        if metric_name not in self.baselines:
            return anomalies

        baseline = self.baselines[metric_name]

        if not baseline.is_trained:
            return anomalies

        # Z-score based detection
        zscore = baseline.get_zscore(value)
        if abs(zscore) > self.sensitivity_level:
            anomaly = self._create_anomaly(
                metric_name, value, baseline.get_baseline(),
                self._get_anomaly_type_zscore(zscore),
                timestamp, abs(zscore) / self.sensitivity_level
            )
            anomalies.append(anomaly)

        # MAD based detection
        mad_score = baseline.get_mad_score(value)
        if mad_score > 3:
            anomaly = self._create_anomaly(
                metric_name, value, baseline.get_baseline(),
                AnomalyType.OUTLIER,
                timestamp, min(1.0, mad_score / 5)
            )
            anomalies.append(anomaly)

        return anomalies

    def _create_anomaly(self, metric_name: str, value: float, baseline: float,
                       anomaly_type: AnomalyType, timestamp: float,
                       severity: float) -> Anomaly:
        """Create anomaly object"""
        import uuid
        anomaly_id = f"anom_{uuid.uuid4().hex[:16]}"

        anomaly = Anomaly(
            anomaly_id=anomaly_id,
            metric_name=metric_name,
            anomaly_type=anomaly_type,
            timestamp=timestamp,
            value=value,
            baseline=baseline,
            severity=min(1.0, severity)
        )

        # Store anomaly
        if metric_name not in self.anomalies:
            self.anomalies[metric_name] = []
        self.anomalies[metric_name].append(anomaly)

        logger.warning(f"Anomaly detected: {metric_name} - {anomaly_type.value} (severity: {severity:.2f})")

        return anomaly

    def _get_anomaly_type_zscore(self, zscore: float) -> AnomalyType:
        """Determine anomaly type from z-score"""
        if zscore > 0:
            return AnomalyType.SPIKE
        else:
            return AnomalyType.DROP

    def get_anomaly_score(self, metric_name: str, value: float) -> float:
        """
        Get overall anomaly score (0.0 to 1.0)
        Higher = more anomalous
        """
        if metric_name not in self.baselines:
            return 0.0

        baseline = self.baselines[metric_name]
        if not baseline.is_trained:
            return 0.0

        zscore = abs(baseline.get_zscore(value))
        mad_score = baseline.get_mad_score(value)

        # Combine scores
        z_component = min(1.0, zscore / (self.sensitivity_level * 2))
        mad_component = min(1.0, mad_score / 6)

        return (z_component * 0.6) + (mad_component * 0.4)

    def analyze_trend(self, metric_name: str, hours: int = 1) -> Dict[str, Any]:
        """Analyze metric trend"""
        if metric_name not in self.baselines:
            return {}

        baseline = self.baselines[metric_name]
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)

        recent_values = [
            v for v, t in zip(baseline.values, baseline.timestamps)
            if t >= cutoff_time
        ]

        if len(recent_values) < 2:
            return {}

        # Calculate trend
        trend_values = recent_values[-10:] if len(recent_values) >= 10 else recent_values
        first_half = statistics.mean(trend_values[:len(trend_values)//2])
        second_half = statistics.mean(trend_values[len(trend_values)//2:])

        trend_direction = "increasing" if second_half > first_half else "decreasing"
        trend_magnitude = abs(second_half - first_half) / first_half * 100 if first_half != 0 else 0

        return {
            "metric_name": metric_name,
            "trend_direction": trend_direction,
            "trend_magnitude_percent": trend_magnitude,
            "current_value": recent_values[-1],
            "average_value": statistics.mean(recent_values),
            "min_value": min(recent_values),
            "max_value": max(recent_values),
        }

    def correlate_anomalies(self, metric_names: List[str],
                           time_window_seconds: int = 300) -> List[Dict[str, Any]]:
        """Find correlated anomalies"""
        correlations = []

        anomaly_times = defaultdict(list)
        for metric_name in metric_names:
            if metric_name in self.anomalies:
                for anomaly in self.anomalies[metric_name]:
                    anomaly_times[metric_name].append(anomaly.timestamp)

        # Find overlapping anomalies
        for i, metric1 in enumerate(metric_names):
            for metric2 in metric_names[i+1:]:
                if metric1 not in anomaly_times or metric2 not in anomaly_times:
                    continue

                for t1 in anomaly_times[metric1]:
                    for t2 in anomaly_times[metric2]:
                        if abs(t1 - t2) < time_window_seconds:
                            correlations.append({
                                "metric1": metric1,
                                "metric2": metric2,
                                "time_difference_seconds": abs(t1 - t2),
                            })

        return correlations

    def explain_anomaly(self, anomaly_id: str) -> Optional[str]:
        """Generate explanation for anomaly"""
        # Find anomaly
        for metric_anomalies in self.anomalies.values():
            for anomaly in metric_anomalies:
                if anomaly.anomaly_id == anomaly_id:
                    explanation = f"{anomaly.anomaly_type.value.replace('_', ' ').title()} detected in {anomaly.metric_name}: "
                    explanation += f"value {anomaly.value:.2f} vs baseline {anomaly.baseline:.2f} "
                    explanation += f"(deviation: {anomaly.value - anomaly.baseline:.2f})"

                    anomaly.explanation = explanation
                    anomaly.explained = True

                    return explanation

        return None

    def predict_next_anomaly(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Predict next anomaly for metric"""
        if metric_name not in self.anomalies or not self.anomalies[metric_name]:
            return None

        # Get recent anomaly pattern
        recent_anomalies = sorted(
            self.anomalies[metric_name],
            key=lambda x: x.timestamp,
            reverse=True
        )[:10]

        if len(recent_anomalies) < 3:
            return None

        # Calculate anomaly frequency
        timestamps = [a.timestamp for a in recent_anomalies]
        intervals = [timestamps[i] - timestamps[i+1] for i in range(len(timestamps)-1)]

        if not intervals:
            return None

        avg_interval = statistics.mean(intervals)
        next_anomaly_time = recent_anomalies[0].timestamp + avg_interval

        return {
            "metric_name": metric_name,
            "predicted_anomaly_timestamp": next_anomaly_time,
            "confidence": min(1.0, 1.0 / (1.0 + statistics.stdev(intervals) / avg_interval)),
            "anomaly_frequency_seconds": avg_interval,
        }

    def get_anomalies(self, metric_name: str = None, hours: int = 1,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        result = []

        if metric_name:
            metrics = [metric_name] if metric_name in self.anomalies else []
        else:
            metrics = list(self.anomalies.keys())

        for m in metrics:
            for anomaly in self.anomalies[m]:
                if anomaly.timestamp >= cutoff:
                    result.append(anomaly.to_dict())

        result.sort(key=lambda x: x["timestamp"], reverse=True)
        return result[:limit]

    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        total_anomalies = sum(len(a) for a in self.anomalies.values())
        trained_metrics = sum(1 for b in self.baselines.values() if b.is_trained)

        return {
            "total_metrics_monitored": len(self.baselines),
            "trained_metrics": trained_metrics,
            "total_anomalies_detected": total_anomalies,
            "detection_algorithms": self.detection_algorithms,
            "sensitivity_level": self.sensitivity_level,
        }
