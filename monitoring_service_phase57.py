"""
Phase 57: Monitoring & Observability - Core Services
Health checks, metrics collection, performance monitoring, distributed tracing,
and comprehensive observability system.
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import time
import json
from threading import Lock
from collections import defaultdict, deque
import hashlib


# ===================== ENUMS =====================

class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MetricType(str, Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    RESOLVED = "resolved"


class TraceLevel(str, Enum):
    """Trace detail level."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


# ===================== DATACLASSES =====================

@dataclass
class HealthCheckResult:
    """Health check result."""
    service_name: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'service_name': self.service_name,
            'status': self.status.value,
            'response_time_ms': self.response_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'message': self.message,
            'details': self.details
        }


@dataclass
class Metric:
    """Single metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels
        }


@dataclass
class TraceSpan:
    """Distributed trace span."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation: str
    service: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    level: TraceLevel = TraceLevel.INFO
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "success"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'operation': self.operation,
            'service': self.service,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration_ms,
            'level': self.level.value,
            'tags': self.tags,
            'logs': self.logs,
            'status': self.status
        }


@dataclass
class Alert:
    """Alert notification."""
    alert_id: str
    service: str
    severity: AlertSeverity
    message: str
    metric_name: str
    threshold: float
    current_value: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'alert_id': self.alert_id,
            'service': self.service,
            'severity': self.severity.value,
            'message': self.message,
            'metric_name': self.metric_name,
            'threshold': self.threshold,
            'current_value': self.current_value,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'metadata': self.metadata
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics summary."""
    service: str
    request_count: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'service': self.service,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'min_response_time_ms': round(self.min_response_time_ms, 2),
            'max_response_time_ms': round(self.max_response_time_ms, 2),
            'p50_response_time_ms': round(self.p50_response_time_ms, 2),
            'p95_response_time_ms': round(self.p95_response_time_ms, 2),
            'p99_response_time_ms': round(self.p99_response_time_ms, 2),
            'throughput_rps': round(self.throughput_rps, 2),
            'error_rate': round(self.error_rate, 4)
        }


# ===================== HEALTH CHECK SERVICE =====================

class HealthCheckService:
    """Health check monitoring service."""
    
    def __init__(self, timeout_seconds: float = 5.0):
        """Initialize health check service."""
        self.timeout_seconds = timeout_seconds
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, List[HealthCheckResult]] = defaultdict(list)
        self._lock = Lock()
        self.max_history = 100
    
    def register_check(self, service_name: str, check_func: Callable) -> bool:
        """Register health check function."""
        if not callable(check_func):
            return False
        
        with self._lock:
            self.checks[service_name] = check_func
        return True
    
    def run_check(self, service_name: str) -> Optional[HealthCheckResult]:
        """Run single health check."""
        if service_name not in self.checks:
            return None
        
        start_time = time.time()
        try:
            check_func = self.checks[service_name]
            result = check_func()
            response_time_ms = (time.time() - start_time) * 1000
            
            health_check = HealthCheckResult(
                service_name=service_name,
                status=result.get('status', HealthStatus.UNKNOWN),
                response_time_ms=response_time_ms,
                message=result.get('message', ''),
                details=result.get('details', {})
            )
            
            with self._lock:
                self.results[service_name].append(health_check)
                if len(self.results[service_name]) > self.max_history:
                    self.results[service_name].pop(0)
            
            return health_check
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            health_check = HealthCheckResult(
                service_name=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                message=f"Check failed: {str(e)}",
                details={'error': str(e)}
            )
            
            with self._lock:
                self.results[service_name].append(health_check)
                if len(self.results[service_name]) > self.max_history:
                    self.results[service_name].pop(0)
            
            return health_check
    
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        results = {}
        for service_name in self.checks.keys():
            result = self.run_check(service_name)
            if result:
                results[service_name] = result
        return results
    
    def get_service_status(self, service_name: str) -> Optional[HealthCheckResult]:
        """Get latest health status for service."""
        with self._lock:
            if service_name in self.results and self.results[service_name]:
                return self.results[service_name][-1]
        return None
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        with self._lock:
            if not self.results:
                return HealthStatus.UNKNOWN
            
            statuses = [r[-1].status for r in self.results.values() if r]
            if not statuses:
                return HealthStatus.UNKNOWN
            
            if HealthStatus.UNHEALTHY in statuses:
                return HealthStatus.UNHEALTHY
            elif HealthStatus.DEGRADED in statuses:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.HEALTHY
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get health check statistics."""
        with self._lock:
            total_checks = sum(len(v) for v in self.results.values())
            return {
                'registered_checks': len(self.checks),
                'total_checks_run': total_checks,
                'services_monitored': list(self.checks.keys())
            }


