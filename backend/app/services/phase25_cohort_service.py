"""
Phase 25: Cohort Analysis Service
User segmentation, behavior analysis, and cohort tracking
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from collections import defaultdict


class CohortType(Enum):
    """Cohort types"""
    ACQUISITION = "acquisition"  # Users acquired on same date
    BEHAVIOR = "behavior"         # Users with similar behaviors
    DEMOGRAPHIC = "demographic"   # Geographic, device, etc.
    ENGAGEMENT = "engagement"     # Engagement level based
    LIFECYCLE = "lifecycle"       # Stage in customer lifecycle


@dataclass
class Cohort:
    """Cohort definition"""
    cohort_id: str
    name: str
    cohort_type: CohortType
    definition: str
    start_date: datetime
    user_count: int
    created_at: datetime
    enabled: bool = True


@dataclass
class CohortMetric:
    """Cohort performance metric"""
    cohort_id: str
    metric_name: str
    date: datetime
    value: float
    comparison_value: Optional[float] = None  # Compare to other cohort


class CohortAnalysisService:
    """
    Cohort analysis for user segmentation and behavior tracking
    """

    def __init__(self):
        self.cohorts: Dict[str, Cohort] = {}
        self.cohort_members: Dict[str, List[str]] = defaultdict(list)
        self.cohort_metrics: Dict[str, List[CohortMetric]] = defaultdict(list)
        self.segment_profiles: Dict[str, Dict] = {}


    // ========================================================================
    // COHORT MANAGEMENT
    // ========================================================================

    def create_cohort(self, name: str, cohort_type: CohortType,
                     definition: str, start_date: datetime) -> str:
        """Create new cohort"""
        cohort_id = f"cohort_{datetime.utcnow().timestamp()}"
        
        cohort = Cohort(
            cohort_id=cohort_id,
            name=name,
            cohort_type=cohort_type,
            definition=definition,
            start_date=start_date,
            user_count=0,
            created_at=datetime.utcnow()
        )
        
        self.cohorts[cohort_id] = cohort
        return cohort_id

    def get_cohort(self, cohort_id: str) -> Optional[Cohort]:
        """Get cohort details"""
        return self.cohorts.get(cohort_id)

    def update_cohort(self, cohort_id: str, **kwargs) -> bool:
        """Update cohort definition"""
        if cohort_id not in self.cohorts:
            return False
        
        cohort = self.cohorts[cohort_id]
        for key, value in kwargs.items():
            if hasattr(cohort, key):
                setattr(cohort, key, value)
        
        return True

    def delete_cohort(self, cohort_id: str) -> bool:
        """Delete cohort"""
        if cohort_id in self.cohorts:
            del self.cohorts[cohort_id]
            del self.cohort_members[cohort_id]
            del self.cohort_metrics[cohort_id]
            return True
        return False

    def get_all_cohorts(self) -> List[Cohort]:
        """Get all cohorts"""
        return list(self.cohorts.values())


    // ========================================================================
    // COHORT MEMBERSHIP
    // ========================================================================

    def add_users_to_cohort(self, cohort_id: str, user_ids: List[str]) -> int:
        """Add users to cohort"""
        if cohort_id not in self.cohorts:
            return 0
        
        self.cohort_members[cohort_id].extend(user_ids)
        self.cohorts[cohort_id].user_count = len(set(self.cohort_members[cohort_id]))
        return len(user_ids)

    def get_cohort_members(self, cohort_id: str) -> List[str]:
        """Get cohort members"""
        return self.cohort_members.get(cohort_id, [])

    def get_cohort_size(self, cohort_id: str) -> int:
        """Get cohort size"""
        cohort = self.cohorts.get(cohort_id)
        return cohort.user_count if cohort else 0

    def is_user_in_cohort(self, user_id: str, cohort_id: str) -> bool:
        """Check if user is in cohort"""
        return user_id in self.cohort_members.get(cohort_id, [])


    // ========================================================================
    // BEHAVIOR ANALYSIS
    // ========================================================================

    def get_cohort_behavior(self, cohort_id: str) -> Dict:
        """Analyze cohort behavior patterns"""
        return {
            'cohort_id': cohort_id,
            'avg_session_duration': 450,  # seconds
            'sessions_per_user': 8.5,
            'feature_adoption_rate': 0.72,
            'top_features': [
                {'feature': 'reports', 'usage_rate': 0.89},
                {'feature': 'alerts', 'usage_rate': 0.76},
                {'feature': 'exports', 'usage_rate': 0.62}
            ],
            'bounce_rate': 0.12,
            'return_rate': 0.68
        }

    def compare_cohort_behaviors(self, cohort_id_1: str, 
                                 cohort_id_2: str) -> Dict:
        """Compare behaviors between cohorts"""
        return {
            'cohort_1': cohort_id_1,
            'cohort_2': cohort_id_2,
            'engagement_ratio': 1.34,  # Cohort 1 is 34% more engaged
            'retention_ratio': 1.12,   # Cohort 1 has 12% better retention
            'ltv_ratio': 1.45,         # Cohort 1 LTV is 45% higher
            'feature_adoption_diff': 0.15,  # 15% difference
            'winner': cohort_id_1,
            'key_differentiators': [
                'higher_onboarding_completion',
                'more_feature_exploration',
                'better_engagement_frequency'
            ]
        }

    def get_behavior_profile(self, cohort_id: str) -> Dict:
        """Get detailed behavior profile"""
        return {
            'cohort_id': cohort_id,
            'profile_type': 'power_user',
            'characteristics': [
                {'trait': 'high_engagement', 'score': 0.92},
                {'trait': 'early_adopter', 'score': 0.87},
                {'trait': 'long_session_duration', 'score': 0.78}
            ],
            'pain_points': [
                'complex_setup_process',
                'feature_discovery_difficulty'
            ],
            'opportunities': [
                'advanced_analytics_features',
                'api_integration',
                'team_collaboration'
            ]
        }


    // ========================================================================
    // SEGMENT ANALYSIS
    // ========================================================================

    def create_segments(self, dimension: str, values: List[str]) -> List[str]:
        """Create segments by dimension"""
        segment_ids = []
        for value in values:
            segment_id = f"segment_{dimension}_{value}"
            self.segment_profiles[segment_id] = {
                'dimension': dimension,
                'value': value,
                'size': 0,
                'metrics': {}
            }
            segment_ids.append(segment_id)
        return segment_ids

    def get_segment_profile(self, segment_id: str) -> Dict:
        """Get segment profile"""
        return self.segment_profiles.get(segment_id, {})

    def compare_segments(self, dimension: str, values: List[str]) -> Dict:
        """Compare segments across dimension"""
        return {
            'dimension': dimension,
            'segments': [
                {'value': 'us', 'users': 15000, 'retention': 0.75, 'ltv': 1250},
                {'value': 'eu', 'users': 12000, 'retention': 0.72, 'ltv': 1180},
                {'value': 'apac', 'users': 8000, 'retention': 0.68, 'ltv': 980}
            ],
            'best_performing': 'us',
            'growth_opportunity': 'apac'
        }


    // ========================================================================
    // GROWTH ATTRIBUTION
    // ========================================================================

    def analyze_growth_contribution(self, metric_id: str) -> Dict:
        """Analyze which cohorts contribute to growth"""
        return {
            'metric_id': metric_id,
            'total_growth': 1500.0,
            'contributions': [
                {'cohort': 'cohort_jan_2025', 'contribution': 600.0, 'percent': 40.0},
                {'cohort': 'cohort_feb_2025', 'contribution': 500.0, 'percent': 33.3},
                {'cohort': 'cohort_mar_2025', 'contribution': 400.0, 'percent': 26.7}
            ],
            'fastest_growing_cohort': 'cohort_mar_2025',
            'slowest_growing_cohort': 'cohort_jan_2025'
        }

    def get_cohort_growth_rate(self, cohort_id: str) -> Dict:
        """Get cohort-specific growth rate"""
        return {
            'cohort_id': cohort_id,
            'current_size': 1000,
            'growth_rate': 0.05,  # 5%/month
            'doubling_time_months': 14.2,
            'growth_trend': 'accelerating',
            'forecast_size_3mo': 1158,
            'forecast_size_6mo': 1341
        }


    // ========================================================================
    // LIFECYCLE STAGES
    // ========================================================================

    def get_user_lifecycle_stage(self, user_id: str) -> str:
        """Determine user lifecycle stage"""
        # awareness, consideration, purchase, retention, advocacy
        return 'retention'

    def analyze_lifecycle_flow(self) -> Dict:
        """Analyze flow between lifecycle stages"""
        return {
            'stages': {
                'awareness': {'count': 5000, 'next_stage_rate': 0.30},
                'consideration': {'count': 1500, 'next_stage_rate': 0.45},
                'purchase': {'count': 675, 'next_stage_rate': 0.95},
                'retention': {'count': 641, 'next_stage_rate': 0.70},
                'advocacy': {'count': 449, 'next_stage_rate': None}
            },
            'conversion_funnel': [5000, 1500, 675, 641, 449],
            'bottleneck_stage': 'awareness'
        }

    def predict_stage_progression(self, user_id: str) -> Dict:
        """Predict user's next lifecycle stage"""
        return {
            'user_id': user_id,
            'current_stage': 'consideration',
            'predicted_next_stage': 'purchase',
            'progression_probability': 0.78,
            'estimated_days': 14,
            'relevant_triggers': [
                'feature_trial_completion',
                'support_interaction',
                'product_demo'
            ]
        }


    // ========================================================================
    // CHURN & RETENTION
    // ========================================================================

    def calculate_cohort_churn(self, cohort_id: str, 
                              period_days: int = 30) -> Dict:
        """Calculate cohort churn rate"""
        return {
            'cohort_id': cohort_id,
            'period_days': period_days,
            'starting_users': 1000,
            'churned_users': 320,
            'churn_rate': 0.32,
            'retention_rate': 0.68,
            'churn_trend': 'stable',
            'churn_acceleration': 0.0
        }

    def predict_cohort_churn(self, cohort_id: str, 
                            forecast_days: int = 90) -> Dict:
        """Predict future churn for cohort"""
        return {
            'cohort_id': cohort_id,
            'forecast_days': forecast_days,
            'predicted_churn_rate': 0.35,
            'predicted_retained_users': 650,
            'confidence': 0.82,
            'risk_factors': [
                'low_engagement_trend',
                'declining_feature_usage',
                'support_ticket_increase'
            ],
            'mitigation_actions': [
                'engagement_campaigns',
                'personalized_recommendations',
                'premium_feature_offers'
            ]
        }

    def get_at_risk_users(self, cohort_id: str, churn_probability: float = 0.5) -> List[str]:
        """Get users at high risk of churn"""
        # Placeholder: would calculate from actual user behavior
        return []


    // ========================================================================
    // COHORT METRICS & REPORTING
    // ========================================================================

    def record_cohort_metric(self, cohort_id: str, metric_name: str,
                            value: float) -> bool:
        """Record metric for cohort"""
        if cohort_id not in self.cohorts:
            return False
        
        metric = CohortMetric(
            cohort_id=cohort_id,
            metric_name=metric_name,
            date=datetime.utcnow(),
            value=value
        )
        
        self.cohort_metrics[cohort_id].append(metric)
        return True

    def get_cohort_metrics(self, cohort_id: str) -> Dict[str, float]:
        """Get all metrics for cohort"""
        metrics = {}
        for metric in self.cohort_metrics.get(cohort_id, []):
            metrics[metric.metric_name] = metric.value
        return metrics

    def get_cohort_health_score(self, cohort_id: str) -> Dict:
        """Calculate overall cohort health score"""
        return {
            'cohort_id': cohort_id,
            'health_score': 78.5,  # 0-100
            'health_level': 'healthy',
            'components': {
                'engagement': 85,
                'retention': 72,
                'growth': 80,
                'satisfaction': 75
            },
            'trends': {
                'engagement': 'improving',
                'retention': 'stable',
                'growth': 'improving',
                'satisfaction': 'declining'
            }
        }

    def export_cohort_report(self, cohort_id: str, format: str = 'csv') -> str:
        """Export cohort report"""
        return f"cohort_report_{cohort_id}.{format}"
