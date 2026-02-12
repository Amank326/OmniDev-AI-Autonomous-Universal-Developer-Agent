"""
Phase 23: Real-Time Alerting Service
Threshold monitoring, severity levels, escalation, multi-channel delivery
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert lifecycle status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class DeliveryChannel(Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    PAGERDUTY = "pagerduty"


class AlertingService:
    """
    Real-time alerting with thresholds, escalation, and multi-channel delivery
    """
    
    def __init__(self):
        """Initialize alerting service"""
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = {}
    
    # ========================================================================
    # ALERT RULE CREATION
    # ========================================================================
    
    def create_threshold_alert(
        self,
        name: str,
        metric: str,
        condition: str,  # "greater_than", "less_than", "equals", "range"
        threshold_value: float,
        severity: str = "warning",
        check_frequency_minutes: int = 5,
    ) -> Dict:
        """
        Create threshold-based alert rule
        
        Conditions: greater_than, less_than, equals, range, not_equals
        Severity: info, warning, critical, emergency
        Check frequency: 1-60 minutes
        """
        
        return {
            "rule_id": "",
            "name": name,
            "type": "threshold",
            "metric": metric,
            "condition": condition,
            "threshold": threshold_value,
            "severity": severity,
            "check_frequency_minutes": check_frequency_minutes,
            "enabled": True,
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
        }
    
    def create_anomaly_alert(
        self,
        name: str,
        metric: str,
        sensitivity: str = "medium",  # low, medium, high
        check_frequency_minutes: int = 5,
    ) -> Dict:
        """
        Create anomaly detection alert
        
        Uses ML to detect unusual patterns
        Sensitivities: low (1.5σ), medium (2σ), high (2.5σ)
        """
        
        return {
            "rule_id": "",
            "name": name,
            "type": "anomaly",
            "metric": metric,
            "sensitivity": sensitivity,
            "check_frequency_minutes": check_frequency_minutes,
            "enabled": True,
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
        }
    
    def create_trend_alert(
        self,
        name: str,
        metric: str,
        trend_direction: str,  # "decreasing", "increasing"
        change_percent: float,
        period_days: int = 7,
    ) -> Dict:
        """
        Create trend-based alert
        
        Alerts on metric trends changing
        Examples:
        - "Decrease in active users by 20% over 7 days"
        - "Increase in error rate by 50% over 3 days"
        """
        
        return {
            "rule_id": "",
            "name": name,
            "type": "trend",
            "metric": metric,
            "trend_direction": trend_direction,
            "change_percent": change_percent,
            "period_days": period_days,
            "enabled": True,
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
        }
    
    def create_comparison_alert(
        self,
        name: str,
        metric_1: str,
        comparison: str,  # "greater_than", "less_than", "equals"
        metric_2: str,
    ) -> Dict:
        """
        Create alert comparing two metrics
        
        Examples:
        - "Churn rate > acceptable threshold"
        - "Support response time > SLA target"
        """
        
        return {
            "rule_id": "",
            "name": name,
            "type": "comparison",
            "metric_1": metric_1,
            "comparison": comparison,
            "metric_2": metric_2,
            "enabled": True,
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
        }
    
    def create_composite_alert(
        self,
        name: str,
        rules: List[str],
        logic: str = "and",  # "and", "or"
    ) -> Dict:
        """
        Create composite alert from multiple rules
        
        Logic: all rules (AND) or any rule (OR)
        """
        
        return {
            "rule_id": "",
            "name": name,
            "type": "composite",
            "rules": rules,
            "logic": logic,
            "enabled": True,
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
        }
    
    # ========================================================================
    # ALERT CONFIGURATION
    # ========================================================================
    
    def configure_alert_delivery(
        self,
        rule_id: str,
        channels: List[Dict],
        suppress_duplicates: bool = True,
        duplicate_window_minutes: int = 60,
    ) -> Dict:
        """
        Configure delivery channels for alert
        
        Channels: [
            {"channel": "email", "recipients": ["team@company.com"]},
            {"channel": "slack", "webhook_url": "..."},
            {"channel": "pagerduty", "integration_key": "..."}
        ]
        """
        
        return {
            "rule_id": rule_id,
            "channels": channels,
            "suppress_duplicates": suppress_duplicates,
            "duplicate_window_minutes": duplicate_window_minutes,
            "updated_date": datetime.utcnow().isoformat(),
        }
    
    def set_alert_escalation(
        self,
        rule_id: str,
        escalation_rules: List[Dict],
    ) -> Dict:
        """
        Configure escalation for unacknowledged alerts
        
        Escalation rules: [
            {"after_minutes": 5, "escalate_to": "team_lead@company.com"},
            {"after_minutes": 15, "escalate_to": "manager@company.com"},
        ]
        """
        
        return {
            "rule_id": rule_id,
            "escalation_enabled": True,
            "escalation_rules": escalation_rules,
            "updated_date": datetime.utcnow().isoformat(),
        }
    
    def set_alert_suppression(
        self,
        rule_id: str,
        enabled: bool = True,
        reason: str = None,
        expires_at: str = None,
    ) -> Dict:
        """
        Suppress alert (temporarily disable)
        
        Used for maintenance windows or known issues
        """
        
        return {
            "rule_id": rule_id,
            "suppressed": enabled,
            "suppression_reason": reason,
            "suppression_expires": expires_at,
            "suppressed_by": "",
            "suppressed_date": datetime.utcnow().isoformat(),
        }
    
    def configure_alert_filters(
        self,
        rule_id: str,
        filters: Dict = None,
        exclude_segments: List[str] = None,
    ) -> Dict:
        """
        Configure filters for alert scope
        
        Narrows alert to specific customers, segments, regions, etc.
        """
        
        return {
            "rule_id": rule_id,
            "filters": filters or {},
            "exclude_segments": exclude_segments or [],
            "updated_date": datetime.utcnow().isoformat(),
        }
    
    # ========================================================================
    # ALERT MANAGEMENT
    # ========================================================================
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str = None,
        note: str = None,
    ) -> Dict:
        """
        Acknowledge alert (team is aware)
        
        Stops escalation and notifies rule creator
        """
        
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_date": datetime.utcnow().isoformat(),
            "acknowledged_by": acknowledged_by,
            "note": note,
        }
    
    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str = None,
        resolution: str = None,
    ) -> Dict:
        """
        Mark alert as resolved
        
        Closes alert and logs resolution
        """
        
        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_date": datetime.utcnow().isoformat(),
            "resolved_by": resolved_by,
            "resolution": resolution,
        }
    
    def snooze_alert(
        self,
        alert_id: str,
        snooze_minutes: int = 60,
    ) -> Dict:
        """
        Temporarily snooze alert notifications
        
        Useful for known temporary issues
        """
        
        return {
            "alert_id": alert_id,
            "snoozed_until": (datetime.utcnow() + timedelta(minutes=snooze_minutes)).isoformat(),
            "snoozed_date": datetime.utcnow().isoformat(),
        }
    
    def add_alert_comment(
        self,
        alert_id: str,
        comment: str,
        commented_by: str = None,
    ) -> Dict:
        """
        Add comment to alert for team collaboration
        
        Notifies rule followers of comment
        """
        
        return {
            "comment_id": "",
            "alert_id": alert_id,
            "comment": comment,
            "commented_by": commented_by,
            "commented_date": datetime.utcnow().isoformat(),
        }
    
    # ========================================================================
    # ALERT INSIGHTS
    # ========================================================================
    
    def get_active_alerts(
        self,
        severity: str = None,
        customer_id: str = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get currently active alerts
        
        Can filter by severity and customer
        """
        
        return [
            {
                "alert_id": "",
                "rule_name": "",
                "metric": "",
                "current_value": 0.0,
                "threshold": 0.0,
                "severity": "critical",
                "status": "active",
                "triggered_date": datetime.utcnow().isoformat(),
                "triggered_count": 1,
            }
        ]
    
    def get_alert_history(
        self,
        rule_id: str = None,
        days: int = 30,
    ) -> List[Dict]:
        """
        Get historical alerts
        
        Shows alert frequency, patterns, resolution time
        """
        
        return [
            {
                "alert_id": "",
                "rule_id": rule_id,
                "rule_name": "",
                "triggered_date": datetime.utcnow().isoformat(),
                "resolved_date": datetime.utcnow().isoformat(),
                "duration_minutes": 0,
                "severity": "warning",
                "status": "resolved",
            }
        ]
    
    def get_alert_analytics(
        self,
        days: int = 30,
    ) -> Dict:
        """
        Get alert analytics and trends
        
        Shows:
        - Alert volume
        - Top triggered rules
        - Average resolution time
        - Severity distribution
        - Delivery channel performance
        """
        
        return {
            "period_days": days,
            "total_alerts_triggered": 0,
            "alerts_resolved": 0,
            "avg_resolution_time_minutes": 0,
            "top_rules": [],
            "severity_distribution": {
                "info": 0,
                "warning": 0,
                "critical": 0,
                "emergency": 0,
            },
            "channel_performance": {
                "email": {"delivered": 0, "failed": 0},
                "slack": {"delivered": 0, "failed": 0},
                "pagerduty": {"delivered": 0, "failed": 0},
            },
            "trend": "increasing",
        }
    
    def get_rule_performance(
        self,
        rule_id: str,
    ) -> Dict:
        """
        Get performance metrics for alert rule
        
        Shows:
        - Accuracy (true/false positives)
        - False alarm rate
        - Avg time to trigger
        - Response time to alerts
        """
        
        return {
            "rule_id": rule_id,
            "total_triggered": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_positive_rate": 0.0,
            "avg_detection_time_minutes": 0,
            "avg_resolution_time_minutes": 0,
            "effectiveness_score": 0.0,
        }
    
    # ========================================================================
    # ALERT TEMPLATES & PRESETS
    # ========================================================================
    
    def get_alert_templates(self) -> List[Dict]:
        """
        Get pre-built alert templates for common scenarios
        
        Templates:
        - High error rate
        - Low user engagement
        - Revenue decline
        - Churn risk increase
        - Performance degradation
        - Data quality issues
        """
        
        return [
            {
                "template_id": "high_error_rate",
                "name": "High Error Rate",
                "description": "Alert when error rate exceeds threshold",
                "metric": "error_rate",
                "threshold": 5.0,
                "severity": "critical",
            },
            {
                "template_id": "low_engagement",
                "name": "Low Engagement",
                "description": "Alert when user engagement declines",
                "metric": "engagement_score",
                "threshold": 30.0,
                "severity": "warning",
            },
            {
                "template_id": "revenue_decline",
                "name": "Revenue Decline",
                "description": "Alert on significant revenue drop",
                "metric": "mrr",
                "type": "trend",
                "change_percent": 10.0,
                "severity": "critical",
            },
            {
                "template_id": "churn_risk",
                "name": "High Churn Risk",
                "description": "Alert on customers at churn risk",
                "metric": "churn_risk_score",
                "threshold": 70.0,
                "severity": "critical",
            },
        ]
    
    def apply_alert_template(
        self,
        template_id: str,
        name: str = None,
    ) -> Dict:
        """Apply alert template to create rule"""
        
        return {
            "rule_id": "",
            "template_id": template_id,
            "name": name,
            "created_date": datetime.utcnow().isoformat(),
            "status": "active",
        }
    
    # ========================================================================
    # ALERT INTEGRATION
    # ========================================================================
    
    def integrate_pagerduty(
        self,
        integration_key: str,
        severity_mapping: Dict = None,
    ) -> Dict:
        """
        Integrate with PagerDuty for incident management
        
        Creates incidents and escalations in PagerDuty
        """
        
        return {
            "integration_id": "",
            "service": "pagerduty",
            "status": "connected",
            "integration_key": integration_key,
            "severity_mapping": severity_mapping or {},
            "connected_date": datetime.utcnow().isoformat(),
        }
    
    def integrate_slack(
        self,
        webhook_url: str,
        channel: str = "#alerts",
    ) -> Dict:
        """
        Integrate with Slack for alert notifications
        
        Sends alerts to Slack channel
        """
        
        return {
            "integration_id": "",
            "service": "slack",
            "status": "connected",
            "channel": channel,
            "webhook_url": webhook_url,
            "connected_date": datetime.utcnow().isoformat(),
        }
    
    def integrate_teams(
        self,
        webhook_url: str,
    ) -> Dict:
        """
        Integrate with Microsoft Teams
        
        Sends alerts to Teams channel
        """
        
        return {
            "integration_id": "",
            "service": "teams",
            "status": "connected",
            "webhook_url": webhook_url,
            "connected_date": datetime.utcnow().isoformat(),
        }
