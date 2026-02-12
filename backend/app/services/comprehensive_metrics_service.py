"""
Comprehensive metrics service for system observability.
Handles metric collection, aggregation, analysis, and alerting.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json
import uuid
from collections import defaultdict
import threading
import statistics


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AggregationPeriod(Enum):
    """Aggregation time periods."""
    MINUTE = "minute"
    FIVE_MINUTES = "five_minutes"
    FIFTEEN_MINUTES = "fifteen_minutes"
    HOUR = "hour"
    DAY = "day"


@dataclass
class MetricLabel:
    """Label for metric dimensionality."""
    name: str
    value: str


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    unit: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Metric definition with data."""
    metric_id: str
    name: str
    metric_type: MetricType
    workspace_id: str
    service_name: str
    description: Optional[str] = None
    unit: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    data_points: List[MetricPoint] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['created_at'] = self.created_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data


@dataclass
class AggregatedMetrics:
    """Aggregated metric statistics."""
    metric_name: str
    period: AggregationPeriod
    start_time: datetime
    end_time: datetime
    count: int
    sum: float
    min: float
    max: float
    mean: float
    median: float
    p95: float
    p99: float
    stddev: float
    labels: Dict[str, str]


@dataclass
class MetricAlert:
    """Alert definition for metrics."""
    alert_id: str
    metric_name: str
    condition: str  # ">, <, ==, !=, >=, <="
    threshold: float
    duration_seconds: int
    workspace_id: str
    enabled: bool = True
    alert_message: Optional[str] = None
    severity: str = "medium"  # critical, high, medium, low
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class AlertEvent:
    """Alert event when threshold is breached."""
    alert_id: str
    metric_name: str
    timestamp: datetime
    triggered_value: float
    threshold: float
    severity: str
    workspace_id: str
    message: str


class MetricFilter:
    """Filter criteria for metrics."""

    def __init__(self,
                 workspace_id: Optional[str] = None,
                 service_name: Optional[str] = None,
                 metric_names: Optional[List[str]] = None,
                 metric_type: Optional[MetricType] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 labels: Optional[Dict[str, str]] = None):
        self.workspace_id = workspace_id
        self.service_name = service_name
        self.metric_names = metric_names or []
        self.metric_type = metric_type
        self.start_time = start_time
        self.end_time = end_time
        self.labels = labels or {}


