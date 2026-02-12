"""
Phase 13: SLA/SLO Manager
Service Level Agreement and Objective tracking
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class SLAType(str, Enum):
    """Types of SLAs"""
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


class SLOStatus(str, Enum):
    """SLO compliance status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    BREACHED = "breached"
    UNKNOWN = "unknown"


class SLO:
    """Service Level Objective"""

    def __init__(self, slo_id: str, metric_name: str, threshold: float,
                 comparison: str, window_seconds: int):
        self.slo_id = slo_id
        self.metric_name = metric_name
        self.threshold = threshold
        self.comparison = comparison  # gt, gte, lt, lte, eq
        self.window_seconds = window_seconds
        self.created_at = datetime.utcnow()

    def evaluate(self, current_value: float) -> bool:
        """Check if SLO is met"""
        if self.comparison == "gt":
            return current_value > self.threshold
        elif self.comparison == "gte":
            return current_value >= self.threshold
        elif self.comparison == "lt":
            return current_value < self.threshold
        elif self.comparison == "lte":
            return current_value <= self.threshold
        elif self.comparison == "eq":
            return current_value == self.threshold
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "slo_id": self.slo_id,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "comparison": self.comparison,
            "window_seconds": self.window_seconds,
            "created_at": self.created_at.isoformat(),
        }


class SLA:
    """Service Level Agreement"""

    def __init__(self, sla_id: str, sla_type: SLAType, subscription_tier: str):
        self.sla_id = sla_id
        self.sla_type = sla_type
        self.subscription_tier = subscription_tier
        self.slos: Dict[str, SLO] = {}
        self.error_budget_percent = self._get_error_budget(subscription_tier)
        self.created_at = datetime.utcnow()

    @staticmethod
    def _get_error_budget(tier: str) -> float:
        """Get error budget for tier"""
        budgets = {
            "FREE": 10.0,
            "STARTER": 2.0,
            "PROFESSIONAL": 0.5,
            "ENTERPRISE": 0.1,
        }
        return budgets.get(tier, 5.0)

    def add_slo(self, slo: SLO) -> None:
        """Add SLO to SLA"""
        self.slos[slo.slo_id] = slo

    def get_error_budget_remaining(self, used_budget: float) -> float:
        """Calculate remaining error budget"""
        return max(0, self.error_budget_percent - used_budget)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "sla_id": self.sla_id,
            "sla_type": self.sla_type.value,
            "subscription_tier": self.subscription_tier,
            "error_budget_percent": self.error_budget_percent,
            "slo_count": len(self.slos),
            "created_at": self.created_at.isoformat(),
        }


class SLAPolicy:
    """SLA policy configuration"""

    def __init__(self):
        self.policies = {
            "FREE": {
                "availability": 95.0,
                "response_time_p99": 2000,  # ms
                "error_rate": 1.0,
                "throughput": 100,
            },
            "STARTER": {
                "availability": 99.0,
                "response_time_p99": 500,
                "error_rate": 0.5,
                "throughput": 1000,
            },
            "PROFESSIONAL": {
                "availability": 99.5,
                "response_time_p99": 200,
                "error_rate": 0.1,
                "throughput": 10000,
            },
            "ENTERPRISE": {
                "availability": 99.95,
                "response_time_p99": 100,
                "error_rate": 0.01,
                "throughput": 100000,
            },
        }

    def get_policy(self, tier: str) -> Dict[str, float]:
        """Get SLA policy for subscription tier"""
        return self.policies.get(tier, self.policies["FREE"])


