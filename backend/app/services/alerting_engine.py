"""
Alerting Engine Service
Alert management, routing, and notification system
Phase 42: Observability & Monitoring Infrastructure
"""

import logging
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
from threading import RLock, Thread
import queue
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(Enum):
    """Alert status"""
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"
    LOG = "log"


@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    description: str
    metric: str
    threshold: float
    comparison: str  # "greater", "less", "equals"
    duration_seconds: int = 60
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    cooldown_seconds: int = 300
    notifications: List[NotificationChannel] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def evaluate(self, current_value: float) -> bool:
        """Evaluate if alert should trigger"""
        if not self.enabled:
            return False
        
        if self.comparison == "greater":
            return current_value > self.threshold
        elif self.comparison == "less":
            return current_value < self.threshold
        elif self.comparison == "equals":
            return current_value == self.threshold
        
        return False


@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule: AlertRule
    status: AlertStatus = AlertStatus.FIRING
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    message: str = ""
    current_value: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self) -> None:
        """Resolve alert"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
    
    def acknowledge(self, user: str) -> None:
        """Acknowledge alert"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user
    
    def get_duration_seconds(self) -> float:
        """Get alert duration in seconds"""
        end_time = self.resolved_at or datetime.utcnow()
        return (end_time - self.triggered_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'rule': self.rule.name,
            'status': self.status.value,
            'severity': self.rule.severity.value,
            'triggered_at': self.triggered_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'duration_seconds': self.get_duration_seconds(),
            'message': self.message,
            'current_value': self.current_value,
            'context': self.context
        }


