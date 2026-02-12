"""
Performance Monitoring Service
Tracks inference latency, throughput, errors, resource utilization, and SLA compliance.
Implements alerting, anomaly detection, and performance tracing.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from threading import RLock
from collections import deque
import statistics
import numpy as np

logger = logging.getLogger(__name__)


# ===================== ENUMS =====================

class MetricType(Enum):
    """Type of performance metric"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE = "resource"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyDetectionMethod(Enum):
    """Anomaly detection algorithms"""
    SIGMA = "3_sigma"  # 3-sigma rule
    IQR = "interquartile_range"
    MOVING_AVERAGE = "moving_average"
    ISOLATION_FOREST = "isolation_forest"


# ===================== DATACLASSES =====================

@dataclass
class LatencyMetric:
    """Latency measurement"""
    timestamp: float
    value_ms: float
    endpoint_id: str
    model_version: int
    bucket: str  # fast, medium, slow, very_slow, timeout


@dataclass
class ThroughputMetric:
    """Throughput measurement"""
    timestamp: float
    requests_per_second: float
    endpoint_id: str
    window_size_seconds: int = 60


@dataclass
class ErrorMetric:
    """Error tracking"""
    timestamp: float
    error_count: int
    total_requests: int
    error_rate: float  # 0-1
    endpoint_id: str
    error_types: Dict[str, int] = field(default_factory=dict)


@dataclass
class ResourceMetric:
    """Resource utilization"""
    timestamp: float
    endpoint_id: str
    cpu_usage_percent: float
    memory_usage_mb: float
    memory_limit_mb: int
    gpu_usage_percent: float = 0.0
    num_active_requests: int = 0
    queue_length: int = 0


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    timestamp: float
    severity: AlertSeverity
    endpoint_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    triggered_by: str  # rule_name or anomaly_detector
    acknowledged: bool = False
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None


@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    rule_name: str
    metric_name: str
    metric_type: MetricType
    endpoint_id: Optional[str] = None  # None = all endpoints
    condition: str = ">"  # >, <, ==, !=
    threshold: float = 0.0
    window_size_seconds: int = 60
    min_samples: int = 5
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    cooldown_seconds: int = 300


@dataclass
class PerformantileStats:
    """Percentile statistics"""
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    p999: float
    min: float
    max: float
    mean: float
    median: float
    stddev: float
    sample_count: int


@dataclass
class SLAConfiguration:
    """Service Level Agreement configuration"""
    sla_id: str
    endpoint_id: str
    name: str
    latency_p99_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    availability_percent: Optional[float] = None
    error_rate_threshold: Optional[float] = None
    throughput_min_rps: Optional[float] = None
    evaluation_window_minutes: int = 5


@dataclass
class SLAViolation:
    """SLA violation record"""
    violation_id: str
    sla_id: str
    endpoint_id: str
    violation_type: str  # latency, availability, error_rate, throughput
    expected_value: float
    actual_value: float
    severity: AlertSeverity
    detected_at: float
    duration_minutes: Optional[float] = None
    remediation_status: str = "open"


@dataclass
class AnomalyDetectionResult:
    """Anomaly detection result"""
    anomaly_id: str
    timestamp: float
    endpoint_id: str
    metric_name: str
    value: float
    baseline: float
    deviation_percent: float
    detection_method: AnomalyDetectionMethod
    confidence: float  # 0-1
    anomaly_type: str  # spike, drop, shift, variance_change


# ===================== PERFORMANCE MONITORING SERVICE =====================

