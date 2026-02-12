"""
Phase 48: Health Monitor & Diagnostic System
=========================================================
Continuous monitoring, health checking, and diagnostics for all services
Provides real-time metrics, alerting, and recovery mechanisms
"""

import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import deque

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str = ""
    status: HealthStatus = HealthStatus.HEALTHY
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def status_from_value(self) -> HealthStatus:
        """Determine status from metric value"""
        if self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return HealthStatus.WARNING
        return HealthStatus.HEALTHY


@dataclass
class ServiceHealth:
    """Complete health snapshot for a service"""
    service_id: str
    service_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    metrics: Dict[str, HealthMetric] = field(default_factory=dict)
    last_check: Optional[datetime] = None
    check_duration_ms: float = 0.0
    error_message: Optional[str] = None
    recovery_attempts: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_duration_ms": self.check_duration_ms,
            "error_message": self.error_message,
            "recovery_attempts": self.recovery_attempts,
            "metrics": {name: {"value": m.value, "unit": m.unit, "status": m.status.value} 
                       for name, m in self.metrics.items()}
        }


class HealthMonitor:
    """
    Comprehensive health monitoring system for all services.
    Tracks metrics, performs periodic checks, and triggers recovery actions.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        check_interval_seconds: int = 30,
        history_size: int = 100,
        recovery_enabled: bool = True
    ):
        if self._initialized:
            return

        self.check_interval_seconds = check_interval_seconds
        self.history_size = history_size
        self.recovery_enabled = recovery_enabled

        self.service_health: Dict[str, ServiceHealth] = {}
        self.health_history: Dict[str, deque] = {}
        self.check_functions: Dict[str, Callable] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        self.alert_handlers: List[Callable] = []

        self._monitoring_thread = None
        self._stop_monitoring = False
        self._lock = threading.RLock()
        self._initialized = True

        logger.info(f"HealthMonitor initialized (interval: {check_interval_seconds}s, history: {history_size})")

    def register_health_check(self, service_id: str, check_fn: Callable) -> None:
        """Register a custom health check function"""
        with self._lock:
            self.check_functions[service_id] = check_fn
            self.service_health[service_id] = ServiceHealth(
                service_id=service_id,
                service_name=service_id
            )
            self.health_history[service_id] = deque(maxlen=self.history_size)

    def register_recovery_handler(self, service_id: str, recovery_fn: Callable) -> None:
        """Register a recovery/remediation function for a service"""
        with self._lock:
            self.recovery_handlers[service_id] = recovery_fn

    def register_alert_handler(self, handler_fn: Callable) -> None:
        """Register a function to handle alerts"""
        with self._lock:
            self.alert_handlers.append(handler_fn)

    def check_service_health(self, service_id: str) -> ServiceHealth:
        """Perform health check on a specific service"""
        with self._lock:
            if service_id not in self.service_health:
                logger.warning(f"No health check registered for {service_id}")
                return ServiceHealth(service_id=service_id, service_name=service_id)

            health = self.service_health[service_id]
            start_time = time.time()

            try:
                # Run check function
                if service_id in self.check_functions:
                    result = self.check_functions[service_id]()
                    health.metrics = result.get("metrics", {})
                    health.status = HealthStatus[result.get("status", "UNKNOWN")]
                    health.error_message = result.get("error", None)
                else:
                    health.status = HealthStatus.UNKNOWN

            except Exception as e:
                health.status = HealthStatus.CRITICAL
                health.error_message = str(e)
                health.recovery_attempts += 1
                logger.error(f"Health check failed for {service_id}: {str(e)}")

                # Trigger recovery if enabled
                if self.recovery_enabled and service_id in self.recovery_handlers:
                    self._trigger_recovery(service_id, e)

            # Update check metadata
            health.last_check = datetime.utcnow()
            health.check_duration_ms = (time.time() - start_time) * 1000

            # Store in history
            if service_id in self.health_history:
                self.health_history[service_id].append(health.to_dict())

            # Check for alerts
            if health.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                self._trigger_alerts(health)

            return health

    def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Perform health checks on all services"""
        results = {}
        for service_id in self.service_health:
            results[service_id] = self.check_service_health(service_id)
        return results

    def start_monitoring(self) -> None:
        """Start continuous monitoring thread"""
        if self._monitoring_thread is not None:
            logger.warning("Monitoring already started")
            return

        self._stop_monitoring = False
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="HealthMonitorThread"
        )
        self._monitoring_thread.start()
        logger.info("Health monitoring started")

    def stop_monitoring(self) -> None:
        """Stop continuous monitoring thread"""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
            self._monitoring_thread = None
        logger.info("Health monitoring stopped")

    def get_service_health(self, service_id: str) -> Optional[ServiceHealth]:
        """Get current health status of a service"""
        with self._lock:
            return self.service_health.get(service_id)

    def get_all_health(self) -> Dict[str, ServiceHealth]:
        """Get health status of all services"""
        with self._lock:
            return dict(self.service_health)

    def get_health_history(self, service_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get health check history for a service"""
        with self._lock:
            if service_id not in self.health_history:
                return []
            return list(self.health_history[service_id])[-limit:]

    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        with self._lock:
            health_status_counts = {
                HealthStatus.HEALTHY.value: 0,
                HealthStatus.WARNING.value: 0,
                HealthStatus.CRITICAL.value: 0,
                HealthStatus.UNKNOWN.value: 0
            }

            for health in self.service_health.values():
                health_status_counts[health.status.value] += 1

            overall_status = HealthStatus.HEALTHY
            if health_status_counts[HealthStatus.CRITICAL.value] > 0:
                overall_status = HealthStatus.CRITICAL
            elif health_status_counts[HealthStatus.WARNING.value] > 0:
                overall_status = HealthStatus.WARNING

            return {
                "overall_status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "total_services": len(self.service_health),
                "status_breakdown": health_status_counts,
                "services_health": {
                    s_id: health.to_dict()
                    for s_id, health in self.service_health.items()
                }
            }

    def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        logger.info(f"Starting monitoring loop (interval: {self.check_interval_seconds}s)")

        while not self._stop_monitoring:
            try:
                self.check_all_services()
                time.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(1)

    def _trigger_recovery(self, service_id: str, error: Exception) -> None:
        """Trigger recovery handler for a service"""
        try:
            logger.warning(f"Triggering recovery for {service_id}: {str(error)}")
            recovery_fn = self.recovery_handlers[service_id]
            recovery_fn()
            logger.info(f"Recovery triggered for {service_id}")
        except Exception as e:
            logger.error(f"Recovery failed for {service_id}: {str(e)}")

    def _trigger_alerts(self, health: ServiceHealth) -> None:
        """Trigger alert handlers"""
        alert_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service_id": health.service_id,
            "service_name": health.service_name,
            "status": health.status.value,
            "error_message": health.error_message,
            "check_duration_ms": health.check_duration_ms
        }

        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {str(e)}")


class DiagnosticCollector:
    """
    Collects diagnostic information for analysis and debugging
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.diagnostics: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._initialized = True

    def collect_diagnostics(self, health_monitor: HealthMonitor) -> Dict[str, Any]:
        """Collect comprehensive diagnostic data"""
        with self._lock:
            diagnostics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_health": health_monitor.get_overall_status(),
                "service_diagnostics": {}
            }

            for service_id, health in health_monitor.get_all_health().items():
                diagnostics["service_diagnostics"][service_id] = {
                    "health": health.to_dict(),
                    "history": health_monitor.get_health_history(service_id, limit=20)
                }

            self.diagnostics = diagnostics
            return diagnostics

    def export_diagnostics(self, output_path: str) -> None:
        """Export diagnostics to file"""
        with self._lock:
            try:
                import pathlib
                pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump(self.diagnostics, f, indent=2)
                logger.info(f"Diagnostics exported to {output_path}")
            except Exception as e:
                logger.error(f"Failed to export diagnostics: {str(e)}")

    def generate_report(self) -> str:
        """Generate a human-readable diagnostic report"""
        report_lines = [
            "=" * 80,
            "System Diagnostic Report",
            f"Generated: {self.diagnostics.get('timestamp', 'Unknown')}",
            "=" * 80,
            ""
        ]

        system_health = self.diagnostics.get("system_health", {})
        report_lines.append(f"Overall Status: {system_health.get('overall_status', 'Unknown').upper()}")
        report_lines.append(f"Total Services: {system_health.get('total_services', 0)}")
        report_lines.append("")

        breakdown = system_health.get("status_breakdown", {})
        report_lines.append("Status Breakdown:")
        for status, count in breakdown.items():
            report_lines.append(f"  {status.upper()}: {count}")
        report_lines.append("")

        report_lines.append("Service Details:")
        report_lines.append("-" * 80)

        services_health = system_health.get("services_health", {})
        for service_id, health_info in services_health.items():
            report_lines.append(f"\n{service_id}:")
            report_lines.append(f"  Status: {health_info.get('status', 'Unknown')}")
            report_lines.append(f"  Last Check: {health_info.get('last_check', 'Never')}")
            report_lines.append(f"  Check Duration: {health_info.get('check_duration_ms', 0):.2f}ms")

            if health_info.get('error_message'):
                report_lines.append(f"  Error: {health_info['error_message']}")

            metrics = health_info.get('metrics', {})
            if metrics:
                report_lines.append("  Metrics:")
                for metric_name, metric_data in metrics.items():
                    report_lines.append(f"    {metric_name}: {metric_data.get('value', 'N/A')} {metric_data.get('unit', '')}")

        return "\n".join(report_lines)
