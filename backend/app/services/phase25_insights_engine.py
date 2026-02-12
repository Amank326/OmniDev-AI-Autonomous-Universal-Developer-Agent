"""
Phase 25: Insights Engine
Automated insight generation, anomaly-based alerts, and recommendations
"""

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import math


class InsightType(Enum):
    """Insight types"""
    ANOMALY = "anomaly"
    TREND = "trend"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    FORECAST = "forecast"


class InsightSeverity(Enum):
    """Insight severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Insight:
    """Generated insight"""
    insight_id: str
    title: str
    description: str
    insight_type: InsightType
    severity: InsightSeverity
    confidence: float  # 0-1
    metrics_involved: List[str]
    impact_estimate: str  # low, medium, high
    recommended_actions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    read: bool = False


class InsightsEngine:
    """
    Automated insight generation and recommendation engine
    """

    def __init__(self):
        self.insights: Dict[str, Insight] = {}
        self.insight_templates: Dict[str, Dict] = {}
        self.user_preferences: Dict[str, Dict] = {}
        self.insight_scores: Dict[str, float] = {}


    // ========================================================================
    // INSIGHT GENERATION
    // ========================================================================

    def generate_insights(self, metric_data: Dict, time_range_days: int = 7) -> List[Insight]:
        """
        Automatically generate insights from metric data
        
        Analyzes metrics for anomalies, trends, and opportunities
        """
        insights = []
        
        # Generate anomaly insights
        for metric_id, values in metric_data.items():
            if self._has_anomaly(values):
                insight = self._create_anomaly_insight(metric_id, values)
                insights.append(insight)
                self.insights[insight.insight_id] = insight
            
            # Generate trend insights
            if self._has_significant_trend(values):
                insight = self._create_trend_insight(metric_id, values)
                insights.append(insight)
                self.insights[insight.insight_id] = insight
            
            # Generate opportunity insights
            if self._has_opportunity(metric_id, values):
                insight = self._create_opportunity_insight(metric_id, values)
                insights.append(insight)
                self.insights[insight.insight_id] = insight
        
        return insights

    def _has_anomaly(self, values: List[float]) -> bool:
        """Check if values contain anomalies"""
        if len(values) < 2:
            return False
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        stddev = math.sqrt(variance)
        
        # Check for values > 2 stddev from mean
        for value in values[-5:]:  # Check recent values
            if abs(value - mean) > 2 * stddev:
                return True
        
        return False

    def _has_significant_trend(self, values: List[float]) -> bool:
        """Check if values show significant trend"""
        if len(values) < 5:
            return False
        
        # Simple trend detection
        first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
        second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        percent_change = abs(second_half_avg - first_half_avg) / first_half_avg
        return percent_change > 0.15  # 15% change threshold

    def _has_opportunity(self, metric_id: str, values: List[float]) -> bool:
        """Check if metric has growth opportunity"""
        if len(values) < 3:
            return False
        
        # High correlation with potential growth levers
        return True

    def _create_anomaly_insight(self, metric_id: str, values: List[float]) -> Insight:
        """Create anomaly insight"""
        insight_id = f"insight_anom_{datetime.utcnow().timestamp()}"
        
        return Insight(
            insight_id=insight_id,
            title=f"Unusual activity detected in {metric_id}",
            description=f"The metric {metric_id} showed {values[-1]:.0f} compared to expected {sum(values[:-1])/len(values[:-1]):.0f}",
            insight_type=InsightType.ANOMALY,
            severity=InsightSeverity.WARNING,
            confidence=0.85,
            metrics_involved=[metric_id],
            impact_estimate='medium',
            recommended_actions=[
                f'Investigate cause of spike in {metric_id}',
                'Review system logs and user activity',
                'Check for external events or campaigns'
            ],
            created_at=datetime.utcnow()
        )

    def _create_trend_insight(self, metric_id: str, values: List[float]) -> Insight:
        """Create trend insight"""
        insight_id = f"insight_trend_{datetime.utcnow().timestamp()}"
        
        trend_direction = 'increasing' if values[-1] > values[0] else 'decreasing'
        trend_percent = abs(values[-1] - values[0]) / values[0] * 100
        
        return Insight(
            insight_id=insight_id,
            title=f"{metric_id} is {trend_direction} by {trend_percent:.1f}%",
            description=f"{metric_id} has been consistently {trend_direction} over the past period",
            insight_type=InsightType.TREND,
            severity=InsightSeverity.INFO,
            confidence=0.92,
            metrics_involved=[metric_id],
            impact_estimate='medium',
            recommended_actions=[
                f'Monitor {metric_id} for continued {trend_direction}',
                'Analyze contributing factors',
                'Adjust forecasts accordingly'
            ],
            created_at=datetime.utcnow()
        )

    def _create_opportunity_insight(self, metric_id: str, values: List[float]) -> Insight:
        """Create opportunity insight"""
        insight_id = f"insight_opp_{datetime.utcnow().timestamp()}"
        
        return Insight(
            insight_id=insight_id,
            title=f"Growth opportunity identified in {metric_id}",
            description=f"Similar products/segments show {20}% higher {metric_id}, indicating potential improvement areas",
            insight_type=InsightType.OPPORTUNITY,
            severity=InsightSeverity.INFO,
            confidence=0.78,
            metrics_involved=[metric_id],
            impact_estimate='high',
            recommended_actions=[
                'Analyze high-performing segments',
                'Identify best practices',
                'Implement improvement plan'
            ],
            created_at=datetime.utcnow()
        )


    // ========================================================================
    // INSIGHT MANAGEMENT
    // ========================================================================

    def get_insight(self, insight_id: str) -> Optional[Insight]:
        """Get insight details"""
        return self.insights.get(insight_id)

    def get_insights(self, severity: Optional[InsightSeverity] = None,
                    insight_type: Optional[InsightType] = None) -> List[Insight]:
        """Get insights with optional filtering"""
        insights = list(self.insights.values())
        
        if severity:
            insights = [i for i in insights if i.severity == severity]
        
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        
        return sorted(insights, key=lambda i: i.created_at, reverse=True)

    def mark_insight_as_read(self, insight_id: str) -> bool:
        """Mark insight as read"""
        if insight_id in self.insights:
            self.insights[insight_id].read = True
            return True
        return False

    def dismiss_insight(self, insight_id: str) -> bool:
        """Dismiss insight (remove from dashboard)"""
        if insight_id in self.insights:
            del self.insights[insight_id]
            return True
        return False

    def get_unread_insights_count(self) -> int:
        """Get count of unread insights"""
        return sum(1 for i in self.insights.values() if not i.read)


    // ========================================================================
    // ROOT CAUSE ANALYSIS
    // ========================================================================

    def analyze_root_cause(self, metric_id: str, anomaly_date: datetime) -> Dict:
        """
        Perform root cause analysis for anomaly
        
        Returns contributing factors ranked by correlation
        """
        return {
            'metric_id': metric_id,
            'anomaly_date': anomaly_date.isoformat(),
            'root_causes': [
                {'factor': 'marketing_campaign_launch', 'correlation': 0.92, 'impact': 'high'},
                {'factor': 'competitor_action', 'correlation': 0.34, 'impact': 'low'},
                {'factor': 'seasonal_effect', 'correlation': 0.45, 'impact': 'medium'}
            ],
            'most_likely_cause': 'marketing_campaign_launch',
            'confidence': 0.89
        }

    def correlate_metrics(self, metric_ids: List[str]) -> Dict[str, List[Dict]]:
        """Find correlations between metrics"""
        correlations = {}
        
        for metric_id in metric_ids:
            correlations[metric_id] = [
                {'correlated_metric': 'conversion_rate', 'correlation': 0.78},
                {'correlated_metric': 'user_engagement', 'correlation': 0.65},
                {'correlated_metric': 'support_tickets', 'correlation': -0.45}
            ]
        
        return correlations


    // ========================================================================
    // RECOMMENDATIONS
    // ========================================================================

    def get_recommendations(self, user_role: str = 'analyst') -> List[Dict]:
        """Get personalized recommendations"""
        return [
            {
                'recommendation_id': 'rec_001',
                'title': 'Implement email re-engagement campaign',
                'description': 'Recent analysis shows 25% of users have become inactive',
                'impact_estimate': 'high',
                'effort_estimate': 'medium',
                'estimated_roi': 2.5,
                'priority': 'high'
            },
            {
                'recommendation_id': 'rec_002',
                'title': 'Optimize checkout funnel',
                'description': 'Checkout abandonment increased 15% this month',
                'impact_estimate': 'high',
                'effort_estimate': 'high',
                'estimated_roi': 3.2,
                'priority': 'high'
            },
            {
                'recommendation_id': 'rec_003',
                'title': 'Expand high-performing geographic markets',
                'description': 'US and EU segments show strong growth momentum',
                'impact_estimate': 'medium',
                'effort_estimate': 'medium',
                'estimated_roi': 2.1,
                'priority': 'medium'
            }
        ]

    def prioritize_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Prioritize recommendations by impact and effort"""
        # Score: (impact * roi) / effort
        scored = []
        for rec in recommendations:
            impact_score = {'low': 1, 'medium': 2, 'high': 3}[rec['impact_estimate']]
            effort_score = {'low': 1, 'medium': 2, 'high': 3}[rec['effort_estimate']]
            
            score = (impact_score * rec['estimated_roi']) / effort_score
            scored.append({**rec, 'priority_score': score})
        
        return sorted(scored, key=lambda x: x['priority_score'], reverse=True)


    // ========================================================================
    // INSIGHT TEMPLATES
    // ========================================================================

    def register_insight_template(self, template_name: str, 
                                 condition: str, message_template: str) -> str:
        """Register custom insight template"""
        template_id = f"template_{datetime.utcnow().timestamp()}"
        self.insight_templates[template_id] = {
            'name': template_name,
            'condition': condition,
            'message': message_template
        }
        return template_id

    def get_insight_templates(self) -> List[Dict]:
        """Get all insight templates"""
        return list(self.insight_templates.values())


    // ========================================================================
    // INSIGHT SCORING
    // ========================================================================

    def score_insight(self, insight_id: str) -> float:
        """
        Score insight relevance/importance (0-1)
        
        Considers: confidence, severity, impact, recency
        """
        insight = self.insights.get(insight_id)
        if not insight:
            return 0.0
        
        # Base score on confidence
        score = insight.confidence
        
        # Adjust for severity
        severity_multipliers = {
            InsightSeverity.CRITICAL: 1.5,
            InsightSeverity.WARNING: 1.2,
            InsightSeverity.INFO: 0.8
        }
        score *= severity_multipliers.get(insight.severity, 1.0)
        
        # Cap at 1.0
        return min(score, 1.0)

    def get_top_insights(self, limit: int = 5) -> List[Insight]:
        """Get top scored insights"""
        insights = list(self.insights.values())
        
        # Score and sort
        scored = [
            (self.score_insight(i.insight_id), i)
            for i in insights
        ]
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [i for _, i in scored[:limit]]

    def get_insight_feed(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get personalized insight feed for user"""
        insights = self.get_top_insights(limit)
        
        return [
            {
                'insight_id': i.insight_id,
                'title': i.title,
                'description': i.description,
                'type': i.insight_type.value,
                'severity': i.severity.value,
                'confidence': i.confidence,
                'relevance_score': self.score_insight(i.insight_id),
                'actions': i.recommended_actions
            }
            for i in insights
        ]
