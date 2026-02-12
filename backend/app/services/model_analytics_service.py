"""
Model Analytics Service
Comprehensive analytics for model performance monitoring and insights.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import RLock
from collections import deque
import uuid
import statistics


class MetricType(Enum):
    """Types of metrics tracked for models."""
    INFERENCE_COUNT = "inference_count"
    LATENCY = "latency"
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


class AnomalyType(Enum):
    """Types of anomalies detected."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ACCURACY_DROP = "accuracy_drop"
    ERROR_SPIKE = "error_spike"
    LATENCY_SPIKE = "latency_spike"
    RESOURCE_ANOMALY = "resource_anomaly"


class ComparisonMetric(Enum):
    """Metrics used for model comparison."""
    LATENCY = "latency"
    ACCURACY = "accuracy"
    THROUGHPUT = "throughput"
    RELIABILITY = "reliability"
    COST_PER_INFERENCE = "cost_per_inference"
    POWER_EFFICIENCY = "power_efficiency"


@dataclass
class MetricDataPoint:
    """Single metric measurement."""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceRecord:
    """Record of single inference execution."""
    request_id: str
    model_id: str
    model_version: int
    timestamp: datetime
    latency_ms: float
    accuracy: Optional[float]
    error: Optional[str]
    input_tokens: int = 0
    output_tokens: int = 0
    batch_size: int = 1
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelQualityMetrics:
    """Quality metrics for a model over time period."""
    model_id: str
    model_version: int
    total_inferences: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_accuracy: float
    min_accuracy: float
    max_accuracy: float
    avg_precision: float
    avg_recall: float
    avg_f1_score: float
    error_rate_percent: float
    error_types: Dict[str, int]
    throughput_requests_per_sec: float
    period_start: datetime
    period_end: datetime


@dataclass
class PerformanceTrend:
    """Performance trend over time."""
    model_id: str
    metric_type: MetricType
    current_value: float
    previous_value: Optional[float]
    trend: str  # "improving" | "degrading" | "stable"
    change_percent: float
    confidence_score: float
    data_points_count: int


@dataclass
class ModelComparison:
    """Comparison between two model versions."""
    baseline_model_id: str
    baseline_version: int
    comparison_model_id: str
    comparison_version: int
    metrics: Dict[ComparisonMetric, Dict[str, float]]  # {metric: {baseline, comparison, difference}}
    recommendation: str
    winner: str  # "baseline" | "comparison" | "inconclusive"


@dataclass
class DetectedAnomaly:
    """Detected anomaly in model behavior."""
    anomaly_id: str
    model_id: str
    anomaly_type: AnomalyType
    detected_at: datetime
    metric_name: str
    current_value: float
    expected_value: float
    deviation_percent: float
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""
    report_id: str
    model_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    quality_metrics: ModelQualityMetrics
    detected_anomalies: List[DetectedAnomaly]
    performance_trends: List[PerformanceTrend]
    recommendations: List[Dict[str, str]]


