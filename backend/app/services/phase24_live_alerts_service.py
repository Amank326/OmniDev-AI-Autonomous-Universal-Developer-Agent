"""
Phase 24: Live Alerts Service
Real-time alert evaluation and instant delivery with deduplication
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import uuid


class AlertState(Enum):
    """Alert state in lifecycle"""
    TRIGGERED = "triggered"
    ACTIVE = "active"
    ESCALATED = "escalated"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertDeliveryStatus(Enum):
    """Alert delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


@dataclass
class AlertEvent:
    """Represents an alert event"""
    alert_id: str
    rule_id: str
    metric_id: str
    severity: str
    timestamp: datetime
    current_value: float
    threshold: float
    condition: str
    metric_name: str = ""
    context_data: Dict = field(default_factory=dict)
    state: AlertState = AlertState.TRIGGERED


@dataclass
class AlertDeliveryLog:
    """Log of alert delivery"""
    delivery_id: str
    alert_id: str
    channel: str
    recipient: str
    sent_at: datetime
    status: AlertDeliveryStatus
    error_message: str = ""


class LiveAlertsService:
    """
    Real-time alerts service
    Evaluates conditions on streaming metrics and delivers alerts instantly
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.alert_rules: Dict[str, Dict] = {}
        self.active_alerts: Dict[str, AlertEvent] = {}
        self.alert_history: Dict[str, List[AlertEvent]] = defaultdict(list)
        self.delivery_logs: Dict[str, List[AlertDeliveryLog]] = defaultdict(list)
        self.alert_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.evaluation_functions: Dict[str, Callable] = {}
        self.deduplication_window_seconds = 300  # 5 minutes
        self.recent_alerts: Dict[str, datetime] = {}  # For deduplication

    # ========================================================================
    # ALERT RULE MANAGEMENT
    # ========================================================================

    def create_alert_rule(
        self,
        rule_name: str,
        metric_id: str,
        condition: str,  # greater_than, less_than, equals, anomaly, trend
        threshold: float = None,
        severity: str = "warning",
        enabled: bool = True,
        metadata: Dict = None,
    ) -> Dict:
        """
        Create alert rule for streaming evaluation
        
        Args:
            rule_name: Rule name
            metric_id: Metric to monitor
            condition: Condition type
            threshold: Threshold value
            severity: Alert severity
            enabled: Enable rule
            metadata: Additional metadata
        
        Returns:
            Alert rule dict
        """
        rule_id = str(uuid.uuid4())

        rule = {
            "rule_id": rule_id,
            "name": rule_name,
            "metric_id": metric_id,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "enabled": enabled,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
            "evaluation_count": 0,
            "trigger_count": 0,
        }

        self.alert_rules[rule_id] = rule

        return rule

    def update_alert_rule(self, rule_id: str, updates: Dict) -> bool:
        """Update alert rule"""
        if rule_id not in self.alert_rules:
            return False

        self.alert_rules[rule_id].update(updates)

        return True

    def enable_alert_rule(self, rule_id: str) -> bool:
        """Enable alert rule"""
        if rule_id not in self.alert_rules:
            return False

        self.alert_rules[rule_id]["enabled"] = True

        return True

    def disable_alert_rule(self, rule_id: str) -> bool:
        """Disable alert rule"""
        if rule_id not in self.alert_rules:
            return False

        self.alert_rules[rule_id]["enabled"] = False

        return True

    def get_alert_rule(self, rule_id: str) -> Optional[Dict]:
        """Get alert rule"""
        return self.alert_rules.get(rule_id)

    # ========================================================================
    # ALERT EVALUATION
    # ========================================================================

    def register_evaluation_function(
        self,
        condition_type: str,
        eval_func: Callable,
    ):
        """
        Register evaluation function for condition type
        
        Args:
            condition_type: Condition type
            eval_func: Callable that evaluates condition
        """
        self.evaluation_functions[condition_type] = eval_func

    def evaluate_condition(
        self,
        rule_id: str,
        current_value: float,
        metric_name: str,
    ) -> Optional[AlertEvent]:
        """
        Evaluate alert rule condition
        
        Args:
            rule_id: Alert rule ID
            current_value: Current metric value
            metric_name: Metric name
        
        Returns:
            AlertEvent if condition triggered, None otherwise
        """
        if rule_id not in self.alert_rules:
            return None

        rule = self.alert_rules[rule_id]

        if not rule["enabled"]:
            return None

        rule["evaluation_count"] += 1

        condition_type = rule["condition"]
        threshold = rule["threshold"]

        # Evaluate condition
        triggered = False

        if condition_type == "greater_than":
            triggered = current_value > threshold
        elif condition_type == "less_than":
            triggered = current_value < threshold
        elif condition_type == "equals":
            triggered = current_value == threshold
        elif condition_type in self.evaluation_functions:
            eval_func = self.evaluation_functions[condition_type]
            triggered = eval_func(current_value, threshold)

        if not triggered:
            return None

        # Check deduplication
        dedup_key = f"{rule_id}"
        if self._is_duplicate_alert(dedup_key):
            return None

        # Create alert event
        alert_id = str(uuid.uuid4())
        alert = AlertEvent(
            alert_id=alert_id,
            rule_id=rule_id,
            metric_id=rule["metric_id"],
            severity=rule["severity"],
            timestamp=datetime.utcnow(),
            current_value=current_value,
            threshold=threshold,
            condition=condition_type,
            metric_name=metric_name,
        )

        rule["trigger_count"] += 1
        self.recent_alerts[dedup_key] = datetime.utcnow()

        return alert

    def _is_duplicate_alert(self, dedup_key: str) -> bool:
        """Check if alert is duplicate based on window"""
        if dedup_key not in self.recent_alerts:
            return False

        last_alert_time = self.recent_alerts[dedup_key]
        time_since_last = (
            (datetime.utcnow() - last_alert_time).total_seconds()
        )

        return time_since_last < self.deduplication_window_seconds

    # ========================================================================
    # ALERT LIFECYCLE
    # ========================================================================

    def trigger_alert(self, alert: AlertEvent) -> bool:
        """
        Trigger alert (activate monitoring)
        
        Args:
            alert: AlertEvent
        
        Returns:
            Success status
        """
        alert.state = AlertState.ACTIVE
        self.active_alerts[alert.alert_id] = alert
        self.alert_history[alert.rule_id].append(alert)

        # Notify subscribers
        self._notify_subscribers(alert.rule_id, alert)

        return True

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge alert (team has seen it)
        
        Args:
            alert_id: Alert ID
            acknowledged_by: User who acknowledged
        
        Returns:
            Success status
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.state = AlertState.ACKNOWLEDGED
        alert.context_data["acknowledged_by"] = acknowledged_by
        alert.context_data["acknowledged_at"] = datetime.utcnow().isoformat()

        return True

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_note: str = "",
    ) -> bool:
        """
        Resolve alert (close it)
        
        Args:
            alert_id: Alert ID
            resolved_by: User who resolved
            resolution_note: Resolution note
        
        Returns:
            Success status
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.state = AlertState.RESOLVED
        alert.context_data["resolved_by"] = resolved_by
        alert.context_data["resolved_at"] = datetime.utcnow().isoformat()
        alert.context_data["resolution_note"] = resolution_note

        del self.active_alerts[alert_id]

        return True

    def suppress_alert(
        self,
        alert_id: str,
        suppress_minutes: int,
        reason: str = "",
    ) -> bool:
        """
        Suppress alert temporarily
        
        Args:
            alert_id: Alert ID
            suppress_minutes: Suppression duration
            reason: Suppression reason
        
        Returns:
            Success status
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.state = AlertState.SUPPRESSED
        alert.context_data["suppressed_until"] = (
            (datetime.utcnow() + timedelta(minutes=suppress_minutes)).isoformat()
        )
        alert.context_data["suppression_reason"] = reason

        return True

    def get_alert(self, alert_id: str) -> Optional[AlertEvent]:
        """Get active alert"""
        return self.active_alerts.get(alert_id)

    def get_active_alerts(self) -> List[AlertEvent]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alerts_by_severity(self, severity: str) -> List[AlertEvent]:
        """Get alerts by severity"""
        return [
            a for a in self.active_alerts.values()
            if a.severity == severity
        ]

    # ========================================================================
    # ALERT DELIVERY
    # ========================================================================

    def deliver_alert(
        self,
        alert: AlertEvent,
        channels: List[str],
        recipients: Dict[str, List[str]],
    ) -> List[AlertDeliveryLog]:
        """
        Deliver alert to specified channels
        
        Args:
            alert: AlertEvent
            channels: List of delivery channels
            recipients: Dict mapping channels to recipients
        
        Returns:
            List of delivery logs
        """
        delivery_logs = []

        for channel in channels:
            if channel not in recipients:
                continue

            for recipient in recipients[channel]:
                delivery_log = self._deliver_to_channel(
                    alert,
                    channel,
                    recipient,
                )
                delivery_logs.append(delivery_log)
                self.delivery_logs[alert.alert_id].append(delivery_log)

        return delivery_logs

    def _deliver_to_channel(
        self,
        alert: AlertEvent,
        channel: str,
        recipient: str,
    ) -> AlertDeliveryLog:
        """Deliver alert to specific channel"""
        delivery_id = str(uuid.uuid4())

        log = AlertDeliveryLog(
            delivery_id=delivery_id,
            alert_id=alert.alert_id,
            channel=channel,
            recipient=recipient,
            sent_at=datetime.utcnow(),
            status=AlertDeliveryStatus.SENT,
        )

        return log

    def get_delivery_logs(self, alert_id: str) -> List[AlertDeliveryLog]:
        """Get delivery logs for alert"""
        return self.delivery_logs.get(alert_id, [])

    # ========================================================================
    # ALERT ESCALATION
    # ========================================================================

    def escalate_alert(
        self,
        alert_id: str,
        escalation_level: int,
    ) -> bool:
        """
        Escalate alert to higher level
        
        Args:
            alert_id: Alert ID
            escalation_level: Escalation level
        
        Returns:
            Success status
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.state = AlertState.ESCALATED
        alert.context_data["escalation_level"] = escalation_level
        alert.context_data["escalated_at"] = datetime.utcnow().isoformat()

        return True

    def check_escalation_needed(
        self,
        alert_id: str,
        unacknowledged_minutes: int,
    ) -> bool:
        """
        Check if alert needs escalation
        
        Args:
            alert_id: Alert ID
            unacknowledged_minutes: Minutes since triggered
        
        Returns:
            True if escalation needed
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]

        if alert.state == AlertState.ACKNOWLEDGED:
            return False

        minutes_since_trigger = (
            (datetime.utcnow() - alert.timestamp).total_seconds() / 60
        )

        return minutes_since_trigger >= unacknowledged_minutes

    # ========================================================================
    # SUBSCRIPTIONS & NOTIFICATIONS
    # ========================================================================

    def subscribe_to_rule(
        self,
        rule_id: str,
        subscriber: Callable,
    ) -> bool:
        """
        Subscribe to rule alerts
        
        Args:
            rule_id: Alert rule ID
            subscriber: Callback function
        
        Returns:
            Success status
        """
        if rule_id not in self.alert_rules:
            return False

        self.alert_subscribers[rule_id].append(subscriber)

        return True

    def unsubscribe_from_rule(
        self,
        rule_id: str,
        subscriber: Callable,
    ) -> bool:
        """Unsubscribe from rule alerts"""
        if rule_id not in self.alert_subscribers:
            return False

        try:
            self.alert_subscribers[rule_id].remove(subscriber)
            return True
        except ValueError:
            return False

    def _notify_subscribers(self, rule_id: str, alert: AlertEvent):
        """Notify subscribers of alert"""
        if rule_id in self.alert_subscribers:
            for subscriber in self.alert_subscribers[rule_id]:
                try:
                    subscriber(alert)
                except Exception:
                    pass

    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================

    def get_rule_analytics(self, rule_id: str) -> Optional[Dict]:
        """
        Get analytics for alert rule
        
        Args:
            rule_id: Alert rule ID
        
        Returns:
            Analytics dict
        """
        if rule_id not in self.alert_rules:
            return None

        rule = self.alert_rules[rule_id]
        alerts = self.alert_history.get(rule_id, [])
        active = [a for a in alerts if a.state == AlertState.ACTIVE]
        acknowledged = [a for a in alerts if a.state == AlertState.ACKNOWLEDGED]

        avg_resolution_time = None
        if acknowledged:
            resolution_times = []
            for alert in acknowledged:
                if "resolved_at" in alert.context_data:
                    resolution_minutes = (
                        (datetime.utcnow() - alert.timestamp).total_seconds() / 60
                    )
                    resolution_times.append(resolution_minutes)

            if resolution_times:
                avg_resolution_time = sum(resolution_times) / len(resolution_times)

        return {
            "rule_id": rule_id,
            "rule_name": rule["name"],
            "evaluation_count": rule["evaluation_count"],
            "trigger_count": rule["trigger_count"],
            "active_alerts": len(active),
            "acknowledged_alerts": len(acknowledged),
            "avg_resolution_time_minutes": avg_resolution_time,
            "trigger_rate": (
                rule["trigger_count"] / max(rule["evaluation_count"], 1) * 100
            ),
        }

    def get_alert_trend(
        self,
        rule_id: str,
        hours: int = 24,
    ) -> Optional[Dict]:
        """
        Get alert trend for rule
        
        Args:
            rule_id: Alert rule ID
            hours: Historical period
        
        Returns:
            Trend dict with time series
        """
        if rule_id not in self.alert_history:
            return None

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        alerts = [
            a for a in self.alert_history[rule_id]
            if a.timestamp >= cutoff_time
        ]

        # Count alerts per hour
        hourly_counts = defaultdict(int)
        for alert in alerts:
            hour_key = alert.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_counts[hour_key] += 1

        return {
            "rule_id": rule_id,
            "total_alerts": len(alerts),
            "time_period_hours": hours,
            "hourly_breakdown": dict(hourly_counts),
        }

    # ========================================================================
    # CLEANUP & MANAGEMENT
    # ========================================================================

    def cleanup_old_alerts(self, retention_days: int = 30) -> int:
        """
        Remove old resolved alerts
        
        Args:
            retention_days: Retention period
        
        Returns:
            Number of alerts removed
        """
        cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
        removed_count = 0

        for rule_id, alerts in self.alert_history.items():
            original_count = len(alerts)
            self.alert_history[rule_id] = [
                a for a in alerts if a.timestamp >= cutoff_time
            ]
            removed_count += original_count - len(self.alert_history[rule_id])

        return removed_count

    def clear_recent_alerts_cache(self) -> int:
        """Clear deduplication cache"""
        count = len(self.recent_alerts)
        self.recent_alerts.clear()

        return count

    def get_all_rules(self) -> List[Dict]:
        """Get all alert rules"""
        return list(self.alert_rules.values())
