"""
Phase 13: Cost Optimizer
Resource cost tracking, analysis, and optimization recommendations
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class CostCategory(str, Enum):
    """Cost categories"""
    COMPUTATION = "computation"
    STORAGE = "storage"
    DATA_TRANSFER = "data_transfer"
    API_CALLS = "api_calls"
    PREMIUM_FEATURES = "premium_features"
    TEAM_MEMBERS = "team_members"


class CostBreakdown:
    """Cost breakdown for resource"""

    def __init__(self, resource_id: str, resource_type: str, tenant_id: str):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.tenant_id = tenant_id
        self.costs: Dict[CostCategory, float] = defaultdict(float)
        self.usage: Dict[str, float] = {}
        self.timestamp = datetime.utcnow()

    def add_cost(self, category: CostCategory, amount: float) -> None:
        """Add cost to category"""
        self.costs[category] += amount

    def set_usage(self, metric_name: str, value: float) -> None:
        """Set usage metric"""
        self.usage[metric_name] = value

    def get_total(self) -> float:
        """Get total cost"""
        return sum(self.costs.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "tenant_id": self.tenant_id,
            "total_cost": self.get_total(),
            "costs_by_category": {k.value: v for k, v in self.costs.items()},
            "usage": self.usage,
            "timestamp": self.timestamp.isoformat(),
        }


class CostOptimization:
    """Cost optimization recommendation"""

    def __init__(self, recommendation_id: str, resource_id: str,
                 title: str, description: str, estimated_savings: float,
                 priority: str):
        self.recommendation_id = recommendation_id
        self.resource_id = resource_id
        self.title = title
        self.description = description
        self.estimated_savings = estimated_savings
        self.priority = priority  # high, medium, low
        self.created_at = datetime.utcnow()
        self.implemented = False
        self.implementation_date: Optional[datetime] = None

    def mark_implemented(self) -> None:
        """Mark recommendation as implemented"""
        self.implemented = True
        self.implementation_date = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "recommendation_id": self.recommendation_id,
            "resource_id": self.resource_id,
            "title": self.title,
            "description": self.description,
            "estimated_savings": self.estimated_savings,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "implemented": self.implemented,
            "implementation_date": self.implementation_date.isoformat() if self.implementation_date else None,
        }


class CostOptimizer:
    """
    Central cost optimization service
    Tracks, analyzes, and optimizes resource costs
    """

    def __init__(self):
        self.cost_breakdowns: Dict[str, CostBreakdown] = {}
        self.recommendations: Dict[str, CostOptimization] = {}
        self.cost_history: Dict[str, List[Dict]] = defaultdict(list)
        self.monthly_costs: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.pricing_config = self._init_pricing()

    def track_resource_cost(self, resource_id: str, resource_type: str,
                           tenant_id: str, category: CostCategory,
                           cost: float, usage_metric: Optional[str] = None,
                           usage_value: Optional[float] = None) -> None:
        """
        Track cost for resource
        """
        # Get or create breakdown
        if resource_id not in self.cost_breakdowns:
            self.cost_breakdowns[resource_id] = CostBreakdown(
                resource_id, resource_type, tenant_id
            )

        breakdown = self.cost_breakdowns[resource_id]
        breakdown.add_cost(category, cost)

        if usage_metric and usage_value:
            breakdown.set_usage(usage_metric, usage_value)

        # Track history
        self.cost_history[resource_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "category": category.value,
            "cost": cost,
            "usage_metric": usage_metric,
            "usage_value": usage_value,
        })

        # Track monthly
        now = datetime.utcnow()
        month_key = f"{now.year}-{now.month:02d}"
        self.monthly_costs[tenant_id][month_key] += cost

        logger.debug(f"Cost tracked: {resource_id} - {cost} ({category.value})")

    def get_cost_breakdown(self, tenant_id: str, group_by: str = "category") -> Dict[str, Any]:
        """
        Get cost breakdown for tenant
        group_by: category, resource, resource_type
        """
        tenant_resources = [
            cb for cb in self.cost_breakdowns.values()
            if cb.tenant_id == tenant_id
        ]

        if group_by == "category":
            breakdown = defaultdict(float)
            for resource in tenant_resources:
                for category, cost in resource.costs.items():
                    breakdown[category.value] += cost
            return {k: v for k, v in breakdown.items()}

        elif group_by == "resource":
            breakdown = {}
            for resource in tenant_resources:
                breakdown[resource.resource_id] = resource.get_total()
            return breakdown

        elif group_by == "resource_type":
            breakdown = defaultdict(float)
            for resource in tenant_resources:
                breakdown[resource.resource_type] += resource.get_total()
            return {k: v for k, v in breakdown.items()}

        return {}

    def get_monthly_costs(self, tenant_id: str, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly cost trends"""
        result = []

        for month_key in sorted(self.monthly_costs[tenant_id].keys())[-months:]:
            result.append({
                "month": month_key,
                "total_cost": self.monthly_costs[tenant_id][month_key],
            })

        return result

    def calculate_roi(self, investment: float, cost_savings: float,
                     months: int = 12) -> Dict[str, float]:
        """Calculate ROI for optimization"""
        monthly_savings = cost_savings / months if months > 0 else 0
        total_savings = cost_savings

        roi_percent = (total_savings / investment * 100) if investment > 0 else 0
        payback_months = investment / monthly_savings if monthly_savings > 0 else 0

        return {
            "investment": investment,
            "total_savings": total_savings,
            "monthly_savings": monthly_savings,
            "roi_percent": roi_percent,
            "payback_months": payback_months,
        }

    def find_inefficiencies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Find cost inefficiencies
        Returns list of problematic resources
        """
        inefficiencies = []

        tenant_resources = [
            cb for cb in self.cost_breakdowns.values()
            if cb.tenant_id == tenant_id
        ]

        for resource in tenant_resources:
            # Check for high storage costs with low usage
            storage_cost = resource.costs.get(CostCategory.STORAGE, 0)
            storage_usage = resource.usage.get("storage_gb", 0)

            if storage_cost > 100 and storage_usage < 10:
                inefficiencies.append({
                    "resource_id": resource.resource_id,
                    "issue": "High storage cost with low usage",
                    "estimated_waste": storage_cost * 0.3,
                    "recommendation": "Consider smaller storage tier",
                })

            # Check for underutilized computation
            compute_cost = resource.costs.get(CostCategory.COMPUTATION, 0)
            compute_usage = resource.usage.get("cpu_percent", 50)

            if compute_usage < 20 and compute_cost > 50:
                inefficiencies.append({
                    "resource_id": resource.resource_id,
                    "issue": "Underutilized compute resources",
                    "estimated_waste": compute_cost * 0.4,
                    "recommendation": "Downsize to smaller instance",
                })

        return inefficiencies

    def recommend_optimizations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations
        Returns list of recommendations
        """
        import uuid

        recommendations = []
        inefficiencies = self.find_inefficiencies(tenant_id)

        for inefficiency in inefficiencies:
            rec_id = f"opt_{uuid.uuid4().hex[:16]}"
            recommendation = CostOptimization(
                rec_id,
                inefficiency["resource_id"],
                inefficiency["issue"],
                inefficiency["recommendation"],
                inefficiency["estimated_waste"],
                "medium"
            )

            self.recommendations[rec_id] = recommendation
            recommendations.append(recommendation.to_dict())

        return recommendations

    def forecast_costs(self, tenant_id: str, months: int = 3) -> Dict[str, Any]:
        """Forecast future costs"""
        monthly_data = self.get_monthly_costs(tenant_id, months=6)

        if len(monthly_data) < 2:
            return {"forecast": [], "confidence": 0}

        costs = [m["total_cost"] for m in monthly_data]
        avg_cost = statistics.mean(costs)
        std_dev = statistics.stdev(costs) if len(costs) > 1 else 0

        forecast = []
        for i in range(1, months + 1):
            # Simple linear trend
            trend = (costs[-1] - costs[0]) / len(costs) if len(costs) > 0 else 0
            forecast_cost = avg_cost + (trend * i)
            forecast.append({
                "month_offset": i,
                "forecasted_cost": max(0, forecast_cost),
            })

        confidence = 1.0 - min(1.0, std_dev / avg_cost) if avg_cost > 0 else 0

        return {
            "forecast": forecast,
            "confidence": confidence,
            "avg_monthly_cost": avg_cost,
        }

    def compare_plans(self, tenant_id: str) -> Dict[str, Any]:
        """Compare current plan vs alternatives"""
        total_cost = sum(
            cb.get_total() for cb in self.cost_breakdowns.values()
            if cb.tenant_id == tenant_id
        )

        plans = {
            "current": {"name": "PROFESSIONAL", "cost": total_cost},
            "alternative_1": {"name": "STARTER", "cost": total_cost * 0.5},
            "alternative_2": {"name": "ENTERPRISE", "cost": total_cost * 1.5},
        }

        return {"plans": plans, "current_plan": "PROFESSIONAL"}

    def optimize_for_budget(self, tenant_id: str, budget: float) -> Dict[str, Any]:
        """
        Get optimization recommendations to fit budget
        """
        current_cost = sum(
            cb.get_total() for cb in self.cost_breakdowns.values()
            if cb.tenant_id == tenant_id
        )

        if current_cost <= budget:
            return {
                "status": "within_budget",
                "current_cost": current_cost,
                "budget": budget,
                "recommendations": [],
            }

        overage = current_cost - budget
        recommendations = self.recommend_optimizations(tenant_id)

        # Sort by savings potential
        recommendations.sort(key=lambda x: x["estimated_savings"], reverse=True)

        # Select recommendations to hit budget
        selected = []
        remaining = overage
        for rec in recommendations:
            if remaining <= 0:
                break
            selected.append(rec)
            remaining -= rec["estimated_savings"]

        return {
            "status": "over_budget",
            "current_cost": current_cost,
            "budget": budget,
            "overage": overage,
            "recommendations": selected,
            "projected_cost_after": current_cost - sum(r["estimated_savings"] for r in selected),
        }

    def get_optimization_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get optimization statistics"""
        recommendations = [
            r for r in self.recommendations.values()
            if r.resource_id in [
                cb.resource_id for cb in self.cost_breakdowns.values()
                if cb.tenant_id == tenant_id
            ]
        ]

        implemented = [r for r in recommendations if r.implemented]
        total_savings = sum(r.estimated_savings for r in recommendations)
        realized_savings = sum(r.estimated_savings for r in implemented)

        return {
            "total_recommendations": len(recommendations),
            "implemented": len(implemented),
            "potential_savings": total_savings,
            "realized_savings": realized_savings,
        }

    def _init_pricing(self) -> Dict[str, float]:
        """Initialize pricing config"""
        return {
            "compute_per_hour": 0.0116,
            "storage_per_gb_month": 0.023,
            "data_transfer_per_gb": 0.12,
            "api_calls_per_1m": 0.002,
            "premium_feature_monthly": 19.99,
            "team_member_monthly": 9.99,
        }
