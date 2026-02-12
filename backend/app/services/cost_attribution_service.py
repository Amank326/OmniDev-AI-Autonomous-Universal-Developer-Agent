"""
Cost Attribution Service
Track and allocate costs across services and components
Phase 43: Advanced Analytics & ML Features
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
import threading
from collections import defaultdict
import statistics


class AttributionModel(Enum):
    """Cost attribution models"""
    TIME_BASED = "time_based"
    REQUEST_BASED = "request_based"
    RESOURCE_BASED = "resource_based"
    WEIGHTED = "weighted"


class CostUnit(Enum):
    """Cost measurement units"""
    USD = "usd"
    CREDITS = "credits"
    COMPUTE_HOURS = "compute_hours"


@dataclass
class CostEntry:
    """Individual cost entry"""
    timestamp: datetime
    service_name: str
    resource_type: str
    cost_amount: float
    cost_unit: CostUnit
    quantity: float
    unit_price: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "service_name": self.service_name,
            "resource_type": self.resource_type,
            "cost_amount": self.cost_amount,
            "cost_unit": self.cost_unit.value,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "metadata": self.metadata,
        }


@dataclass
class ServiceCostBreakdown:
    """Cost breakdown for a service"""
    service_name: str
    total_cost: float
    cost_by_resource: Dict[str, float]
    cost_by_hour: Dict[str, float]
    entry_count: int
    period_start: datetime
    period_end: datetime
    trend: str  # up, down, stable
    percent_change: float

    def to_dict(self):
        return {
            "service_name": self.service_name,
            "total_cost": self.total_cost,
            "cost_by_resource": self.cost_by_resource,
            "entry_count": self.entry_count,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "trend": self.trend,
            "percent_change": self.percent_change,
        }


@dataclass
class Budget:
    """Budget configuration and tracking"""
    id: str
    service_name: str
    monthly_limit: float
    alert_threshold_percent: float
    currency: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def to_dict(self):
        return {
            "id": self.id,
            "service_name": self.service_name,
            "monthly_limit": self.monthly_limit,
            "alert_threshold_percent": self.alert_threshold_percent,
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }


@dataclass
class CostForecast:
    """Cost forecast for service"""
    service_name: str
    forecast_date: datetime
    predicted_cost: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    trend_direction: str
    method: str

    def to_dict(self):
        return {
            "service_name": self.service_name,
            "forecast_date": self.forecast_date.isoformat(),
            "predicted_cost": self.predicted_cost,
            "confidence_interval_lower": self.confidence_interval_lower,
            "confidence_interval_upper": self.confidence_interval_upper,
            "trend_direction": self.trend_direction,
            "method": self.method,
        }


class CostAttributionService:
    """Manages cost tracking and attribution"""

    def __init__(self, default_model: AttributionModel = AttributionModel.TIME_BASED):
        self.cost_entries: List[CostEntry] = []
        self.budgets: Dict[str, Budget] = {}
        self.service_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.attribution_model = default_model
        self.callbacks: List[Callable] = []
        self.lock = threading.RLock()

    def record_cost(
        self,
        service_name: str,
        resource_type: str,
        cost_amount: float,
        quantity: float = 1.0,
        unit_price: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEntry:
        """Record a cost entry"""
        with self.lock:
            entry = CostEntry(
                timestamp=datetime.now(),
                service_name=service_name,
                resource_type=resource_type,
                cost_amount=cost_amount,
                cost_unit=CostUnit.USD,
                quantity=quantity,
                unit_price=unit_price,
                metadata=metadata or {},
            )

            self.cost_entries.append(entry)

            # Check budget alerts
            self._check_budget_alert(service_name)

            # Notify callbacks
            self._notify_callbacks({
                "event": "cost_recorded",
                "service": service_name,
                "amount": cost_amount,
            })

            return entry

    def get_service_costs(
        self, service_name: str, days: int = 30
    ) -> ServiceCostBreakdown:
        """Get cost breakdown for service"""
        with self.lock:
            cutoff = datetime.now() - timedelta(days=days)

            # Filter entries for service and timeframe
            entries = [
                e for e in self.cost_entries
                if e.service_name == service_name and e.timestamp >= cutoff
            ]

            if not entries:
                return ServiceCostBreakdown(
                    service_name=service_name,
                    total_cost=0.0,
                    cost_by_resource={},
                    cost_by_hour={},
                    entry_count=0,
                    period_start=cutoff,
                    period_end=datetime.now(),
                    trend="stable",
                    percent_change=0.0,
                )

            # Calculate totals
            total_cost = sum(e.cost_amount for e in entries)

            # Cost by resource
            cost_by_resource = defaultdict(float)
            for entry in entries:
                cost_by_resource[entry.resource_type] += entry.cost_amount

            # Cost by hour (for trend)
            cost_by_hour = defaultdict(float)
            for entry in entries:
                hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
                cost_by_hour[hour_key] += entry.cost_amount

            # Calculate trend
            sorted_hours = sorted(cost_by_hour.items())
            trend = "stable"
            percent_change = 0.0

            if len(sorted_hours) > 2:
                first_half_avg = statistics.mean(
                    [v for _, v in sorted_hours[: len(sorted_hours) // 2]]
                )
                second_half_avg = statistics.mean(
                    [v for _, v in sorted_hours[len(sorted_hours) // 2 :]]
                )

                if second_half_avg > first_half_avg:
                    trend = "up"
                    percent_change = (
                        (second_half_avg - first_half_avg) / first_half_avg * 100
                    )
                elif second_half_avg < first_half_avg:
                    trend = "down"
                    percent_change = (
                        (first_half_avg - second_half_avg) / first_half_avg * 100
                    )

            return ServiceCostBreakdown(
                service_name=service_name,
                total_cost=total_cost,
                cost_by_resource=dict(cost_by_resource),
                cost_by_hour={},
                entry_count=len(entries),
                period_start=entries[0].timestamp,
                period_end=entries[-1].timestamp,
                trend=trend,
                percent_change=percent_change,
            )

    def get_total_costs(self, days: int = 30) -> Dict[str, float]:
        """Get total costs across all services"""
        with self.lock:
            cutoff = datetime.now() - timedelta(days=days)
            entries = [e for e in self.cost_entries if e.timestamp >= cutoff]

            costs = defaultdict(float)
            for entry in entries:
                costs[entry.service_name] += entry.cost_amount

            return dict(costs)

    def allocate_costs_by_model(
        self, metric_values: Dict[str, float], cost_pool: float
    ) -> Dict[str, float]:
        """Allocate costs using configured attribution model"""
        if not metric_values or cost_pool <= 0:
            return {}

        total = sum(metric_values.values())
        if total == 0:
            return {}

        if self.attribution_model == AttributionModel.TIME_BASED:
            # Allocate proportionally to time
            return {
                service: (value / total) * cost_pool
                for service, value in metric_values.items()
            }

        elif self.attribution_model == AttributionModel.REQUEST_BASED:
            # Allocate proportionally to requests
            return {
                service: (value / total) * cost_pool
                for service, value in metric_values.items()
            }

        elif self.attribution_model == AttributionModel.RESOURCE_BASED:
            # Allocate based on resource usage (CPU, memory)
            return {
                service: (value / total) * cost_pool
                for service, value in metric_values.items()
            }

        elif self.attribution_model == AttributionModel.WEIGHTED:
            # Custom weighted allocation
            return {
                service: (value / total) * cost_pool
                for service, value in metric_values.items()
            }

        return {}

    def set_budget(
        self, service_name: str, monthly_limit: float, alert_threshold_percent: float = 80.0
    ) -> Budget:
        """Set monthly budget for service"""
        with self.lock:
            budget_id = f"budget_{service_name}_{int(datetime.now().timestamp())}"

            budget = Budget(
                id=budget_id,
                service_name=service_name,
                monthly_limit=monthly_limit,
                alert_threshold_percent=alert_threshold_percent,
                currency="USD",
            )

            self.budgets[service_name] = budget

            self._notify_callbacks({
                "event": "budget_set",
                "service": service_name,
                "limit": monthly_limit,
            })

            return budget

    def get_budget(self, service_name: str) -> Optional[Budget]:
        """Get budget for service"""
        with self.lock:
            return self.budgets.get(service_name)

    def _check_budget_alert(self, service_name: str) -> None:
        """Check if service budget alert should fire"""
        budget = self.budgets.get(service_name)
        if not budget or not budget.is_active:
            return

        # Get current month costs
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        costs = self.get_service_costs(service_name, days=(now - month_start).days + 1)
        spent = costs.total_cost
        percent_spent = (spent / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0

        if percent_spent >= budget.alert_threshold_percent:
            self._notify_callbacks({
                "event": "budget_alert",
                "service": service_name,
                "spent": spent,
                "limit": budget.monthly_limit,
                "percent_spent": percent_spent,
            })

    def forecast_costs(self, service_name: str, days_ahead: int = 30) -> Optional[CostForecast]:
        """Forecast future costs"""
        with self.lock:
            # Get historical data
            cutoff = datetime.now() - timedelta(days=30)
            entries = [
                e for e in self.cost_entries
                if e.service_name == service_name and e.timestamp >= cutoff
            ]

            if len(entries) < 5:
                return None

            # Simple average-based forecast
            daily_costs = defaultdict(float)
            for entry in entries:
                day_key = entry.timestamp.date().isoformat()
                daily_costs[day_key] += entry.cost_amount

            if not daily_costs:
                return None

            avg_daily_cost = statistics.mean(daily_costs.values())
            forecast_date = datetime.now() + timedelta(days=days_ahead)
            predicted_cost = avg_daily_cost * days_ahead

            # Simple confidence interval (±20%)
            confidence_lower = predicted_cost * 0.8
            confidence_upper = predicted_cost * 1.2

            # Determine trend (simplified)
            sorted_days = sorted(daily_costs.items())
            if len(sorted_days) > 2:
                recent_avg = statistics.mean([v for _, v in sorted_days[-7:]])
                earlier_avg = statistics.mean([v for _, v in sorted_days[:7]])
                trend = "up" if recent_avg > earlier_avg else "down" if recent_avg < earlier_avg else "stable"
            else:
                trend = "stable"

            return CostForecast(
                service_name=service_name,
                forecast_date=forecast_date,
                predicted_cost=predicted_cost,
                confidence_interval_lower=confidence_lower,
                confidence_interval_upper=confidence_upper,
                trend_direction=trend,
                method="moving_average",
            )

    def get_cost_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        with self.lock:
            total_costs = self.get_total_costs(days)
            total = sum(total_costs.values())

            service_breakdowns = {
                service: self.get_service_costs(service, days).to_dict()
                for service in total_costs.keys()
            }

            forecasts = {
                service: self.forecast_costs(service).to_dict()
                for service in total_costs.keys()
                if self.forecast_costs(service)
            }

            return {
                "period_days": days,
                "total_cost": total,
                "generated_at": datetime.now().isoformat(),
                "cost_by_service": total_costs,
                "service_breakdowns": service_breakdowns,
                "forecasts": forecasts,
                "budgets": {
                    name: budget.to_dict()
                    for name, budget in self.budgets.items()
                },
            }

    def register_callback(self, callback: Callable) -> None:
        """Register callback for cost events"""
        with self.lock:
            self.callbacks.append(callback)

    def _notify_callbacks(self, event: Dict[str, Any]) -> None:
        """Notify callbacks"""
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in cost callback: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self.lock:
            total_entries = len(self.cost_entries)
            total_cost = sum(e.cost_amount for e in self.cost_entries)
            services = set(e.service_name for e in self.cost_entries)

            return {
                "total_cost_entries": total_entries,
                "total_cost": total_cost,
                "services_tracked": len(services),
                "active_budgets": sum(1 for b in self.budgets.values() if b.is_active),
                "attribution_model": self.attribution_model.value,
            }


# Global singleton
_cost_service = None


def get_cost_attribution_service(
    model: AttributionModel = AttributionModel.TIME_BASED,
) -> CostAttributionService:
    """Get or create cost attribution service singleton"""
    global _cost_service
    if _cost_service is None:
        _cost_service = CostAttributionService(model)
    return _cost_service
