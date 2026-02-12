"""
Alert Rules Engine - Smart alert rule evaluation and execution
Phase 27: Advanced Notifications & Real-time Alerts System
"""

import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Callable, Tuple
import json


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


class ConditionType(Enum):
    """Types of rule conditions"""
    THRESHOLD = "threshold"
    COMPARISON = "comparison"
    CONTAINS = "contains"
    REGEX = "regex"
    TIME_BASED = "time_based"
    COMPOSITE = "composite"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


@dataclass
class AlertCondition:
    """Individual alert condition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    condition_type: ConditionType = ConditionType.THRESHOLD
    field: str = ""
    operator: str = ""  # >, <, ==, !=, >=, <=, contains, regex_match
    value: Any = None
    enabled: bool = True


@dataclass
class AlertEscalation:
    """Alert escalation configuration"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trigger_severity: AlertSeverity = AlertSeverity.WARNING
    target_severity: AlertSeverity = AlertSeverity.CRITICAL
    delay_minutes: int = 5
    action: str = ""  # "escalate", "notify_manager", "create_ticket"
    enabled: bool = True


@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    conditions: List[AlertCondition] = field(default_factory=list)
    logical_operator: str = "AND"  # AND, OR
    target_severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    escalation_rules: List[AlertEscalation] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=lambda: ["in_app"])
    cooldown_minutes: int = 15  # Prevent duplicate alerts
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    last_triggered: Optional[datetime] = None


