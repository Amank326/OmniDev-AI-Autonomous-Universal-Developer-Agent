"""
Security Monitor - Security & Governance Infrastructure (Phase 47)

Provides real-time threat detection, security event monitoring, and incident
response capabilities.

Features:
- Real-time security event monitoring
- Threat detection and anomaly analysis
- Incident detection and alerting
- Security metrics and KPIs
- Integration with audit logs
- Automated response capabilities
- Dashboard and reporting
- Performance optimization
- Thread-safe singleton pattern

Integrates with:
- audit_logger: Monitor security events
- access_control_service: Track unauthorized access attempts
- encryption_service: Monitor encryption health
- auth_service: Monitor authentication anomalies
"""

import json
import time
import threading
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import re


class ThreatLevel(Enum):
    """Threat severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class DetectionType(Enum):
    """Types of security detections."""
    BRUTE_FORCE = "brute_force"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ENCRYPTION_FAILURE = "encryption_failure"
    AUDIT_LOG_TAMPERING = "audit_log_tampering"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    MALWARE_DETECTED = "malware_detected"
    DDOS_ATTACK = "ddos_attack"
    CONFIGURATION_CHANGE = "configuration_change"


class SecurityMonitorConfig:
    """Configuration for security monitor."""
    
    def __init__(
        self,
        enable_real_time_monitoring: bool = True,
        threat_detection_enabled: bool = True,
        anomaly_detection_enabled: bool = True,
        incident_response_enabled: bool = True,
        auto_response_enabled: bool = False,
        alert_threshold: ThreatLevel = ThreatLevel.MEDIUM,
        monitoring_interval_seconds: int = 60,
        incident_retention_days: int = 90,
        metrics_storage_path: Optional[str] = None,
    ):
        """Initialize security monitor configuration."""
        self.enable_real_time_monitoring = enable_real_time_monitoring
        self.threat_detection_enabled = threat_detection_enabled
        self.anomaly_detection_enabled = anomaly_detection_enabled
        self.incident_response_enabled = incident_response_enabled
        self.auto_response_enabled = auto_response_enabled
        self.alert_threshold = alert_threshold
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self.incident_retention_days = incident_retention_days
        self.metrics_storage_path = metrics_storage_path or "./security_metrics"


@dataclass
class SecurityEvent:
    """Security event detected by monitor."""
    event_id: str
    timestamp: str
    event_type: DetectionType
    threat_level: ThreatLevel
    description: str
    source_ip: Optional[str] = None
    affected_user: Optional[str] = None
    affected_resource: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0


@dataclass
class Incident:
    """Security incident."""
    incident_id: str
    title: str
    description: str
    threat_level: ThreatLevel
    status: IncidentStatus
    detection_type: DetectionType
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    detected_by: Optional[str] = None
    investigating_team: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    affected_resources: List[str] = field(default_factory=list)
    root_cause: Optional[str] = None
    remediation_steps: List[str] = field(default_factory=list)
    resolution_time: Optional[str] = None
    impact_assessment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityMetrics:
    """Security monitoring metrics."""
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    total_incidents: int = 0
    critical_incidents: int = 0
    incidents_resolved: int = 0
    false_positives: int = 0
    avg_detection_latency_ms: float = 0.0
    avg_resolution_time_hours: float = 0.0
    last_major_incident: Optional[str] = None


class SecurityMonitor:
    """
    Production-grade security monitoring with threat detection and incident response.
    
    Features:
    - Real-time security event monitoring
    - Threat detection and analysis
    - Incident detection and alerting
    - Automated response capabilities
    - Security metrics and dashboards
    - Audit integration
    - Thread-safe singleton
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, config: Optional[SecurityMonitorConfig] = None):
        """Singleton pattern for security monitor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[SecurityMonitorConfig] = None):
        """Initialize security monitor."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config = config or SecurityMonitorConfig()
        self.events: List[SecurityEvent] = []
        self.incidents: Dict[str, Incident] = {}
        self.detection_rules: List[Callable] = []
        self.response_handlers: Dict[DetectionType, List[Callable]] = defaultdict(list)
        self.metrics = SecurityMetrics()
        self.alert_handlers: List[Callable] = []
        self.monitoring_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None
        self._running = True
        
        # Create metrics storage directory
        Path(self.config.metrics_storage_path).mkdir(parents=True, exist_ok=True)
        
        # Register default detection rules
        self._register_default_rules()
        
        # Start background tasks
        self._start_background_tasks()
        
        self._initialized = True
    
    def register_detection_rule(self, rule_function: Callable) -> None:
        """Register custom threat detection rule."""
        with self._lock:
            self.detection_rules.append(rule_function)
    
    def register_alert_handler(self, handler: Callable) -> None:
        """Register alert handler (e.g., email, Slack, PagerDuty)."""
        with self._lock:
            self.alert_handlers.append(handler)
    
    def register_response_handler(
        self,
        detection_type: DetectionType,
        handler: Callable,
    ) -> None:
        """Register automated response handler."""
        with self._lock:
            self.response_handlers[detection_type].append(handler)
    
    def detect_event(
        self,
        event_type: DetectionType,
        threat_level: ThreatLevel,
        description: str,
        source_ip: Optional[str] = None,
        affected_user: Optional[str] = None,
        affected_resource: Optional[str] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        """
        Record a security event.
        
        Args:
            event_type: Type of detection
            threat_level: Threat severity
            description: Event description
            source_ip: Source IP address
            affected_user: Affected user ID
            affected_resource: Affected resource
            raw_data: Additional event data
            
        Returns:
            SecurityEvent object
        """
        start_time = time.time()
        
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            threat_level=threat_level,
            description=description,
            source_ip=source_ip,
            affected_user=affected_user,
            affected_resource=affected_resource,
            raw_data=raw_data or {},
            confidence_score=0.95,
        )
        
        with self._lock:
            self.events.append(event)
            
            # Update metrics
            self.metrics.total_events += 1
            self.metrics.events_by_type[event_type.value] += 1
            
            # Check if should create incident
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                incident = self._create_incident(event)
                
                # Send alerts
                self._send_alerts(incident)
                
                # Execute automated responses if enabled
                if self.config.auto_response_enabled:
                    self._execute_responses(incident)
            
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.avg_detection_latency_ms = (
                (self.metrics.avg_detection_latency_ms * (self.metrics.total_events - 1) + latency_ms)
                / self.metrics.total_events
            )
        
        return event
    
    def create_incident(
        self,
        title: str,
        description: str,
        threat_level: ThreatLevel,
        detection_type: DetectionType,
        detected_by: Optional[str] = None,
        affected_users: Optional[List[str]] = None,
        affected_resources: Optional[List[str]] = None,
    ) -> Incident:
        """Create new incident."""
        with self._lock:
            incident = Incident(
                incident_id=str(uuid.uuid4()),
                title=title,
                description=description,
                threat_level=threat_level,
                status=IncidentStatus.DETECTED,
                detection_type=detection_type,
                detected_by=detected_by,
                affected_users=affected_users or [],
                affected_resources=affected_resources or [],
            )
            
            self.incidents[incident.incident_id] = incident
            self.metrics.total_incidents += 1
            
            if threat_level == ThreatLevel.CRITICAL:
                self.metrics.critical_incidents += 1
                self.metrics.last_major_incident = datetime.utcnow().isoformat()
            
            # Send alerts
            self._send_alerts(incident)
            
            return incident
    
    def update_incident_status(
        self,
        incident_id: str,
        status: IncidentStatus,
        notes: Optional[str] = None,
    ) -> Optional[Incident]:
        """Update incident status."""
        with self._lock:
            incident = self.incidents.get(incident_id)
            if not incident:
                return None
            
            incident.status = status
            
            if status == IncidentStatus.RESOLVED:
                detected_time = datetime.fromisoformat(incident.detected_at)
                resolution_time = (datetime.utcnow() - detected_time).total_seconds() / 3600
                incident.resolution_time = datetime.utcnow().isoformat()
                
                self.metrics.incidents_resolved += 1
                self.metrics.avg_resolution_time_hours = (
                    (self.metrics.avg_resolution_time_hours * (self.metrics.incidents_resolved - 1) + resolution_time)
                    / self.metrics.incidents_resolved
                )
            
            if status == IncidentStatus.FALSE_POSITIVE:
                self.metrics.false_positives += 1
            
            return incident
    
    def add_remediation(
        self,
        incident_id: str,
        remediation_steps: List[str],
        root_cause: Optional[str] = None,
    ) -> Optional[Incident]:
        """Add remediation info to incident."""
        with self._lock:
            incident = self.incidents.get(incident_id)
            if not incident:
                return None
            
            incident.remediation_steps = remediation_steps
            incident.root_cause = root_cause
            
            return incident
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident details."""
        with self._lock:
            return self.incidents.get(incident_id)
    
    def get_open_incidents(self) -> List[Incident]:
        """Get all open incidents."""
        with self._lock:
            return [
                i for i in self.incidents.values()
                if i.status not in [IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE]
            ]
    
    def get_recent_events(self, hours: int = 24) -> List[SecurityEvent]:
        """Get recent security events."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            return [
                e for e in self.events
                if datetime.fromisoformat(e.timestamp) > cutoff_time
            ]
    
    def analyze_threat_patterns(self) -> Dict[str, Any]:
        """Analyze threat patterns."""
        with self._lock:
            recent_events = self.get_recent_events(24)
            
            # Analyze patterns
            source_ips = defaultdict(int)
            affected_users_count = defaultdict(int)
            event_type_sequence = []
            
            for event in sorted(recent_events, key=lambda e: e.timestamp):
                if event.source_ip:
                    source_ips[event.source_ip] += 1
                if event.affected_user:
                    affected_users_count[event.affected_user] += 1
                event_type_sequence.append(event.event_type.value)
            
            # Identify patterns
            suspicious_ips = {ip: count for ip, count in source_ips.items() if count > 5}
            suspicious_users = {user: count for user, count in affected_users_count.items() if count > 3}
            
            return {
                "total_events_24h": len(recent_events),
                "suspicious_ips": suspicious_ips,
                "suspicious_users": suspicious_users,
                "event_type_distribution": dict(self.metrics.events_by_type),
                "top_threat_level": self._get_highest_threat_level(recent_events),
            }
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data."""
        with self._lock:
            return {
                "total_incidents": self.metrics.total_incidents,
                "critical_incidents": self.metrics.critical_incidents,
                "open_incidents": len(self.get_open_incidents()),
                "incidents_resolved": self.metrics.incidents_resolved,
                "false_positives": self.metrics.false_positives,
                "avg_resolution_time_hours": round(self.metrics.avg_resolution_time_hours, 1),
                "total_events_detected": self.metrics.total_events,
                "events_last_24h": len(self.get_recent_events(24)),
                "avg_detection_latency_ms": round(self.metrics.avg_detection_latency_ms, 2),
                "threat_patterns": self.analyze_threat_patterns(),
            }
    
    def _register_default_rules(self):
        """Register default threat detection rules."""
        self.register_detection_rule(self._rule_brute_force_attempts)
        self.register_detection_rule(self._rule_privilege_escalation)
        self.register_detection_rule(self._rule_data_exfiltration)
        self.register_detection_rule(self._rule_encryption_failure)
    
    def _rule_brute_force_attempts(self) -> Optional[Dict[str, Any]]:
        """Detect brute force login attempts."""
        recent_events = self.get_recent_events(1)
        failed_logins = [
            e for e in recent_events
            if "login" in e.description.lower() and "failed" in e.description.lower()
        ]
        
        if len(failed_logins) > 10:
            return {
                "type": DetectionType.BRUTE_FORCE,
                "threat_level": ThreatLevel.HIGH,
                "description": f"Detected {len(failed_logins)} failed login attempts in 1 hour",
            }
        
        return None
    
    def _rule_privilege_escalation(self) -> Optional[Dict[str, Any]]:
        """Detect unusual privilege escalations."""
        recent_events = self.get_recent_events(1)
        escalations = [e for e in recent_events if "escalat" in e.description.lower()]
        
        if len(escalations) > 3:
            return {
                "type": DetectionType.PRIVILEGE_ESCALATION,
                "threat_level": ThreatLevel.HIGH,
                "description": "Multiple privilege escalation attempts detected",
            }
        
        return None
    
    def _rule_data_exfiltration(self) -> Optional[Dict[str, Any]]:
        """Detect potential data exfiltration."""
        recent_events = self.get_recent_events(1)
        large_exports = [
            e for e in recent_events
            if "export" in e.description.lower() and int(e.raw_data.get("size", 0)) > 1000000
        ]
        
        if large_exports:
            return {
                "type": DetectionType.DATA_EXFILTRATION,
                "threat_level": ThreatLevel.CRITICAL,
                "description": f"Large data export detected: {len(large_exports)} events",
            }
        
        return None
    
    def _rule_encryption_failure(self) -> Optional[Dict[str, Any]]:
        """Detect encryption failures."""
        recent_events = self.get_recent_events(1)
        failures = [e for e in recent_events if "encryption" in e.description.lower() and "fail" in e.description.lower()]
        
        if failures:
            return {
                "type": DetectionType.ENCRYPTION_FAILURE,
                "threat_level": ThreatLevel.CRITICAL,
                "description": "Encryption operation failure detected",
            }
        
        return None
    
    def _create_incident(self, event: SecurityEvent) -> Incident:
        """Create incident from security event."""
        incident = Incident(
            incident_id=str(uuid.uuid4()),
            title=f"Security Incident: {event.event_type.value}",
            description=event.description,
            threat_level=event.threat_level,
            status=IncidentStatus.DETECTED,
            detection_type=event.event_type,
            events=[event.event_id],
            affected_users=[event.affected_user] if event.affected_user else [],
            affected_resources=[event.affected_resource] if event.affected_resource else [],
        )
        
        self.incidents[incident.incident_id] = incident
        return incident
    
    def _send_alerts(self, incident: Incident) -> None:
        """Send alerts to registered handlers."""
        for handler in self.alert_handlers:
            try:
                handler(incident)
            except Exception as e:
                print(f"Error in alert handler: {e}")
    
    def _execute_responses(self, incident: Incident) -> None:
        """Execute automated responses."""
        handlers = self.response_handlers.get(incident.detection_type, [])
        
        for handler in handlers:
            try:
                handler(incident)
            except Exception as e:
                print(f"Error in response handler: {e}")
    
    def _get_highest_threat_level(self, events: List[SecurityEvent]) -> str:
        """Get highest threat level from events."""
        if not events:
            return "info"
        
        threat_hierarchy = {
            ThreatLevel.CRITICAL: 5,
            ThreatLevel.HIGH: 4,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.LOW: 2,
            ThreatLevel.INFO: 1,
        }
        
        max_level = max(threat_hierarchy.get(e.threat_level, 0) for e in events)
        
        for level, score in threat_hierarchy.items():
            if score == max_level:
                return level.value
        
        return "info"
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        if self.config.enable_real_time_monitoring:
            self.monitoring_thread = threading.Thread(target=self._periodic_monitoring, daemon=True)
            self.monitoring_thread.start()
        
        self.cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self.cleanup_thread.start()
    
    def _periodic_monitoring(self):
        """Periodically run detection rules."""
        while self._running:
            for rule in self.detection_rules:
                try:
                    result = rule()
                    if result:
                        self.detect_event(
                            event_type=result["type"],
                            threat_level=result["threat_level"],
                            description=result["description"],
                        )
                except Exception:
                    pass
            
            time.sleep(self.config.monitoring_interval_seconds)
    
    def _periodic_cleanup(self):
        """Clean up old incidents."""
        while self._running:
            with self._lock:
                cutoff_time = datetime.utcnow() - timedelta(days=self.config.incident_retention_days)
                
                old_incidents = [
                    iid for iid, incident in self.incidents.items()
                    if datetime.fromisoformat(incident.detected_at) < cutoff_time
                ]
                
                for iid in old_incidents:
                    del self.incidents[iid]
            
            time.sleep(86400)  # Daily cleanup
    
    def shutdown(self):
        """Gracefully shutdown security monitor."""
        self._running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