# ===================== METRICS COLLECTOR =====================

class MetricsCollector:
    """Metrics collection and aggregation service."""
    
    def __init__(self, window_size_minutes: int = 5):
        """Initialize metrics collector."""
        self.window_size_minutes = window_size_minutes
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = Lock()
        self.base_time = time.time()
    
    def record_metric(self, name: str, value: float, 
                     metric_type: MetricType = MetricType.GAUGE,
                     labels: Optional[Dict[str, str]] = None) -> bool:
        """Record a metric."""
        labels = labels or {}
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels
        )
        
        with self._lock:
            self.metrics[name].append(metric)
        
        return True
    
    def record_counter(self, name: str, increment: float = 1.0,
                      labels: Optional[Dict[str, str]] = None) -> bool:
        """Record counter metric."""
        return self.record_metric(name, increment, MetricType.COUNTER, labels)
    
    def record_gauge(self, name: str, value: float,
                    labels: Optional[Dict[str, str]] = None) -> bool:
        """Record gauge metric."""
        return self.record_metric(name, value, MetricType.GAUGE, labels)
    
    def record_histogram(self, name: str, value: float,
                        labels: Optional[Dict[str, str]] = None) -> bool:
        """Record histogram metric."""
        return self.record_metric(name, value, MetricType.HISTOGRAM, labels)
    
    def record_timer(self, name: str, duration_ms: float,
                    labels: Optional[Dict[str, str]] = None) -> bool:
        """Record timer metric."""
        return self.record_metric(name, duration_ms, MetricType.TIMER, labels)
    
    def get_metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metric summary statistics."""
        with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return None
            
            metric_list = list(self.metrics[name])
            values = [m.value for m in metric_list]
            
            values_sorted = sorted(values)
            n = len(values_sorted)
            
            return {
                'name': name,
                'count': len(metric_list),
                'sum': sum(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'p50': values_sorted[n // 2],
                'p95': values_sorted[int(n * 0.95)],
                'p99': values_sorted[int(n * 0.99)]
            }
    
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get all recorded metrics."""
        with self._lock:
            metrics_list = []
            for metric_deque in self.metrics.values():
                for metric in metric_deque:
                    metrics_list.append(metric.to_dict())
            return metrics_list
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get metrics statistics."""
        with self._lock:
            total_metrics = sum(len(v) for v in self.metrics.values())
            return {
                'metric_names': len(self.metrics),
                'total_data_points': total_metrics,
                'metrics': list(self.metrics.keys())
            }


# ===================== DISTRIBUTED TRACING =====================

class DistributedTracer:
    """Distributed tracing service."""
    
    def __init__(self):
        """Initialize distributed tracer."""
        self.traces: Dict[str, List[TraceSpan]] = defaultdict(list)
        self._lock = Lock()
        self.max_spans_per_trace = 1000
        self._span_counter = 0
    
    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """Start a new distributed trace."""
        if not trace_id:
            trace_id = self._generate_trace_id()
        
        with self._lock:
            self.traces[trace_id] = []
        
        return trace_id
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID."""
        timestamp = str(int(time.time() * 1000000))
        counter = str(self._span_counter).zfill(6)
        self._span_counter += 1
        trace_id = f"trace_{timestamp}_{counter}"
        return trace_id
    
    def _generate_span_id(self) -> str:
        """Generate unique span ID."""
        timestamp = str(int(time.time() * 1000000))
        counter = str(self._span_counter).zfill(6)
        self._span_counter += 1
        span_id = f"span_{timestamp}_{counter}"
        return span_id
    
    def add_span(self, trace_id: str, operation: str, service: str,
                parent_span_id: Optional[str] = None,
                tags: Optional[Dict[str, Any]] = None) -> str:
        """Add span to trace."""
        span_id = self._generate_span_id()
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation=operation,
            service=service,
            start_time=time.time(),
            tags=tags or {}
        )
        
        with self._lock:
            if trace_id in self.traces:
                if len(self.traces[trace_id]) < self.max_spans_per_trace:
                    self.traces[trace_id].append(span)
        
        return span_id
    
    def end_span(self, trace_id: str, span_id: str, status: str = "success") -> bool:
        """End a span."""
        with self._lock:
            if trace_id in self.traces:
                for span in self.traces[trace_id]:
                    if span.span_id == span_id:
                        span.end_time = time.time()
                        span.duration_ms = (span.end_time - span.start_time) * 1000
                        span.status = status
                        return True
        return False
    
    def add_span_log(self, trace_id: str, span_id: str, message: str,
                    level: TraceLevel = TraceLevel.INFO) -> bool:
        """Add log entry to span."""
        with self._lock:
            if trace_id in self.traces:
                for span in self.traces[trace_id]:
                    if span.span_id == span_id:
                        span.logs.append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'level': level.value,
                            'message': message
                        })
                        return True
        return False
    
    def get_trace(self, trace_id: str) -> Optional[List[TraceSpan]]:
        """Get all spans for a trace."""
        with self._lock:
            return self.traces.get(trace_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        with self._lock:
            total_spans = sum(len(v) for v in self.traces.values())
            return {
                'active_traces': len(self.traces),
                'total_spans': total_spans,
                'avg_spans_per_trace': total_spans / len(self.traces) if self.traces else 0
            }


# ===================== ALERT MANAGER =====================

class AlertManager:
    """Alert management and notification service."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._lock = Lock()
        self.max_history = 1000
        self._alert_counter = 0
    
    def create_alert(self, service: str, severity: AlertSeverity,
                    message: str, metric_name: str, 
                    threshold: float, current_value: float,
                    metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """Create new alert."""
        alert_id = self._generate_alert_id()
        alert = Alert(
            alert_id=alert_id,
            service=service,
            severity=severity,
            message=message,
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.alerts[alert_id] = alert
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history:
                self.alert_history.pop(0)
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert."""
        with self._lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.resolved_at = datetime.utcnow()
                alert.severity = AlertSeverity.RESOLVED
                del self.alerts[alert_id]
                return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts."""
        with self._lock:
            alerts = list(self.alerts.values())
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            return alerts
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        with self._lock:
            return self.alert_history[-limit:]
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        timestamp = str(int(time.time() * 1000000))
        counter = str(self._alert_counter).zfill(6)
        self._alert_counter += 1
        return f"alert_{timestamp}_{counter}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        with self._lock:
            active = self.alerts
            history = self.alert_history
            
            critical_count = len([a for a in active.values() if a.severity == AlertSeverity.CRITICAL])
            warning_count = len([a for a in active.values() if a.severity == AlertSeverity.WARNING])
            
            return {
                'active_alerts': len(active),
                'critical_alerts': critical_count,
                'warning_alerts': warning_count,
                'total_alerts_history': len(history)
            }


# ===================== SINGLETON PATTERN =====================

_health_check_service: Optional[HealthCheckService] = None
_metrics_collector: Optional[MetricsCollector] = None
_distributed_tracer: Optional[DistributedTracer] = None
_alert_manager: Optional[AlertManager] = None


def get_health_check_service() -> HealthCheckService:
    """Get health check service singleton."""
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service


def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector singleton."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_distributed_tracer() -> DistributedTracer:
    """Get distributed tracer singleton."""
    global _distributed_tracer
    if _distributed_tracer is None:
        _distributed_tracer = DistributedTracer()
    return _distributed_tracer


def get_alert_manager() -> AlertManager:
    """Get alert manager singleton."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def reset_health_check_service():
    """Reset health check service."""
    global _health_check_service
    _health_check_service = None


def reset_metrics_collector():
    """Reset metrics collector."""
    global _metrics_collector
    _metrics_collector = None


def reset_distributed_tracer():
    """Reset distributed tracer."""
    global _distributed_tracer
    _distributed_tracer = None


def reset_alert_manager():
    """Reset alert manager."""
    global _alert_manager
    _alert_manager = None
