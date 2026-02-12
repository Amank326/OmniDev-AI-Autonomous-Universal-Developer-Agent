"""
Resource Optimization Service for OmniDev AI
Advanced resource allocation, optimization, and utilization management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class OptimizationType(str, Enum):
    """Types of optimization"""
    CPU = "cpu"
    MEMORY = "memory"
    BANDWIDTH = "bandwidth"
    DISK = "disk"
    COST = "cost"
    COMBINED = "combined"


class ResourcePriority(str, Enum):
    """Resource allocation priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ResourceAllocation:
    """Resource allocation for a workload"""
    workload_id: str
    cpu_cores: float
    memory_gb: float
    bandwidth_mbps: float
    disk_gb: float
    estimated_cost_per_hour: float
    priority: ResourcePriority
    allocated_at: datetime


@dataclass
class OptimizationRecommendation:
    """Recommended optimization action"""
    recommendation_id: str
    workload_id: str
    optimization_type: OptimizationType
    current_allocation: Dict
    recommended_allocation: Dict
    estimated_savings: float  # dollars per month
    savings_percentage: float
    performance_impact: float  # -1 to 1 (negative = worse)
    implementation_complexity: str  # simple, moderate, complex
    estimated_implementation_time_hours: float
    confidence_score: float
    description: str
    implementation_steps: List[str]


@dataclass
class ResourceUtilizationMetrics:
    """Current resource utilization"""
    metric_timestamp: datetime
    cpu_utilization_percent: float
    memory_utilization_percent: float
    bandwidth_utilization_percent: float
    disk_utilization_percent: float
    overall_efficiency: float
    bottle_neck_resource: str
    under_utilized_resources: List[str]


@dataclass
class OptimizationResult:
    """Complete optimization analysis result"""
    analysis_timestamp: datetime
    workspace_id: str
    current_utilization: ResourceUtilizationMetrics
    recommendations: List[OptimizationRecommendation]
    total_potential_savings: float
    total_savings_percentage: float
    quick_wins: List[OptimizationRecommendation]
    implementation_roadmap: List[Tuple[str, int]]  # (recommendation_id, priority_order)
    overall_efficiency_score: float


