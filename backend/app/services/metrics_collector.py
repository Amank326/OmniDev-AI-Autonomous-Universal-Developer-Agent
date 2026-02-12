"""
Metrics Collector Service
Prometheus metrics collection, aggregation, and exposure for observability
Phase 42: Observability & Monitoring Infrastructure
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from threading import RLock, Thread
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Prometheus metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricUnit(Enum):
    """Standard metric units"""
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    MICROSECONDS = "microseconds"
    BYTES = "bytes"
    REQUESTS = "requests"
    ERRORS = "errors"
    OPERATIONS = "operations"
    PERCENT = "percent"


@dataclass
class MetricLabel:
    """Label for metric"""
    name: str
    value: str


@dataclass
class MetricSample:
    """Individual metric sample"""
    timestamp: datetime
    value: float
    labels: List[MetricLabel] = field(default_factory=list)


@dataclass
class Metric:
    """Base metric definition"""
    name: str
    type: MetricType
    help_text: str
    unit: MetricUnit
    samples: List[MetricSample] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_sample(self, value: float, labels: Optional[List[MetricLabel]] = None) -> None:
        """Add sample to metric"""
        sample = MetricSample(
            timestamp=datetime.utcnow(),
            value=value,
            labels=labels or []
        )
        self.samples.append(sample)
    
    def get_latest_value(self) -> Optional[float]:
        """Get latest sample value"""
        if self.samples:
            return self.samples[-1].value
        return None
    
    def get_value_by_labels(self, labels: Dict[str, str]) -> Optional[float]:
        """Get value for specific label combination"""
        for sample in reversed(self.samples):
            if self._labels_match(sample.labels, labels):
                return sample.value
        return None
    
    @staticmethod
    def _labels_match(sample_labels: List[MetricLabel], target_labels: Dict[str, str]) -> bool:
        """Check if sample labels match target"""
        sample_dict = {l.name: l.value for l in sample_labels}
        return all(
            sample_dict.get(k) == v
            for k, v in target_labels.items()
        )
    
    def get_statistics(self) -> Dict[str, float]:
        """Calculate metric statistics"""
        if not self.samples:
            return {}
        
        values = [s.value for s in self.samples]
        
        stats = {
            'count': len(values),
            'latest': values[-1],
            'min': min(values),
            'max': max(values),
            'sum': sum(values),
            'mean': sum(values) / len(values),
        }
        
        # Calculate rate (per second)
        if len(self.samples) > 1:
            time_diff = (self.samples[-1].timestamp - self.samples[0].timestamp).total_seconds()
            if time_diff > 0:
                value_diff = values[-1] - values[0]
                stats['rate'] = value_diff / time_diff
        
        return stats


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: datetime
    metrics: Dict[str, Any]
    
    def to_prometheus_format(self) -> str:
        """Convert to Prometheus text exposition format"""
        lines = []
        lines.append(f"# HELP snapshot MetricSnapshot at {self.timestamp.isoformat()}")
        lines.append("# TYPE snapshot gauge")
        
        for metric_name, value in self.metrics.items():
            if isinstance(value, (int, float)):
                lines.append(f"{metric_name} {value}")
        
        return "\n".join(lines)


class MetricsCollector:
    """Collects and manages metrics"""
    
    def __init__(self, retention_seconds: int = 3600):
        self.metrics: Dict[str, Metric] = {}
        self.retention_seconds = retention_seconds
        self.lock = RLock()
        self.callbacks: List[Callable] = []
        self.snapshots: List[MetricSnapshot] = []
        self._cleanup_thread = None
        self._start_cleanup()
    
    def register_metric(self, name: str, metric_type: MetricType, 
                       help_text: str, unit: MetricUnit = MetricUnit.OPERATIONS) -> Metric:
        """Register a new metric"""
        with self.lock:
            metric = Metric(
                name=name,
                type=metric_type,
                help_text=help_text,
                unit=unit
            )
            self.metrics[name] = metric
            logger.info(f"Registered metric: {name}")
            return metric
    
    def record_metric(self, name: str, value: float, 
                     labels: Optional[Dict[str, str]] = None) -> None:
        """Record metric value"""
        with self.lock:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not registered")
                return
            
            metric_labels = []
            if labels:
                metric_labels = [MetricLabel(k, v) for k, v in labels.items()]
            
            metric.add_sample(value, metric_labels)
            self._trigger_callbacks(metric)
    
    def increment_counter(self, name: str, amount: float = 1.0,
                         labels: Optional[Dict[str, str]] = None) -> None:
        """Increment counter metric"""
        with self.lock:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Counter {name} not registered")
                return
            
            latest = metric.get_latest_value() or 0.0
            metric_labels = []
            if labels:
                metric_labels = [MetricLabel(k, v) for k, v in labels.items()]
            
            metric.add_sample(latest + amount, metric_labels)
            self._trigger_callbacks(metric)
    
    def set_gauge(self, name: str, value: float,
                 labels: Optional[Dict[str, str]] = None) -> None:
        """Set gauge metric"""
        with self.lock:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Gauge {name} not registered")
                return
            
            metric_labels = []
            if labels:
                metric_labels = [MetricLabel(k, v) for k, v in labels.items()]
            
            metric.add_sample(value, metric_labels)
            self._trigger_callbacks(metric)
    
    def observe_histogram(self, name: str, value: float,
                         labels: Optional[Dict[str, str]] = None) -> None:
        """Record histogram observation"""
        self.record_metric(name, value, labels)
    
    def take_snapshot(self) -> MetricSnapshot:
        """Take snapshot of current metrics"""
        with self.lock:
            metrics_data = {}
            
            for metric_name, metric in self.metrics.items():
                latest = metric.get_latest_value()
                if latest is not None:
                    metrics_data[metric_name] = {
                        'value': latest,
                        'type': metric.type.value,
                        'unit': metric.unit.value,
                        'stats': metric.get_statistics()
                    }
            
            snapshot = MetricSnapshot(
                timestamp=datetime.utcnow(),
                metrics=metrics_data
            )
            
            self.snapshots.append(snapshot)
            return snapshot
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get metric by name"""
        with self.lock:
            return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics"""
        with self.lock:
            return dict(self.metrics)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self.lock:
            summary = {
                'total_metrics': len(self.metrics),
                'by_type': defaultdict(int),
                'metrics': {}
            }
            
            for metric_name, metric in self.metrics.items():
                summary['by_type'][metric.type.value] += 1
                summary['metrics'][metric_name] = {
                    'type': metric.type.value,
                    'samples': len(metric.samples),
                    'latest': metric.get_latest_value(),
                    'stats': metric.get_statistics()
                }
            
            return dict(summary)
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text exposition format"""
        lines = []
        
        with self.lock:
            for metric_name, metric in self.metrics.items():
                # Add HELP and TYPE lines
                lines.append(f"# HELP {metric_name} {metric.help_text}")
                lines.append(f"# TYPE {metric_name} {metric.type.value}")
                
                # Add samples
                latest_sample = metric.samples[-1] if metric.samples else None
                if latest_sample:
                    labels_str = ""
                    if latest_sample.labels:
                        label_pairs = [f'{l.name}="{l.value}"' for l in latest_sample.labels]
                        labels_str = "{" + ",".join(label_pairs) + "}"
                    
                    timestamp_ms = int(latest_sample.timestamp.timestamp() * 1000)
                    lines.append(f"{metric_name}{labels_str} {latest_sample.value} {timestamp_ms}")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def get_alert_candidates(self, threshold: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify metrics exceeding thresholds"""
        candidates = []
        
        with self.lock:
            for metric_name, threshold_value in threshold.items():
                metric = self.metrics.get(metric_name)
                if metric:
                    latest = metric.get_latest_value()
                    if latest and latest > threshold_value:
                        candidates.append({
                            'metric': metric_name,
                            'threshold': threshold_value,
                            'current': latest,
                            'exceeds_by': latest - threshold_value,
                            'timestamp': metric.samples[-1].timestamp if metric.samples else None
                        })
        
        return candidates
    
    def register_callback(self, callback: Callable[[Metric], None]) -> None:
        """Register callback for metric updates"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callbacks(self, metric: Metric) -> None:
        """Trigger callbacks for metric"""
        for callback in self.callbacks:
            try:
                callback(metric)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _start_cleanup(self) -> None:
        """Start cleanup thread for old samples"""
        self._cleanup_thread = Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_loop(self) -> None:
        """Periodically clean up old samples"""
        while True:
            try:
                time.sleep(60)  # Clean up every minute
                self._cleanup_old_samples()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _cleanup_old_samples(self) -> None:
        """Remove samples older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.retention_seconds)
        
        with self.lock:
            for metric in self.metrics.values():
                # Keep only recent samples
                metric.samples = [
                    s for s in metric.samples
                    if s.timestamp > cutoff_time
                ]


# Standard system metrics
class SystemMetricsCollector:
    """Collects system-level metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector
        self._register_system_metrics()
    
    def _register_system_metrics(self) -> None:
        """Register standard system metrics"""
        self.collector.register_metric(
            "cpu_usage_percent",
            MetricType.GAUGE,
            "CPU usage percentage",
            MetricUnit.PERCENT
        )
        self.collector.register_metric(
            "memory_usage_bytes",
            MetricType.GAUGE,
            "Memory usage in bytes",
            MetricUnit.BYTES
        )
        self.collector.register_metric(
            "disk_usage_bytes",
            MetricType.GAUGE,
            "Disk usage in bytes",
            MetricUnit.BYTES
        )
        self.collector.register_metric(
            "network_requests_total",
            MetricType.COUNTER,
            "Total network requests",
            MetricUnit.REQUESTS
        )
        self.collector.register_metric(
            "network_request_duration_ms",
            MetricType.HISTOGRAM,
            "Network request duration",
            MetricUnit.MILLISECONDS
        )
    
    def record_cpu_usage(self, percent: float) -> None:
        """Record CPU usage"""
        self.collector.set_gauge("cpu_usage_percent", percent)
    
    def record_memory_usage(self, bytes_used: float) -> None:
        """Record memory usage"""
        self.collector.set_gauge("memory_usage_bytes", bytes_used)
    
    def record_disk_usage(self, bytes_used: float) -> None:
        """Record disk usage"""
        self.collector.set_gauge("disk_usage_bytes", bytes_used)
    
    def increment_requests(self, amount: float = 1.0,
                          labels: Optional[Dict[str, str]] = None) -> None:
        """Increment request counter"""
        self.collector.increment_counter("network_requests_total", amount, labels)
    
    def record_request_duration(self, duration_ms: float,
                               labels: Optional[Dict[str, str]] = None) -> None:
        """Record request duration"""
        self.collector.observe_histogram("network_request_duration_ms", duration_ms, labels)


# Application metrics
class ApplicationMetricsCollector:
    """Collects application-level metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector
        self._register_app_metrics()
    
    def _register_app_metrics(self) -> None:
        """Register application metrics"""
        self.collector.register_metric(
            "api_requests_total",
            MetricType.COUNTER,
            "Total API requests",
            MetricUnit.REQUESTS
        )
        self.collector.register_metric(
            "api_request_duration_ms",
            MetricType.HISTOGRAM,
            "API request duration",
            MetricUnit.MILLISECONDS
        )
        self.collector.register_metric(
            "api_errors_total",
            MetricType.COUNTER,
            "Total API errors",
            MetricUnit.ERRORS
        )
        self.collector.register_metric(
            "database_queries_total",
            MetricType.COUNTER,
            "Total database queries",
            MetricUnit.OPERATIONS
        )
        self.collector.register_metric(
            "database_query_duration_ms",
            MetricType.HISTOGRAM,
            "Database query duration",
            MetricUnit.MILLISECONDS
        )
        self.collector.register_metric(
            "cache_hits_total",
            MetricType.COUNTER,
            "Total cache hits",
            MetricUnit.OPERATIONS
        )
        self.collector.register_metric(
            "cache_misses_total",
            MetricType.COUNTER,
            "Total cache misses",
            MetricUnit.OPERATIONS
        )
        self.collector.register_metric(
            "active_connections",
            MetricType.GAUGE,
            "Number of active connections",
            MetricUnit.OPERATIONS
        )
    
    def record_api_request(self, duration_ms: float,
                          status_code: int, endpoint: str) -> None:
        """Record API request"""
        labels = {'endpoint': endpoint, 'status': str(status_code)}
        self.collector.increment_counter("api_requests_total", labels=labels)
        self.collector.observe_histogram("api_request_duration_ms", duration_ms, labels)
        
        if status_code >= 400:
            self.collector.increment_counter("api_errors_total", labels={'status': str(status_code)})
    
    def record_database_query(self, duration_ms: float, query_type: str) -> None:
        """Record database query"""
        labels = {'query_type': query_type}
        self.collector.increment_counter("database_queries_total", labels=labels)
        self.collector.observe_histogram("database_query_duration_ms", duration_ms, labels)
    
    def record_cache_hit(self, cache_name: str) -> None:
        """Record cache hit"""
        self.collector.increment_counter("cache_hits_total", labels={'cache': cache_name})
    
    def record_cache_miss(self, cache_name: str) -> None:
        """Record cache miss"""
        self.collector.increment_counter("cache_misses_total", labels={'cache': cache_name})
    
    def set_active_connections(self, count: int) -> None:
        """Set active connection count"""
        self.collector.set_gauge("active_connections", float(count))


# Global collectors
_metrics_collector: Optional[MetricsCollector] = None
_system_metrics: Optional[SystemMetricsCollector] = None
_app_metrics: Optional[ApplicationMetricsCollector] = None


def get_metrics_collector(retention_seconds: int = 3600) -> MetricsCollector:
    """Get or create metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(retention_seconds)
    return _metrics_collector


def get_system_metrics() -> SystemMetricsCollector:
    """Get system metrics collector"""
    global _system_metrics
    if _system_metrics is None:
        _system_metrics = SystemMetricsCollector(get_metrics_collector())
    return _system_metrics


def get_app_metrics() -> ApplicationMetricsCollector:
    """Get application metrics collector"""
    global _app_metrics
    if _app_metrics is None:
        _app_metrics = ApplicationMetricsCollector(get_metrics_collector())
    return _app_metrics
