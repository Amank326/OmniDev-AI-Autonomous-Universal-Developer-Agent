"""
Phase 26: Team Analytics Service
Team metrics, productivity tracking, member contributions
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

# ========================================================================
# ENUMS
# ========================================================================

class ContributionType(Enum):
    """Types of contributions to team"""
    METRIC_CREATED = "metric_created"
    INSIGHT_GENERATED = "insight_generated"
    FORECAST_GENERATED = "forecast_generated"
    ANOMALY_DETECTED = "anomaly_detected"
    DASHBOARD_SHARED = "dashboard_shared"

class TeamMetricType(Enum):
    """Types of team-level metrics"""
    INSIGHTS_PER_DAY = "insights_per_day"
    METRICS_CREATED = "metrics_created"
    TEAM_ENGAGEMENT = "team_engagement"
    FORECAST_ACCURACY = "forecast_accuracy"
    ANOMALIES_DETECTED = "anomalies_detected"
    ACTIVE_MEMBERS = "active_members"


# ========================================================================
# DATACLASSES
# ========================================================================

@dataclass
class MemberContribution:
    """Member contribution data"""
    user_id: str
    workspace_id: str
    contribution_type: ContributionType
    count: int = 1
    last_contributed: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)

@dataclass
class TeamMetric:
    """Team-level aggregated metric"""
    metric_id: str
    workspace_id: str
    metric_type: TeamMetricType
    value: float
    timestamp: datetime
    period: str = "daily"  # daily, weekly, monthly
    comparison_value: Optional[float] = None  # previous period

@dataclass
class MemberStats:
    """Member productivity statistics"""
    user_id: str
    workspace_id: str
    workspace_name: str
    metrics_created: int = 0
    insights_generated: int = 0
    forecasts_generated: int = 0
    anomalies_detected: int = 0
    dashboards_shared: int = 0
    total_contributions: int = 0
    last_active: datetime = field(default_factory=datetime.utcnow)
    productivity_score: float = 0.0  # 0-100

@dataclass
class TeamHealthScore:
    """Overall team health assessment"""
    workspace_id: str
    score: float  # 0-100
    engagement_score: float
    productivity_score: float
    collaboration_score: float
    trend: str  # improving, stable, declining
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ========================================================================
# TEAM ANALYTICS SERVICE
# ========================================================================

class TeamAnalyticsService:
    """Team-level analytics and productivity tracking"""
    
    def __init__(self):
        self.contributions: Dict[str, List[MemberContribution]] = {}
        self.team_metrics: Dict[str, List[TeamMetric]] = {}
        self.member_stats: Dict[str, MemberStats] = {}
        self.team_health: Dict[str, TeamHealthScore] = {}
    
    
    # ====================================================================
    # CONTRIBUTION TRACKING
    # ====================================================================
    
    def record_contribution(self, user_id: str, workspace_id: str,
                           contribution_type: ContributionType,
                           metadata: Optional[Dict] = None) -> MemberContribution:
        """Record member contribution"""
        key = f"{workspace_id}:{user_id}"
        
        contribution = MemberContribution(
            user_id=user_id,
            workspace_id=workspace_id,
            contribution_type=contribution_type,
            metadata=metadata or {}
        )
        
        if key not in self.contributions:
            self.contributions[key] = []
        
        self.contributions[key].append(contribution)
        
        # Update member stats
        self._update_member_stats(user_id, workspace_id, contribution_type)
        
        return contribution
    
    def _update_member_stats(self, user_id: str, workspace_id: str,
                            contribution_type: ContributionType) -> None:
        """Update member statistics"""
        key = f"{workspace_id}:{user_id}"
        
        if key not in self.member_stats:
            self.member_stats[key] = MemberStats(
                user_id=user_id,
                workspace_id=workspace_id,
                workspace_name="Unknown"
            )
        
        stats = self.member_stats[key]
        
        if contribution_type == ContributionType.METRIC_CREATED:
            stats.metrics_created += 1
        elif contribution_type == ContributionType.INSIGHT_GENERATED:
            stats.insights_generated += 1
        elif contribution_type == ContributionType.FORECAST_GENERATED:
            stats.forecasts_generated += 1
        elif contribution_type == ContributionType.ANOMALY_DETECTED:
            stats.anomalies_detected += 1
        elif contribution_type == ContributionType.DASHBOARD_SHARED:
            stats.dashboards_shared += 1
        
        stats.total_contributions += 1
        stats.last_active = datetime.utcnow()
        
        # Calculate productivity score (0-100)
        stats.productivity_score = self._calculate_productivity_score(stats)
    
    def _calculate_productivity_score(self, stats: MemberStats) -> float:
        """Calculate productivity score based on contributions"""
        score = 0
        
        # Weight different contribution types
        score += stats.metrics_created * 2
        score += stats.insights_generated * 3
        score += stats.forecasts_generated * 2.5
        score += stats.anomalies_detected * 1.5
        score += stats.dashboards_shared * 2
        
        # Cap at 100
        return min(score, 100)
    
    
    # ====================================================================
    # MEMBER STATISTICS
    # ====================================================================
    
    def get_member_stats(self, user_id: str, workspace_id: str) -> Optional[MemberStats]:
        """Get member statistics"""
        key = f"{workspace_id}:{user_id}"
        return self.member_stats.get(key)
    
    def get_team_members_stats(self, workspace_id: str) -> List[MemberStats]:
        """Get all team members' statistics"""
        return [stats for stats in self.member_stats.values() 
                if stats.workspace_id == workspace_id]
    
    def get_top_contributors(self, workspace_id: str, limit: int = 10) -> List[MemberStats]:
        """Get top contributors by productivity score"""
        members = self.get_team_members_stats(workspace_id)
        # Sort by productivity score descending
        sorted_members = sorted(members, 
                               key=lambda m: m.productivity_score, 
                               reverse=True)
        return sorted_members[:limit]
    
    def get_contributions_leaderboard(self, workspace_id: str) -> List[Dict]:
        """Get contributions leaderboard"""
        members = self.get_team_members_stats(workspace_id)
        
        leaderboard = []
        for rank, member in enumerate(sorted(members, 
                                             key=lambda m: m.total_contributions,
                                             reverse=True)[:20], 1):
            leaderboard.append({
                "rank": rank,
                "user_id": member.user_id,
                "total_contributions": member.total_contributions,
                "metrics_created": member.metrics_created,
                "insights_generated": member.insights_generated,
                "forecasts_generated": member.forecasts_generated,
                "productivity_score": member.productivity_score
            })
        
        return leaderboard
    
    
    # ====================================================================
    # TEAM METRICS
    # ====================================================================
    
    def record_team_metric(self, workspace_id: str, metric_type: TeamMetricType,
                          value: float, period: str = "daily") -> TeamMetric:
        """Record team-level metric"""
        metric = TeamMetric(
            metric_id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            period=period
        )
        
        if workspace_id not in self.team_metrics:
            self.team_metrics[workspace_id] = []
        
        self.team_metrics[workspace_id].append(metric)
        return metric
    
    def get_team_metric(self, workspace_id: str, metric_type: TeamMetricType,
                       hours: int = 24) -> List[TeamMetric]:
        """Get team metric for last N hours"""
        if workspace_id not in self.team_metrics:
            return []
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        metrics = [m for m in self.team_metrics[workspace_id]
                  if m.metric_type == metric_type and m.timestamp > cutoff]
        
        return sorted(metrics, key=lambda m: m.timestamp)
    
    def calculate_insights_per_day(self, workspace_id: str) -> float:
        """Calculate insights generated per day"""
        key = f"{workspace_id}:*"
        contributions = []
        
        for contrib_list in self.contributions.values():
            for contrib in contrib_list:
                if (contrib.workspace_id == workspace_id and
                    contrib.contribution_type == ContributionType.INSIGHT_GENERATED):
                    contributions.append(contrib)
        
        if not contributions:
            return 0.0
        
        # Get date range
        latest = max(c.last_contributed for c in contributions)
        earliest = min(c.last_contributed for c in contributions)
        days = max((latest - earliest).days, 1)
        
        return len(contributions) / days
    
    def calculate_forecast_accuracy(self, workspace_id: str) -> float:
        """Calculate average forecast accuracy"""
        metrics = self.get_team_metric(workspace_id, TeamMetricType.FORECAST_ACCURACY, hours=168)
        
        if not metrics:
            return 0.0
        
        # Average accuracy over past week
        accuracy = sum(m.value for m in metrics) / len(metrics)
        return accuracy
    
    def calculate_active_members(self, workspace_id: str, hours: int = 24) -> int:
        """Count active members in past N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        active_users = set()
        for contrib_list in self.contributions.values():
            for contrib in contrib_list:
                if (contrib.workspace_id == workspace_id and 
                    contrib.last_contributed > cutoff):
                    active_users.add(contrib.user_id)
        
        return len(active_users)
    
    
    # ====================================================================
    # TEAM HEALTH SCORING
    # ====================================================================
    
    def calculate_team_health(self, workspace_id: str) -> TeamHealthScore:
        """Calculate overall team health score"""
        members = self.get_team_members_stats(workspace_id)
        
        if not members:
            return TeamHealthScore(
                workspace_id=workspace_id,
                score=0,
                engagement_score=0,
                productivity_score=0,
                collaboration_score=0,
                trend="stable"
            )
        
        # Engagement: active members / total members ratio
        active_members = sum(1 for m in members 
                           if (datetime.utcnow() - m.last_active).days < 7)
        engagement_score = (active_members / max(len(members), 1)) * 100
        
        # Productivity: average productivity score
        productivity_score = sum(m.productivity_score for m in members) / len(members)
        
        # Collaboration: based on shared resources
        shared = sum(1 for m in members if m.dashboards_shared > 0)
        collaboration_score = (shared / max(len(members), 1)) * 100
        
        # Overall score
        overall_score = (engagement_score * 0.3 + 
                        productivity_score * 0.4 + 
                        collaboration_score * 0.3)
        
        # Determine trend
        trend = self._calculate_health_trend(workspace_id, overall_score)
        
        health = TeamHealthScore(
            workspace_id=workspace_id,
            score=overall_score,
            engagement_score=engagement_score,
            productivity_score=productivity_score,
            collaboration_score=collaboration_score,
            trend=trend
        )
        
        self.team_health[workspace_id] = health
        return health
    
    def _calculate_health_trend(self, workspace_id: str, current_score: float) -> str:
        """Calculate health trend"""
        if workspace_id not in self.team_health:
            return "stable"
        
        previous_score = self.team_health[workspace_id].score
        
        if current_score > previous_score * 1.1:
            return "improving"
        elif current_score < previous_score * 0.9:
            return "declining"
        else:
            return "stable"
    
    def get_team_health(self, workspace_id: str) -> Optional[TeamHealthScore]:
        """Get team health score"""
        if workspace_id in self.team_health:
            return self.team_health[workspace_id]
        return self.calculate_team_health(workspace_id)
    
    
    # ====================================================================
    # TEAM INSIGHTS
    # ====================================================================
    
    def get_team_insights(self, workspace_id: str) -> Dict:
        """Generate team-level insights"""
        members = self.get_team_members_stats(workspace_id)
        health = self.get_team_health(workspace_id)
        
        insights = {
            "health_score": health.score,
            "health_trend": health.trend,
            "total_members": len(members),
            "active_members": self.calculate_active_members(workspace_id),
            "top_contributors": self.get_top_contributors(workspace_id, 3),
            "insights_per_day": self.calculate_insights_per_day(workspace_id),
            "forecast_accuracy": self.calculate_forecast_accuracy(workspace_id),
            "total_contributions": sum(m.total_contributions for m in members)
        }
        
        return insights
    
    
    # ====================================================================
    # BENCHMARKING
    # ====================================================================
    
    def get_member_benchmark(self, user_id: str, workspace_id: str) -> Dict:
        """Get member performance benchmark"""
        stats = self.get_member_stats(user_id, workspace_id)
        if not stats:
            return {}
        
        team_stats = self.get_team_members_stats(workspace_id)
        
        # Calculate percentiles
        productivity_scores = [s.productivity_score for s in team_stats]
        contributions = [s.total_contributions for s in team_stats]
        
        productivity_percentile = (
            sum(1 for s in productivity_scores if s <= stats.productivity_score) 
            / max(len(productivity_scores), 1) * 100
        )
        
        contribution_percentile = (
            sum(1 for c in contributions if c <= stats.total_contributions)
            / max(len(contributions), 1) * 100
        )
        
        return {
            "user_id": user_id,
            "productivity_score": stats.productivity_score,
            "productivity_percentile": productivity_percentile,
            "total_contributions": stats.total_contributions,
            "contribution_percentile": contribution_percentile,
            "rank": sum(1 for s in team_stats if s.productivity_score > stats.productivity_score) + 1
        }
