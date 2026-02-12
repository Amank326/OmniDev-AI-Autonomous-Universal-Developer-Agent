"""
Phase 13: Alert Manager
Multi-channel alert orchestration and notifications
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Alert types"""
    SLO_BREACH = "slo_breach"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_SPIKE = "error_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    ANOMALY_DETECTED = "anomaly_detected"
    QUOTA_EXCEEDED = "quota_exceeded"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"
    IN_APP = "in_app"


class AlertStatus(str, Enum):
    """Alert status"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"


class Alert:
    """Alert event"""

    def __init__(self, alert_id: str, alert_type: AlertType,
                 severity: AlertSeverity, title: str, description: str,
                 tenant_id: str):
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.description = description
        self.tenant_id = tenant_id
        self.status = AlertStatus.OPEN
        self.created_at = datetime.utcnow()
        self.acknowledged_at: Optional[datetime] = None
        self.resolved_at: Optional[datetime] = None
        self.acknowledged_by: Optional[str] = None
        self.resolved_by: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.notification_count = 0

    def acknowledge(self, user_id: str) -> None:
        """Acknowledge alert"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id

    def resolve(self, user_id: str = None) -> None:
        """Resolve alert"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id

    def silence(self, duration_minutes: int = 60) -> None:
        """Silence alert for duration"""
        self.status = AlertStatus.SILENCED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by,
            "notification_count": self.notification_count,
            "metadata": self.metadata,
        }


class AlertRule:
    """Alert rule configuration"""

    def __init__(self, rule_id: str, alert_type: AlertType,
                 condition: str, severity: AlertSeverity,
                 notification_channels: List[NotificationChannel]):
        self.rule_id = rule_id
        self.alert_type = alert_type
        self.condition = condition
        self.severity = severity
        self.notification_channels = notification_channels
        self.enabled = True
        self.created_at = datetime.utcnow()
        self.escalation_enabled = False
        self.escalation_minutes = 15
        self.deduplication_window_seconds = 300

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rule_id": self.rule_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "condition": self.condition,
            "channels": [c.value for c in self.notification_channels],
            "enabled": self.enabled,
            "escalation_enabled": self.escalation_enabled,
            "escalation_minutes": self.escalation_minutes,
            "created_at": self.created_at.isoformat(),
        }


class Notification:
    """Notification sent to channel"""

    def __init__(self, notification_id: str, alert_id: str,
                 channel: NotificationChannel):
        self.notification_id = notification_id
        self.alert_id = alert_id
        self.channel = channel
        self.created_at = datetime.utcnow()
        self.sent = False
        self.sent_at: Optional[datetime] = None
        self.error: Optional[str] = None

    def mark_sent(self) -> None:
        """Mark notification as sent"""
        self.sent = True
        self.sent_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "notification_id": self.notification_id,
            "alert_id": self.alert_id,
            "channel": self.channel.value,
            "created_at": self.created_at.isoformat(),
            "sent": self.sent,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error": self.error,
        }


class AlertManager:
    """
    Central alert management service
    Multi-channel notification orchestration
    """

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notifications: List[Notification] = []
        self.deduplication_cache: Dict[str, Dict] = {}
        self.notification_templates = self._init_templates()

    def create_alert_rule(self, alert_type: AlertType, condition: str,
                         severity: AlertSeverity,
                         channels: List[NotificationChannel]) -> str:
        """
        Create alert rule
        Returns rule_id
        """
        import uuid
        rule_id = f"rule_{uuid.uuid4().hex[:16]}"

        rule = AlertRule(rule_id, alert_type, condition, severity, channels)
        self.alert_rules[rule_id] = rule

        logger.debug(f"Alert rule created: {rule_id}")

        return rule_id

    def create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                    title: str, description: str, tenant_id: str) -> str:
        """
        Create alert
        Returns alert_id
        """
        import uuid
        alert_id = f"alert_{uuid.uuid4().hex[:16]}"

        alert = Alert(alert_id, alert_type, severity, title, description, tenant_id)
        self.alerts[alert_id] = alert

        logger.warning(f"Alert created: {alert_id} - {title}")

        return alert_id

    def evaluate_alert_rule(self, rule_id: str, metric_value: float,
                           metric_name: str, tenant_id: str) -> Optional[str]:
        """
        Evaluate alert rule against metric
        Returns alert_id if triggered, None otherwise
        """
        if rule_id not in self.alert_rules:
            return None

        rule = self.alert_rules[rule_id]

        if not rule.enabled:
            return None

        # Check deduplication
        cache_key = f"{rule_id}:{tenant_id}"
        if cache_key in self.deduplication_cache:
            cache_entry = self.deduplication_cache[cache_key]
            if (datetime.utcnow() - cache_entry["timestamp"]).total_seconds() < rule.deduplication_window_seconds:
                return None

        # Evaluate condition (simplified)
        triggered = self._evaluate_condition(rule.condition, metric_value)

        if triggered:
            alert_id = self.create_alert(
                rule.alert_type,
                rule.severity,
                f"{rule.alert_type.value.replace('_', ' ').title()} Alert",
                f"Metric {metric_name} triggered alert rule {rule_id}",
                tenant_id
            )

            # Send notifications
            self.send_notification(alert_id, rule.notification_channels)

            # Update dedup cache
            self.deduplication_cache[cache_key] = {
                "alert_id": alert_id,
                "timestamp": datetime.utcnow(),
            }

            return alert_id

        return None

    def _evaluate_condition(self, condition: str, value: float) -> bool:
        """
        Evaluate alert condition
        Simplified: supports "gt:100", "lt:50", etc.
        """
        try:
            parts = condition.split(":")
            if len(parts) != 2:
                return False

            operator = parts[0]
            threshold = float(parts[1])

            if operator == "gt":
                return value > threshold
            elif operator == "gte":
                return value >= threshold
            elif operator == "lt":
                return value < threshold
            elif operator == "lte":
                return value <= threshold
            elif operator == "eq":
                return value == threshold

            return False
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def send_notification(self, alert_id: str,
                         channels: List[NotificationChannel]) -> None:
        """Send notifications for alert"""
        if alert_id not in self.alerts:
            return

        alert = self.alerts[alert_id]

        for channel in channels:
            self._send_to_channel(alert, channel)

    def _send_to_channel(self, alert: Alert, channel: NotificationChannel) -> None:
        """Send alert to specific channel"""
        import uuid
        notification_id = f"notif_{uuid.uuid4().hex[:16]}"
        notification = Notification(notification_id, alert.alert_id, channel)

        try:
            # Simulate sending
            if channel == NotificationChannel.EMAIL:
                self._send_email(alert)
            elif channel == NotificationChannel.SLACK:
                self._send_slack(alert)
            elif channel == NotificationChannel.PAGERDUTY:
                self._send_pagerduty(alert)
            elif channel == NotificationChannel.WEBHOOK:
                self._send_webhook(alert)
            elif channel == NotificationChannel.SMS:
                self._send_sms(alert)
            elif channel == NotificationChannel.IN_APP:
                self._send_in_app(alert)

            notification.mark_sent()
            logger.debug(f"Notification sent to {channel.value}: {alert.alert_id}")

        except Exception as e:
            notification.error = str(e)
            logger.error(f"Error sending to {channel.value}: {e}")

        alert.notification_count += 1
        self.notifications.append(notification)

    def _send_email(self, alert: Alert) -> None:
        """Send email notification"""
        template = self.notification_templates.get("email", {})
        # In production: use email service
        logger.info(f"Email sent for alert {alert.alert_id}")

    def _send_slack(self, alert: Alert) -> None:
        """Send Slack notification"""
        # In production: use Slack API
        logger.info(f"Slack message sent for alert {alert.alert_id}")

    def _send_pagerduty(self, alert: Alert) -> None:
        """Send PagerDuty notification"""
        # In production: use PagerDuty API
        logger.info(f"PagerDuty incident created for alert {alert.alert_id}")

    def _send_webhook(self, alert: Alert) -> None:
        """Send webhook notification"""
        # In production: HTTP POST to webhook URL
        logger.info(f"Webhook sent for alert {alert.alert_id}")

    def _send_sms(self, alert: Alert) -> None:
        """Send SMS notification"""
        # In production: use SMS service
        logger.info(f"SMS sent for alert {alert.alert_id}")

    def _send_in_app(self, alert: Alert) -> None:
        """Send in-app notification"""
        logger.info(f"In-app notification created for alert {alert.alert_id}")

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge alert"""
        if alert_id not in self.alerts:
            return False

        self.alerts[alert_id].acknowledge(user_id)
        logger.info(f"Alert {alert_id} acknowledged by {user_id}")
        return True

    def resolve_alert(self, alert_id: str, user_id: str = None) -> bool:
        """Resolve alert"""
        if alert_id not in self.alerts:
            return False

        self.alerts[alert_id].resolve(user_id)
        logger.info(f"Alert {alert_id} resolved")
        return True

    def silence_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """Silence alert"""
        if alert_id not in self.alerts:
            return False

        self.alerts[alert_id].silence(duration_minutes)
        logger.info(f"Alert {alert_id} silenced for {duration_minutes} minutes")
        return True

    def get_active_alerts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get active alerts for tenant"""
        active = [
            a for a in self.alerts.values()
            if a.tenant_id == tenant_id and a.status in [AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]
        ]

        active.sort(key=lambda x: x.created_at, reverse=True)
        return [a.to_dict() for a in active]

    def get_alert_history(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history for tenant"""
        tenant_alerts = [
            a for a in self.alerts.values()
            if a.tenant_id == tenant_id
        ]

        tenant_alerts.sort(key=lambda x: x.created_at, reverse=True)
        return [a.to_dict() for a in tenant_alerts[:limit]]

    def deduplicate_alerts(self) -> int:
        """Remove duplicate recent alerts"""
        seen = {}
        duplicates_removed = 0

        for alert_id, alert in list(self.alerts.items()):
            key = f"{alert.alert_type.value}:{alert.tenant_id}"

            if key in seen:
                prev_alert = seen[key]
                if (alert.created_at - prev_alert.created_at).total_seconds() < 300:
                    del self.alerts[alert_id]
                    duplicates_removed += 1
                    continue

            seen[key] = alert

        return duplicates_removed

    def get_alert_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get alert statistics"""
        tenant_alerts = [a for a in self.alerts.values() if a.tenant_id == tenant_id]

        return {
            "total_alerts": len(tenant_alerts),
            "open_alerts": sum(1 for a in tenant_alerts if a.status == AlertStatus.OPEN),
            "acknowledged": sum(1 for a in tenant_alerts if a.status == AlertStatus.ACKNOWLEDGED),
            "resolved": sum(1 for a in tenant_alerts if a.status == AlertStatus.RESOLVED),
            "total_rules": len(self.alert_rules),
            "active_rules": sum(1 for r in self.alert_rules.values() if r.enabled),
        }

    def _init_templates(self) -> Dict[str, Dict]:
        """Initialize notification templates"""
        return {
            "email": {
                "subject": "Alert: {title}",
                "body": "Alert Type: {alert_type}\nSeverity: {severity}\nDescription: {description}",
            },
            "slack": {
                "color": {"critical": "danger", "high": "warning", "medium": "warning", "low": "good"},
            },
        }