@dataclass
class Alert:
    """Alert instance"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    user_id: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    title: str = ""
    message: str = ""
    source: str = ""  # "metric", "forecast", "system", "user"
    data: Dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    escalation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertAggregation:
    """Aggregated alert (multiple instances into one)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_ids: List[str] = field(default_factory=list)
    count: int = 1
    first_occurred: datetime = field(default_factory=datetime.utcnow)
    last_occurred: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertRulesEngine:
    """Engine for evaluating and executing alert rules"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: Dict[str, List[Alert]] = {}
        self.aggregations: Dict[str, AlertAggregation] = {}
        self.suppression_rules: Dict[str, Dict[str, Any]] = {}
        self._init_operators()

    def _init_operators(self):
        """Initialize condition operators"""
        self.operators: Dict[str, Callable] = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "contains": lambda a, b: b in str(a),
            "regex_match": lambda a, b: __import__('re').match(b, str(a)) is not None,
            "in_list": lambda a, b: a in b,
        }

    def create_rule(
        self,
        name: str,
        description: str,
        conditions: List[AlertCondition],
        target_severity: AlertSeverity,
        created_by: str,
        logical_operator: str = "AND",
        cooldown_minutes: int = 15,
        notification_channels: Optional[List[str]] = None
    ) -> AlertRule:
        """Create new alert rule"""
        rule = AlertRule(
            name=name,
            description=description,
            conditions=conditions,
            logical_operator=logical_operator,
            target_severity=target_severity,
            created_by=created_by,
            cooldown_minutes=cooldown_minutes,
            notification_channels=notification_channels or ["in_app"]
        )
        self.rules[rule.id] = rule
        return rule

    def evaluate_rule(self, rule_id: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate if rule conditions match data"""
        rule = self.rules.get(rule_id)
        if not rule or not rule.enabled:
            return False, {}

        results = []
        for condition in rule.conditions:
            if not condition.enabled:
                continue

            field_value = data.get(condition.field)
            operator_func = self.operators.get(condition.operator)

            if operator_func and field_value is not None:
                try:
                    result = operator_func(field_value, condition.value)
                    results.append(result)
                except Exception as e:
                    results.append(False)

        # Handle logical operators
        if rule.logical_operator == "AND":
            matched = all(results) if results else False
        else:  # OR
            matched = any(results) if results else False

        return matched, {"conditions_evaluated": len(results), "condition_results": results}

    def trigger_alert(
        self,
        rule_id: str,
        user_id: str,
        title: str,
        message: str,
        source: str = "system",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """Trigger an alert from rule"""
        rule = self.rules.get(rule_id)
        if not rule:
            return None

        # Check cooldown
        if rule.last_triggered:
            elapsed = (datetime.utcnow() - rule.last_triggered).total_seconds() / 60
            if elapsed < rule.cooldown_minutes:
                return None  # Still in cooldown

        alert = Alert(
            rule_id=rule_id,
            user_id=user_id,
            severity=rule.target_severity,
            title=title,
            message=message,
            source=source,
            data=data or {}
        )

        self.alerts[alert.id] = alert

        # Add to history
        if user_id not in self.alert_history:
            self.alert_history[user_id] = []
        self.alert_history[user_id].append(alert)

        # Update rule last triggered
        rule.last_triggered = datetime.utcnow()

        return alert

    def check_suppression(self, alert: Alert) -> bool:
        """Check if alert is suppressed"""
        for suppression_id, suppression in self.suppression_rules.items():
            if self._matches_suppression(alert, suppression):
                return True
        return False

    def _matches_suppression(self, alert: Alert, suppression: Dict[str, Any]) -> bool:
        """Check if alert matches suppression rule"""
        # Match by rule_id and severity
        if "rule_ids" in suppression:
            if alert.rule_id not in suppression["rule_ids"]:
                return False

        if "min_severity" in suppression:
            severity_order = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.CRITICAL, AlertSeverity.URGENT]
            if severity_order.index(alert.severity) < severity_order.index(suppression["min_severity"]):
                return False

        # Check time window
        if "active_until" in suppression:
            if datetime.utcnow() > suppression["active_until"]:
                return False

        return True

    def add_suppression_rule(
        self,
        rule_ids: List[str],
        min_severity: AlertSeverity = AlertSeverity.WARNING,
        duration_minutes: int = 60
    ) -> str:
        """Add alert suppression rule"""
        suppression_id = str(uuid.uuid4())
        self.suppression_rules[suppression_id] = {
            "rule_ids": rule_ids,
            "min_severity": min_severity,
            "active_until": datetime.utcnow() + timedelta(minutes=duration_minutes)
        }
        return suppression_id

    def escalate_alert(self, alert_id: str, escalation_rule: AlertEscalation) -> Optional[Alert]:
        """Escalate alert to higher severity"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return None

        # Record escalation
        alert.escalation_history.append({
            "from_severity": alert.severity.value,
            "to_severity": escalation_rule.target_severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": escalation_rule.action
        })

        alert.severity = escalation_rule.target_severity
        alert.status = AlertStatus.ESCALATED

        return alert

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge alert"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = user_id
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            return True
        return False

    def get_active_alerts(self, user_id: str, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts for user"""
        alerts = self.alert_history.get(user_id, [])
        active = [a for a in alerts if a.status == AlertStatus.ACTIVE]

        if severity:
            active = [a for a in active if a.severity == severity]

        return sorted(active, key=lambda a: a.created_at, reverse=True)

    def get_alert_timeline(self, user_id: str, hours: int = 24) -> List[Alert]:
        """Get alert timeline for user"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        alerts = self.alert_history.get(user_id, [])
        return [a for a in alerts if a.created_at >= cutoff]

    def aggregate_alerts(self, alert_ids: List[str]) -> AlertAggregation:
        """Aggregate multiple alerts into one"""
        aggregation = AlertAggregation(
            alert_ids=alert_ids,
            count=len(alert_ids)
        )

        if alert_ids:
            first_alert = self.alerts.get(alert_ids[0])
            if first_alert:
                aggregation.first_occurred = first_alert.created_at

        self.aggregations[aggregation.id] = aggregation
        return aggregation

    def get_alert_statistics(self, user_id: str) -> Dict[str, int]:
        """Get alert statistics"""
        alerts = self.alert_history.get(user_id, [])

        stats = {
            "total": len(alerts),
            "active": len([a for a in alerts if a.status == AlertStatus.ACTIVE]),
            "resolved": len([a for a in alerts if a.status == AlertStatus.RESOLVED]),
            "acknowledged": len([a for a in alerts if a.status == AlertStatus.ACKNOWLEDGED]),
            "escalated": len([a for a in alerts if a.status == AlertStatus.ESCALATED]),
        }

        # By severity
        for severity in AlertSeverity:
            stats[f"severity_{severity.value}"] = len([a for a in alerts if a.severity == severity])

        return stats

    def update_rule(self, rule_id: str, **kwargs) -> Optional[AlertRule]:
        """Update alert rule"""
        rule = self.rules.get(rule_id)
        if not rule:
            return None

        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Delete alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def list_rules(self, enabled_only: bool = False) -> List[AlertRule]:
        """List alert rules"""
        rules = list(self.rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return sorted(rules, key=lambda r: r.created_at, reverse=True)
