"""
ML-Based Anomaly Detection Service
Statistical and machine learning anomaly detection
Phase 43: Advanced Analytics & ML Features
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
import statistics
import threading
from collections import deque
import math


class AnomalyType(Enum):
    """Types of anomalies detected"""
    STATISTICAL = "statistical"
    CONTEXTUAL = "contextual"
    COLLECTIVE = "collective"
    DRIFT = "drift"


class DetectionMethod(Enum):
    """Anomaly detection methods"""
    ZSCORE = "zscore"
    IQR = "iqr"
    EWMA = "ewma"
    ISOLATION_FOREST = "isolation_forest"
    SEASONAL = "seasonal"
    DBT = "dbt"


@dataclass
class AnomalyDetectionConfig:
    """Configuration for anomaly detection"""
    method: DetectionMethod = DetectionMethod.ZSCORE
    zscore_threshold: float = 3.0
    iqr_multiplier: float = 1.5
    ewma_alpha: float = 0.3
    window_size: int = 100
    min_samples: int = 10
    baseline_period_days: int = 7
    retrain_interval_hours: int = 24
    enabled: bool = True


@dataclass
class AnomalyScore:
    """Anomaly score for a data point"""
    timestamp: datetime
    value: float
    score: float  # 0-1, where 1 is most anomalous
    method: DetectionMethod
    is_anomaly: bool
    severity: str  # low, medium, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "score": self.score,
            "method": self.method.value,
            "is_anomaly": self.is_anomaly,
            "severity": self.severity,
            "metadata": self.metadata,
        }


@dataclass
class AnomalyAlert:
    """Alert for detected anomaly"""
    id: str
    metric_name: str
    anomaly_type: AnomalyType
    timestamp: datetime
    value: float
    baseline: float
    deviation: float
    severity: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "anomaly_type": self.anomaly_type.value,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "baseline": self.baseline,
            "deviation": self.deviation,
            "severity": self.severity,
            "message": self.message,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
        }


class BaselineModel:
    """Learns baseline behavior for a metric"""

    def __init__(self, metric_name: str, window_size: int = 100):
        self.metric_name = metric_name
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        self.mean = 0.0
        self.stddev = 0.0
        self.min_value = float('inf')
        self.max_value = float('-inf')
        self.trained = False
        self.last_retrain = datetime.now()

    def add_sample(self, value: float, timestamp: datetime) -> None:
        """Add sample to baseline"""
        self.values.append(value)
        self.timestamps.append(timestamp)
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)

    def train(self) -> bool:
        """Train baseline model"""
        if len(self.values) < 3:
            return False

        values_list = list(self.values)
        self.mean = statistics.mean(values_list)

        try:
            self.stddev = statistics.stdev(values_list)
        except:
            self.stddev = 0.0

        self.trained = True
        self.last_retrain = datetime.now()
        return True

    def get_baseline(self) -> Dict[str, float]:
        """Get current baseline statistics"""
        return {
            "mean": self.mean,
            "stddev": self.stddev,
            "min": self.min_value,
            "max": self.max_value,
            "samples": len(self.values),
            "trained": self.trained,
        }


class ZScoreDetector:
    """Z-Score based anomaly detection"""

    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.baselines: Dict[str, BaselineModel] = {}

    def add_metric(self, metric_name: str, value: float, timestamp: datetime) -> None:
        """Add metric value"""
        if metric_name not in self.baselines:
            self.baselines[metric_name] = BaselineModel(metric_name)

        self.baselines[metric_name].add_sample(value, timestamp)
        self.baselines[metric_name].train()

    def detect(self, metric_name: str, value: float, timestamp: datetime) -> Optional[AnomalyScore]:
        """Detect anomaly using Z-score"""
        if metric_name not in self.baselines:
            return None

        baseline = self.baselines[metric_name]

        if not baseline.trained or baseline.stddev == 0:
            return AnomalyScore(
                timestamp=timestamp,
                value=value,
                score=0.0,
                method=DetectionMethod.ZSCORE,
                is_anomaly=False,
                severity="low",
            )

        z_score = abs((value - baseline.mean) / baseline.stddev)
        is_anomaly = z_score > self.threshold
        score = min(z_score / self.threshold, 1.0)

        # Determine severity
        if z_score > 4:
            severity = "critical"
        elif z_score > 3:
            severity = "high"
        elif z_score > 2:
            severity = "medium"
        else:
            severity = "low"

        return AnomalyScore(
            timestamp=timestamp,
            value=value,
            score=score,
            method=DetectionMethod.ZSCORE,
            is_anomaly=is_anomaly,
            severity=severity,
            metadata={
                "z_score": z_score,
                "mean": baseline.mean,
                "stddev": baseline.stddev,
            },
        )


class IQRDetector:
    """Interquartile Range (IQR) based anomaly detection"""

    def __init__(self, multiplier: float = 1.5):
        self.multiplier = multiplier
        self.baselines: Dict[str, BaselineModel] = {}

    def add_metric(self, metric_name: str, value: float, timestamp: datetime) -> None:
        """Add metric value"""
        if metric_name not in self.baselines:
            self.baselines[metric_name] = BaselineModel(metric_name)

        self.baselines[metric_name].add_sample(value, timestamp)
        self.baselines[metric_name].train()

    def detect(self, metric_name: str, value: float, timestamp: datetime) -> Optional[AnomalyScore]:
        """Detect anomaly using IQR"""
        if metric_name not in self.baselines:
            return None

        baseline = self.baselines[metric_name]

        if len(baseline.values) < 4:
            return AnomalyScore(
                timestamp=timestamp,
                value=value,
                score=0.0,
                method=DetectionMethod.IQR,
                is_anomaly=False,
                severity="low",
            )

        sorted_values = sorted(list(baseline.values))
        q1_idx = len(sorted_values) // 4
        q3_idx = (3 * len(sorted_values)) // 4
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1

        lower_bound = q1 - self.multiplier * iqr
        upper_bound = q3 + self.multiplier * iqr

        is_anomaly = value < lower_bound or value > upper_bound
        distance = max(0, abs(value - baseline.mean) - self.multiplier * iqr)
        score = min(distance / (iqr or 1), 1.0)

        # Determine severity
        if distance > 2 * iqr:
            severity = "critical"
        elif distance > iqr:
            severity = "high"
        else:
            severity = "medium" if is_anomaly else "low"

        return AnomalyScore(
            timestamp=timestamp,
            value=value,
            score=score,
            method=DetectionMethod.IQR,
            is_anomaly=is_anomaly,
            severity=severity,
            metadata={
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            },
        )


class EWMADetector:
    """Exponential Weighted Moving Average anomaly detection"""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.ewma_values: Dict[str, float] = {}
        self.ewma_variance: Dict[str, float] = {}
        self.samples: Dict[str, int] = {}

    def add_metric(self, metric_name: str, value: float) -> None:
        """Add metric value"""
        if metric_name not in self.ewma_values:
            self.ewma_values[metric_name] = value
            self.ewma_variance[metric_name] = 0.0
            self.samples[metric_name] = 1
        else:
            # Update EWMA
            prev_ewma = self.ewma_values[metric_name]
            self.ewma_values[metric_name] = self.alpha * value + (1 - self.alpha) * prev_ewma

            # Update EWMA variance
            error = value - prev_ewma
            prev_variance = self.ewma_variance[metric_name]
            self.ewma_variance[metric_name] = self.alpha * (error ** 2) + (1 - self.alpha) * prev_variance

            self.samples[metric_name] += 1

    def detect(self, metric_name: str, value: float, timestamp: datetime) -> Optional[AnomalyScore]:
        """Detect anomaly using EWMA"""
        if metric_name not in self.ewma_values:
            return AnomalyScore(
                timestamp=timestamp,
                value=value,
                score=0.0,
                method=DetectionMethod.EWMA,
                is_anomaly=False,
                severity="low",
            )

        ewma_mean = self.ewma_values[metric_name]
        ewma_std = math.sqrt(self.ewma_variance[metric_name]) if self.ewma_variance[metric_name] > 0 else 1.0

        z_score = abs((value - ewma_mean) / ewma_std) if ewma_std > 0 else 0
        is_anomaly = z_score > 3.0
        score = min(z_score / 3.0, 1.0)

        severity = "critical" if z_score > 4 else "high" if z_score > 3 else "medium" if is_anomaly else "low"

        return AnomalyScore(
            timestamp=timestamp,
            value=value,
            score=score,
            method=DetectionMethod.EWMA,
            is_anomaly=is_anomaly,
            severity=severity,
            metadata={
                "ewma_mean": ewma_mean,
                "ewma_std": ewma_std,
                "z_score": z_score,
            },
        )


class AnomalyDetectionEngine:
    """Main anomaly detection engine"""

    def __init__(self, config: AnomalyDetectionConfig = None):
        self.config = config or AnomalyDetectionConfig()
        self.zscore_detector = ZScoreDetector(self.config.zscore_threshold)
        self.iqr_detector = IQRDetector(self.config.iqr_multiplier)
        self.ewma_detector = EWMADetector(self.config.ewma_alpha)
        self.alerts: Dict[str, AnomalyAlert] = {}
        self.alert_history: List[AnomalyAlert] = []
        self.callbacks: List[Callable] = []
        self.lock = threading.RLock()
        self.alert_counter = 0

    def add_metric(self, metric_name: str, value: float, timestamp: datetime) -> None:
        """Add metric for analysis"""
        with self.lock:
            self.zscore_detector.add_metric(metric_name, value, timestamp)
            self.iqr_detector.add_metric(metric_name, value, timestamp)
            self.ewma_detector.add_metric(metric_name, value)

    def detect_anomalies(
        self, metric_name: str, value: float, timestamp: datetime
    ) -> List[AnomalyScore]:
        """Detect anomalies using configured methods"""
        scores = []

        with self.lock:
            if self.config.method == DetectionMethod.ZSCORE or self.config.method == DetectionMethod.DBT:
                score = self.zscore_detector.detect(metric_name, value, timestamp)
                if score:
                    scores.append(score)

            elif self.config.method == DetectionMethod.IQR:
                score = self.iqr_detector.detect(metric_name, value, timestamp)
                if score:
                    scores.append(score)

            elif self.config.method == DetectionMethod.EWMA:
                score = self.ewma_detector.detect(metric_name, value, timestamp)
                if score:
                    scores.append(score)

        # Check for anomalies and create alerts
        for score in scores:
            if score.is_anomaly:
                self._create_anomaly_alert(metric_name, value, score, timestamp)

        return scores

    def _create_anomaly_alert(
        self, metric_name: str, value: float, score: AnomalyScore, timestamp: datetime
    ) -> None:
        """Create alert for anomaly"""
        with self.lock:
            self.alert_counter += 1
            alert_id = f"anomaly_{self.alert_counter}_{int(timestamp.timestamp())}"

            baseline = self.zscore_detector.baselines.get(metric_name)
            baseline_value = baseline.mean if baseline else value

            alert = AnomalyAlert(
                id=alert_id,
                metric_name=metric_name,
                anomaly_type=AnomalyType.STATISTICAL,
                timestamp=timestamp,
                value=value,
                baseline=baseline_value,
                deviation=abs(value - baseline_value),
                severity=score.severity,
                message=f"Anomaly detected in {metric_name}: value {value:.2f} deviates from baseline {baseline_value:.2f}",
                context={
                    "method": score.method.value,
                    "score": score.score,
                    "metadata": score.metadata,
                },
            )

            self.alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback({
                        "event": "anomaly_detected",
                        "alert": alert.to_dict(),
                    })
                except Exception as e:
                    print(f"Error in anomaly callback: {e}")

    def get_active_anomalies(self) -> List[Dict]:
        """Get active anomalies"""
        with self.lock:
            return [alert.to_dict() for alert in self.alerts.values()]

    def get_anomaly_history(self, metric_name: Optional[str] = None, hours: int = 24) -> List[Dict]:
        """Get anomaly history"""
        with self.lock:
            cutoff = datetime.now() - timedelta(hours=hours)
            history = [
                alert for alert in self.alert_history
                if alert.timestamp >= cutoff
                and (metric_name is None or alert.metric_name == metric_name)
            ]
            return [alert.to_dict() for alert in history]

    def get_metric_baseline(self, metric_name: str) -> Dict[str, float]:
        """Get metric baseline"""
        with self.lock:
            baseline = self.zscore_detector.baselines.get(metric_name)
            return baseline.get_baseline() if baseline else {}

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve anomaly alert"""
        with self.lock:
            if alert_id in self.alerts:
                del self.alerts[alert_id]
                return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        with self.lock:
            return {
                "active_anomalies": len(self.alerts),
                "total_alerts": len(self.alert_history),
                "metrics_tracked": len(self.zscore_detector.baselines),
                "callbacks_registered": len(self.callbacks),
                "detection_method": self.config.method.value,
            }

    def register_callback(self, callback: Callable) -> None:
        """Register callback for anomaly events"""
        with self.lock:
            self.callbacks.append(callback)

    def update_config(self, **kwargs) -> bool:
        """Update configuration"""
        try:
            with self.lock:
                for key, value in kwargs.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False


# Global singleton
_anomaly_detector = None


def get_anomaly_detector(config: AnomalyDetectionConfig = None) -> AnomalyDetectionEngine:
    """Get or create anomaly detection engine singleton"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetectionEngine(config)
    return _anomaly_detector
