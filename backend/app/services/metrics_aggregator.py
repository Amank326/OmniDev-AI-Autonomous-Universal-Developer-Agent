"""
Phase 13: Metrics Aggregator
Time-series metrics collection and aggregation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric:
    """Individual metric data point"""

    def __init__(self, name: str, metric_type: MetricType, value: float,
                 timestamp: float, labels: Dict[str, str] = None):
        self.name = name
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp
        self.labels = labels or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels,
        }


class TimeSeries:
    """Time series of metric values"""

    def __init__(self, name: str, metric_type: MetricType):
        self.name = name
        self.metric_type = metric_type
        self.values: List[Metric] = []

    def add(self, metric: Metric) -> None:
        """Add metric to series"""
        self.values.append(metric)
        # Sort by timestamp
        self.values.sort(key=lambda m: m.timestamp)

    def get_latest(self) -> Optional[Metric]:
        """Get latest metric"""
        return self.values[-1] if self.values else None

    def get_range(self, start_timestamp: float, end_timestamp: float) -> List[Metric]:
        """Get metrics in time range"""
        return [
            m for m in self.values
            if start_timestamp <= m.timestamp <= end_timestamp
        ]

    def aggregate(self, operation: str, start_time: float = None,
                 end_time: float = None) -> Optional[float]:
        """
        Aggregate metrics
        Operations: sum, avg, min, max, count, p50, p95, p99
        """
        metrics = self.values
        if start_time and end_time:
            metrics = self.get_range(start_time, end_time)

        if not metrics:
            return None

        values = [m.value for m in metrics]

        if operation == "sum":
            return sum(values)
        elif operation == "avg":
            return statistics.mean(values)
        elif operation == "min":
            return min(values)
        elif operation == "max":
            return max(values)
        elif operation == "count":
            return len(values)
        elif operation == "p50":
            return self._percentile(values, 50)
        elif operation == "p95":
            return self._percentile(values, 95)
        elif operation == "p99":
            return self._percentile(values, 99)

        return None

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "count": len(self.values),
            "latest_value": self.get_latest().to_dict() if self.get_latest() else None,
        }


class RollingWindow:
    """Rolling window for aggregations"""

    def __init__(self, window_size_seconds: int):
        self.window_size = window_size_seconds
        self.data: List[tuple[float, float]] = []

    def add(self, timestamp: float, value: float) -> None:
        """Add value to window"""
        self.data.append((timestamp, value))
        self._prune()

    def _prune(self) -> None:
        """Remove data outside window"""
        cutoff = datetime.utcnow().timestamp() - self.window_size
        self.data = [(t, v) for t, v in self.data if t >= cutoff]

    def get_values(self) -> List[float]:
        """Get all values in window"""
        return [v for _, v in self.data]

    def get_average(self) -> Optional[float]:
        """Get average in window"""
        values = self.get_values()
        return statistics.mean(values) if values else None

    def get_sum(self) -> float:
        """Get sum in window"""
        return sum(v for _, v in self.data)


class MetricsAggregator:
    """
    Central metrics collection and aggregation service
    Supports counters, gauges, histograms, summaries
    """

    def __init__(self):
        self.series: Dict[str, TimeSeries] = {}
        self.rolling_windows: Dict[str, RollingWindow] = {}
        self.tenant_metrics: Dict[str, Dict[str, TimeSeries]] = defaultdict(dict)
        self.metric_retention_days = 90
        self.rollup_intervals = {
            "1m": 60,
            "5m": 300,
            "1h": 3600,
            "1d": 86400,
        }

    def record_metric(self, tenant_id: str, metric_name: str,
                     value: float, metric_type: MetricType = MetricType.GAUGE,
                     labels: Dict[str, str] = None) -> None:
        """
        Record a metric
        """
        timestamp = datetime.utcnow().timestamp()

        metric = Metric(metric_name, metric_type, value, timestamp, labels)

        # Store in global series
        key = metric_name
        if metric_name not in self.series:
            self.series[key] = TimeSeries(metric_name, metric_type)
        self.series[key].add(metric)

        # Store in tenant-specific series
        tenant_key = f"{tenant_id}:{metric_name}"
        if tenant_key not in self.tenant_metrics[tenant_id]:
            self.tenant_metrics[tenant_id][metric_name] = TimeSeries(metric_name, metric_type)
        self.tenant_metrics[tenant_id][metric_name].add(metric)

        # Update rolling windows
        window_key = f"{tenant_id}:{metric_name}:5m"
        if window_key not in self.rolling_windows:
            self.rolling_windows[window_key] = RollingWindow(300)  # 5 min window
        self.rolling_windows[window_key].add(timestamp, value)

        logger.debug(f"Metric recorded: {metric_name} = {value}")

    def get_metric(self, tenant_id: str, metric_name: str,
                  limit: int = 1000) -> Optional[Dict[str, Any]]:
        """Get metric time series"""
        if metric_name not in self.tenant_metrics[tenant_id]:
            return None

        series = self.tenant_metrics[tenant_id][metric_name]
        values = series.values[-limit:] if series.values else []

        return {
            "name": metric_name,
            "type": series.metric_type.value,
            "values": [m.to_dict() for m in values],
        }

    def get_metrics_list(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for tenant"""
        metrics = []
        for metric_name, series in self.tenant_metrics[tenant_id].items():
            metrics.append({
                "name": metric_name,
                "type": series.metric_type.value,
                "latest_value": series.get_latest().value if series.get_latest() else None,
                "latest_timestamp": series.get_latest().timestamp if series.get_latest() else None,
            })
        return metrics

    def aggregate(self, tenant_id: str, metric_name: str,
                 operation: str, start_time: float = None,
                 end_time: float = None) -> Optional[float]:
        """
        Aggregate metric over time range
        Operations: sum, avg, min, max, count, p50, p95, p99
        """
        if metric_name not in self.tenant_metrics[tenant_id]:
            return None

        series = self.tenant_metrics[tenant_id][metric_name]
        return series.aggregate(operation, start_time, end_time)

    def get_percentile(self, tenant_id: str, metric_name: str,
                      percentile: int = 95, hours: int = 1) -> Optional[float]:
        """Get percentile for metric"""
        if metric_name not in self.tenant_metrics[tenant_id]:
            return None

        end_time = datetime.utcnow().timestamp()
        start_time = end_time - (hours * 3600)

        series = self.tenant_metrics[tenant_id][metric_name]
        metrics = series.get_range(start_time, end_time)

        if not metrics:
            return None

        values = sorted([m.value for m in metrics])
        index = int((percentile / 100) * len(values))
        return values[min(index, len(values) - 1)]

    def compare_periods(self, tenant_id: str, metric_name: str,
                       period1_start: float, period1_end: float,
                       period2_start: float, period2_end: float) -> Dict[str, float]:
        """Compare metric across two time periods"""
        if metric_name not in self.tenant_metrics[tenant_id]:
            return {}

        series = self.tenant_metrics[tenant_id][metric_name]

        p1_metrics = series.get_range(period1_start, period1_end)
        p2_metrics = series.get_range(period2_start, period2_end)

        if not p1_metrics or not p2_metrics:
            return {}

        p1_avg = statistics.mean([m.value for m in p1_metrics])
        p2_avg = statistics.mean([m.value for m in p2_metrics])

        change = p2_avg - p1_avg
        change_pct = (change / p1_avg * 100) if p1_avg != 0 else 0

        return {
            "period1_avg": p1_avg,
            "period2_avg": p2_avg,
            "absolute_change": change,
            "percent_change": change_pct,
        }

    def get_rolling_average(self, tenant_id: str, metric_name: str,
                           window_minutes: int = 5) -> Optional[float]:
        """Get rolling average for metric"""
        window_key = f"{tenant_id}:{metric_name}:{window_minutes}m"

        if window_key not in self.rolling_windows:
            return None

        return self.rolling_windows[window_key].get_average()

    def export_metrics(self, tenant_id: str, format: str = "prometheus") -> str:
        """
        Export metrics in specified format
        Formats: prometheus, json
        """
        if format == "prometheus":
            return self._export_prometheus(tenant_id)
        else:
            return self._export_json(tenant_id)

    def _export_prometheus(self, tenant_id: str) -> str:
        """Export in Prometheus format"""
        lines = []
        for metric_name, series in self.tenant_metrics[tenant_id].items():
            latest = series.get_latest()
            if latest:
                labels = f'tenant_id="{tenant_id}"'
                lines.append(f'{metric_name}{{{labels}}} {latest.value} {int(latest.timestamp * 1000)}')
        return "\n".join(lines)

    def _export_json(self, tenant_id: str) -> str:
        """Export in JSON format"""
        import json
        data = {}
        for metric_name, series in self.tenant_metrics[tenant_id].items():
            data[metric_name] = series.to_dict()
        return json.dumps(data, indent=2)

    def cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period"""
        cutoff_timestamp = (datetime.utcnow() - timedelta(days=self.metric_retention_days)).timestamp()

        cleaned_count = 0
        for series in self.series.values():
            initial_count = len(series.values)
            series.values = [m for m in series.values if m.timestamp >= cutoff_timestamp]
            cleaned_count += initial_count - len(series.values)

        logger.info(f"Cleaned up {cleaned_count} old metrics")

    def get_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get metrics statistics for tenant"""
        metrics = self.tenant_metrics[tenant_id]

        return {
            "total_metrics": len(metrics),
            "active_metrics": sum(1 for s in metrics.values() if s.get_latest()),
            "metric_names": list(metrics.keys()),
            "retention_days": self.metric_retention_days,
        }