@dataclass
class AlertGroup:
    """Group of similar alerts"""
    id: str
    rule_name: str
    alerts: List[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_alert: Optional[datetime] = None
    
    def add_alert(self, alert: Alert) -> None:
        """Add alert to group"""
        self.alerts.append(alert)
        self.last_alert = datetime.utcnow()
    
    def get_active_count(self) -> int:
        """Get count of active (non-resolved) alerts"""
        return sum(1 for a in self.alerts if a.status in [AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED])


class NotificationHandler:
    """Handles sending notifications"""
    
    def __init__(self):
        self.handlers: Dict[NotificationChannel, Callable] = {
            NotificationChannel.LOG: self._notify_log,
            NotificationChannel.EMAIL: self._notify_email,
            NotificationChannel.SLACK: self._notify_slack,
            NotificationChannel.WEBHOOK: self._notify_webhook,
            NotificationChannel.PAGERDUTY: self._notify_pagerduty,
            NotificationChannel.SMS: self._notify_sms,
        }
    
    def send(self, alert: Alert, channel: NotificationChannel, config: Dict[str, Any]) -> bool:
        """Send notification"""
        handler = self.handlers.get(channel)
        if not handler:
            logger.warning(f"Unknown notification channel: {channel}")
            return False
        
        try:
            handler(alert, config)
            return True
        except Exception as e:
            logger.error(f"Notification error ({channel.value}): {e}")
            return False
    
    @staticmethod
    def _notify_log(alert: Alert, config: Dict[str, Any]) -> None:
        """Send log notification"""
        logger.warning(f"ALERT [{alert.rule.severity.value}] {alert.rule.name}: {alert.message}")
    
    @staticmethod
    def _notify_email(alert: Alert, config: Dict[str, Any]) -> None:
        """Send email notification"""
        try:
            smtp_server = config.get('smtp_server', 'localhost')
            smtp_port = config.get('smtp_port', 587)
            sender = config.get('sender', 'noreply@example.com')
            recipients = config.get('recipients', [])
            
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[{alert.rule.severity.value.upper()}] {alert.rule.name}"
            
            body = f"""
Alert: {alert.rule.name}
Severity: {alert.rule.severity.value}
Status: {alert.status.value}
Message: {alert.message}
Current Value: {alert.current_value}
Triggered At: {alert.triggered_at.isoformat()}

Rule: {alert.rule.description}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # For demonstration, just log
            logger.debug(f"Email notification to {recipients}")
        
        except Exception as e:
            logger.error(f"Email notification error: {e}")
    
    @staticmethod
    def _notify_slack(alert: Alert, config: Dict[str, Any]) -> None:
        """Send Slack notification"""
        try:
            webhook_url = config.get('webhook_url')
            if not webhook_url:
                logger.warning("Slack webhook URL not configured")
                return
            
            # Build Slack message
            severity_color = {
                AlertSeverity.CRITICAL: "#FF0000",
                AlertSeverity.HIGH: "#FF6600",
                AlertSeverity.MEDIUM: "#FFBB00",
                AlertSeverity.LOW: "#0099FF",
                AlertSeverity.INFO: "#00FF00",
            }.get(alert.rule.severity, "#999999")
            
            payload = {
                "attachments": [
                    {
                        "color": severity_color,
                        "title": alert.rule.name,
                        "text": alert.message,
                        "fields": [
                            {"title": "Severity", "value": alert.rule.severity.value, "short": True},
                            {"title": "Status", "value": alert.status.value, "short": True},
                            {"title": "Current Value", "value": str(alert.current_value), "short": True},
                            {"title": "Triggered At", "value": alert.triggered_at.isoformat(), "short": False},
                        ]
                    }
                ]
            }
            
            # For demonstration, just log
            logger.debug(f"Slack notification: {alert.rule.name}")
        
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
    
    @staticmethod
    def _notify_webhook(alert: Alert, config: Dict[str, Any]) -> None:
        """Send webhook notification"""
        try:
            webhook_url = config.get('webhook_url')
            if not webhook_url:
                logger.warning("Webhook URL not configured")
                return
            
            payload = alert.to_dict()
            
            # For demonstration, just log
            logger.debug(f"Webhook notification to {webhook_url}")
        
        except Exception as e:
            logger.error(f"Webhook notification error: {e}")
    
    @staticmethod
    def _notify_pagerduty(alert: Alert, config: Dict[str, Any]) -> None:
        """Send PagerDuty notification"""
        try:
            integration_key = config.get('integration_key')
            if not integration_key:
                logger.warning("PagerDuty integration key not configured")
                return
            
            # For demonstration, just log
            logger.debug(f"PagerDuty notification for {alert.rule.name}")
        
        except Exception as e:
            logger.error(f"PagerDuty notification error: {e}")
    
    @staticmethod
    def _notify_sms(alert: Alert, config: Dict[str, Any]) -> None:
        """Send SMS notification"""
        try:
            phone_numbers = config.get('phone_numbers', [])
            if not phone_numbers:
                logger.warning("Phone numbers not configured for SMS")
                return
            
            message = f"{alert.rule.name}: {alert.message}"
            
            # For demonstration, just log
            logger.debug(f"SMS notification to {phone_numbers}")
        
        except Exception as e:
            logger.error(f"SMS notification error: {e}")


class AlertingEngine:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_groups: Dict[str, AlertGroup] = {}
        self.last_triggered: Dict[str, datetime] = {}
        self.notification_handler = NotificationHandler()
        self.notification_config: Dict[NotificationChannel, Dict[str, Any]] = {}
        self.lock = RLock()
        self.queue = queue.Queue()
        self.callbacks: List[Callable] = []
        self._start_processor()
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule"""
        with self.lock:
            self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> None:
        """Remove alert rule"""
        with self.lock:
            if rule_name in self.rules:
                del self.rules[rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
    
    def evaluate_rules(self, metric_name: str, current_value: float) -> List[Alert]:
        """Evaluate rules for a metric"""
        triggered_alerts = []
        
        with self.lock:
            for rule in self.rules.values():
                if rule.metric == metric_name and rule.evaluate(current_value):
                    # Check cooldown
                    last_trigger = self.last_triggered.get(rule.name)
                    if last_trigger and (datetime.utcnow() - last_trigger).total_seconds() < rule.cooldown_seconds:
                        continue
                    
                    # Create alert
                    import uuid
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        rule=rule,
                        message=f"{rule.name}: {rule.description} (current: {current_value}, threshold: {rule.threshold})",
                        current_value=current_value
                    )
                    
                    self.alerts[alert.id] = alert
                    self.last_triggered[rule.name] = datetime.utcnow()
                    triggered_alerts.append(alert)
                    
                    # Add to group
                    self._add_to_group(alert)
                    
                    # Queue for processing
                    self.queue.put(alert)
                    self._trigger_callbacks(alert)
                    
                    logger.warning(f"Alert triggered: {alert.rule.name} (value: {current_value})")
        
        return triggered_alerts
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self.lock:
            alert = self.alerts.get(alert_id)
            if alert:
                alert.resolve()
                logger.info(f"Resolved alert: {alert.rule.name}")
                return True
        
        return False
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert"""
        with self.lock:
            alert = self.alerts.get(alert_id)
            if alert:
                alert.acknowledge(user)
                logger.info(f"Acknowledged alert {alert_id} by {user}")
                return True
        
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        with self.lock:
            return [a for a in self.alerts.values() if a.status in [AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED]]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity"""
        with self.lock:
            return [a for a in self.alerts.values() if a.rule.severity == severity]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        with self.lock:
            active_alerts = self.get_active_alerts()
            
            stats = {
                'total_rules': len(self.rules),
                'total_alerts': len(self.alerts),
                'active_alerts': len(active_alerts),
                'by_severity': {
                    severity.value: len([a for a in active_alerts if a.rule.severity == severity])
                    for severity in AlertSeverity
                },
                'acknowledged': sum(1 for a in active_alerts if a.status == AlertStatus.ACKNOWLEDGED),
                'firing': sum(1 for a in active_alerts if a.status == AlertStatus.FIRING),
            }
        
        return stats
    
    def set_notification_config(self, channel: NotificationChannel, config: Dict[str, Any]) -> None:
        """Set notification channel configuration"""
        with self.lock:
            self.notification_config[channel] = config
        logger.info(f"Configured notification channel: {channel.value}")
    
    def register_callback(self, callback: Callable[[Alert], None]) -> None:
        """Register callback for alerts"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _add_to_group(self, alert: Alert) -> None:
        """Add alert to group"""
        group_name = alert.rule.name
        
        with self.lock:
            if group_name not in self.alert_groups:
                import uuid
                self.alert_groups[group_name] = AlertGroup(
                    id=str(uuid.uuid4()),
                    rule_name=group_name
                )
            
            self.alert_groups[group_name].add_alert(alert)
    
    def _trigger_callbacks(self, alert: Alert) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _start_processor(self) -> None:
        """Start background alert processor"""
        processor_thread = Thread(target=self._processor_loop, daemon=True)
        processor_thread.start()
    
    def _processor_loop(self) -> None:
        """Background loop for processing alerts"""
        while True:
            try:
                alert = self.queue.get(timeout=5)
                self._process_alert(alert)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processor error: {e}")
    
    def _process_alert(self, alert: Alert) -> None:
        """Process alert (send notifications)"""
        # Send notifications
        for channel in alert.rule.notifications:
            config = self.notification_config.get(channel, {})
            self.notification_handler.send(alert, channel, config)


# Global alerting engine
_alerting_engine: Optional[AlertingEngine] = None


def get_alerting_engine() -> AlertingEngine:
    """Get or create alerting engine"""
    global _alerting_engine
    if _alerting_engine is None:
        _alerting_engine = AlertingEngine()
    return _alerting_engine
