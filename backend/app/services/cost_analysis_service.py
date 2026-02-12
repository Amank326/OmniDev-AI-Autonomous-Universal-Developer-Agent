"""
Cost Analysis Service for OmniDev AI
Cost tracking, allocation, optimization, and financial reporting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class CostCategory(str, Enum):
    """Cost categories"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    ANALYTICS = "analytics"
    ML = "ml"
    MONITORING = "monitoring"
    OTHER = "other"


class CostTrendDirection(str, Enum):
    """Cost trend direction"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


@dataclass
class CostBreakdown:
    """Cost breakdown by category"""
    timestamp: datetime
    category: CostCategory
    cost_dollars: float
    percentage_of_total: float
    unit_cost: float
    units_consumed: float
    trend: CostTrendDirection


@dataclass
class CostAllocation:
    """Cost allocation to workloads/teams"""
    allocation_id: str
    workspace_id: str
    owner: str
    cost_dollars: float
    percentage_of_workspace: float
    primary_cost_driver: CostCategory
    allocated_at: datetime
    allocated_through: datetime


@dataclass
class CostOptimizationOpportunity:
    """Opportunity to optimize costs"""
    opportunity_id: str
    category: CostCategory
    current_spend: float
    recommended_spend: float
    potential_savings: float
    savings_percentage: float
    effort_level: str  # easy, moderate, difficult
    payback_period_months: float
    risk_level: str  # low, medium, high
    description: str
    actions: List[str]


@dataclass
class CostForecast:
    """Cost forecast"""
    forecast_period_start: datetime
    forecast_period_end: datetime
    forecasted_total_cost: float
    forecasted_breakdown: Dict[str, float]
    confidence_score: float
    growth_rate: float
    seasonality_factor: float


@dataclass
class CostAnalysisResult:
    """Complete cost analysis"""
    analysis_timestamp: datetime
    workspace_id: str
    period_start: datetime
    period_end: datetime
    total_cost: float
    cost_by_category: Dict[str, float]
    cost_breakdown: List[CostBreakdown]
    allocations: List[CostAllocation]
    opportunities: List[CostOptimizationOpportunity]
    forecast: CostForecast
    cost_per_user: float
    cost_trend: CostTrendDirection
    optimization_potential: float


class CostAnalysisService:
    """Service for cost analysis and financial management"""

    def __init__(self):
        """Initialize cost analysis service"""
        self.cost_history: Dict[str, List[Dict]] = {}
        self.allocations: Dict[str, List[CostAllocation]] = {}
        self.cost_baselines: Dict[str, Dict[str, float]] = {}

    def track_cost(
        self,
        workspace_id: str,
        category: CostCategory,
        cost_amount: float,
        units_consumed: float = 1.0,
    ) -> Dict:
        """
        Track a cost entry
        
        Args:
            workspace_id: Workspace identifier
            category: Cost category
            cost_amount: Cost in dollars
            units_consumed: Units consumed
            
        Returns:
            Cost tracking entry
        """
        cost_entry = {
            'timestamp': datetime.utcnow(),
            'category': category.value,
            'cost_dollars': cost_amount,
            'units_consumed': units_consumed,
        }

        if workspace_id not in self.cost_history:
            self.cost_history[workspace_id] = []

        self.cost_history[workspace_id].append(cost_entry)
        # Keep last 10,000 entries
        self.cost_history[workspace_id] = self.cost_history[workspace_id][-10000:]

        return cost_entry

    def analyze_costs(
        self,
        workspace_id: str,
        period_days: int = 30,
        num_users: int = 10,
    ) -> CostAnalysisResult:
        """
        Analyze costs for workspace
        
        Args:
            workspace_id: Workspace identifier
            period_days: Period to analyze (days)
            num_users: Number of active users
            
        Returns:
            Complete cost analysis
        """
        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()

        # Get cost history for period
        cost_history = self.cost_history.get(workspace_id, [])
        period_costs = [
            c for c in cost_history
            if datetime.fromisoformat(c['timestamp'].isoformat() if isinstance(c['timestamp'], datetime) else c['timestamp'])
            >= period_start
        ]

        # Calculate costs by category
        cost_by_category = {}
        for cost_entry in period_costs:
            category = cost_entry['category']
            cost_by_category[category] = cost_by_category.get(category, 0) + cost_entry['cost_dollars']

        # Generate simulated costs if no history
        if not cost_by_category:
            cost_by_category = {
                'compute': 1500.0,
                'storage': 500.0,
                'network': 300.0,
                'database': 800.0,
                'analytics': 400.0,
                'ml': 600.0,
                'monitoring': 150.0,
                'other': 200.0,
            }

        total_cost = sum(cost_by_category.values())

        # Build cost breakdown
        cost_breakdown = []
        for category, cost in cost_by_category.items():
            breakdown = CostBreakdown(
                timestamp=datetime.utcnow(),
                category=CostCategory(category),
                cost_dollars=round(cost, 2),
                percentage_of_total=round((cost / total_cost * 100), 2),
                unit_cost=round(cost / period_days, 2),
                units_consumed=period_days,
                trend=CostTrendDirection.STABLE if cost < 1000 else CostTrendDirection.INCREASING,
            )
            cost_breakdown.append(breakdown)

        # Allocate costs to teams/owners
        allocations = self._allocate_costs(workspace_id, cost_by_category)

        # Identify optimization opportunities
        opportunities = self._identify_cost_opportunities(cost_by_category, total_cost)

        # Generate forecast
        forecast = self._generate_cost_forecast(workspace_id, cost_by_category, period_days)

        # Calculate cost per user
        cost_per_user = total_cost / max(1, num_users)

        # Determine trend
        trend = CostTrendDirection.STABLE
        if total_cost > 3500:
            trend = CostTrendDirection.INCREASING

        # Calculate optimization potential
        optimization_potential = sum(
            opp.potential_savings for opp in opportunities
        ) / max(1, total_cost)

        result = CostAnalysisResult(
            analysis_timestamp=datetime.utcnow(),
            workspace_id=workspace_id,
            period_start=period_start,
            period_end=period_end,
            total_cost=round(total_cost, 2),
            cost_by_category={k: round(v, 2) for k, v in cost_by_category.items()},
            cost_breakdown=cost_breakdown,
            allocations=allocations,
            opportunities=opportunities,
            forecast=forecast,
            cost_per_user=round(cost_per_user, 2),
            cost_trend=trend,
            optimization_potential=round(optimization_potential * 100, 2),
        )

        return result

    def _allocate_costs(
        self,
        workspace_id: str,
        cost_by_category: Dict[str, float],
    ) -> List[CostAllocation]:
        """Allocate costs to teams/workloads"""
        total_cost = sum(cost_by_category.values())
        allocations = []

        teams = ['platform', 'analytics', 'ml_ops', 'infrastructure']
        allocation_percentages = [0.35, 0.25, 0.25, 0.15]

        for i, team in enumerate(teams):
            team_cost = total_cost * allocation_percentages[i]
            primary_driver = max(cost_by_category.items(), key=lambda x: x[1])[0]

            allocation = CostAllocation(
                allocation_id=f"{workspace_id}:{team}:{int(datetime.utcnow().timestamp())}",
                workspace_id=workspace_id,
                owner=team,
                cost_dollars=round(team_cost, 2),
                percentage_of_workspace=round(allocation_percentages[i] * 100, 2),
                primary_cost_driver=CostCategory(primary_driver),
                allocated_at=datetime.utcnow(),
                allocated_through=datetime.utcnow() + timedelta(days=30),
            )
            allocations.append(allocation)

        return allocations

    def _identify_cost_opportunities(
        self,
        cost_by_category: Dict[str, float],
        total_cost: float,
    ) -> List[CostOptimizationOpportunity]:
        """Identify cost optimization opportunities"""
        opportunities = []

        # Compute optimization
        if cost_by_category.get('compute', 0) > 1000:
            opportunities.append(
                CostOptimizationOpportunity(
                    opportunity_id="opp_compute_rightsizing",
                    category=CostCategory.COMPUTE,
                    current_spend=cost_by_category.get('compute', 0),
                    recommended_spend=cost_by_category.get('compute', 0) * 0.75,
                    potential_savings=cost_by_category.get('compute', 0) * 0.25,
                    savings_percentage=25,
                    effort_level="moderate",
                    payback_period_months=2,
                    risk_level="low",
                    description="Right-size compute instances based on actual usage",
                    actions=[
                        "Review instance utilization metrics",
                        "Downsize over-provisioned instances",
                        "Test with reduced resources",
                    ],
                )
            )

        # Storage optimization
        if cost_by_category.get('storage', 0) > 300:
            opportunities.append(
                CostOptimizationOpportunity(
                    opportunity_id="opp_storage_tiering",
                    category=CostCategory.STORAGE,
                    current_spend=cost_by_category.get('storage', 0),
                    recommended_spend=cost_by_category.get('storage', 0) * 0.80,
                    potential_savings=cost_by_category.get('storage', 0) * 0.20,
                    savings_percentage=20,
                    effort_level="moderate",
                    payback_period_months=3,
                    risk_level="low",
                    description="Implement storage tiering to move cold data to cheaper tiers",
                    actions=[
                        "Analyze data access patterns",
                        "Move infrequently accessed data to cold storage",
                        "Monitor retrieval costs",
                    ],
                )
            )

        # Database optimization
        if cost_by_category.get('database', 0) > 500:
            opportunities.append(
                CostOptimizationOpportunity(
                    opportunity_id="opp_database_reserved",
                    category=CostCategory.DATABASE,
                    current_spend=cost_by_category.get('database', 0),
                    recommended_spend=cost_by_category.get('database', 0) * 0.70,
                    potential_savings=cost_by_category.get('database', 0) * 0.30,
                    savings_percentage=30,
                    effort_level="easy",
                    payback_period_months=1.5,
                    risk_level="low",
                    description="Purchase reserved database capacity (1-3 year commitment)",
                    actions=[
                        "Calculate baseline DB usage",
                        "Purchase reserved capacity",
                        "Configure auto-scaling for burst",
                    ],
                )
            )

        # Network optimization
        if cost_by_category.get('network', 0) > 200:
            opportunities.append(
                CostOptimizationOpportunity(
                    opportunity_id="opp_network_regional",
                    category=CostCategory.NETWORK,
                    current_spend=cost_by_category.get('network', 0),
                    recommended_spend=cost_by_category.get('network', 0) * 0.85,
                    potential_savings=cost_by_category.get('network', 0) * 0.15,
                    savings_percentage=15,
                    effort_level="moderate",
                    payback_period_months=4,
                    risk_level="medium",
                    description="Optimize data transfer costs with regional architecture",
                    actions=[
                        "Analyze cross-region traffic",
                        "Deploy regional edge caches",
                        "Test latency impact",
                    ],
                )
            )

        return opportunities

    def _generate_cost_forecast(
        self,
        workspace_id: str,
        cost_by_category: Dict[str, float],
        period_days: int,
    ) -> CostForecast:
        """Generate cost forecast"""
        total_monthly_cost = sum(cost_by_category.values()) * (30 / period_days)

        # Simulate 20% annual growth
        growth_rate = 0.02  # 2% monthly
        forecast_months = 12

        forecasted_total = total_monthly_cost * ((1 + growth_rate) ** forecast_months)
        forecasted_breakdown = {
            cat: cost * (30 / period_days) * ((1 + growth_rate) ** forecast_months)
            for cat, cost in cost_by_category.items()
        }

        forecast = CostForecast(
            forecast_period_start=datetime.utcnow(),
            forecast_period_end=datetime.utcnow() + timedelta(days=365),
            forecasted_total_cost=round(forecasted_total, 2),
            forecasted_breakdown={k: round(v, 2) for k, v in forecasted_breakdown.items()},
            confidence_score=0.75,
            growth_rate=growth_rate * 100,
            seasonality_factor=1.05,
        )

        return forecast

    def calculate_roi(
        self,
        investment_amount: float,
        annual_savings: float,
    ) -> Dict:
        """Calculate ROI for cost optimization investment"""
        payback_months = (investment_amount / (annual_savings / 12)) if annual_savings > 0 else float('inf')
        roi_percentage = ((annual_savings - (investment_amount / 3)) / investment_amount * 100) if investment_amount > 0 else 0

        return {
            "investment_amount": round(investment_amount, 2),
            "annual_savings": round(annual_savings, 2),
            "payback_period_months": round(payback_months, 1) if payback_months != float('inf') else "N/A",
            "roi_percentage": round(roi_percentage, 1),
            "break_even_date": (datetime.utcnow() + timedelta(days=int(payback_months * 30))).isoformat()
            if payback_months != float('inf')
            else "N/A",
        }

    def generate_cost_report(
        self,
        workspace_id: str,
        period_days: int = 90,
    ) -> Dict:
        """Generate comprehensive cost report"""
        analysis = self.analyze_costs(workspace_id, period_days)

        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "workspace_id": workspace_id,
            "period": f"{period_days} days",
            "summary": {
                "total_cost": analysis.total_cost,
                "cost_per_day": round(analysis.total_cost / period_days, 2),
                "cost_per_user": analysis.cost_per_user,
                "trend": analysis.cost_trend.value,
            },
            "breakdown": {
                cat.value: cost for cat, cost in analysis.cost_by_category.items()
            },
            "allocations": [
                {
                    "owner": alloc.owner,
                    "cost": alloc.cost_dollars,
                    "percentage": alloc.percentage_of_workspace,
                    "primary_driver": alloc.primary_cost_driver.value,
                }
                for alloc in analysis.allocations
            ],
            "opportunities": [
                {
                    "category": opp.category.value,
                    "current_spend": opp.current_spend,
                    "potential_savings": opp.potential_savings,
                    "effort": opp.effort_level,
                    "payback_months": opp.payback_period_months,
                    "description": opp.description,
                }
                for opp in analysis.opportunities
            ],
            "forecast": {
                "annual_projected": analysis.forecast.forecasted_total_cost,
                "growth_rate": analysis.forecast.growth_rate,
            },
            "optimization_potential": f"{analysis.optimization_potential}%",
        }

        return report