class ModelAnalyticsService:
    """Service for comprehensive model analytics and insights."""

    def __init__(self, max_records: int = 100000, max_anomalies: int = 10000):
        """Initialize service."""
        self._lock = RLock()
        self.max_records = max_records
        self.max_anomalies = max_anomalies
        
        # Storage
        self.inference_records: Dict[str, deque] = {}  # model_id -> deque of records
        self.quality_metrics: Dict[str, Dict[int, deque]] = {}  # model_id -> {version -> deque of metrics}
        self.performance_trends: Dict[str, List[PerformanceTrend]] = {}  # model_id -> trends
        self.detected_anomalies: deque = deque(maxlen=max_anomalies)
        self.user_segments: Dict[str, Dict[str, int]] = {}  # model_id -> {segment -> count}
        self.reports: Dict[str, AnalyticsReport] = {}  # report_id -> report
        
        # Event callbacks
        self.callbacks: Dict[str, List] = {
            'metric_recorded': [],
            'anomaly_detected': [],
            'trend_change': [],
            'report_generated': []
        }

    def record_inference(
        self,
        request_id: str,
        model_id: str,
        model_version: int,
        latency_ms: float,
        accuracy: Optional[float] = None,
        error: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        batch_size: int = 1,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Record inference execution."""
        with self._lock:
            if model_id not in self.inference_records:
                self.inference_records[model_id] = deque(maxlen=self.max_records)
            
            record = InferenceRecord(
                request_id=request_id,
                model_id=model_id,
                model_version=model_version,
                timestamp=datetime.utcnow(),
                latency_ms=latency_ms,
                accuracy=accuracy,
                error=error,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                batch_size=batch_size,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            self.inference_records[model_id].append(record)
            
            # Trigger callbacks
            for callback in self.callbacks['metric_recorded']:
                callback(model_id, record)
            
            return request_id

    def get_model_quality_metrics(
        self,
        model_id: str,
        model_version: Optional[int] = None,
        time_period_hours: int = 24
    ) -> Optional[ModelQualityMetrics]:
        """Get quality metrics for model over time period."""
        with self._lock:
            if model_id not in self.inference_records:
                return None
            
            records = list(self.inference_records[model_id])
            if not records:
                return None
            
            # Filter by version if specified
            if model_version:
                records = [r for r in records if r.model_version == model_version]
            
            # Filter by time period
            cutoff_time = datetime.utcnow() - timedelta(hours=time_period_hours)
            records = [r for r in records if r.timestamp >= cutoff_time]
            
            if not records:
                return None
            
            # Calculate metrics
            latencies = [r.latency_ms for r in records]
            accuracies = [r.accuracy for r in records if r.accuracy is not None]
            errors = [r for r in records if r.error is not None]
            
            # Count error types
            error_types: Dict[str, int] = {}
            for err_record in errors:
                error_type = err_record.error.split(':')[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Calculate percentiles
            sorted_latencies = sorted(latencies)
            p50_idx = len(sorted_latencies) // 2
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            
            avg_latency = statistics.mean(latencies)
            avg_accuracy = statistics.mean(accuracies) if accuracies else 0.0
            
            # Calculate throughput (inferences per second)
            time_span_seconds = (records[-1].timestamp - records[0].timestamp).total_seconds()
            throughput = len(records) / max(time_span_seconds, 1)
            
            return ModelQualityMetrics(
                model_id=model_id,
                model_version=model_version or records[0].model_version,
                total_inferences=len(records),
                avg_latency_ms=avg_latency,
                p50_latency_ms=sorted_latencies[p50_idx] if p50_idx < len(sorted_latencies) else 0,
                p95_latency_ms=sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else 0,
                p99_latency_ms=sorted_latencies[p99_idx] if p99_idx < len(sorted_latencies) else 0,
                avg_accuracy=avg_accuracy,
                min_accuracy=min(accuracies) if accuracies else 0.0,
                max_accuracy=max(accuracies) if accuracies else 0.0,
                avg_precision=avg_accuracy * 0.98,  # Estimated
                avg_recall=avg_accuracy * 0.97,  # Estimated
                avg_f1_score=(2 * (avg_accuracy * 0.98 * avg_accuracy * 0.97) / (avg_accuracy * 0.98 + avg_accuracy * 0.97)) if avg_accuracy > 0 else 0,
                error_rate_percent=(len(errors) / len(records) * 100) if records else 0,
                error_types=error_types,
                throughput_requests_per_sec=throughput,
                period_start=records[0].timestamp,
                period_end=records[-1].timestamp
            )

    def detect_anomalies(
        self,
        model_id: str,
        model_version: Optional[int] = None,
        latency_threshold_percentile: float = 0.95,
        accuracy_threshold_percent: float = 2.0
    ) -> List[DetectedAnomaly]:
        """Detect anomalies in model behavior."""
        with self._lock:
            anomalies = []
            
            metrics = self.get_model_quality_metrics(model_id, model_version, time_period_hours=24)
            if not metrics:
                return anomalies
            
            # Get historical baseline (7 days ago)
            baseline = self.get_model_quality_metrics(model_id, model_version, time_period_hours=168)
            
            if not baseline:
                return anomalies
            
            # Latency spike detection
            if metrics.p95_latency_ms > baseline.p95_latency_ms * 1.5:
                anomaly = DetectedAnomaly(
                    anomaly_id=str(uuid.uuid4()),
                    model_id=model_id,
                    anomaly_type=AnomalyType.LATENCY_SPIKE,
                    detected_at=datetime.utcnow(),
                    metric_name="p95_latency_ms",
                    current_value=metrics.p95_latency_ms,
                    expected_value=baseline.p95_latency_ms,
                    deviation_percent=((metrics.p95_latency_ms - baseline.p95_latency_ms) / baseline.p95_latency_ms * 100),
                    severity="high" if metrics.p95_latency_ms > baseline.p95_latency_ms * 2.0 else "medium",
                    description=f"P95 latency increased from {baseline.p95_latency_ms}ms to {metrics.p95_latency_ms}ms"
                )
                anomalies.append(anomaly)
                self.detected_anomalies.append(anomaly)
                for callback in self.callbacks['anomaly_detected']:
                    callback(anomaly)
            
            # Accuracy degradation detection
            if baseline.avg_accuracy > 0 and (baseline.avg_accuracy - metrics.avg_accuracy) > accuracy_threshold_percent:
                anomaly = DetectedAnomaly(
                    anomaly_id=str(uuid.uuid4()),
                    model_id=model_id,
                    anomaly_type=AnomalyType.ACCURACY_DROP,
                    detected_at=datetime.utcnow(),
                    metric_name="avg_accuracy",
                    current_value=metrics.avg_accuracy,
                    expected_value=baseline.avg_accuracy,
                    deviation_percent=-((baseline.avg_accuracy - metrics.avg_accuracy) / baseline.avg_accuracy * 100),
                    severity="critical" if (baseline.avg_accuracy - metrics.avg_accuracy) > 5.0 else "high",
                    description=f"Accuracy degraded from {baseline.avg_accuracy}% to {metrics.avg_accuracy}%"
                )
                anomalies.append(anomaly)
                self.detected_anomalies.append(anomaly)
                for callback in self.callbacks['anomaly_detected']:
                    callback(anomaly)
            
            # Error spike detection
            if metrics.error_rate_percent > baseline.error_rate_percent * 2.0:
                anomaly = DetectedAnomaly(
                    anomaly_id=str(uuid.uuid4()),
                    model_id=model_id,
                    anomaly_type=AnomalyType.ERROR_SPIKE,
                    detected_at=datetime.utcnow(),
                    metric_name="error_rate_percent",
                    current_value=metrics.error_rate_percent,
                    expected_value=baseline.error_rate_percent,
                    deviation_percent=((metrics.error_rate_percent - baseline.error_rate_percent) / max(baseline.error_rate_percent, 0.1) * 100),
                    severity="high",
                    description=f"Error rate increased from {baseline.error_rate_percent}% to {metrics.error_rate_percent}%"
                )
                anomalies.append(anomaly)
                self.detected_anomalies.append(anomaly)
                for callback in self.callbacks['anomaly_detected']:
                    callback(anomaly)
            
            return anomalies

    def analyze_performance_trends(
        self,
        model_id: str,
        model_version: Optional[int] = None,
        lookback_hours: int = 168
    ) -> List[PerformanceTrend]:
        """Analyze performance trends over time."""
        with self._lock:
            trends = []
            
            # Get current and previous metrics
            current = self.get_model_quality_metrics(model_id, model_version, time_period_hours=24)
            previous = self.get_model_quality_metrics(model_id, model_version, time_period_hours=168)
            
            if not current or not previous:
                return trends
            
            # Latency trend
            latency_change = ((current.avg_latency_ms - previous.avg_latency_ms) / previous.avg_latency_ms * 100) if previous.avg_latency_ms > 0 else 0
            trends.append(PerformanceTrend(
                model_id=model_id,
                metric_type=MetricType.LATENCY,
                current_value=current.avg_latency_ms,
                previous_value=previous.avg_latency_ms,
                trend="degrading" if latency_change > 5 else "improving" if latency_change < -5 else "stable",
                change_percent=latency_change,
                confidence_score=0.95,
                data_points_count=current.total_inferences
            ))
            
            # Accuracy trend
            accuracy_change = current.avg_accuracy - previous.avg_accuracy
            trends.append(PerformanceTrend(
                model_id=model_id,
                metric_type=MetricType.ACCURACY,
                current_value=current.avg_accuracy,
                previous_value=previous.avg_accuracy,
                trend="improving" if accuracy_change > 0.5 else "degrading" if accuracy_change < -0.5 else "stable",
                change_percent=(accuracy_change / max(previous.avg_accuracy, 0.1) * 100),
                confidence_score=0.92,
                data_points_count=current.total_inferences
            ))
            
            # Throughput trend
            throughput_change = ((current.throughput_requests_per_sec - previous.throughput_requests_per_sec) / previous.throughput_requests_per_sec * 100) if previous.throughput_requests_per_sec > 0 else 0
            trends.append(PerformanceTrend(
                model_id=model_id,
                metric_type=MetricType.THROUGHPUT,
                current_value=current.throughput_requests_per_sec,
                previous_value=previous.throughput_requests_per_sec,
                trend="improving" if throughput_change > 5 else "degrading" if throughput_change < -5 else "stable",
                change_percent=throughput_change,
                confidence_score=0.90,
                data_points_count=current.total_inferences
            ))
            
            # Error rate trend
            error_change = current.error_rate_percent - previous.error_rate_percent
            trends.append(PerformanceTrend(
                model_id=model_id,
                metric_type=MetricType.ERROR_RATE,
                current_value=current.error_rate_percent,
                previous_value=previous.error_rate_percent,
                trend="degrading" if error_change > 0.5 else "improving" if error_change < -0.5 else "stable",
                change_percent=(error_change / max(previous.error_rate_percent, 0.1) * 100),
                confidence_score=0.88,
                data_points_count=current.total_inferences
            ))
            
            if model_id not in self.performance_trends:
                self.performance_trends[model_id] = []
            
            self.performance_trends[model_id] = trends
            
            # Trigger trend callbacks
            for trend in trends:
                if trend.trend != "stable":
                    for callback in self.callbacks['trend_change']:
                        callback(trend)
            
            return trends

    def compare_model_versions(
        self,
        baseline_model_id: str,
        baseline_version: int,
        comparison_model_id: str,
        comparison_version: int
    ) -> ModelComparison:
        """Compare two model versions."""
        with self._lock:
            baseline_metrics = self.get_model_quality_metrics(baseline_model_id, baseline_version)
            comparison_metrics = self.get_model_quality_metrics(comparison_model_id, comparison_version)
            
            if not baseline_metrics or not comparison_metrics:
                raise ValueError("Models not found for comparison")
            
            metrics_dict = {
                ComparisonMetric.LATENCY: {
                    "baseline": baseline_metrics.avg_latency_ms,
                    "comparison": comparison_metrics.avg_latency_ms,
                    "difference": baseline_metrics.avg_latency_ms - comparison_metrics.avg_latency_ms
                },
                ComparisonMetric.ACCURACY: {
                    "baseline": baseline_metrics.avg_accuracy,
                    "comparison": comparison_metrics.avg_accuracy,
                    "difference": comparison_metrics.avg_accuracy - baseline_metrics.avg_accuracy
                },
                ComparisonMetric.THROUGHPUT: {
                    "baseline": baseline_metrics.throughput_requests_per_sec,
                    "comparison": comparison_metrics.throughput_requests_per_sec,
                    "difference": comparison_metrics.throughput_requests_per_sec - baseline_metrics.throughput_requests_per_sec
                },
                ComparisonMetric.RELIABILITY: {
                    "baseline": 100 - baseline_metrics.error_rate_percent,
                    "comparison": 100 - comparison_metrics.error_rate_percent,
                    "difference": (100 - comparison_metrics.error_rate_percent) - (100 - baseline_metrics.error_rate_percent)
                }
            }
            
            # Determine winner
            baseline_wins = 0
            comparison_wins = 0
            
            if metrics_dict[ComparisonMetric.LATENCY]["difference"] < 0:
                comparison_wins += 1
            else:
                baseline_wins += 1
            
            if metrics_dict[ComparisonMetric.ACCURACY]["difference"] > 0:
                comparison_wins += 1
            else:
                baseline_wins += 1
            
            if metrics_dict[ComparisonMetric.THROUGHPUT]["difference"] > 0:
                comparison_wins += 1
            else:
                baseline_wins += 1
            
            winner = "comparison" if comparison_wins > baseline_wins else "baseline" if baseline_wins > comparison_wins else "inconclusive"
            
            recommendation = f"{'Comparison' if winner == 'comparison' else 'Baseline'} model is recommended with {abs(comparison_wins - baseline_wins)} metric advantages"
            
            return ModelComparison(
                baseline_model_id=baseline_model_id,
                baseline_version=baseline_version,
                comparison_model_id=comparison_model_id,
                comparison_version=comparison_version,
                metrics=metrics_dict,
                recommendation=recommendation,
                winner=winner
            )

    def generate_report(
        self,
        model_id: str,
        model_version: Optional[int] = None,
        time_period_hours: int = 24
    ) -> AnalyticsReport:
        """Generate comprehensive analytics report."""
        with self._lock:
            report_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            quality_metrics = self.get_model_quality_metrics(model_id, model_version, time_period_hours)
            if not quality_metrics:
                raise ValueError(f"No data for model {model_id}")
            
            anomalies = self.detect_anomalies(model_id, model_version)
            trends = self.analyze_performance_trends(model_id, model_version)
            
            # Generate recommendations
            recommendations = []
            
            for trend in trends:
                if trend.trend == "degrading":
                    recommendations.append({
                        "type": trend.metric_type.value,
                        "action": f"Investigate {trend.metric_type.value} degradation trend",
                        "priority": "high" if trend.change_percent > 10 else "medium"
                    })
            
            for anomaly in anomalies:
                recommendations.append({
                    "type": anomaly.anomaly_type.value,
                    "action": f"Address {anomaly.anomaly_type.value}: {anomaly.description}",
                    "priority": anomaly.severity
                })
            
            report = AnalyticsReport(
                report_id=report_id,
                model_id=model_id,
                generated_at=now,
                period_start=quality_metrics.period_start,
                period_end=quality_metrics.period_end,
                quality_metrics=quality_metrics,
                detected_anomalies=anomalies,
                performance_trends=trends,
                recommendations=recommendations
            )
            
            self.reports[report_id] = report
            
            # Trigger callback
            for callback in self.callbacks['report_generated']:
                callback(report)
            
            return report

    def get_user_segment_analytics(
        self,
        model_id: str,
        model_version: Optional[int] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze model performance by user segment."""
        with self._lock:
            if model_id not in self.inference_records:
                return {}
            
            records = list(self.inference_records[model_id])
            if model_version:
                records = [r for r in records if r.model_version == model_version]
            
            segments = {}
            
            for record in records:
                user_id = record.user_id or "anonymous"
                if user_id not in segments:
                    segments[user_id] = {
                        "count": 0,
                        "avg_latency": 0,
                        "total_latency": 0,
                        "avg_accuracy": 0,
                        "total_accuracy": 0,
                        "accuracy_count": 0,
                        "error_count": 0
                    }
                
                seg = segments[user_id]
                seg["count"] += 1
                seg["total_latency"] += record.latency_ms
                
                if record.accuracy is not None:
                    seg["total_accuracy"] += record.accuracy
                    seg["accuracy_count"] += 1
                
                if record.error:
                    seg["error_count"] += 1
            
            # Calculate averages
            for user_id, seg in segments.items():
                seg["avg_latency"] = seg["total_latency"] / seg["count"] if seg["count"] > 0 else 0
                seg["avg_accuracy"] = seg["total_accuracy"] / seg["accuracy_count"] if seg["accuracy_count"] > 0 else 0
                seg["error_rate"] = seg["error_count"] / seg["count"] * 100 if seg["count"] > 0 else 0
            
            return segments

    def register_callback(self, event_type: str, callback):
        """Register callback for event."""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        with self._lock:
            total_records = sum(len(records) for records in self.inference_records.values())
            
            return {
                "total_inferences_tracked": total_records,
                "total_models_tracked": len(self.inference_records),
                "total_anomalies_detected": len(self.detected_anomalies),
                "total_reports_generated": len(self.reports),
                "anomalies_by_type": {
                    anomaly_type.value: sum(1 for a in self.detected_anomalies if a.anomaly_type == anomaly_type)
                    for anomaly_type in AnomalyType
                },
                "models_with_data": list(self.inference_records.keys()),
                "capacity_used_percent": (total_records / (self.max_records * len(self.inference_records)) * 100) if self.inference_records else 0
            }

    def health_check(self) -> Dict[str, Any]:
        """Health check status."""
        with self._lock:
            return {
                "status": "healthy",
                "service": "model_analytics",
                "records_in_memory": sum(len(records) for records in self.inference_records.values()),
                "anomalies_detected": len(self.detected_anomalies),
                "models_tracked": len(self.inference_records),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global service instance
_analytics_service: Optional[ModelAnalyticsService] = None


def get_analytics_service() -> ModelAnalyticsService:
    """Get or create service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = ModelAnalyticsService()
    return _analytics_service