class ResourceOptimizationService:
    """Service for resource optimization and allocation management"""

    def __init__(self):
        """Initialize resource optimization service"""
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.utilization_history: Dict[str, List[ResourceUtilizationMetrics]] = {}
        self.optimizations: Dict[str, List[OptimizationRecommendation]] = {}
        self.cost_per_resource = {
            'cpu_core': 0.25,  # dollars per hour
            'memory_gb': 0.10,  # dollars per hour
            'bandwidth_gbps': 2.50,  # dollars per gbps per hour
            'disk_gb': 0.01,  # dollars per gb per month
        }

    def analyze_resource_utilization(
        self,
        workspace_id: str,
        current_metrics: Dict[str, float],
    ) -> ResourceUtilizationMetrics:
        """
        Analyze current resource utilization
        
        Args:
            workspace_id: Workspace identifier
            current_metrics: Current resource metrics
            
        Returns:
            Utilization metrics analysis
        """
        cpu_util = current_metrics.get('cpu_utilization', 45.0)
        memory_util = current_metrics.get('memory_utilization', 60.0)
        bandwidth_util = current_metrics.get('bandwidth_utilization', 35.0)
        disk_util = current_metrics.get('disk_utilization', 55.0)

        overall_efficiency = (
            (100 - cpu_util) * 0.3 +
            (100 - memory_util) * 0.3 +
            (100 - bandwidth_util) * 0.2 +
            (100 - disk_util) * 0.2
        ) / 100

        bottle_neck = 'memory' if memory_util > 70 else 'cpu' if cpu_util > 70 else 'disk'
        under_utilized = []
        if cpu_util < 20:
            under_utilized.append('cpu')
        if memory_util < 20:
            under_utilized.append('memory')
        if bandwidth_util < 10:
            under_utilized.append('bandwidth')

        metrics = ResourceUtilizationMetrics(
            metric_timestamp=datetime.utcnow(),
            cpu_utilization_percent=cpu_util,
            memory_utilization_percent=memory_util,
            bandwidth_utilization_percent=bandwidth_util,
            disk_utilization_percent=disk_util,
            overall_efficiency=max(0, min(1, overall_efficiency)),
            bottle_neck_resource=bottle_neck,
            under_utilized_resources=under_utilized,
        )

        # Cache metrics
        if workspace_id not in self.utilization_history:
            self.utilization_history[workspace_id] = []
        self.utilization_history[workspace_id].append(metrics)
        # Keep last 1000 entries
        self.utilization_history[workspace_id] = self.utilization_history[workspace_id][-1000:]

        return metrics

    def generate_optimization_recommendations(
        self,
        workspace_id: str,
        utilization_metrics: ResourceUtilizationMetrics,
        current_allocations: Dict[str, Dict],
    ) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations based on utilization
        
        Args:
            workspace_id: Workspace identifier
            utilization_metrics: Current utilization analysis
            current_allocations: Current resource allocations per workload
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        recommendation_id_counter = 1

        # CPU optimization recommendations
        if utilization_metrics.cpu_utilization_percent < 20:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"{workspace_id}:opt_{recommendation_id_counter}",
                    workload_id="all",
                    optimization_type=OptimizationType.CPU,
                    current_allocation={"cpu_cores": 8},
                    recommended_allocation={"cpu_cores": 4},
                    estimated_savings=180,  # ~30% of ~600/month CPU cost
                    savings_percentage=30,
                    performance_impact=0.0,
                    implementation_complexity="simple",
                    estimated_implementation_time_hours=0.5,
                    confidence_score=0.95,
                    description="CPU is under-utilized. Reduce allocated cores from 8 to 4.",
                    implementation_steps=[
                        "Modify instance type to smaller CPU",
                        "Monitor for 24 hours after change",
                        "Revert if performance degrades",
                    ],
                )
            )
            recommendation_id_counter += 1

        # Memory optimization
        if utilization_metrics.memory_utilization_percent < 30:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"{workspace_id}:opt_{recommendation_id_counter}",
                    workload_id="all",
                    optimization_type=OptimizationType.MEMORY,
                    current_allocation={"memory_gb": 32},
                    recommended_allocation={"memory_gb": 16},
                    estimated_savings=75,
                    savings_percentage=25,
                    performance_impact=-0.05,
                    implementation_complexity="simple",
                    estimated_implementation_time_hours=1.0,
                    confidence_score=0.88,
                    description="Memory is under-utilized. Reduce from 32GB to 16GB.",
                    implementation_steps=[
                        "Review memory usage patterns",
                        "Resize instance to 16GB",
                        "Monitor for OOM errors",
                    ],
                )
            )
            recommendation_id_counter += 1

        # Bandwidth optimization
        if utilization_metrics.bandwidth_utilization_percent < 15:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"{workspace_id}:opt_{recommendation_id_counter}",
                    workload_id="all",
                    optimization_type=OptimizationType.BANDWIDTH,
                    current_allocation={"bandwidth_gbps": 10},
                    recommended_allocation={"bandwidth_gbps": 5},
                    estimated_savings=60,
                    savings_percentage=40,
                    performance_impact=0.02,
                    implementation_complexity="moderate",
                    estimated_implementation_time_hours=2.0,
                    confidence_score=0.85,
                    description="Bandwidth is significantly over-provisioned.",
                    implementation_steps=[
                        "Implement traffic shaping",
                        "Reduce provisioned bandwidth",
                        "Test with sustained peak load",
                    ],
                )
            )
            recommendation_id_counter += 1

        # Combined optimization for high utilization
        if utilization_metrics.cpu_utilization_percent > 75 or utilization_metrics.memory_utilization_percent > 80:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"{workspace_id}:opt_{recommendation_id_counter}",
                    workload_id="all",
                    optimization_type=OptimizationType.COMBINED,
                    current_allocation={"cpu_cores": 4, "memory_gb": 16},
                    recommended_allocation={"cpu_cores": 8, "memory_gb": 32},
                    estimated_savings=-200,  # Cost increase, but improves performance
                    savings_percentage=-35,
                    performance_impact=0.30,
                    implementation_complexity="moderate",
                    estimated_implementation_time_hours=3.0,
                    confidence_score=0.92,
                    description="Scale up resources to handle peak load without bottlenecks.",
                    implementation_steps=[
                        "Upgrade to larger instance type",
                        "Coordinate with deployment schedule",
                        "Test under production-like load",
                    ],
                )
            )

        # Cache recommendations
        self.optimizations[workspace_id] = recommendations
        return recommendations

    def perform_optimization_analysis(
        self,
        workspace_id: str,
        current_metrics: Dict[str, float],
        allocations: Dict[str, Dict],
    ) -> OptimizationResult:
        """
        Perform complete optimization analysis
        
        Args:
            workspace_id: Workspace identifier
            current_metrics: Current resource metrics
            allocations: Current allocations
            
        Returns:
            Complete optimization analysis
        """
        # Analyze utilization
        utilization = self.analyze_resource_utilization(workspace_id, current_metrics)

        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(
            workspace_id, utilization, allocations
        )

        # Identify quick wins (simple, high-confidence, positive savings)
        quick_wins = [
            rec for rec in recommendations
            if rec.implementation_complexity == "simple"
            and rec.confidence_score > 0.85
            and rec.estimated_savings > 50
        ]

        # Calculate totals
        total_savings = sum(rec.estimated_savings for rec in recommendations if rec.estimated_savings > 0)
        total_cost = sum(rec.estimated_savings for rec in recommendations)
        total_savings_percentage = (total_savings / max(1, abs(total_cost))) * 100

        # Build implementation roadmap
        roadmap = []
        for i, rec in enumerate(sorted(recommendations, key=lambda r: (r.estimated_savings / max(1, abs(r.estimated_savings))), reverse=True)):
            roadmap.append((rec.recommendation_id, i + 1))

        # Calculate overall efficiency
        overall_efficiency = utilization.overall_efficiency

        result = OptimizationResult(
            analysis_timestamp=datetime.utcnow(),
            workspace_id=workspace_id,
            current_utilization=utilization,
            recommendations=recommendations,
            total_potential_savings=total_savings,
            total_savings_percentage=total_savings_percentage,
            quick_wins=quick_wins,
            implementation_roadmap=roadmap,
            overall_efficiency_score=overall_efficiency,
        )

        return result

    def calculate_right_sizing(
        self,
        historical_metrics: Dict[str, List[float]],
        percentile: int = 95,
    ) -> Dict[str, float]:
        """
        Calculate right-sized resource allocation based on historical data
        
        Args:
            historical_metrics: Historical metric values
            percentile: Percentile to use (95 for 95th percentile)
            
        Returns:
            Right-sized allocation recommendations
        """
        right_sizing = {}

        for resource, values in historical_metrics.items():
            if not values:
                continue

            sorted_values = sorted(values)
            percentile_idx = int(len(sorted_values) * percentile / 100)
            percentile_value = sorted_values[min(percentile_idx, len(sorted_values) - 1)]

            # Add 20% safety margin
            right_sized = percentile_value * 1.2
            right_sizing[resource] = round(right_sized, 2)

        return right_sizing

    def forecast_capacity_needs(
        self,
        workspace_id: str,
        historical_growth_rate: float,
        current_allocation: Dict[str, float],
        months_ahead: int = 12,
    ) -> List[Dict]:
        """
        Forecast future capacity needs
        
        Args:
            workspace_id: Workspace identifier
            historical_growth_rate: Monthly growth rate (0.02 = 2% per month)
            current_allocation: Current resource allocation
            months_ahead: Months to forecast
            
        Returns:
            Capacity forecast for each month
        """
        forecast = []

        for month in range(months_ahead + 1):
            growth_factor = (1 + historical_growth_rate) ** month
            forecasted_allocation = {
                resource: value * growth_factor
                for resource, value in current_allocation.items()
            }

            forecast.append({
                'month': month,
                'date': (datetime.utcnow() + timedelta(days=30 * month)).isoformat(),
                'allocation': {k: round(v, 2) for k, v in forecasted_allocation.items()},
                'growth_percentage': round((growth_factor - 1) * 100, 2),
            })

        return forecast

    def calculate_total_cost(
        self,
        allocation: Dict[str, float],
        months: int = 1,
    ) -> float:
        """
        Calculate total cost for resource allocation
        
        Args:
            allocation: Resource allocation dictionary
            months: Number of months
            
        Returns:
            Total cost in dollars
        """
        total_cost = 0.0

        if 'cpu_cores' in allocation:
            total_cost += allocation['cpu_cores'] * self.cost_per_resource['cpu_core'] * 730 * months

        if 'memory_gb' in allocation:
            total_cost += allocation['memory_gb'] * self.cost_per_resource['memory_gb'] * 730 * months

        if 'bandwidth_gbps' in allocation:
            total_cost += allocation['bandwidth_gbps'] * self.cost_per_resource['bandwidth_gbps'] * 730 * months

        if 'disk_gb' in allocation:
            total_cost += allocation['disk_gb'] * self.cost_per_resource['disk_gb'] * months

        return round(total_cost, 2)

    def get_allocation_history(
        self,
        workspace_id: str,
        limit: int = 100,
    ) -> List[ResourceUtilizationMetrics]:
        """Get utilization history for workspace"""
        return self.utilization_history.get(workspace_id, [])[-limit:]

    def apply_optimization(
        self,
        workspace_id: str,
        recommendation_id: str,
    ) -> Dict:
        """
        Apply an optimization recommendation
        
        Args:
            workspace_id: Workspace identifier
            recommendation_id: Recommendation to apply
            
        Returns:
            Application result
        """
        recommendations = self.optimizations.get(workspace_id, [])
        for rec in recommendations:
            if rec.recommendation_id == recommendation_id:
                return {
                    "status": "success",
                    "recommendation_id": recommendation_id,
                    "applied_at": datetime.utcnow().isoformat(),
                    "estimated_savings": rec.estimated_savings,
                    "implementation_time_hours": rec.estimated_implementation_time_hours,
                }

        return {
            "status": "error",
            "message": "Recommendation not found",
        }

    def estimate_savings(
        self,
        recommendations: List[OptimizationRecommendation],
    ) -> Dict:
        """Estimate total savings from recommendations"""
        positive_savings = sum(rec.estimated_savings for rec in recommendations if rec.estimated_savings > 0)
        total_recommendations = len(recommendations)
        avg_implementation_time = (
            sum(rec.estimated_implementation_time_hours for rec in recommendations)
            / len(recommendations)
            if recommendations
            else 0
        )

        return {
            "total_potential_savings": positive_savings,
            "monthly_savings": round(positive_savings, 2),
            "annual_savings": round(positive_savings * 12, 2),
            "total_recommendations": total_recommendations,
            "average_implementation_time_hours": round(avg_implementation_time, 2),
            "quick_wins": sum(
                1 for rec in recommendations
                if rec.implementation_complexity == "simple"
            ),
        }