class PerformanceMonitoringService:
    """
    Comprehensive performance monitoring for model serving endpoints.
    Tracks metrics, detects anomalies, triggers alerts, and monitors SLAs.
    """
    
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        
        # Metrics storage with time-based windows
        self.latency_metrics: Dict[str, deque] = {}  # endpoint_id -> latencies
        self.throughput_metrics: Dict[str, deque] = {}  # endpoint_id -> throughput
        self.error_metrics: Dict[str, deque] = {}  # endpoint_id -> errors
        self.resource_metrics: Dict[str, deque] = {}  # endpoint_id -> resources
        self.custom_metrics: Dict[str, deque] = {}  # metric_name -> values
        
        # Alert management
        self.alert_rules: Dict[str, AlertRule] = {}  # rule_id -> rule
        self.active_alerts: Dict[str, PerformanceAlert] = {}  # alert_id -> alert
        self.alert_history: Dict[str, deque] = {}  # endpoint_id -> alert history
        
        # SLA monitoring
        self.sla_configs: Dict[str, SLAConfiguration] = {}  # sla_id -> config
        self.sla_violations: Dict[str, deque] = {}  # endpoint_id -> violations
        
        # Anomaly detection
        self.anomaly_baselines: Dict[str, Dict[str, float]] = {}  # endpoint_id -> {metric -> baseline}
        self.anomalies: Dict[str, deque] = {}  # endpoint_id -> anomalies
        
        # Thread safety
        self.lock = RLock()
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            'alert_triggered': [],
            'alert_resolved': [],
            'anomaly_detected': [],
            'sla_violated': []
        }
    
    def record_latency(self, endpoint_id: str, latency_ms: float, model_version: int) -> None:
        """Record latency measurement"""
        with self.lock:
            if endpoint_id not in self.latency_metrics:
                self.latency_metrics[endpoint_id] = deque(maxlen=100000)
            
            # Determine bucket
            if latency_ms < 10:
                bucket = "fast"
            elif latency_ms < 50:
                bucket = "medium"
            elif latency_ms < 100:
                bucket = "slow"
            elif latency_ms < 500:
                bucket = "very_slow"
            else:
                bucket = "timeout"
            
            metric = LatencyMetric(
                timestamp=datetime.utcnow().timestamp(),
                value_ms=latency_ms,
                endpoint_id=endpoint_id,
                model_version=model_version,
                bucket=bucket
            )
            
            self.latency_metrics[endpoint_id].append(metric)
            
            # Check anomaly
            self._check_metric_anomaly(endpoint_id, 'latency', latency_ms)
    
    def record_error(self, endpoint_id: str, error_count: int, total_requests: int) -> None:
        """Record error metrics"""
        error_rate = error_count / max(total_requests, 1)
        
        with self.lock:
            if endpoint_id not in self.error_metrics:
                self.error_metrics[endpoint_id] = deque(maxlen=10000)
            
            metric = ErrorMetric(
                timestamp=datetime.utcnow().timestamp(),
                error_count=error_count,
                total_requests=total_requests,
                error_rate=error_rate,
                endpoint_id=endpoint_id
            )
            
            self.error_metrics[endpoint_id].append(metric)
            
            # Check SLA
            self._check_sla_violation(endpoint_id, 'error_rate', error_rate)
    
    def record_throughput(self, endpoint_id: str, requests_per_second: float) -> None:
        """Record throughput measurement"""
        with self.lock:
            if endpoint_id not in self.throughput_metrics:
                self.throughput_metrics[endpoint_id] = deque(maxlen=10000)
            
            metric = ThroughputMetric(
                timestamp=datetime.utcnow().timestamp(),
                requests_per_second=requests_per_second,
                endpoint_id=endpoint_id
            )
            
            self.throughput_metrics[endpoint_id].append(metric)
    
    def record_resource(self, endpoint_id: str, cpu_percent: float, memory_mb: int,
                       memory_limit_mb: int, gpu_percent: float = 0.0,
                       active_requests: int = 0, queue_length: int = 0) -> None:
        """Record resource utilization"""
        with self.lock:
            if endpoint_id not in self.resource_metrics:
                self.resource_metrics[endpoint_id] = deque(maxlen=10000)
            
            metric = ResourceMetric(
                timestamp=datetime.utcnow().timestamp(),
                endpoint_id=endpoint_id,
                cpu_usage_percent=cpu_percent,
                memory_usage_mb=memory_mb,
                memory_limit_mb=memory_limit_mb,
                gpu_usage_percent=gpu_percent,
                num_active_requests=active_requests,
                queue_length=queue_length
            )
            
            self.resource_metrics[endpoint_id].append(metric)
    
    def record_custom_metric(self, metric_name: str, value: float,
                            endpoint_id: str, tags: Dict[str, str] = None) -> None:
        """Record custom metric"""
        with self.lock:
            if metric_name not in self.custom_metrics:
                self.custom_metrics[metric_name] = deque(maxlen=100000)
            
            # Store with timestamp
            self.custom_metrics[metric_name].append({
                'timestamp': datetime.utcnow().timestamp(),
                'value': value,
                'endpoint_id': endpoint_id,
                'tags': tags or {}
            })
    
    def get_latency_stats(self, endpoint_id: str, window_minutes: int = 5) -> Optional[PerformantileStats]:
        """Get latency percentiles and statistics"""
        with self.lock:
            if endpoint_id not in self.latency_metrics:
                return None
            
            cutoff_time = datetime.utcnow().timestamp() - (window_minutes * 60)
            latencies = [m.value_ms for m in self.latency_metrics[endpoint_id]
                        if m.timestamp >= cutoff_time]
            
            if not latencies:
                return None
            
            latencies.sort()
            
            return PerformantileStats(
                p50=np.percentile(latencies, 50),
                p75=np.percentile(latencies, 75),
                p90=np.percentile(latencies, 90),
                p95=np.percentile(latencies, 95),
                p99=np.percentile(latencies, 99),
                p999=np.percentile(latencies, 99.9),
                min=min(latencies),
                max=max(latencies),
                mean=np.mean(latencies),
                median=np.median(latencies),
                stddev=np.std(latencies),
                sample_count=len(latencies)
            )
    
    def create_alert_rule(self, rule: AlertRule) -> str:
        """Create alert rule"""
        with self.lock:
            rule_id = rule.rule_id or f"rule_{id(rule)}"
            rule.rule_id = rule_id
            self.alert_rules[rule_id] = rule
            
            logger.info(f"Created alert rule {rule_id}: {rule.rule_name}")
            return rule_id
    
    def evaluate_alert_rules(self, endpoint_id: str) -> None:
        """Evaluate all alert rules for endpoint"""
        with self.lock:
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                if rule.endpoint_id and rule.endpoint_id != endpoint_id:
                    continue
                
                self._evaluate_rule(rule, endpoint_id)
    
    def _evaluate_rule(self, rule: AlertRule, endpoint_id: str) -> None:
        """Evaluate single alert rule"""
        if rule.metric_type == MetricType.LATENCY:
            stats = self.get_latency_stats(endpoint_id, 
                                          window_minutes=rule.window_size_seconds // 60)
            if not stats or stats.sample_count < rule.min_samples:
                return
            value = stats.p95  # Default to p95
        
        elif rule.metric_type == MetricType.ERROR_RATE:
            if endpoint_id not in self.error_metrics:
                return
            
            cutoff_time = datetime.utcnow().timestamp() - rule.window_size_seconds
            recent = [m for m in self.error_metrics[endpoint_id]
                     if m.timestamp >= cutoff_time]
            
            if len(recent) < rule.min_samples:
                return
            
            value = np.mean([m.error_rate for m in recent])
        
        elif rule.metric_type == MetricType.THROUGHPUT:
            if endpoint_id not in self.throughput_metrics:
                return
            
            cutoff_time = datetime.utcnow().timestamp() - rule.window_size_seconds
            recent = [m for m in self.throughput_metrics[endpoint_id]
                     if m.timestamp >= cutoff_time]
            
            if len(recent) < rule.min_samples:
                return
            
            value = np.mean([m.requests_per_second for m in recent])
        
        else:
            return
        
        # Evaluate condition
        triggered = False
        if rule.condition == ">":
            triggered = value > rule.threshold
        elif rule.condition == "<":
            triggered = value < rule.threshold
        elif rule.condition == "==":
            triggered = value == rule.threshold
        elif rule.condition == "!=":
            triggered = value != rule.threshold
        
        if triggered:
            self._trigger_alert(rule, endpoint_id, value)
    
    def _trigger_alert(self, rule: AlertRule, endpoint_id: str, value: float) -> None:
        """Trigger alert for rule violation"""
        alert_key = f"{rule.rule_id}_{endpoint_id}"
        
        # Check if already alerted and in cooldown
        if alert_key in self.active_alerts:
            existing = self.active_alerts[alert_key]
            cooldown_expired = (datetime.utcnow().timestamp() - existing.timestamp) > rule.cooldown_seconds
            if not cooldown_expired:
                return
        
        alert = PerformanceAlert(
            alert_id=f"alert_{id(rule)}_{int(time.time() * 1000)}",
            timestamp=datetime.utcnow().timestamp(),
            severity=rule.severity,
            endpoint_id=endpoint_id,
            metric_name=rule.metric_name,
            current_value=value,
            threshold_value=rule.threshold,
            message=f"{rule.rule_name}: {rule.metric_name} {rule.condition} {rule.threshold}",
            triggered_by=rule.rule_name
        )
        
        with self.lock:
            self.active_alerts[alert_key] = alert
            
            if endpoint_id not in self.alert_history:
                self.alert_history[endpoint_id] = deque(maxlen=10000)
            
            self.alert_history[endpoint_id].append(alert)
        
        logger.warning(f"Alert triggered: {alert.message}")
        self._trigger_callback('alert_triggered', {
            'alert_id': alert.alert_id,
            'endpoint_id': endpoint_id,
            'severity': alert.severity.value,
            'message': alert.message
        })
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = None) -> bool:
        """Acknowledge alert"""
        with self.lock:
            for alert in self.active_alerts.values():
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.utcnow().timestamp()
                    alert.acknowledged_by = acknowledged_by
                    return True
        
        return False
    
    def create_sla(self, sla_config: SLAConfiguration) -> str:
        """Create SLA configuration"""
        with self.lock:
            self.sla_configs[sla_config.sla_id] = sla_config
            
            if sla_config.endpoint_id not in self.sla_violations:
                self.sla_violations[sla_config.endpoint_id] = deque(maxlen=10000)
            
            logger.info(f"Created SLA {sla_config.sla_id}: {sla_config.name}")
            return sla_config.sla_id
    
    def _check_sla_violation(self, endpoint_id: str, metric_name: str, value: float) -> None:
        """Check for SLA violations"""
        with self.lock:
            for sla_id, sla in self.sla_configs.items():
                if sla.endpoint_id != endpoint_id:
                    continue
                
                threshold = None
                violation_type = metric_name
                
                if metric_name == 'latency_p99' and sla.latency_p99_ms:
                    threshold = sla.latency_p99_ms
                elif metric_name == 'latency_p95' and sla.latency_p95_ms:
                    threshold = sla.latency_p95_ms
                elif metric_name == 'error_rate' and sla.error_rate_threshold:
                    threshold = sla.error_rate_threshold
                
                if threshold and value > threshold:
                    violation = SLAViolation(
                        violation_id=f"sla_{id(sla)}_{int(time.time() * 1000)}",
                        sla_id=sla_id,
                        endpoint_id=endpoint_id,
                        violation_type=violation_type,
                        expected_value=threshold,
                        actual_value=value,
                        severity=AlertSeverity.CRITICAL,
                        detected_at=datetime.utcnow().timestamp()
                    )
                    
                    self.sla_violations[endpoint_id].append(violation)
                    
                    self._trigger_callback('sla_violated', {
                        'violation_id': violation.violation_id,
                        'sla_id': sla_id,
                        'endpoint_id': endpoint_id,
                        'metric': violation_type
                    })
    
    def _check_metric_anomaly(self, endpoint_id: str, metric_name: str, value: float) -> None:
        """Check for anomalies using 3-sigma rule"""
        with self.lock:
            if endpoint_id not in self.anomaly_baselines:
                self.anomaly_baselines[endpoint_id] = {}
            
            baselines = self.anomaly_baselines[endpoint_id]
            
            # Collect recent values
            if metric_name == 'latency' and endpoint_id in self.latency_metrics:
                recent = [m.value_ms for m in list(self.latency_metrics[endpoint_id])[-100:]]
            else:
                return
            
            if len(recent) < 20:  # Need minimum data
                return
            
            mean = np.mean(recent)
            stddev = np.std(recent)
            
            if stddev == 0:
                return
            
            # 3-sigma rule
            z_score = abs((value - mean) / stddev)
            
            if z_score > 3:
                if endpoint_id not in self.anomalies:
                    self.anomalies[endpoint_id] = deque(maxlen=10000)
                
                anomaly = AnomalyDetectionResult(
                    anomaly_id=f"anomaly_{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.utcnow().timestamp(),
                    endpoint_id=endpoint_id,
                    metric_name=metric_name,
                    value=value,
                    baseline=mean,
                    deviation_percent=(abs(value - mean) / mean * 100) if mean != 0 else 0,
                    detection_method=AnomalyDetectionMethod.SIGMA,
                    confidence=min(z_score / 5, 1.0),
                    anomaly_type="spike" if value > mean else "drop"
                )
                
                self.anomalies[endpoint_id].append(anomaly)
                
                self._trigger_callback('anomaly_detected', {
                    'anomaly_id': anomaly.anomaly_id,
                    'endpoint_id': endpoint_id,
                    'metric': metric_name,
                    'value': value,
                    'baseline': mean,
                    'confidence': anomaly.confidence
                })
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self.lock:
            return {
                'endpoints_monitored': len(set(m.endpoint_id for metrics in 
                                               [self.latency_metrics.values(),
                                                self.error_metrics.values()] 
                                               for m in metrics for m in m)),
                'total_metrics_recorded': sum(len(m) for m in self.latency_metrics.values()) +
                                         sum(len(m) for m in self.error_metrics.values()),
                'active_alerts': len(self.active_alerts),
                'total_alert_rules': len(self.alert_rules),
                'sla_configurations': len(self.sla_configs),
                'timestamp': datetime.utcnow().timestamp()
            }
    
    def _trigger_callback(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger registered callbacks"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for event"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)


import uuid