class SLOTracker:
    """Track SLO compliance"""

    def __init__(self):
        self.slo_breaches: Dict[str, List[Dict]] = {}
        self.slo_history: Dict[str, List[Dict]] = {}
        self.current_status: Dict[str, SLOStatus] = {}

    def record_slo_check(self, slo_id: str, metric_value: float,
                        is_compliant: bool) -> None:
        """Record SLO check result"""
        timestamp = datetime.utcnow()

        if slo_id not in self.slo_history:
            self.slo_history[slo_id] = []

        self.slo_history[slo_id].append({
            "timestamp": timestamp.isoformat(),
            "value": metric_value,
            "compliant": is_compliant,
        })

        if not is_compliant:
            if slo_id not in self.slo_breaches:
                self.slo_breaches[slo_id] = []

            self.slo_breaches[slo_id].append({
                "timestamp": timestamp.isoformat(),
                "value": metric_value,
            })

    def get_slo_status(self, slo_id: str, hours: int = 1) -> SLOStatus:
        """Get SLO status for time period"""
        if slo_id not in self.slo_history:
            return SLOStatus.UNKNOWN

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [
            h for h in self.slo_history[slo_id]
            if datetime.fromisoformat(h["timestamp"]) >= cutoff
        ]

        if not recent:
            return SLOStatus.UNKNOWN

        compliant_count = sum(1 for h in recent if h["compliant"])
        compliance_rate = compliant_count / len(recent) * 100

        if compliance_rate >= 99:
            return SLOStatus.HEALTHY
        elif compliance_rate >= 95:
            return SLOStatus.WARNING
        else:
            return SLOStatus.BREACHED

    def get_slo_compliance_rate(self, slo_id: str, hours: int = 1) -> float:
        """Get SLO compliance rate"""
        if slo_id not in self.slo_history:
            return 0

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [
            h for h in self.slo_history[slo_id]
            if datetime.fromisoformat(h["timestamp"]) >= cutoff
        ]

        if not recent:
            return 0

        return sum(1 for h in recent if h["compliant"]) / len(recent) * 100

    def get_breach_events(self, slo_id: str, limit: int = 100) -> List[Dict]:
        """Get recent SLO breach events"""
        if slo_id not in self.slo_breaches:
            return []

        return self.slo_breaches[slo_id][-limit:]

    def predict_slo_breach(self, slo_id: str) -> Optional[Dict[str, Any]]:
        """Predict if SLO will breach in next hour"""
        if slo_id not in self.slo_history:
            return None

        # Get recent 30 minutes of data
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        recent = [
            h for h in self.slo_history[slo_id]
            if datetime.fromisoformat(h["timestamp"]) >= cutoff
        ]

        if len(recent) < 5:
            return None

        compliant_count = sum(1 for h in recent if h["compliant"])
        compliance_trend = compliant_count / len(recent)

        # If trend is declining, predict breach
        if compliance_trend < 0.8:
            return {
                "slo_id": slo_id,
                "predicted_breach": True,
                "confidence": min(1.0, (1.0 - compliance_trend) * 2),
                "recommendation": "Check metric source and consider increasing resources",
            }

        return None


