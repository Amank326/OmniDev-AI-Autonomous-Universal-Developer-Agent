"""
Phase 24: Real-time Metrics Service
Live metric calculations with streaming aggregations and incremental updates
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json
import uuid


class MetricStatus(Enum):
    """Metric calculation status"""
    CALCULATING = "calculating"
    READY = "ready"
    STALE = "stale"
    ERROR = "error"


@dataclass
class MetricValue:
    """Represents a metric value at a point in time"""
    metric_id: str
    value: float
    timestamp: datetime
    dimension_values: Dict[str, Any] = field(default_factory=dict)
    calculation_time_ms: float = 0.0
    status: MetricStatus = MetricStatus.READY


@dataclass
class MetricCache:
    """Cache for metric calculations"""
    metric_id: str
    cached_value: float
    cached_at: datetime
    expires_at: datetime
    is_valid: bool = True
    hit_count: int = 0
    miss_count: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.expires_at


@dataclass
class MetricDelta:
    """Represents change in metric value"""
    metric_id: str
    previous_value: float
    current_value: float
    delta_absolute: float
    delta_percent: float
    timestamp: datetime
    dimension_values: Dict[str, Any] = field(default_factory=dict)


class RealtimeMetricsService:
    """
    Real-time metrics service
    Calculates metrics from streaming data with caching and incremental updates
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.streaming_metrics: Dict[str, Dict] = {}
        self.metric_values: Dict[str, MetricValue] = {}
        self.metric_cache: Dict[str, MetricCache] = {}
        self.metric_history: Dict[str, List[MetricValue]] = defaultdict(list)
        self.metric_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.metric_calculations: Dict[str, Callable] = {}
        self.delta_threshold = 0.01  # 1% threshold
        self.cache_ttl_seconds = 300  # 5 minutes

    # ========================================================================
    # METRIC CONFIGURATION
    # ========================================================================

    def create_streaming_metric(
        self,
        metric_name: str,
        metric_type: str,  # simple, calculated, composite, streaming
        calculation_func: Callable,
        aggregation_window_seconds: int = 60,
        cache_ttl_seconds: int = None,
        dimensions: List[str] = None,
        metadata: Dict = None,
    ) -> Dict:
        """
        Create streaming metric
        
        Args:
            metric_name: Metric name
            metric_type: Type of metric
            calculation_func: Function to calculate metric value
            aggregation_window_seconds: Window for aggregation
            cache_ttl_seconds: Cache TTL in seconds
            dimensions: Dimension names for breakdowns
            metadata: Metadata dict
        
        Returns:
            Metric configuration dict
        """
        metric_id = str(uuid.uuid4())

        metric_config = {
            "metric_id": metric_id,
            "name": metric_name,
            "type": metric_type,
            "aggregation_window_seconds": aggregation_window_seconds,
            "cache_ttl_seconds": cache_ttl_seconds or self.cache_ttl_seconds,
            "dimensions": dimensions or [],
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
        }

        self.streaming_metrics[metric_id] = metric_config
        self.metric_calculations[metric_id] = calculation_func
        self.metric_history[metric_id] = []

        return metric_config

    def get_metric_config(self, metric_id: str) -> Optional[Dict]:
        """Get metric configuration"""
        return self.streaming_metrics.get(metric_id)

    # ========================================================================
    # METRIC CALCULATION
    # ========================================================================

    def calculate_streaming_metric(
        self,
        metric_id: str,
        event_data: List[Dict],
        dimension_values: Dict[str, Any] = None,
    ) -> Optional[MetricValue]:
        """
        Calculate metric value from streaming events
        
        Args:
            metric_id: Metric ID
            event_data: List of event data dicts
            dimension_values: Dimension breakdown values
        
        Returns:
            MetricValue or None if calculation failed
        """
        if metric_id not in self.metric_calculations:
            return None

        try:
            start_time = datetime.utcnow()
            calc_func = self.metric_calculations[metric_id]
            value = calc_func(event_data)
            end_time = datetime.utcnow()
            calc_time = (end_time - start_time).total_seconds() * 1000

            metric_value = MetricValue(
                metric_id=metric_id,
                value=value,
                timestamp=datetime.utcnow(),
                dimension_values=dimension_values or {},
                calculation_time_ms=calc_time,
                status=MetricStatus.READY,
            )

            return metric_value
        except Exception:
            return None

    def update_metric(
        self,
        metric_id: str,
        value: float,
        dimension_values: Dict[str, Any] = None,
    ) -> bool:
        """
        Update metric with new value
        
        Args:
            metric_id: Metric ID
            value: New metric value
            dimension_values: Dimension values
        
        Returns:
            Success status
        """
        if metric_id not in self.streaming_metrics:
            return False

        metric_value = MetricValue(
            metric_id=metric_id,
            value=value,
            timestamp=datetime.utcnow(),
            dimension_values=dimension_values or {},
            status=MetricStatus.READY,
        )

        self.metric_values[metric_id] = metric_value
        self.metric_history[metric_id].append(metric_value)

        # Notify subscribers
        self._notify_subscribers(metric_id, metric_value)

        return True

    def get_metric_value(self, metric_id: str) -> Optional[MetricValue]:
        """Get latest metric value"""
        return self.metric_values.get(metric_id)

    # ========================================================================
    # INCREMENTAL UPDATES & DELTA DELIVERY
    # ========================================================================

    def track_metric_change(self, metric_id: str) -> Optional[MetricDelta]:
        """
        Track change in metric value
        
        Args:
            metric_id: Metric ID
        
        Returns:
            MetricDelta with previous/current values
        """
        if metric_id not in self.metric_values:
            return None

        current_value = self.metric_values[metric_id]
        metric_history = self.metric_history[metric_id]

        if len(metric_history) < 2:
            return None

        previous_value = metric_history[-2]
        delta_abs = current_value.value - previous_value.value
        delta_pct = (
            (delta_abs / abs(previous_value.value)) * 100
            if previous_value.value != 0
            else 0
        )

        return MetricDelta(
            metric_id=metric_id,
            previous_value=previous_value.value,
            current_value=current_value.value,
            delta_absolute=delta_abs,
            delta_percent=delta_pct,
            timestamp=current_value.timestamp,
            dimension_values=current_value.dimension_values,
        )

    def should_publish_delta(self, metric_id: str, delta: MetricDelta) -> bool:
        """
        Check if delta should be published (exceeds threshold)
        
        Args:
            metric_id: Metric ID
            delta: MetricDelta
        
        Returns:
            True if delta exceeds threshold
        """
        return abs(delta.delta_percent) >= (self.delta_threshold * 100)

    def get_metric_deltas(
        self,
        metric_id: str,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> List[MetricDelta]:
        """
        Get metric deltas within time range
        
        Args:
            metric_id: Metric ID
            start_time: Start timestamp
            end_time: End timestamp
        
        Returns:
            List of MetricDelta objects
        """
        if metric_id not in self.metric_history:
            return []

        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if end_time is None:
            end_time = datetime.utcnow()

        history = self.metric_history[metric_id]
        filtered = [v for v in history if start_time <= v.timestamp <= end_time]
        deltas = []

        for i in range(1, len(filtered)):
            prev = filtered[i - 1]
            curr = filtered[i]
            delta_abs = curr.value - prev.value
            delta_pct = (
                (delta_abs / abs(prev.value)) * 100 if prev.value != 0 else 0
            )

            delta = MetricDelta(
                metric_id=metric_id,
                previous_value=prev.value,
                current_value=curr.value,
                delta_absolute=delta_abs,
                delta_percent=delta_pct,
                timestamp=curr.timestamp,
                dimension_values=curr.dimension_values,
            )
            deltas.append(delta)

        return deltas

    # ========================================================================
    # CACHING
    # ========================================================================

    def cache_metric_value(
        self,
        metric_id: str,
        value: float,
        ttl_seconds: int = None,
    ) -> bool:
        """
        Cache metric value
        
        Args:
            metric_id: Metric ID
            value: Value to cache
            ttl_seconds: Time to live
        
        Returns:
            Success status
        """
        ttl = ttl_seconds or self.cache_ttl_seconds
        now = datetime.utcnow()

        cache_entry = MetricCache(
            metric_id=metric_id,
            cached_value=value,
            cached_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )

        self.metric_cache[metric_id] = cache_entry

        return True

    def get_cached_metric(self, metric_id: str) -> Optional[float]:
        """
        Get metric value from cache
        
        Args:
            metric_id: Metric ID
        
        Returns:
            Cached value or None
        """
        if metric_id not in self.metric_cache:
            return None

        cache = self.metric_cache[metric_id]

        if cache.is_expired():
            cache.is_valid = False
            cache.miss_count += 1
            return None

        cache.hit_count += 1

        return cache.cached_value

    def invalidate_cache(self, metric_id: str) -> bool:
        """
        Invalidate metric cache
        
        Args:
            metric_id: Metric ID
        
        Returns:
            Success status
        """
        if metric_id not in self.metric_cache:
            return False

        self.metric_cache[metric_id].is_valid = False

        return True

    def get_cache_stats(self, metric_id: str) -> Optional[Dict]:
        """Get cache statistics for metric"""
        if metric_id not in self.metric_cache:
            return None

        cache = self.metric_cache[metric_id]
        total_requests = cache.hit_count + cache.miss_count
        hit_rate = (
            (cache.hit_count / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "metric_id": metric_id,
            "cached_value": cache.cached_value,
            "cached_at": cache.cached_at.isoformat(),
            "expires_at": cache.expires_at.isoformat(),
            "is_valid": cache.is_valid,
            "hit_count": cache.hit_count,
            "miss_count": cache.miss_count,
            "hit_rate_percent": hit_rate,
        }

    # ========================================================================
    # SUBSCRIPTIONS & NOTIFICATIONS
    # ========================================================================

    def subscribe_to_metric(
        self,
        metric_id: str,
        subscriber: Callable,
    ) -> bool:
        """
        Subscribe to metric updates
        
        Args:
            metric_id: Metric ID
            subscriber: Callback function for updates
        
        Returns:
            Success status
        """
        if metric_id not in self.streaming_metrics:
            return False

        self.metric_subscribers[metric_id].append(subscriber)

        return True

    def unsubscribe_from_metric(
        self,
        metric_id: str,
        subscriber: Callable,
    ) -> bool:
        """Unsubscribe from metric updates"""
        if metric_id not in self.metric_subscribers:
            return False

        try:
            self.metric_subscribers[metric_id].remove(subscriber)
            return True
        except ValueError:
            return False

    def _notify_subscribers(self, metric_id: str, metric_value: MetricValue):
        """Notify all subscribers of metric update"""
        if metric_id in self.metric_subscribers:
            for subscriber in self.metric_subscribers[metric_id]:
                try:
                    subscriber(metric_value)
                except Exception:
                    pass

    def get_subscriber_count(self, metric_id: str) -> int:
        """Get number of subscribers for metric"""
        return len(self.metric_subscribers.get(metric_id, []))

    # ========================================================================
    # METRIC HISTORY & TRENDS
    # ========================================================================

    def get_metric_history(
        self,
        metric_id: str,
        limit: int = 100,
    ) -> List[MetricValue]:
        """
        Get metric value history
        
        Args:
            metric_id: Metric ID
            limit: Maximum number of values
        
        Returns:
            List of MetricValues
        """
        if metric_id not in self.metric_history:
            return []

        return self.metric_history[metric_id][-limit:]

    def calculate_metric_trend(
        self,
        metric_id: str,
        window_size: int = 10,
    ) -> Optional[str]:
        """
        Calculate metric trend
        
        Args:
            metric_id: Metric ID
            window_size: Number of values for trend
        
        Returns:
            Trend direction: "increasing", "decreasing", "stable"
        """
        history = self.get_metric_history(metric_id, limit=window_size)

        if len(history) < 2:
            return None

        values = [v.value for v in history]
        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
        decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1])

        if increases > decreases * 1.5:
            return "increasing"
        elif decreases > increases * 1.5:
            return "decreasing"
        else:
            return "stable"

    def get_metric_statistics(self, metric_id: str) -> Optional[Dict]:
        """
        Get metric statistics
        
        Args:
            metric_id: Metric ID
        
        Returns:
            Statistics dict with min, max, avg, stddev
        """
        history = self.get_metric_history(metric_id, limit=1000)

        if not history:
            return None

        values = [v.value for v in history]
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)

        # Calculate standard deviation
        variance = sum((x - avg_val) ** 2 for x in values) / len(values)
        stddev = variance ** 0.5

        return {
            "metric_id": metric_id,
            "sample_count": len(values),
            "min_value": min_val,
            "max_value": max_val,
            "avg_value": avg_val,
            "stddev": stddev,
        }

    # ========================================================================
    # STREAMING AGGREGATIONS
    # ========================================================================

    def aggregate_metric_by_dimension(
        self,
        metric_id: str,
        dimension: str,
    ) -> Dict[str, float]:
        """
        Aggregate metric values by dimension
        
        Args:
            metric_id: Metric ID
            dimension: Dimension name
        
        Returns:
            Dict mapping dimension values to aggregated metrics
        """
        history = self.get_metric_history(metric_id, limit=1000)
        aggregations = defaultdict(list)

        for value in history:
            dim_value = value.dimension_values.get(dimension)
            if dim_value is not None:
                aggregations[dim_value].append(value.value)

        return {
            key: sum(values) / len(values) for key, values in aggregations.items()
        }

    def compare_metric_periods(
        self,
        metric_id: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime,
    ) -> Optional[Dict]:
        """
        Compare metric values across two time periods
        
        Args:
            metric_id: Metric ID
            period1_start: Period 1 start
            period1_end: Period 1 end
            period2_start: Period 2 start
            period2_end: Period 2 end
        
        Returns:
            Comparison dict with values and change percent
        """
        history = self.get_metric_history(metric_id, limit=10000)

        period1_values = [
            v.value for v in history
            if period1_start <= v.timestamp <= period1_end
        ]
        period2_values = [
            v.value for v in history
            if period2_start <= v.timestamp <= period2_end
        ]

        if not period1_values or not period2_values:
            return None

        p1_avg = sum(period1_values) / len(period1_values)
        p2_avg = sum(period2_values) / len(period2_values)
        change_pct = ((p2_avg - p1_avg) / p1_avg * 100) if p1_avg != 0 else 0

        return {
            "period1_avg": p1_avg,
            "period2_avg": p2_avg,
            "change_percent": change_pct,
        }

    # ========================================================================
    # MANAGEMENT
    # ========================================================================

    def get_all_metrics(self) -> List[Dict]:
        """Get all streaming metrics"""
        return list(self.streaming_metrics.values())

    def delete_metric(self, metric_id: str) -> bool:
        """Delete streaming metric"""
        if metric_id not in self.streaming_metrics:
            return False

        del self.streaming_metrics[metric_id]
        del self.metric_calculations[metric_id]
        del self.metric_history[metric_id]

        if metric_id in self.metric_values:
            del self.metric_values[metric_id]
        if metric_id in self.metric_cache:
            del self.metric_cache[metric_id]

        return True
