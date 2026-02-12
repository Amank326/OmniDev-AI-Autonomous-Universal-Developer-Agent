"""
Cost Optimization Service
Comprehensive cost analysis, tracking, and optimization recommendations for cloud infrastructure.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from threading import RLock
import json
import uuid


class CostCategory(Enum):
    """Cost categories for resource tracking."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    ML_INFERENCE = "ml_inference"
    ML_TRAINING = "ml_training"
    MONITORING = "monitoring"
    CACHING = "caching"
    SECURITY = "security"
    OTHER = "other"


class OptimizationStrategy(Enum):
    """Cost optimization strategies."""
    RESERVED_INSTANCES = "reserved_instances"
    SPOT_INSTANCES = "spot_instances"
    AUTO_SCALING = "auto_scaling"
    RIGHT_SIZING = "right_sizing"
    STORAGE_OPTIMIZATION = "storage_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"
    BATCH_PROCESSING = "batch_processing"
    CACHING_STRATEGY = "caching_strategy"
    DATABASE_OPTIMIZATION = "database_optimization"
    WORKLOAD_CONSOLIDATION = "workload_consolidation"


class PricingModel(Enum):
    """Pricing models for cost calculation."""
    PAY_AS_YOU_GO = "pay_as_you_go"
    RESERVED_1_YEAR = "reserved_1_year"
    RESERVED_3_YEAR = "reserved_3_year"
    SPOT = "spot"
    COMMITMENT_1_YEAR = "commitment_1_year"
    COMMITMENT_3_YEAR = "commitment_3_year"


