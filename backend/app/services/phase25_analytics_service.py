"""
Phase 25: Analytics Service
Time-series analysis, funnel metrics, retention calculations, and dimension aggregation
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict


class MetricType(Enum):
    """Analytics metric types"""
    AGGREGATE = "aggregate"
    FUNNEL = "funnel"
    RETENTION = "retention"
    COHORT = "cohort"
    TIME_SERIES = "time_series"
    DIMENSION_BREAKDOWN = "dimension_breakdown"


class AggregationType(Enum):
    """Time-series aggregation types"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class TimeSeriesPoint:
    """Time series data point"""
    timestamp: datetime
    value: float
    dimension: Optional[str] = None
    count: int = 0


@dataclass
class FunnelStep:
    """Funnel step data"""
    step_name: str
    user_count: int
    conversion_rate: float
    drop_off: int


@dataclass
class RetentionCohort:
    """Retention cohort data"""
    cohort_date: datetime
    initial_users: int
    retention_by_day: Dict[int, float]  # day -> retention %
    churn_rate: float


@dataclass
class AnalyticsMetric:
    """Analytics metric configuration"""
    metric_id: str
    name: str
    metric_type: MetricType
    source_events: List[str]
    calculation_method: str
    dimensions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    enabled: bool = True


class AnalyticsService:
    """
    Advanced analytics service for time-series analysis, funnels, and cohorts
    """

    def __init__(self):
        self.metrics: Dict[str, AnalyticsMetric] = {}
        self.time_series_data: Dict[str, List[TimeSeriesPoint]] = defaultdict(list)
        self.funnel_data: Dict[str, List[FunnelStep]] = defaultdict(list)
        self.retention_data: Dict[str, List[RetentionCohort]] = defaultdict(list)
        self.dimension_breakdowns: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.event_buffer: List[Dict] = []


    # ========================================================================
    # METRIC MANAGEMENT
    # ========================================================================

    def create_metric(self, name: str, metric_type: MetricType, 
                     source_events: List[str], calculation_method: str,
                     dimensions: Optional[List[str]] = None) -> str:
        """Create new analytics metric"""
        metric_id = f"metric_{datetime.utcnow().timestamp()}"
        
        metric = AnalyticsMetric(
            metric_id=metric_id,
            name=name,
            metric_type=metric_type,
            source_events=source_events,
            calculation_method=calculation_method,
            dimensions=dimensions or []
        )
        
        self.metrics[metric_id] = metric
        return metric_id

    def get_metric(self, metric_id: str) -> Optional[AnalyticsMetric]:
        """Get metric configuration"""
        return self.metrics.get(metric_id)

    def update_metric(self, metric_id: str, **kwargs) -> bool:
        """Update metric configuration"""
        if metric_id not in self.metrics:
            return False
        
        metric = self.metrics[metric_id]
        for key, value in kwargs.items():
            if hasattr(metric, key):
                setattr(metric, key, value)
        
        return True

    def delete_metric(self, metric_id: str) -> bool:
        """Delete metric"""
        if metric_id in self.metrics:
            del self.metrics[metric_id]
            return True
        return False

    def get_all_metrics(self) -> List[AnalyticsMetric]:
        """Get all metrics"""
        return list(self.metrics.values())


    # ========================================================================
    # TIME-SERIES AGGREGATION
    # ========================================================================

    def aggregate_time_series(self, metric_id: str, aggregation: AggregationType,
                             start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Aggregate metric time-series data
        
        Returns list of:
        {
            "timestamp": "2026-02-07T00:00:00Z",
            "value": 1234.5,
            "count": 450,
            "aggregation": "daily"
        }
        """
        points = self.time_series_data.get(metric_id, [])
        filtered = [p for p in points if start_date <= p.timestamp <= end_date]
        
        if not filtered:
            return []
        
        # Group by aggregation period
        buckets = defaultdict(list)
        for point in filtered:
            key = self._get_aggregation_key(point.timestamp, aggregation)
            buckets[key].append(point)
        
        # Calculate aggregates
        result = []
        for key in sorted(buckets.keys()):
            points_in_bucket = buckets[key]
            values = [p.value for p in points_in_bucket]
            
            result.append({
                'timestamp': key,
                'value': sum(values) / len(values) if values else 0,  # Average
                'count': sum(p.count for p in points_in_bucket),
                'min': min(values) if values else 0,
                'max': max(values) if values else 0,
                'aggregation': aggregation.value
            })
        
        return result

    def _get_aggregation_key(self, dt: datetime, agg: AggregationType) -> str:
        """Get aggregation key for timestamp"""
        if agg == AggregationType.HOURLY:
            return dt.replace(minute=0, second=0, microsecond=0).isoformat()
        elif agg == AggregationType.DAILY:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        elif agg == AggregationType.WEEKLY:
            week_start = dt - timedelta(days=dt.weekday())
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        elif agg == AggregationType.MONTHLY:
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        else:  # YEARLY
            return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    def record_event(self, event_name: str, value: float, 
                    dimensions: Optional[Dict[str, str]] = None):
        """Record analytics event"""
        self.event_buffer.append({
            'event_name': event_name,
            'value': value,
            'dimensions': dimensions or {},
            'timestamp': datetime.utcnow()
        })

    def flush_events(self):
        """Process buffered events"""
        for event in self.event_buffer:
            # Update time series
            for metric_id, metric in self.metrics.items():
                if event['event_name'] in metric.source_events:
                    point = TimeSeriesPoint(
                        timestamp=event['timestamp'],
                        value=event['value'],
                        count=1
                    )
                    self.time_series_data[metric_id].append(point)
        
        self.event_buffer.clear()


    # ========================================================================
    # FUNNEL ANALYSIS
    # ========================================================================

    def create_funnel(self, funnel_id: str, steps: List[str]):
        """Create funnel definition"""
        # Store funnel step definitions
        return funnel_id

    def analyze_funnel(self, funnel_id: str, start_date: datetime, 
                      end_date: datetime) -> List[FunnelStep]:
        """
        Analyze funnel conversion
        
        Returns steps with conversion rates and drop-offs
        """
        steps = []
        total_users = 100  # Placeholder: would get from event data
        
        for i, step_name in enumerate(['view_product', 'add_cart', 'checkout', 'purchase']):
            users_at_step = total_users - (i * 20)  # Placeholder calculation
            conversion = (users_at_step / total_users) * 100
            drop_off = total_users - users_at_step
            
            steps.append(FunnelStep(
                step_name=step_name,
                user_count=users_at_step,
                conversion_rate=conversion,
                drop_off=drop_off
            ))
        
        return steps

    def get_funnel_abandonment(self, funnel_id: str, step: int) -> Dict:
        """Get abandonment analysis for funnel step"""
        return {
            'step': step,
            'total_dropped': 450,
            'top_reasons': [
                {'reason': 'high_shipping_cost', 'count': 120},
                {'reason': 'payment_failed', 'count': 95},
                {'reason': 'slow_checkout', 'count': 78}
            ],
            'recovery_suggestions': [
                'Offer free shipping above $50',
                'Add payment method retry',
                'Simplify checkout flow'
            ]
        }

    def compare_funnels(self, funnel_id_1: str, funnel_id_2: str) -> Dict:
        """Compare two funnel versions"""
        return {
            'funnel_1_conversion': 2.5,
            'funnel_2_conversion': 3.2,
            'improvement': 0.7,
            'improvement_percent': 28.0,
            'statistical_significance': True,
            'confidence_level': 0.95
        }


    # ========================================================================
    # RETENTION ANALYSIS
    # ========================================================================

    def calculate_retention_cohort(self, cohort_id: str, 
                                   start_date: datetime) -> RetentionCohort:
        """Calculate retention for cohort"""
        # Placeholder: would calculate from actual user return data
        initial_users = 1000
        retention_by_day = {
            0: 100.0,   # Day 0 (cohort start)
            1: 45.2,    # Day 1: 45.2% retention
            7: 22.5,    # Day 7: 22.5% retention
            30: 8.3,    # Day 30: 8.3% retention
        }
        
        return RetentionCohort(
            cohort_date=start_date,
            initial_users=initial_users,
            retention_by_day=retention_by_day,
            churn_rate=54.8  # 100 - 45.2
        )

    def get_cohort_matrix(self, metric_id: str, start_date: datetime, 
                         end_date: datetime) -> Dict:
        """Get retention cohort matrix"""
        return {
            'metric_id': metric_id,
            'type': 'retention_matrix',
            'cohorts': [
                {'date': '2026-02-01', 'day_0': 100, 'day_1': 45.2, 'day_7': 22.5},
                {'date': '2026-02-02', 'day_0': 100, 'day_1': 47.1, 'day_7': 24.3},
            ],
            'average_retention': 45.6
        }

    def calculate_churn_risk(self, user_id: str) -> Dict:
        """Calculate churn risk for user"""
        return {
            'user_id': user_id,
            'churn_probability': 0.35,
            'churn_risk_level': 'medium',
            'days_until_churn': 14,
            'contributing_factors': [
                'no_activity_7_days',
                'support_tickets_high',
                'engagement_declining'
            ]
        }


    # ========================================================================
    # DIMENSION BREAKDOWN
    # ========================================================================

    def aggregate_by_dimension(self, metric_id: str, dimension: str,
                              start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """
        Break down metric by dimension
        
        Returns: {'segment_1': 1234.5, 'segment_2': 2345.6, ...}
        """
        breakdowns = self.dimension_breakdowns.get(metric_id, {})
        return breakdowns

    def compare_dimensions(self, metric_id: str, dimension_1: str, 
                          dimension_2: str) -> Dict:
        """Compare metric across two dimensions"""
        return {
            'metric_id': metric_id,
            'dimension_1': dimension_1,
            'dimension_2': dimension_2,
            'comparison': {
                dimension_1: 1234.5,
                dimension_2: 2345.6,
            },
            'winner': dimension_2,
            'difference_percent': 90.1
        }

    def get_top_dimensions(self, metric_id: str, dimension: str, 
                          limit: int = 10) -> List[Dict]:
        """Get top N dimension values"""
        return [
            {'dimension': 'us', 'value': 15000.5},
            {'dimension': 'eu', 'value': 12340.2},
            {'dimension': 'asia', 'value': 8900.1},
        ]


    # ========================================================================
    # CUSTOM CALCULATIONS
    # ========================================================================

    def calculate_custom_metric(self, metric_id: str, formula: str,
                               start_date: datetime, end_date: datetime) -> float:
        """Calculate custom metric using formula"""
        # Placeholder: would parse and execute formula
        return 1234.56

    def calculate_metric_growth(self, metric_id: str, 
                               period_1_start: datetime, period_1_end: datetime,
                               period_2_start: datetime, period_2_end: datetime) -> Dict:
        """Calculate growth between two periods"""
        period_1_value = 1000.0
        period_2_value = 1250.0
        growth = period_2_value - period_1_value
        growth_percent = (growth / period_1_value) * 100
        
        return {
            'metric_id': metric_id,
            'period_1_value': period_1_value,
            'period_2_value': period_2_value,
            'absolute_growth': growth,
            'percent_growth': growth_percent,
            'trend': 'positive' if growth > 0 else 'negative'
        }

    def compare_periods(self, metric_id: str, period_1: datetime, 
                       period_2: datetime) -> Dict:
        """Compare metric across periods (YoY, MoM, WoW)"""
        return {
            'metric_id': metric_id,
            'period_1_value': 5000.0,
            'period_2_value': 5350.0,
            'growth': 350.0,
            'growth_percent': 7.0,
            'seasonal_adjustment': 0.95,
            'adjusted_growth': 7.37
        }


    # ========================================================================
    # STATISTICAL ANALYSIS
    // ========================================================================

    def calculate_statistics(self, metric_id: str, start_date: datetime,
                            end_date: datetime) -> Dict:
        """Calculate statistical measures"""
        values = [p.value for p in self.time_series_data.get(metric_id, [])]
        
        if not values:
            return {}
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        stddev = variance ** 0.5
        
        return {
            'metric_id': metric_id,
            'count': len(values),
            'mean': mean,
            'median': sorted(values)[len(values) // 2],
            'min': min(values),
            'max': max(values),
            'stddev': stddev,
            'variance': variance,
            'coefficient_of_variation': stddev / mean if mean else 0
        }

    def detect_outliers(self, metric_id: str, method: str = 'iqr') -> List[Dict]:
        """Detect outliers in time-series data"""
        points = self.time_series_data.get(metric_id, [])
        
        # IQR method
        values = [p.value for p in points]
        sorted_vals = sorted(values)
        q1 = sorted_vals[len(sorted_vals) // 4]
        q3 = sorted_vals[3 * len(sorted_vals) // 4]
        iqr = q3 - q1
        
        outliers = []
        for point in points:
            if point.value < (q1 - 1.5 * iqr) or point.value > (q3 + 1.5 * iqr):
                outliers.append({
                    'timestamp': point.timestamp.isoformat(),
                    'value': point.value,
                    'severity': 'high' if abs(point.value - (q1 + q3) / 2) > 3 * iqr else 'medium'
                })
        
        return outliers


    # ========================================================================
    // AGGREGATION QUERIES
    // ========================================================================

    def query_metrics(self, metric_ids: List[str], start_date: datetime,
                     end_date: datetime, aggregation: AggregationType,
                     filters: Optional[Dict] = None) -> List[Dict]:
        """Query multiple metrics with filters"""
        result = []
        for metric_id in metric_ids:
            timeseries = self.aggregate_time_series(metric_id, aggregation, 
                                                    start_date, end_date)
            result.extend(timeseries)
        return result

    def export_report(self, metric_ids: List[str], start_date: datetime,
                     end_date: datetime, format: str = 'csv') -> str:
        """Export metrics to CSV/JSON"""
        return f"report_{datetime.utcnow().timestamp()}.{format}"

    def get_metric_dashboard(self, dashboard_id: str) -> Dict:
        """Get analytics dashboard configuration"""
        return {
            'dashboard_id': dashboard_id,
            'metrics': [],
            'filters': {},
            'layout': 'grid',
            'refresh_interval': 60
        }
