"""
Metrics Aggregation Service for OmniDev AI
Aggregates metrics from multiple sources for analysis and reporting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json


class AggregationType(str, Enum):
    """Types of aggregation"""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


@dataclass
class AggregatedMetric:
    """Aggregated metric result"""
    name: str
    value: float
    aggregation_type: AggregationType
    time_period_start: datetime
    time_period_end: datetime
    sample_count: int = 0
    metadata: Dict = field(default_factory=dict)


class MetricsAggregationService:
    """Service for aggregating metrics across system"""

    def __init__(self):
        """Initialize aggregation service"""
        self.aggregated_cache: Dict[str, AggregatedMetric] = {}
        self.cache_expiry: Dict[str, datetime] = {}

    def aggregate_metrics(
        self,
        metric_values: List[float],
        aggregation_type: AggregationType,
        percentile: float = 95.0,
    ) -> float:
        """
        Aggregate metric values
        
        Args:
            metric_values: List of metric values
            aggregation_type: Type of aggregation
            percentile: Percentile for percentile aggregation
            
        Returns:
            Aggregated value
        """
        if not metric_values:
            return 0.0
        
        if aggregation_type == AggregationType.SUM:
            return sum(metric_values)
        elif aggregation_type == AggregationType.AVERAGE:
            return sum(metric_values) / len(metric_values)
        elif aggregation_type == AggregationType.MIN:
            return min(metric_values)
        elif aggregation_type == AggregationType.MAX:
            return max(metric_values)
        elif aggregation_type == AggregationType.COUNT:
            return float(len(metric_values))
        elif aggregation_type == AggregationType.PERCENTILE:
            sorted_values = sorted(metric_values)
            index = int((percentile / 100.0) * len(sorted_values))
            return sorted_values[min(index, len(sorted_values) - 1)]
        
        return 0.0

    def calculate_rate_of_change(
        self,
        old_values: List[float],
        new_values: List[float],
    ) -> float:
        """Calculate rate of change between two datasets"""
        old_avg = sum(old_values) / len(old_values) if old_values else 0
        new_avg = sum(new_values) / len(new_values) if new_values else 0
        
        if old_avg == 0:
            return 0.0
        
        return ((new_avg - old_avg) / old_avg) * 100

    def calculate_percentile(
        self,
        values: List[float],
        percentile: float,
    ) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_percentile_range(
        self,
        values: List[float],
    ) -> Dict[str, float]:
        """Get common percentile values"""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        
        return {
            "p50": self.calculate_percentile(values, 50),
            "p75": self.calculate_percentile(values, 75),
            "p90": self.calculate_percentile(values, 90),
            "p95": self.calculate_percentile(values, 95),
            "p99": self.calculate_percentile(values, 99),
        }

    def aggregate_by_dimension(
        self,
        metrics: List[Dict],
        dimension: str,
        value_field: str,
        aggregation_type: AggregationType,
    ) -> Dict[str, float]:
        """
        Aggregate metrics grouped by dimension
        
        Args:
            metrics: List of metric dictionaries
            dimension: Field to group by
            value_field: Field to aggregate
            aggregation_type: Type of aggregation
            
        Returns:
            {dimension_value: aggregated_value}
        """
        grouped = defaultdict(list)
        
        for metric in metrics:
            if dimension in metric and value_field in metric:
                dim_value = metric[dimension]
                grouped[dim_value].append(metric[value_field])
        
        result = {}
        for dim_value, values in grouped.items():
            result[str(dim_value)] = self.aggregate_metrics(
                values, aggregation_type
            )
        
        return result

    def calculate_moving_average(
        self,
        values: List[float],
        window_size: int = 5,
    ) -> List[float]:
        """Calculate moving average"""
        if window_size > len(values):
            window_size = len(values)
        
        moving_averages = []
        for i in range(len(values) - window_size + 1):
            window = values[i:i + window_size]
            avg = sum(window) / len(window)
            moving_averages.append(avg)
        
        return moving_averages

    def detect_trends(
        self,
        values: List[Tuple[datetime, float]],
        window_size: int = 5,
    ) -> Dict:
        """
        Detect trend in time series data
        
        Args:
            values: List of (timestamp, value) tuples
            window_size: Window for trend calculation
            
        Returns:
            Trend analysis
        """
        if len(values) < window_size:
            return {"trend": "insufficient_data"}
        
        sorted_values = sorted(values, key=lambda x: x[0])
        value_list = [v for _, v in sorted_values]
        
        # Calculate moving averages
        ma = self.calculate_moving_average(value_list, window_size)
        
        # Determine trend direction
        if len(ma) < 2:
            trend_direction = "stable"
        elif ma[-1] > ma[0]:
            trend_direction = "increasing"
        elif ma[-1] < ma[0]:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        # Calculate trend strength
        changes = [ma[i+1] - ma[i] for i in range(len(ma) - 1)]
        avg_change = sum(changes) / len(changes) if changes else 0
        
        return {
            "trend": trend_direction,
            "avg_change": avg_change,
            "latest_value": value_list[-1],
            "first_value": value_list[0],
            "change_percent": ((value_list[-1] - value_list[0]) / value_list[0] * 100) if value_list[0] != 0 else 0,
        }

    def calculate_correlation(
        self,
        values1: List[float],
        values2: List[float],
    ) -> float:
        """Calculate Pearson correlation between two datasets"""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
        
        n = len(values1)
        mean1 = sum(values1) / n
        mean2 = sum(values2) / n
        
        numerator = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(n))
        
        variance1 = sum((x - mean1) ** 2 for x in values1)
        variance2 = sum((x - mean2) ** 2 for x in values2)
        
        denominator = (variance1 * variance2) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator

    def calculate_standard_deviation(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def normalize_values(self, values: List[float]) -> List[float]:
        """Normalize values to 0-1 range"""
        if not values:
            return []
        
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val
        
        if range_val == 0:
            return [0.5] * len(values)
        
        return [(v - min_val) / range_val for v in values]

    def get_distribution(
        self,
        values: List[float],
        bins: int = 10,
    ) -> Dict[str, int]:
        """Get distribution of values in bins"""
        if not values:
            return {}
        
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val
        
        if range_val == 0:
            return {f"{min_val}": len(values)}
        
        bin_width = range_val / bins
        distribution = defaultdict(int)
        
        for value in values:
            bin_idx = int((value - min_val) / bin_width)
            if bin_idx >= bins:
                bin_idx = bins - 1
            
            bin_start = min_val + (bin_idx * bin_width)
            bin_end = bin_start + bin_width
            bin_label = f"{bin_start:.2f}-{bin_end:.2f}"
            distribution[bin_label] += 1
        
        return dict(distribution)

    def cache_aggregation(
        self,
        key: str,
        metric: AggregatedMetric,
        ttl_seconds: int = 300,
    ) -> None:
        """Cache aggregated metric"""
        self.aggregated_cache[key] = metric
        self.cache_expiry[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    def get_cached_aggregation(self, key: str) -> Optional[AggregatedMetric]:
        """Get cached aggregation if valid"""
        if key not in self.aggregated_cache:
            return None
        
        if datetime.utcnow() > self.cache_expiry.get(key, datetime.min):
            del self.aggregated_cache[key]
            if key in self.cache_expiry:
                del self.cache_expiry[key]
            return None
        
        return self.aggregated_cache[key]

    def clear_expired_cache(self) -> int:
        """Clear expired cache entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, expiry in self.cache_expiry.items()
            if now > expiry
        ]
        
        for key in expired_keys:
            if key in self.aggregated_cache:
                del self.aggregated_cache[key]
            del self.cache_expiry[key]
        
        return len(expired_keys)

    def compare_distributions(
        self,
        values1: List[float],
        values2: List[float],
    ) -> Dict:
        """Compare two distributions"""
        return {
            "distribution1": self.get_distribution(values1),
            "distribution2": self.get_distribution(values2),
            "mean1": sum(values1) / len(values1) if values1 else 0,
            "mean2": sum(values2) / len(values2) if values2 else 0,
            "std_dev1": self.calculate_standard_deviation(values1),
            "std_dev2": self.calculate_standard_deviation(values2),
            "correlation": self.calculate_correlation(values1, values2),
        }