class CostTrendDirection(Enum):
    """Direction of cost trend."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


@dataclass
class CostRecord:
    """Individual cost record."""
    timestamp: datetime
    category: CostCategory
    resource_id: str
    resource_name: str
    cost_usd: float
    unit: str  # hour, month, gb-month, request
    quantity: float
    pricing_model: PricingModel
    region: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostBreakdown:
    """Cost breakdown by category."""
    total_cost_usd: float
    period: str  # daily, weekly, monthly
    start_date: datetime
    end_date: datetime
    breakdown: Dict[CostCategory, float]  # category -> cost
    top_resources: List[Dict]  # [{resource_id, resource_name, cost, percentage}]


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""
    recommendation_id: str
    strategy: OptimizationStrategy
    affected_categories: List[CostCategory]
    current_monthly_cost_usd: float
    estimated_savings_usd: float
    savings_percentage: float
    implementation_effort: str  # low, medium, high
    estimated_implementation_days: int
    roi_months: float
    risk_level: str  # low, medium, high
    priority: str  # low, medium, high, critical
    description: str
    implementation_steps: List[str]
    affected_resources: Dict[str, List[str]]  # resource_type -> [resource_ids]


@dataclass
class CostForecast:
    """Cost forecast for future periods."""
    forecast_id: str
    start_date: datetime
    end_date: datetime
    forecast_period_days: int
    forecast_data: List[Dict]  # [{date, forecasted_cost_usd, confidence_percent}]
    trend_direction: CostTrendDirection
    monthly_trend_percentage: float
    peak_cost_day: Dict  # {date, cost_usd}
    baseline_cost_usd: float
    seasonal_factors: Dict[str, float]  # month -> adjustment_factor


@dataclass
class BudgetAnalysis:
    """Budget vs actual analysis."""
    budget_id: str
    budget_name: str
    budgeted_amount_usd: float
    actual_amount_usd: float
    spend_percentage: float
    variance_usd: float
    variance_percentage: float
    burn_rate_usd_per_day: float
    days_until_budget_exceeded: Optional[int]
    current_month_costs: float
    last_month_costs: float
    month_over_month_change_percent: float
    budget_period: str  # monthly, quarterly, yearly


@dataclass
class CostPolicy:
    """Cost control policy."""
    policy_id: str
    policy_name: str
    max_daily_spend_usd: float
    max_monthly_spend_usd: float
    alert_threshold_percent: float
    auto_shutdown_enabled: bool
    auto_shutdown_threshold_usd: float
    category_limits: Dict[CostCategory, float]
    created_at: datetime
    updated_at: datetime


class CostOptimizationService:
    """
    Service for cost tracking, analysis, and optimization.
    
    Features:
    - Real-time cost tracking across all categories
    - Cost breakdown analysis by resource, category, region
    - Automated cost forecasting and trend analysis
    - Actionable optimization recommendations
    - Budget tracking and variance analysis
    - Cost control policies and alerts
    - ROI calculation for optimization strategies
    - Historical cost reporting
    """

    def __init__(self, max_concurrent_analyses: int = 5, max_cost_history_months: int = 24):
        """Initialize cost optimization service."""
        self._lock = RLock()
        
        # Cost tracking
        self.cost_records: List[CostRecord] = []
        self.cost_index_by_resource: Dict[str, List[CostRecord]] = {}
        self.cost_index_by_category: Dict[CostCategory, List[CostRecord]] = {}
        
        # Forecasting
        self.forecasts: Dict[str, CostForecast] = {}
        self.forecast_patterns: Dict[str, List[float]] = {}
        
        # Optimization
        self.recommendations: Dict[str, OptimizationRecommendation] = {}
        self.active_strategies: Dict[str, Dict] = {}
        
        # Budget management
        self.budgets: Dict[str, BudgetAnalysis] = {}
        self.policies: Dict[str, CostPolicy] = {}
        
        # Configuration
        self.max_concurrent_analyses = max_concurrent_analyses
        self.max_cost_history_months = max_cost_history_months
        
        # Callbacks
        self.callbacks: Dict[str, List] = {
            'cost_spike_detected': [],
            'budget_exceeded': [],
            'forecast_updated': [],
            'recommendation_generated': [],
            'policy_violated': []
        }

    def record_cost(
        self,
        category: CostCategory,
        resource_id: str,
        resource_name: str,
        cost_usd: float,
        unit: str,
        quantity: float,
        pricing_model: PricingModel,
        region: str,
        metadata: Dict = None
    ) -> str:
        """
        Record a cost transaction.
        
        Args:
            category: Cost category
            resource_id: Resource identifier
            resource_name: Resource display name
            cost_usd: Cost in USD
            unit: Unit of measurement (hour, month, gb-month, request)
            quantity: Quantity of units
            pricing_model: Pricing model used
            region: Cloud region
            metadata: Additional metadata
        
        Returns:
            Record ID
        """
        with self._lock:
            record = CostRecord(
                timestamp=datetime.utcnow(),
                category=category,
                resource_id=resource_id,
                resource_name=resource_name,
                cost_usd=cost_usd,
                unit=unit,
                quantity=quantity,
                pricing_model=pricing_model,
                region=region,
                metadata=metadata or {}
            )
            
            self.cost_records.append(record)
            
            # Index by resource
            if resource_id not in self.cost_index_by_resource:
                self.cost_index_by_resource[resource_id] = []
            self.cost_index_by_resource[resource_id].append(record)
            
            # Index by category
            if category not in self.cost_index_by_category:
                self.cost_index_by_category[category] = []
            self.cost_index_by_category[category].append(record)
            
            # Detect cost spikes
            self._check_cost_spike(resource_id, cost_usd)
            
            return f"cost_{len(self.cost_records)}"

    def get_cost_breakdown(
        self,
        period: str = "monthly",
        days: int = 30,
        category_filter: Optional[CostCategory] = None
    ) -> CostBreakdown:
        """
        Get cost breakdown for specified period.
        
        Args:
            period: Period type (daily, weekly, monthly)
            days: Number of days to analyze
            category_filter: Optional category filter
        
        Returns:
            Cost breakdown analysis
        """
        with self._lock:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Filter records
            records = [r for r in self.cost_records if r.timestamp >= cutoff_date]
            if category_filter:
                records = [r for r in records if r.category == category_filter]
            
            # Calculate breakdown by category
            breakdown: Dict[CostCategory, float] = {}
            for record in records:
                if record.category not in breakdown:
                    breakdown[record.category] = 0.0
                breakdown[record.category] += record.cost_usd
            
            total_cost = sum(breakdown.values())
            
            # Identify top resources
            resource_costs: Dict[str, float] = {}
            for record in records:
                if record.resource_id not in resource_costs:
                    resource_costs[record.resource_id] = 0.0
                resource_costs[record.resource_id] += record.cost_usd
            
            top_resources = sorted(
                [
                    {
                        'resource_id': rid,
                        'resource_name': self._get_resource_name(rid),
                        'cost': cost,
                        'percentage': (cost / total_cost * 100) if total_cost > 0 else 0
                    }
                    for rid, cost in resource_costs.items()
                ],
                key=lambda x: x['cost'],
                reverse=True
            )[:10]
            
            return CostBreakdown(
                total_cost_usd=total_cost,
                period=period,
                start_date=cutoff_date,
                end_date=datetime.utcnow(),
                breakdown=breakdown,
                top_resources=top_resources
            )

    def generate_forecast(
        self,
        forecast_days: int = 90,
        confidence_level: str = "medium"
    ) -> CostForecast:
        """
        Generate cost forecast using historical data.
        
        Args:
            forecast_days: Number of days to forecast
            confidence_level: Confidence level (low, medium, high)
        
        Returns:
            Cost forecast
        """
        with self._lock:
            forecast_id = str(uuid.uuid4())
            
            # Calculate trends from recent data
            recent_cutoff = datetime.utcnow() - timedelta(days=90)
            recent_records = [r for r in self.cost_records if r.timestamp >= recent_cutoff]
            
            daily_costs = self._aggregate_daily_costs(recent_records)
            
            # Simple trend-based forecast
            avg_daily_cost = sum(daily_costs.values()) / len(daily_costs) if daily_costs else 0
            trend_direction = self._calculate_trend_direction(daily_costs)
            
            # Generate forecast data
            forecast_data = []
            current_date = datetime.utcnow()
            confidence_noise = 0.05 if confidence_level == "high" else 0.10
            
            for i in range(forecast_days):
                forecast_date = current_date + timedelta(days=i)
                # Apply trend factor
                trend_factor = 1.0 + (0.02 if trend_direction == CostTrendDirection.INCREASING else -0.01)
                forecasted_cost = avg_daily_cost * (trend_factor ** (i / 30))
                
                confidence_percent = 90 if confidence_level == "high" else 75
                
                forecast_data.append({
                    'date': forecast_date.isoformat(),
                    'forecasted_cost_usd': round(forecasted_cost, 2),
                    'confidence_percent': confidence_percent
                })
            
            # Calculate peak
            peak_cost = max([d['forecasted_cost_usd'] for d in forecast_data], default=0)
            peak_date = next(
                d['date'] for d in forecast_data
                if d['forecasted_cost_usd'] == peak_cost
            )
            
            # Calculate monthly trend
            monthly_trend = ((avg_daily_cost * 30) - (sum(daily_costs.values()) / 3)) / (sum(daily_costs.values()) / 3) * 100
            
            forecast = CostForecast(
                forecast_id=forecast_id,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=forecast_days),
                forecast_period_days=forecast_days,
                forecast_data=forecast_data,
                trend_direction=trend_direction,
                monthly_trend_percentage=round(monthly_trend, 2),
                peak_cost_day={
                    'date': peak_date,
                    'cost_usd': round(peak_cost, 2)
                },
                baseline_cost_usd=round(avg_daily_cost * 30, 2),
                seasonal_factors={
                    'January': 1.1, 'February': 1.05, 'March': 1.0,
                    'April': 0.95, 'May': 0.95, 'June': 1.0,
                    'July': 1.15, 'August': 1.15, 'September': 1.05,
                    'October': 1.0, 'November': 1.2, 'December': 1.3
                }
            )
            
            self.forecasts[forecast_id] = forecast
            self._trigger_callback('forecast_updated', forecast)
            
            return forecast

    def get_optimization_recommendations(
        self,
        min_savings_usd: float = 100,
        include_high_effort: bool = False
    ) -> List[OptimizationRecommendation]:
        """
        Get cost optimization recommendations.
        
        Args:
            min_savings_usd: Minimum savings threshold
            include_high_effort: Include high-effort recommendations
        
        Returns:
            List of optimization recommendations
        """
        with self._lock:
            recommendations = []
            
            # Get current costs by category
            breakdown = self.get_cost_breakdown(days=30)
            monthly_cost = breakdown.total_cost_usd
            
            # Strategy 1: Reserved Instances
            if CostCategory.COMPUTE in breakdown.breakdown:
                compute_cost = breakdown.breakdown[CostCategory.COMPUTE]
                savings = compute_cost * 0.35  # 35% savings with 1-year reserved
                if savings > min_savings_usd:
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        strategy=OptimizationStrategy.RESERVED_INSTANCES,
                        affected_categories=[CostCategory.COMPUTE],
                        current_monthly_cost_usd=compute_cost,
                        estimated_savings_usd=savings,
                        savings_percentage=35,
                        implementation_effort="low",
                        estimated_implementation_days=5,
                        roi_months=3.4,
                        risk_level="low",
                        priority="critical",
                        description="Switch to 1-year reserved instances for compute resources",
                        implementation_steps=[
                            "Analyze current compute usage patterns",
                            "Identify suitable instances for reservation",
                            "Purchase 1-year reserved instances",
                            "Migrate workloads to reserved instances"
                        ],
                        affected_resources={"compute": list(self.cost_index_by_resource.keys())}
                    ))
            
            # Strategy 2: Auto-scaling
            savings = monthly_cost * 0.15
            if savings > min_savings_usd:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    strategy=OptimizationStrategy.AUTO_SCALING,
                    affected_categories=list(breakdown.breakdown.keys()),
                    current_monthly_cost_usd=monthly_cost,
                    estimated_savings_usd=savings,
                    savings_percentage=15,
                    implementation_effort="medium",
                    estimated_implementation_days=10,
                    roi_months=6.7,
                    risk_level="medium",
                    priority="high",
                    description="Implement advanced auto-scaling policies",
                    implementation_steps=[
                        "Define scaling metrics and thresholds",
                        "Test scaling policies in staging",
                        "Deploy to production gradually",
                        "Monitor and tune thresholds"
                    ],
                    affected_resources={"all": list(self.cost_index_by_resource.keys())}
                ))
            
            # Strategy 3: Storage Optimization
            if CostCategory.STORAGE in breakdown.breakdown:
                storage_cost = breakdown.breakdown[CostCategory.STORAGE]
                savings = storage_cost * 0.40
                if savings > min_savings_usd:
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        strategy=OptimizationStrategy.STORAGE_OPTIMIZATION,
                        affected_categories=[CostCategory.STORAGE],
                        current_monthly_cost_usd=storage_cost,
                        estimated_savings_usd=savings,
                        savings_percentage=40,
                        implementation_effort="medium",
                        estimated_implementation_days=14,
                        roi_months=2.5,
                        risk_level="low",
                        priority="high",
                        description="Optimize storage tiers and lifecycle policies",
                        implementation_steps=[
                            "Audit storage usage by tier",
                            "Implement lifecycle policies",
                            "Archive old data to cold storage",
                            "Monitor storage metrics"
                        ],
                        affected_resources={"storage": list(self.cost_index_by_resource.keys())}
                    ))
            
            self.recommendations = {r.recommendation_id: r for r in recommendations}
            
            for rec in recommendations:
                self._trigger_callback('recommendation_generated', rec)
            
            return recommendations

    def analyze_budget(
        self,
        budget_name: str,
        budgeted_amount_usd: float,
        period_days: int = 30
    ) -> BudgetAnalysis:
        """
        Analyze spending vs budget.
        
        Args:
            budget_name: Budget name
            budgeted_amount_usd: Budgeted amount
            period_days: Period to analyze
        
        Returns:
            Budget analysis
        """
        with self._lock:
            breakdown_current = self.get_cost_breakdown(days=period_days)
            breakdown_previous = self.get_cost_breakdown(days=period_days * 2)
            
            current_cost = breakdown_current.total_cost_usd
            prev_cost = breakdown_previous.total_cost_usd - current_cost
            
            spend_percentage = (current_cost / budgeted_amount_usd * 100) if budgeted_amount_usd > 0 else 0
            variance_usd = current_cost - budgeted_amount_usd
            variance_percentage = (variance_usd / budgeted_amount_usd * 100) if budgeted_amount_usd > 0 else 0
            
            burn_rate = current_cost / period_days
            days_until_exceeded = (budgeted_amount_usd - current_cost) / burn_rate if burn_rate > 0 else None
            
            month_over_month = ((current_cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0
            
            budget_analysis = BudgetAnalysis(
                budget_id=str(uuid.uuid4()),
                budget_name=budget_name,
                budgeted_amount_usd=budgeted_amount_usd,
                actual_amount_usd=current_cost,
                spend_percentage=round(spend_percentage, 2),
                variance_usd=round(variance_usd, 2),
                variance_percentage=round(variance_percentage, 2),
                burn_rate_usd_per_day=round(burn_rate, 2),
                days_until_budget_exceeded=int(days_until_exceeded) if days_until_exceeded else None,
                current_month_costs=current_cost,
                last_month_costs=prev_cost,
                month_over_month_change_percent=round(month_over_month, 2),
                budget_period=f"{period_days}_days"
            )
            
            self.budgets[budget_analysis.budget_id] = budget_analysis
            
            if spend_percentage > 80:
                self._trigger_callback('budget_exceeded', budget_analysis)
            
            return budget_analysis

    def create_policy(
        self,
        policy_name: str,
        max_daily_spend_usd: float,
        max_monthly_spend_usd: float,
        alert_threshold_percent: float = 80,
        category_limits: Dict[str, float] = None
    ) -> CostPolicy:
        """Create cost control policy."""
        with self._lock:
            policy = CostPolicy(
                policy_id=str(uuid.uuid4()),
                policy_name=policy_name,
                max_daily_spend_usd=max_daily_spend_usd,
                max_monthly_spend_usd=max_monthly_spend_usd,
                alert_threshold_percent=alert_threshold_percent,
                auto_shutdown_enabled=False,
                auto_shutdown_threshold_usd=max_daily_spend_usd * 1.5,
                category_limits=category_limits or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.policies[policy.policy_id] = policy
            return policy

    def check_policy_compliance(self) -> List[Dict]:
        """Check if current spending violates any policies."""
        with self._lock:
            violations = []
            
            for policy in self.policies.values():
                daily_breakdown = self.get_cost_breakdown(days=1)
                daily_cost = daily_breakdown.total_cost_usd
                
                if daily_cost > policy.max_daily_spend_usd:
                    violation = {
                        'policy_id': policy.policy_id,
                        'policy_name': policy.policy_name,
                        'violation_type': 'daily_limit_exceeded',
                        'limit_usd': policy.max_daily_spend_usd,
                        'actual_usd': daily_cost,
                        'overage_usd': daily_cost - policy.max_daily_spend_usd,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    violations.append(violation)
                    self._trigger_callback('policy_violated', violation)
            
            return violations

    def get_service_stats(self) -> Dict:
        """Get service statistics."""
        with self._lock:
            return {
                'total_cost_records': len(self.cost_records),
                'active_budgets': len(self.budgets),
                'active_policies': len(self.policies),
                'total_recommendations': len(self.recommendations),
                'total_forecasts': len(self.forecasts),
                'total_spend_30_days_usd': self.get_cost_breakdown(days=30).total_cost_usd,
                'cost_categories': len(self.cost_index_by_category),
                'tracked_resources': len(self.cost_index_by_resource)
            }

    # Helper methods

    def _get_resource_name(self, resource_id: str) -> str:
        """Get resource name from records."""
        if resource_id in self.cost_index_by_resource:
            records = self.cost_index_by_resource[resource_id]
            if records:
                return records[0].resource_name
        return resource_id

    def _aggregate_daily_costs(self, records: List[CostRecord]) -> Dict[str, float]:
        """Aggregate costs by day."""
        daily_costs: Dict[str, float] = {}
        for record in records:
            day_key = record.timestamp.date().isoformat()
            if day_key not in daily_costs:
                daily_costs[day_key] = 0.0
            daily_costs[day_key] += record.cost_usd
        return daily_costs

    def _calculate_trend_direction(self, daily_costs: Dict[str, float]) -> CostTrendDirection:
        """Calculate cost trend direction."""
        if len(daily_costs) < 2:
            return CostTrendDirection.STABLE
        
        sorted_costs = sorted(daily_costs.items())
        first_half = sum(v for k, v in sorted_costs[:len(sorted_costs)//2])
        second_half = sum(v for k, v in sorted_costs[len(sorted_costs)//2:])
        
        if second_half > first_half * 1.1:
            return CostTrendDirection.INCREASING
        elif second_half < first_half * 0.9:
            return CostTrendDirection.DECREASING
        return CostTrendDirection.STABLE

    def _check_cost_spike(self, resource_id: str, new_cost: float) -> None:
        """Check for cost spikes."""
        if resource_id in self.cost_index_by_resource:
            records = self.cost_index_by_resource[resource_id]
            if len(records) > 5:
                recent_costs = [r.cost_usd for r in records[-5:]]
                avg_cost = sum(recent_costs) / len(recent_costs)
                
                if new_cost > avg_cost * 2:
                    self._trigger_callback('cost_spike_detected', {
                        'resource_id': resource_id,
                        'new_cost': new_cost,
                        'average_cost': avg_cost,
                        'spike_percent': (new_cost - avg_cost) / avg_cost * 100
                    })

    def _trigger_callback(self, event_type: str, data: Any) -> None:
        """Trigger registered callbacks."""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    pass  # Ignore callback errors

    def register_callback(self, event_type: str, callback) -> None:
        """Register event callback."""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    def health_check(self) -> Dict:
        """Health check."""
        return {
            'service': 'cost_optimization',
            'status': 'operational',
            'cost_records_tracked': len(self.cost_records),
            'last_record_time': self.cost_records[-1].timestamp.isoformat() if self.cost_records else None,
            'budgets_active': len(self.budgets),
            'policies_active': len(self.policies)
        }
