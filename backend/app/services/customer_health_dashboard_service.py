"""
Customer Health Dashboard Service - Aggregates health metrics and generates alerts
Real-time health monitoring, CSM recommendations, and at-risk customer alerts
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Action needed within 24 hours
    MEDIUM = "medium"      # Action needed within 1 week
    LOW = "low"            # Monitor and plan


class CSMActionType(Enum):
    """CSM action recommendations"""
    URGENT_OUTREACH = "urgent_outreach"
    BUSINESS_REVIEW = "business_review"
    TRAINING = "training"
    EXPANSION = "expansion"
    RETENTION = "retention"
    CELEBRATION = "celebration"


class CustomerHealthDashboardService:
    """
    Aggregate customer health across all metrics
    Generate alerts and CSM action items
    """
    
    def __init__(self):
        """Initialize dashboard service"""
        self.health_snapshots = {}
        self.alerts = {}
        self.csm_actions = {}
        self.dashboard_metrics = {}
    
    # ========================================================================
    # HEALTH AGGREGATION
    # ========================================================================
    
    def create_health_snapshot(
        self,
        customer_id: str,
        health_score: Dict,
        onboarding_progress: Dict,
        usage_metrics: Dict,
        recent_interactions: int,
        expansion_opportunities: List[Dict],
    ) -> Dict:
        """
        Create comprehensive health snapshot
        Combines all health signals into single view
        """
        
        snapshot = {
            "customer_id": customer_id,
            "snapshot_date": datetime.utcnow().isoformat(),
            "overall_health": health_score.get("health_level"),
            "health_score": health_score.get("overall_score"),
            "onboarding_status": {
                "completion_percent": onboarding_progress.get("completion_percent"),
                "current_phase": onboarding_progress.get("current_phase"),
                "days_remaining": onboarding_progress.get("days_remaining"),
            },
            "usage_metrics": {
                "monthly_executions": usage_metrics.get("executions", 0),
                "active_users": usage_metrics.get("active_users", 0),
                "features_used": usage_metrics.get("features_used", 0),
                "api_calls": usage_metrics.get("api_calls", 0),
            },
            "engagement": {
                "last_activity_days_ago": usage_metrics.get("days_since_last_activity", 0),
                "logins_last_30_days": usage_metrics.get("logins_last_30_days", 0),
                "interaction_count": recent_interactions,
            },
            "health_components": health_score.get("component_scores", {}),
            "key_drivers": health_score.get("key_drivers", []),
            "risk_factors": health_score.get("risk_factors", []),
            "expansion_opportunities": len(expansion_opportunities),
            "trend": health_score.get("trend", "stable"),
        }
        
        self.health_snapshots[customer_id] = snapshot
        return snapshot
    
    # ========================================================================
    # ALERT GENERATION
    # ========================================================================
    
    def generate_alerts(
        self,
        customer_id: str,
        health_snapshot: Dict,
    ) -> List[Dict]:
        """
        Generate alerts based on health snapshot
        
        Alert triggers:
        - Churn risk (health score < 40)
        - Disengagement (>30 days inactivity)
        - No onboarding progress (stuck for 14 days)
        - Feature adoption plateau
        - Revenue decline
        """
        
        alerts = []
        
        # Critical health score
        health_score = health_snapshot.get("health_score", 100)
        if health_score < 40:
            alerts.append({
                "alert_id": f"alert_critical_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "level": AlertLevel.CRITICAL.value,
                "type": "health_critical",
                "title": "Critical Account Health",
                "description": f"Customer health score critically low at {health_score}",
                "action_required": "Immediate executive outreach",
                "generated_at": datetime.utcnow().isoformat(),
            })
        
        elif health_score < 60:
            alerts.append({
                "alert_id": f"alert_high_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "level": AlertLevel.HIGH.value,
                "type": "health_declining",
                "title": "Account Health Declining",
                "description": f"Health score declining. Current: {health_score}",
                "action_required": "Business review required",
                "generated_at": datetime.utcnow().isoformat(),
            })
        
        # Disengagement alert
        days_since_activity = health_snapshot.get("engagement", {}).get("last_activity_days_ago", 0)
        if days_since_activity > 30:
            alerts.append({
                "alert_id": f"alert_disengaged_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "level": AlertLevel.HIGH.value if days_since_activity > 60 else AlertLevel.MEDIUM.value,
                "type": "disengagement",
                "title": "Customer Disengaged",
                "description": f"No activity for {days_since_activity} days",
                "action_required": "Re-engagement campaign needed",
                "generated_at": datetime.utcnow().isoformat(),
            })
        
        # Onboarding stuck alert
        onboarding_status = health_snapshot.get("onboarding_status", {})
        completion_percent = onboarding_status.get("completion_percent", 100)
        days_remaining = onboarding_status.get("days_remaining", 0)
        
        if completion_percent < 100 and days_remaining < 0:
            alerts.append({
                "alert_id": f"alert_stuck_onboarding_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "level": AlertLevel.MEDIUM.value,
                "type": "onboarding_stuck",
                "title": "Onboarding Stalled",
                "description": f"Onboarding {completion_percent}% complete, overdue",
                "action_required": "Check-in call to unblock",
                "generated_at": datetime.utcnow().isoformat(),
            })
        
        # Positive alerts
        if health_snapshot.get("trend") == "improving":
            alerts.append({
                "alert_id": f"alert_improving_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "level": AlertLevel.LOW.value,
                "type": "positive_trend",
                "title": "Account Improving!",
                "description": "Customer health score improving - momentum building",
                "action_required": "Nurture and expand",
                "generated_at": datetime.utcnow().isoformat(),
            })
        
        # Store alerts
        if customer_id not in self.alerts:
            self.alerts[customer_id] = []
        self.alerts[customer_id].extend(alerts)
        
        return alerts
    
    # ========================================================================
    # CSM ACTION RECOMMENDATIONS
    # ========================================================================
    
    def generate_csm_actions(
        self,
        customer_id: str,
        health_snapshot: Dict,
        expansion_opportunities: List[Dict],
    ) -> List[Dict]:
        """
        Generate prioritized CSM action items
        
        Actions are:
        - Time-bound (due date)
        - Specific (clear next step)
        - Measurable (success criteria)
        """
        
        actions = []
        health_level = health_snapshot.get("overall_health")
        health_score = health_snapshot.get("health_score", 0)
        engagement = health_snapshot.get("engagement", {})
        
        # Critical/At-Risk - Urgent outreach
        if health_level in ["critical", "at_risk"]:
            actions.append({
                "action_id": f"action_urgent_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "type": CSMActionType.URGENT_OUTREACH.value,
                "priority": "critical" if health_level == "critical" else "high",
                "title": f"Urgent Outreach - {'Critical' if health_level == 'critical' else 'At-Risk'} Account",
                "description": f"Health score {health_score} - intervention needed",
                "due_date": (datetime.utcnow() + timedelta(hours=4)).isoformat() if health_level == "critical" else (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "csm_activity": "Executive call - understand issues, create retention plan",
                "expected_outcome": "Recovery plan or account save",
            })
        
        # Healthy - Business Review
        elif health_level == "healthy":
            actions.append({
                "action_id": f"action_biz_review_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "type": CSMActionType.BUSINESS_REVIEW.value,
                "priority": "medium",
                "title": "Quarterly Business Review",
                "description": "Align on goals, review progress, identify growth",
                "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "csm_activity": "Scheduled QBR call - agenda, metrics review, roadmap",
                "expected_outcome": "Customer satisfaction and alignment",
            })
        
        # Thriving - Expansion focus
        if health_level == "thriving" and expansion_opportunities:
            actions.append({
                "action_id": f"action_expansion_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "type": CSMActionType.EXPANSION.value,
                "priority": "high",
                "title": f"Expansion Opportunity ({len(expansion_opportunities)} identified)",
                "description": f"Customer ready to expand - {len(expansion_opportunities)} opportunities",
                "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                "csm_activity": "Expansion conversation - discuss opportunities and value",
                "expected_outcome": "Identified next upsell/expansion",
            })
        
        # Disengaged - Re-engagement training
        if engagement.get("last_activity_days_ago", 0) > 14:
            actions.append({
                "action_id": f"action_training_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "type": CSMActionType.TRAINING.value,
                "priority": "medium",
                "title": "Feature Adoption Training",
                "description": "Low engagement - training could improve adoption",
                "due_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
                "csm_activity": "Personalized training session - features and best practices",
                "expected_outcome": "Increased feature adoption and engagement",
            })
        
        # Success story - Celebration
        if health_score >= 90 and engagement.get("interaction_count", 0) > 5:
            actions.append({
                "action_id": f"action_celebration_{customer_id}_{datetime.utcnow().timestamp()}",
                "customer_id": customer_id,
                "type": CSMActionType.CELEBRATION.value,
                "priority": "low",
                "title": "Success Story Opportunity",
                "description": "Highly engaged, successful customer - potential case study",
                "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "csm_activity": "Case study interview, customer reference program",
                "expected_outcome": "Marketing asset and peer learning",
            })
        
        # Store actions
        if customer_id not in self.csm_actions:
            self.csm_actions[customer_id] = []
        self.csm_actions[customer_id].extend(actions)
        
        return actions
    
    # ========================================================================
    # DASHBOARD METRICS
    # ========================================================================
    
    def get_portfolio_health(self) -> Dict:
        """
        Get aggregate health metrics across customer portfolio
        
        Shows:
        - Health distribution
        - At-risk MRR
        - Expansion potential
        - CSM workload
        """
        
        if not self.health_snapshots:
            return {"error": "No health data available"}
        
        total_customers = len(self.health_snapshots)
        health_levels = {"thriving": 0, "healthy": 0, "at_risk": 0, "critical": 0}
        alert_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        total_expansion_opportunities = 0
        csm_actions_pending = 0
        total_health_score = 0
        
        for customer_data in self.health_snapshots.values():
            # Health distribution
            health_level = customer_data.get("overall_health")
            health_levels[health_level] += 1
            total_health_score += customer_data.get("health_score", 0)
            
            # Expansion opportunities
            total_expansion_opportunities += customer_data.get("expansion_opportunities", 0)
        
        # Count alerts
        for customer_alerts in self.alerts.values():
            for alert in customer_alerts:
                level = alert.get("level")
                alert_counts[level] += 1
        
        # Count CSM actions
        for actions_list in self.csm_actions.values():
            csm_actions_pending += len(actions_list)
        
        avg_health_score = (total_health_score / total_customers) if total_customers > 0 else 0
        
        return {
            "total_customers": total_customers,
            "avg_health_score": round(avg_health_score, 1),
            "health_distribution": health_levels,
            "health_percentages": {
                k: round(v / total_customers * 100, 1) for k, v in health_levels.items()
            },
            "alerts": {
                "total": sum(alert_counts.values()),
                "by_level": alert_counts,
            },
            "at_risk_customers": health_levels["at_risk"] + health_levels["critical"],
            "at_risk_percent": round((health_levels["at_risk"] + health_levels["critical"]) / total_customers * 100, 1) if total_customers > 0 else 0,
            "expansion_opportunities_total": total_expansion_opportunities,
            "csm_actions_pending": csm_actions_pending,
            "health_trend": self._calculate_portfolio_trend(),
        }
    
    def _calculate_portfolio_trend(self) -> str:
        """Determine if portfolio health is improving/declining"""
        # Placeholder - would compare snapshots over time
        return "stable"
    
    def get_csm_workload(self) -> Dict:
        """
        Get CSM workload and action priorities
        
        Shows:
        - Actions by priority
        - Actions by type
        - CSM time estimates
        """
        
        actions_by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        actions_by_type = {}
        
        for actions_list in self.csm_actions.values():
            for action in actions_list:
                priority = action.get("priority", "medium")
                actions_by_priority[priority] += 1
                
                action_type = action.get("type")
                if action_type not in actions_by_type:
                    actions_by_type[action_type] = 0
                actions_by_type[action_type] += 1
        
        # Estimate time per action type
        time_estimates = {
            CSMActionType.URGENT_OUTREACH.value: 1.0,  # hours
            CSMActionType.BUSINESS_REVIEW.value: 1.5,
            CSMActionType.TRAINING.value: 2.0,
            CSMActionType.EXPANSION.value: 1.5,
            CSMActionType.RETENTION.value: 1.0,
            CSMActionType.CELEBRATION.value: 0.5,
        }
        
        total_hours = sum(
            actions_by_type.get(atype, 0) * time_estimates.get(atype, 1)
            for atype in actions_by_type
        )
        
        return {
            "total_pending_actions": sum(actions_by_priority.values()),
            "by_priority": actions_by_priority,
            "by_type": actions_by_type,
            "estimated_hours": round(total_hours, 1),
            "estimated_days_for_1_csm": round(total_hours / 8, 1),
            "recommended_team_size": max(1, int(total_hours / 40)),  # 40 hour work week
        }
    
    def get_at_risk_summary(self) -> Dict:
        """
        Get summary of critical and at-risk accounts
        
        For immediate CSM action
        """
        
        critical = []
        at_risk = []
        
        for customer_id, snapshot in self.health_snapshots.items():
            health_level = snapshot.get("overall_health")
            health_score = snapshot.get("health_score", 0)
            
            risk_data = {
                "customer_id": customer_id,
                "health_score": health_score,
                "trend": snapshot.get("trend"),
                "key_risk": snapshot.get("risk_factors")[0] if snapshot.get("risk_factors") else "unknown",
                "last_activity_days": snapshot.get("engagement", {}).get("last_activity_days_ago", 0),
            }
            
            if health_level == "critical":
                critical.append(risk_data)
            elif health_level == "at_risk":
                at_risk.append(risk_data)
        
        # Sort by score (lowest first)
        critical.sort(key=lambda x: x["health_score"])
        at_risk.sort(key=lambda x: x["health_score"])
        
        return {
            "critical_accounts": critical,
            "at_risk_accounts": at_risk,
            "total_at_risk": len(critical) + len(at_risk),
            "urgent_action_required": len(critical),
            "summary": f"{len(critical)} critical, {len(at_risk)} at-risk accounts requiring immediate attention",
        }
