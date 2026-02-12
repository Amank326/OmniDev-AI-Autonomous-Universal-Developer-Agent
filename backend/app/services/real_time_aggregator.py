"""
Real-Time Aggregator - Streaming aggregations and time-series computations
Provides windowed aggregations, rolling calculations, and dimension-based rollups
"""

import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import statistics


class AggregationType(Enum):
    """Aggregation types"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    STDDEV = "stddev"
    P50 = "p50"
    P95 = "p95"
    P99 = "p99"
    DISTINCT_COUNT = "distinct_count"


class TimeWindow(Enum):
    """Time window sizes"""
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    FIFTEEN_MINUTES = 900
    ONE_HOUR = 3600
    ONE_DAY = 86400


@dataclass
class AggregationResult:
    """Result of aggregation"""
    aggregation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    aggregation_type: AggregationType = AggregationType.SUM
    value: Any = None
    window_start: float = 0.0
    window_end: float = 0.0
    sample_count: int = 0
    dimensions: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    is_partial: bool = False  # Incomplete window


@dataclass
class RollingMetric:
    """Rolling window metric"""
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    window_size: int = 60  # seconds
    values: deque = field(default_factory=deque)
    timestamps: deque = field(default_factory=deque)
    created_at: float = field(default_factory=time.time)
    
    def add_value(self, value: float, timestamp: float) -> None:
        """Add value to rolling window"""
        cutoff = timestamp - self.window_size
        
        # Remove expired values
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()
            self.values.popleft()
        
        self.values.append(value)
        self.timestamps.append(timestamp)
    
    def get_values(self) -> List[float]:
        """Get all values in window"""
        return list(self.values)
    
    def calculate(self, agg_type: AggregationType) -> Optional[float]:
        """Calculate aggregation"""
        if not self.values:
            return None
        
        values = list(self.values)
        
        if agg_type == AggregationType.COUNT:
            return float(len(values))
        elif agg_type == AggregationType.SUM:
            return sum(values)
        elif agg_type == AggregationType.AVG:
            return statistics.mean(values)
        elif agg_type == AggregationType.MIN:
            return min(values)
        elif agg_type == AggregationType.MAX:
            return max(values)
        elif agg_type == AggregationType.STDDEV:
            return statistics.stdev(values) if len(values) > 1 else 0.0
        elif agg_type == AggregationType.P50:
            sorted_vals = sorted(values)
            return sorted_vals[len(sorted_vals) // 2]
        elif agg_type == AggregationType.P95:
            sorted_vals = sorted(values)
            return sorted_vals[int(len(sorted_vals) * 0.95)]
        elif agg_type == AggregationType.P99:
            sorted_vals = sorted(values)
            return sorted_vals[int(len(sorted_vals) * 0.99)]
        
        return None


@dataclass
class DimensionRollup:
    """Dimension-based rollup configuration"""
    rollup_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    dimensions: List[str] = field(default_factory=list)  # Fields to group by
    aggregations: List[AggregationType] = field(default_factory=list)
    time_window: TimeWindow = TimeWindow.ONE_MINUTE
    retention_hours: int = 24


@dataclass
class AggregatorStatistics:
    """Aggregator statistics"""
    total_metrics_processed: int = 0
    total_aggregations: int = 0
    total_dimensions_created: int = 0
    avg_aggregation_latency_ms: float = 0.0
    active_rolling_metrics: int = 0
    active_rollups: int = 0


class RealTimeAggregator:
    """Real-time metric aggregation engine"""
    
    def __init__(self):
        self.rolling_metrics: Dict[str, RollingMetric] = {}
        self.windows: Dict[str, deque] = defaultdict(deque)  # metric_name -> window values
        self.rollups: Dict[str, DimensionRollup] = {}
        self.rollup_values: Dict[str, Dict[str, Any]] = defaultdict(dict)  # rollup_id -> dimension_key -> value
        self.aggregation_results: Dict[str, List[AggregationResult]] = defaultdict(list)
        self.stats = AggregatorStatistics()
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        self.output_handlers: Dict[str, Callable] = {}
    
    def add_metric(self, metric_name: str, value: float, timestamp: float,
                  dimensions: Optional[Dict[str, str]] = None) -> None:
        """Add metric for aggregation"""
        with self.lock:
            self.stats.total_metrics_processed += 1
        
        dimensions = dimensions or {}
        
        # Add to rolling metrics
        rolling_key = f"{metric_name}:rolling"
        if rolling_key not in self.rolling_metrics:
            self.rolling_metrics[rolling_key] = RollingMetric(
                metric_name=metric_name,
                window_size=60  # Default 1 minute
            )
        
        self.rolling_metrics[rolling_key].add_value(value, timestamp)
        
        # Add to windows for other aggregations
        window_key = f"{metric_name}"
        with self.lock:
            if len(self.windows[window_key]) >= 10000:
                self.windows[window_key].popleft()
            self.windows[window_key].append((timestamp, value, dimensions))
    
    def create_rolling_metric(self, metric_name: str, window_size_seconds: int) -> str:
        """Create rolling metric"""
        rolling_key = f"{metric_name}:rolling:{window_size_seconds}"
        
        with self.lock:
            if rolling_key not in self.rolling_metrics:
                self.rolling_metrics[rolling_key] = RollingMetric(
                    metric_name=metric_name,
                    window_size=window_size_seconds
                )
                self.stats.active_rolling_metrics += 1
        
        return rolling_key
    
    def get_rolling_metric(self, rolling_key: str, agg_type: AggregationType) -> Optional[float]:
        """Get rolling metric value"""
        with self.lock:
            if rolling_key not in self.rolling_metrics:
                return None
            
            metric = self.rolling_metrics[rolling_key]
            return metric.calculate(agg_type)
    
    def aggregate_window(self, metric_name: str, window_start: float, window_end: float,
                        agg_types: List[AggregationType]) -> List[AggregationResult]:
        """Aggregate metric values in time window"""
        with self.lock:
            window_key = f"{metric_name}"
            values = [
                value for ts, value, dims in self.windows[window_key]
                if window_start <= ts < window_end
            ]
        
        results = []
        
        if not values:
            return results
        
        for agg_type in agg_types:
            result = self._calculate_aggregation(
                metric_name,
                values,
                agg_type,
                window_start,
                window_end
            )
            
            if result:
                results.append(result)
                self.stats.total_aggregations += 1
        
        # Trigger output handlers
        for handler in self.output_handlers.values():
            for result in results:
                try:
                    handler(result)
                except Exception:
                    pass
        
        return results
    
    def _calculate_aggregation(self, metric_name: str, values: List[float],
                              agg_type: AggregationType,
                              window_start: float, window_end: float) -> Optional[AggregationResult]:
        """Calculate single aggregation"""
        if not values:
            return None
        
        if agg_type == AggregationType.COUNT:
            result_value = len(values)
        elif agg_type == AggregationType.SUM:
            result_value = sum(values)
        elif agg_type == AggregationType.AVG:
            result_value = statistics.mean(values)
        elif agg_type == AggregationType.MIN:
            result_value = min(values)
        elif agg_type == AggregationType.MAX:
            result_value = max(values)
        elif agg_type == AggregationType.STDDEV:
            result_value = statistics.stdev(values) if len(values) > 1 else 0.0
        elif agg_type == AggregationType.P50:
            sorted_vals = sorted(values)
            result_value = sorted_vals[len(sorted_vals) // 2]
        elif agg_type == AggregationType.P95:
            sorted_vals = sorted(values)
            result_value = sorted_vals[int(len(sorted_vals) * 0.95)]
        elif agg_type == AggregationType.P99:
            sorted_vals = sorted(values)
            result_value = sorted_vals[int(len(sorted_vals) * 0.99)]
        else:
            return None
        
        return AggregationResult(
            metric_name=metric_name,
            aggregation_type=agg_type,
            value=result_value,
            window_start=window_start,
            window_end=window_end,
            sample_count=len(values),
        )
    
    def create_dimension_rollup(self, metric_name: str, dimensions: List[str],
                               aggregations: List[AggregationType],
                               time_window: TimeWindow) -> str:
        """Create dimension-based rollup"""
        rollup = DimensionRollup(
            metric_name=metric_name,
            dimensions=dimensions,
            aggregations=aggregations,
            time_window=time_window
        )
        
        with self.lock:
            self.rollups[rollup.rollup_id] = rollup
            self.stats.active_rollups += 1
        
        self._trigger_callback("dimension_rollup_created", rollup.rollup_id)
        return rollup.rollup_id
    
    def update_rollup_values(self, rollup_id: str, dimension_key: str, values: Dict[str, float]) -> None:
        """Update dimension rollup values"""
        with self.lock:
            self.rollup_values[rollup_id][dimension_key] = values
            self.stats.total_dimensions_created += 1
    
    def get_rollup_results(self, rollup_id: str) -> List[Dict]:
        """Get dimension rollup results"""
        with self.lock:
            if rollup_id not in self.rollup_values:
                return []
            
            results = []
            for dimension_key, values in self.rollup_values[rollup_id].items():
                results.append({
                    "dimension": dimension_key,
                    "values": values,
                    "timestamp": time.time(),
                })
            
            return results
    
    def register_output_handler(self, name: str, handler: Callable[[AggregationResult], None]) -> None:
        """Register output handler for aggregation results"""
        with self.lock:
            self.output_handlers[name] = handler
    
    def get_metric_statistics(self, metric_name: str) -> Optional[Dict]:
        """Get statistics for metric"""
        with self.lock:
            window_key = f"{metric_name}"
            if window_key not in self.windows:
                return None
            
            values = [value for _, value, _ in self.windows[window_key]]
            
            if not values:
                return None
            
            return {
                "metric": metric_name,
                "count": len(values),
                "sum": sum(values),
                "avg": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "p50": sorted(values)[len(values) // 2],
                "p95": sorted(values)[int(len(values) * 0.95)],
                "p99": sorted(values)[int(len(values) * 0.99)],
            }
    
    def cleanup_expired_windows(self, max_age_seconds: int = 3600) -> int:
        """Remove expired window data"""
        with self.lock:
            cutoff_time = time.time() - max_age_seconds
            removed_count = 0
            
            for window_key in self.windows:
                # Remove old entries
                new_window = deque(
                    (ts, val, dims) for ts, val, dims in self.windows[window_key]
                    if ts >= cutoff_time
                )
                removed_count += len(self.windows[window_key]) - len(new_window)
                self.windows[window_key] = new_window
            
            return removed_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        with self.lock:
            return {
                "total_metrics_processed": self.stats.total_metrics_processed,
                "total_aggregations": self.stats.total_aggregations,
                "total_dimensions_created": self.stats.total_dimensions_created,
                "active_rolling_metrics": self.stats.active_rolling_metrics,
                "active_rollups": len(self.rollups),
                "avg_aggregation_latency_ms": self.stats.avg_aggregation_latency_ms,
                "total_dimensions": sum(
                    len(self.rollup_values[rid]) for rid in self.rollup_values
                ),
            }
    
    def register_callback(self, callback: Callable[[str, ...], None]) -> None:
        """Register event callback"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callback(self, event_type: str, *args, **kwargs) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(event_type, *args, **kwargs)
            except Exception:
                pass


# Singleton instance
_aggregator: Optional[RealTimeAggregator] = None


def get_real_time_aggregator() -> RealTimeAggregator:
    """Get or create singleton aggregator"""
    global _aggregator
    if _aggregator is None:
        _aggregator = RealTimeAggregator()
    return _aggregator


def reset_real_time_aggregator() -> None:
    """Reset aggregator (for testing)"""
    global _aggregator
    _aggregator = None