class ComprehensiveMetricsService:
    """
    Comprehensive metrics service for system observability.

    Features:
    - Multiple metric types (counter, gauge, histogram, summary)
    - Time-series data collection and storage
    - Aggregation across time windows
    - Percentile calculations (p50, p95, p99)
    - Metric labels and dimensions
    - Alert definitions and conditions
    - Cardinality management
    - Data retention policies
    - Real-time metric streaming
    - Service-level metrics
    """

    def __init__(self,
                 max_metrics: int = 100000,
                 max_data_points: int = 1000000,
                 retention_days: int = 30):
        """Initialize metrics service."""
        self.max_metrics = max_metrics
        self.max_data_points = max_data_points
        self.retention_days = retention_days

        # Storage
        self.metrics: Dict[str, Metric] = {}
        self.metric_index: Dict[str, List[str]] = defaultdict(list)  # workspace_id -> metric_ids
        self.alerts: Dict[str, MetricAlert] = {}
        self.alert_events: List[AlertEvent] = []

        # Aggregated data
        self.aggregated: Dict[Tuple, AggregatedMetrics] = {}  # (metric_name, period, start_time) -> data

        # Thresholds and baselines
        self.thresholds: Dict[str, float] = {}
        self.baselines: Dict[str, float] = {}

        # Tracking
        self.alert_state: Dict[str, bool] = {}  # metric_name -> is_alerting
        self.metric_cardinality: Dict[str, int] = defaultdict(int)

        # Threading
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.running = False

        # Callbacks
        self.metric_callbacks: List[callable] = []
        self.alert_callbacks: List[callable] = []

    def start(self):
        """Start the metrics service."""
        with self.lock:
            if self.running:
                return
            self.running = True

    def stop(self):
        """Stop the metrics service."""
        with self.lock:
            self.running = False

    def record_metric(self,
                     workspace_id: str,
                     metric_name: str,
                     metric_type: MetricType,
                     value: float,
                     service_name: str,
                     labels: Optional[Dict[str, str]] = None,
                     unit: Optional[str] = None,
                     timestamp: Optional[datetime] = None) -> Metric:
        """Record a metric value."""
        timestamp = timestamp or datetime.utcnow()
        labels = labels or {}

        metric_key = self._build_metric_key(metric_name, labels)

        with self.lock:
            # Get or create metric
            if metric_key not in self.metrics:
                metric_id = str(uuid.uuid4())
                metric = Metric(
                    metric_id=metric_id,
                    name=metric_name,
                    metric_type=metric_type,
                    workspace_id=workspace_id,
                    service_name=service_name,
                    unit=unit,
                    labels=labels,
                )
                self.metrics[metric_key] = metric
                self.metric_index[workspace_id].append(metric_id)
            else:
                metric = self.metrics[metric_key]

            # Add data point
            point = MetricPoint(
                timestamp=timestamp,
                value=value,
                unit=unit,
                labels=labels,
            )
            metric.data_points.append(point)
            metric.last_updated = datetime.utcnow()

            # Enforce size limits
            if len(metric.data_points) > 10000:
                metric.data_points = metric.data_points[-10000:]

            # Update cardinality
            cardinality_key = f"{workspace_id}_{metric_name}"
            self.metric_cardinality[cardinality_key] = len(set(
                json.dumps(point.labels, sort_keys=True)
                for point in metric.data_points
            ))

            # Check alerts
            self._check_alerts(metric_name, value, workspace_id)

            # Invoke callbacks
            for callback in self.metric_callbacks:
                try:
                    callback(metric)
                except Exception:
                    pass

            return metric

    def record_counter(self,
                      workspace_id: str,
                      metric_name: str,
                      increment: float,
                      service_name: str,
                      labels: Optional[Dict[str, str]] = None,
                      **kwargs) -> Metric:
        """Record a counter metric (monotonically increasing)."""
        return self.record_metric(
            workspace_id,
            metric_name,
            MetricType.COUNTER,
            increment,
            service_name,
            labels,
            **kwargs
        )

    def record_gauge(self,
                    workspace_id: str,
                    metric_name: str,
                    value: float,
                    service_name: str,
                    labels: Optional[Dict[str, str]] = None,
                    **kwargs) -> Metric:
        """Record a gauge metric (absolute value)."""
        return self.record_metric(
            workspace_id,
            metric_name,
            MetricType.GAUGE,
            value,
            service_name,
            labels,
            **kwargs
        )

    def record_histogram(self,
                        workspace_id: str,
                        metric_name: str,
                        value: float,
                        service_name: str,
                        labels: Optional[Dict[str, str]] = None,
                        **kwargs) -> Metric:
        """Record a histogram metric (distribution of values)."""
        return self.record_metric(
            workspace_id,
            metric_name,
            MetricType.HISTOGRAM,
            value,
            service_name,
            labels,
            **kwargs
        )

    def record_summary(self,
                      workspace_id: str,
                      metric_name: str,
                      value: float,
                      service_name: str,
                      labels: Optional[Dict[str, str]] = None,
                      **kwargs) -> Metric:
        """Record a summary metric (pre-calculated percentiles)."""
        return self.record_metric(
            workspace_id,
            metric_name,
            MetricType.SUMMARY,
            value,
            service_name,
            labels,
            **kwargs
        )

    def get_metric(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Metric]:
        """Get a specific metric."""
        metric_key = self._build_metric_key(metric_name, labels or {})
        with self.lock:
            return self.metrics.get(metric_key)

    def get_metrics(self, workspace_id: str, filter: Optional[MetricFilter] = None) -> List[Metric]:
        """Get metrics matching filter criteria."""
        filter = filter or MetricFilter()

        with self.lock:
            results = []

            for metric_id in self.metric_index.get(workspace_id, []):
                for metric in self.metrics.values():
                    if metric.metric_id != metric_id:
                        continue

                    # Apply filters
                    if filter.service_name and metric.service_name != filter.service_name:
                        continue

                    if filter.metric_names and metric.name not in filter.metric_names:
                        continue

                    if filter.metric_type and metric.metric_type != filter.metric_type:
                        continue

                    if filter.labels:
                        if not all(metric.labels.get(k) == v for k, v in filter.labels.items()):
                            continue

                    # Time range filter on data points
                    if filter.start_time or filter.end_time:
                        filtered_points = [
                            p for p in metric.data_points
                            if (not filter.start_time or p.timestamp >= filter.start_time) and
                               (not filter.end_time or p.timestamp <= filter.end_time)
                        ]
                        if not filtered_points:
                            continue

                    results.append(metric)
                    break

            return results

    def aggregate_metric(self,
                        metric_name: str,
                        period: AggregationPeriod = AggregationPeriod.MINUTE,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        labels: Optional[Dict[str, str]] = None) -> Optional[AggregatedMetrics]:
        """Aggregate metric over time period."""
        metric = self.get_metric(metric_name, labels)
        if not metric:
            return None

        start_time = start_time or (datetime.utcnow() - timedelta(hours=1))
        end_time = end_time or datetime.utcnow()

        with self.lock:
            # Filter data points
            points = [
                p.value for p in metric.data_points
                if start_time <= p.timestamp <= end_time
            ]

            if not points:
                return None

            # Calculate statistics
            sorted_points = sorted(points)
            agg = AggregatedMetrics(
                metric_name=metric_name,
                period=period,
                start_time=start_time,
                end_time=end_time,
                count=len(points),
                sum=sum(points),
                min=min(points),
                max=max(points),
                mean=sum(points) / len(points),
                median=sorted_points[len(points) // 2],
                p95=sorted_points[int(len(points) * 0.95)] if len(points) > 0 else 0,
                p99=sorted_points[int(len(points) * 0.99)] if len(points) > 0 else 0,
                stddev=statistics.stdev(points) if len(points) > 1 else 0,
                labels=labels or {},
            )

            return agg

    def create_alert(self,
                    metric_name: str,
                    condition: str,
                    threshold: float,
                    duration_seconds: int,
                    workspace_id: str,
                    severity: str = "medium",
                    alert_message: Optional[str] = None,
                    notification_channels: Optional[List[str]] = None) -> MetricAlert:
        """Create an alert for a metric."""
        alert_id = str(uuid.uuid4())

        with self.lock:
            alert = MetricAlert(
                alert_id=alert_id,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                duration_seconds=duration_seconds,
                workspace_id=workspace_id,
                severity=severity,
                alert_message=alert_message,
                notification_channels=notification_channels or [],
            )
            self.alerts[alert_id] = alert

            return alert

    def remove_alert(self, alert_id: str):
        """Remove an alert."""
        with self.lock:
            if alert_id in self.alerts:
                del self.alerts[alert_id]

    def get_alert_events(self,
                        workspace_id: str,
                        limit: int = 100,
                        severity: Optional[str] = None) -> List[AlertEvent]:
        """Get alert events."""
        with self.lock:
            events = [
                e for e in self.alert_events
                if e.workspace_id == workspace_id
            ]

            if severity:
                events = [e for e in events if e.severity == severity]

            return events[-limit:]

    def _check_alerts(self, metric_name: str, value: float, workspace_id: str):
        """Check if any alerts are triggered."""
        for alert_id, alert in self.alerts.items():
            if alert.metric_name != metric_name or alert.workspace_id != workspace_id:
                continue

            triggered = False
            if alert.condition == ">":
                triggered = value > alert.threshold
            elif alert.condition == "<":
                triggered = value < alert.threshold
            elif alert.condition == ">=":
                triggered = value >= alert.threshold
            elif alert.condition == "<=":
                triggered = value <= alert.threshold
            elif alert.condition == "==":
                triggered = value == alert.threshold
            elif alert.condition == "!=":
                triggered = value != alert.threshold

            if triggered:
                event = AlertEvent(
                    alert_id=alert_id,
                    metric_name=metric_name,
                    timestamp=datetime.utcnow(),
                    triggered_value=value,
                    threshold=alert.threshold,
                    severity=alert.severity,
                    workspace_id=workspace_id,
                    message=alert.alert_message or f"Alert: {metric_name} {alert.condition} {alert.threshold}",
                )
                self.alert_events.append(event)

                # Invoke callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(event)
                    except Exception:
                        pass

                # Enforce alert event size limit
                if len(self.alert_events) > 10000:
                    self.alert_events = self.alert_events[-10000:]

    def set_threshold(self, metric_name: str, threshold: float):
        """Set an expected threshold for a metric."""
        with self.lock:
            self.thresholds[metric_name] = threshold

    def set_baseline(self, metric_name: str, baseline: float):
        """Set a baseline value for a metric."""
        with self.lock:
            self.baselines[metric_name] = baseline

    def get_metric_comparison(self,
                             metric_name: str,
                             current_value: float) -> Dict[str, Any]:
        """Compare metric value to baseline and threshold."""
        with self.lock:
            baseline = self.baselines.get(metric_name)
            threshold = self.thresholds.get(metric_name)

            comparison = {
                "current_value": current_value,
                "baseline": baseline,
                "threshold": threshold,
            }

            if baseline:
                comparison["vs_baseline_pct"] = ((current_value - baseline) / baseline) * 100

            if threshold:
                comparison["vs_threshold"] = "OK" if current_value <= threshold else "EXCEEDED"

            return comparison

    def add_metric_callback(self, callback: callable):
        """Add callback for new metrics."""
        with self.lock:
            self.metric_callbacks.append(callback)

    def add_alert_callback(self, callback: callable):
        """Add callback for alert events."""
        with self.lock:
            self.alert_callbacks.append(callback)

    def cleanup_old_data(self, workspace_id: Optional[str] = None):
        """Clean up data older than retention policy."""
        cutoff_time = datetime.utcnow() - timedelta(days=self.retention_days)

        with self.lock:
            for metric in self.metrics.values():
                if workspace_id and metric.workspace_id != workspace_id:
                    continue

                metric.data_points = [
                    p for p in metric.data_points
                    if p.timestamp > cutoff_time
                ]

    def get_stats(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics service statistics."""
        with self.lock:
            total_metrics = len(self.metrics)
            total_data_points = sum(len(m.data_points) for m in self.metrics.values())
            total_alerts = len(self.alerts)
            active_alerts = sum(1 for e in self.alert_events if (
                datetime.utcnow() - e.timestamp).total_seconds() < 3600)

            return {
                "total_metrics": total_metrics,
                "total_data_points": total_data_points,
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "alert_events": len(self.alert_events),
                "cardinality": dict(self.metric_cardinality),
            }

    def _build_metric_key(self, metric_name: str, labels: Dict[str, str]) -> str:
        """Build unique key for metric with labels."""
        label_str = json.dumps(labels, sort_keys=True) if labels else ""
        return f"{metric_name}:{label_str}"