class SLAManager:
    """
    Central SLA/SLO management service
    Tracks service agreements and objectives
    """

    def __init__(self):
        self.slas: Dict[str, SLA] = {}
        self.slo_tracker = SLOTracker()
        self.sla_policy = SLAPolicy()
        self.breach_alerts: List[Dict] = []

    def create_sla(self, tenant_id: str, sla_type: SLAType,
                  subscription_tier: str) -> str:
        """
        Create SLA for tenant
        Returns sla_id
        """
        import uuid
        sla_id = f"sla_{uuid.uuid4().hex[:16]}"

        sla = SLA(sla_id, sla_type, subscription_tier)
        self.slas[sla_id] = sla

        logger.debug(f"SLA created: {sla_id} ({sla_type.value})")

        return sla_id

    def add_slo_to_sla(self, sla_id: str, metric_name: str,
                      threshold: float, comparison: str,
                      window_seconds: int = 300) -> str:
        """
        Add SLO to SLA
        Returns slo_id
        """
        import uuid
        if sla_id not in self.slas:
            return None

        slo_id = f"slo_{uuid.uuid4().hex[:16]}"
        slo = SLO(slo_id, metric_name, threshold, comparison, window_seconds)

        self.slas[sla_id].add_slo(slo)

        logger.debug(f"SLO added: {slo_id} to SLA {sla_id}")

        return slo_id

    def track_slo_metric(self, slo_id: str, sla_id: str,
                        metric_value: float) -> bool:
        """
        Track metric against SLO
        Returns whether SLO is compliant
        """
        if sla_id not in self.slas:
            return False

        sla = self.slas[sla_id]
        if slo_id not in sla.slos:
            return False

        slo = sla.slos[slo_id]
        is_compliant = slo.evaluate(metric_value)

        self.slo_tracker.record_slo_check(slo_id, metric_value, is_compliant)

        if not is_compliant:
            self._record_breach(slo_id, sla_id, metric_value)

        return is_compliant

    def _record_breach(self, slo_id: str, sla_id: str, metric_value: float) -> None:
        """Record SLO breach"""
        self.breach_alerts.append({
            "timestamp": datetime.utcnow().isoformat(),
            "slo_id": slo_id,
            "sla_id": sla_id,
            "metric_value": metric_value,
        })

        logger.warning(f"SLO breach: {slo_id} - value {metric_value}")

    def check_slo_compliance(self, slo_id: str) -> Dict[str, Any]:
        """Check SLO compliance status"""
        status = self.slo_tracker.get_slo_status(slo_id)
        compliance_rate = self.slo_tracker.get_slo_compliance_rate(slo_id)

        return {
            "slo_id": slo_id,
            "status": status.value,
            "compliance_rate": compliance_rate,
            "recent_breaches": len(self.slo_tracker.get_breach_events(slo_id, limit=10)),
        }

    def get_slo_budget(self, sla_id: str, time_window_hours: int = 24) -> Dict[str, float]:
        """
        Get error budget for SLA
        Returns budget information
        """
        if sla_id not in self.slas:
            return {}

        sla = self.slas[sla_id]

        # Calculate total breach events in window
        cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_breaches = [
            b for b in self.breach_alerts
            if b["sla_id"] == sla_id and datetime.fromisoformat(b["timestamp"]) >= cutoff
        ]

        used_budget = len(recent_breaches) * (sla.error_budget_percent / 100)
        remaining = sla.get_error_budget_remaining(used_budget)

        return {
            "sla_id": sla_id,
            "total_budget_percent": sla.error_budget_percent,
            "used_budget_percent": used_budget,
            "remaining_budget_percent": remaining,
            "breach_events": len(recent_breaches),
        }

    def predict_slo_breach(self, slo_id: str) -> Optional[Dict[str, Any]]:
        """Predict imminent SLO breach"""
        return self.slo_tracker.predict_slo_breach(slo_id)

    def generate_sla_report(self, sla_id: str, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive SLA report"""
        if sla_id not in self.slas:
            return {}

        sla = self.slas[sla_id]
        slo_reports = []

        for slo_id, slo in sla.slos.items():
            status = self.slo_tracker.get_slo_status(slo_id, hours=hours)
            compliance = self.slo_tracker.get_slo_compliance_rate(slo_id, hours=hours)

            slo_reports.append({
                "slo_id": slo_id,
                "metric_name": slo.metric_name,
                "status": status.value,
                "compliance_rate": compliance,
                "breaches": len(self.slo_tracker.get_breach_events(slo_id, limit=100)),
            })

        return {
            "sla_id": sla_id,
            "sla_type": sla.sla_type.value,
            "subscription_tier": sla.subscription_tier,
            "report_period_hours": hours,
            "slos": slo_reports,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def alert_on_breach(self) -> List[Dict[str, Any]]:
        """Get recent breach alerts"""
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_alerts = [
            a for a in self.breach_alerts
            if datetime.fromisoformat(a["timestamp"]) >= cutoff
        ]
        return recent_alerts

    def get_sla_statistics(self) -> Dict[str, Any]:
        """Get SLA management statistics"""
        return {
            "total_slas": len(self.slas),
            "total_slos": sum(len(sla.slos) for sla in self.slas.values()),
            "recent_breaches": len(self.alert_on_breach()),
            "tracked_slos": len(self.slo_tracker.slo_history),
        }
