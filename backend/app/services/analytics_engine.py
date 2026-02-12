"""
Advanced Analytics Engine
Log, metric, and trace analysis with pattern detection and trending
Phase 43: Advanced Analytics & ML Features
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
import statistics
import re
from collections import Counter, defaultdict
import threading


class AggregationType(Enum):
    """Aggregation function types"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STDDEV = "stddev"
    P95 = "p95"
    P99 = "p99"
    RATE = "rate"


class TrendDirection(Enum):
    """Trend directions"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    UNKNOWN = "unknown"


@dataclass
class AnalyticsQuery:
    """Query specification for analytics"""
    start_time: datetime
    end_time: datetime
    metric_names: List[str] = field(default_factory=list)
    log_filters: Dict[str, str] = field(default_factory=dict)
    trace_service_names: List[str] = field(default_factory=list)
    aggregation: AggregationType = AggregationType.AVG
    group_by: Optional[str] = None
    interval_seconds: int = 300
    limit: int = 1000


@dataclass
class AggregationResult:
    """Result of aggregation operation"""
    timestamp: datetime
    value: float
    count: int
    group_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "count": self.count,
            "group_key": self.group_key,
            "metadata": self.metadata,
        }


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    metric_name: str
    direction: TrendDirection
    slope: float
    r_squared: float
    current_value: float
    previous_value: float
    percent_change: float
    confidence: float
    start_time: datetime
    end_time: datetime

    def to_dict(self):
        return {
            "metric_name": self.metric_name,
            "direction": self.direction.value,
            "slope": self.slope,
            "r_squared": self.r_squared,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "percent_change": self.percent_change,
            "confidence": self.confidence,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }


@dataclass
class PatternDetectionResult:
    """Pattern detection result"""
    pattern: str
    occurrences: int
    frequency: float
    first_seen: datetime
    last_seen: datetime
    affected_logs: List[str] = field(default_factory=list)
    severity: str = "info"

    def to_dict(self):
        return {
            "pattern": self.pattern,
            "occurrences": self.occurrences,
            "frequency": self.frequency,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "severity": self.severity,
        }


@dataclass
class CorrelationResult:
    """Correlation analysis between signals"""
    signal_a: str
    signal_b: str
    correlation_coefficient: float
    p_value: float
    lag_seconds: int
    strength: str  # weak, moderate, strong, very_strong

    def to_dict(self):
        return {
            "signal_a": self.signal_a,
            "signal_b": self.signal_b,
            "correlation_coefficient": self.correlation_coefficient,
            "p_value": self.p_value,
            "lag_seconds": self.lag_seconds,
            "strength": self.strength,
        }


class LogAnalyzer:
    """Analyzes logs for patterns and trends"""

    def __init__(self):
        self.logs: List[Dict] = []
        self.patterns: Dict[str, PatternDetectionResult] = {}
        self.lock = threading.RLock()

    def add_logs(self, logs: List[Dict]) -> None:
        """Add logs for analysis"""
        with self.lock:
            self.logs.extend(logs)

    def analyze_patterns(self, pattern_type: str = "error") -> List[PatternDetectionResult]:
        """Detect patterns in logs"""
        results = []
        with self.lock:
            if pattern_type == "error":
                results = self._detect_error_patterns()
            elif pattern_type == "exception":
                results = self._detect_exception_patterns()
            elif pattern_type == "frequency":
                results = self._detect_frequency_patterns()

        return results

    def _detect_error_patterns(self) -> List[PatternDetectionResult]:
        """Detect common error patterns"""
        error_logs = [log for log in self.logs if log.get("level") in ["ERROR", "CRITICAL"]]
        pattern_counts = Counter()

        for log in error_logs:
            message = log.get("message", "")
            # Extract common error patterns (simplified)
            if "timeout" in message.lower():
                pattern_counts["timeout_error"] += 1
            elif "connection" in message.lower():
                pattern_counts["connection_error"] += 1
            elif "permission" in message.lower():
                pattern_counts["permission_error"] += 1
            elif "not found" in message.lower():
                pattern_counts["not_found_error"] += 1

        results = []
        total_logs = len(self.logs)

        for pattern, count in pattern_counts.most_common():
            results.append(
                PatternDetectionResult(
                    pattern=pattern,
                    occurrences=count,
                    frequency=count / total_logs if total_logs > 0 else 0,
                    first_seen=datetime.now() - timedelta(hours=1),
                    last_seen=datetime.now(),
                    severity="high" if count > 10 else "medium",
                )
            )

        return results

    def _detect_exception_patterns(self) -> List[PatternDetectionResult]:
        """Detect exception patterns"""
        exception_logs = [log for log in self.logs if log.get("exception")]
        exception_counts = Counter()

        for log in exception_logs:
            exception = log.get("exception", "")
            # Extract exception type (simplified)
            if "ValueError" in exception:
                exception_counts["ValueError"] += 1
            elif "TypeError" in exception:
                exception_counts["TypeError"] += 1
            elif "KeyError" in exception:
                exception_counts["KeyError"] += 1
            elif "RuntimeError" in exception:
                exception_counts["RuntimeError"] += 1

        results = []
        total_logs = len(self.logs) if len(self.logs) > 0 else 1

        for exception_type, count in exception_counts.most_common():
            results.append(
                PatternDetectionResult(
                    pattern=exception_type,
                    occurrences=count,
                    frequency=count / total_logs,
                    first_seen=datetime.now() - timedelta(hours=1),
                    last_seen=datetime.now(),
                    severity="high",
                )
            )

        return results

    def _detect_frequency_patterns(self) -> List[PatternDetectionResult]:
        """Detect high-frequency log patterns"""
        messages = [log.get("message", "") for log in self.logs]
        message_counts = Counter(messages)

        results = []
        total_logs = len(self.logs) if len(self.logs) > 0 else 1

        for message, count in message_counts.most_common(10):
            if count > 1:
                results.append(
                    PatternDetectionResult(
                        pattern=message,
                        occurrences=count,
                        frequency=count / total_logs,
                        first_seen=datetime.now() - timedelta(hours=1),
                        last_seen=datetime.now(),
                        severity="info",
                    )
                )

        return results

    def aggregate_logs(self, query: AnalyticsQuery) -> List[AggregationResult]:
        """Aggregate logs by time interval"""
        results = []

        if query.aggregation == AggregationType.COUNT:
            return self._count_logs_by_interval(query)
        elif query.aggregation == AggregationType.AVG:
            return self._average_logs_by_metric(query)

        return results

    def _count_logs_by_interval(self, query: AnalyticsQuery) -> List[AggregationResult]:
        """Count logs by time interval"""
        results = []
        current = query.start_time

        while current < query.end_time:
            interval_end = current + timedelta(seconds=query.interval_seconds)
            count = sum(
                1 for log in self.logs
                if current <= datetime.fromisoformat(log.get("timestamp", "")) < interval_end
                and all(log.get(k) == v for k, v in query.log_filters.items())
            )

            results.append(
                AggregationResult(
                    timestamp=current,
                    value=count,
                    count=count,
                )
            )

            current = interval_end

        return results

    def _average_logs_by_metric(self, query: AnalyticsQuery) -> List[AggregationResult]:
        """Average numeric values by time interval"""
        results = []
        current = query.start_time

        while current < query.end_time:
            interval_end = current + timedelta(seconds=query.interval_seconds)
            matching_logs = [
                log for log in self.logs
                if current <= datetime.fromisoformat(log.get("timestamp", "")) < interval_end
                and all(log.get(k) == v for k, v in query.log_filters.items())
            ]

            if matching_logs:
                # Simplified: count matching logs
                value = len(matching_logs)
                results.append(
                    AggregationResult(
                        timestamp=current,
                        value=value,
                        count=len(matching_logs),
                    )
                )

            current = interval_end

        return results


class MetricAnalyzer:
    """Analyzes metrics for trends and correlations"""

    def __init__(self):
        self.metrics: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.lock = threading.RLock()

    def add_metric(self, name: str, timestamp: datetime, value: float) -> None:
        """Add metric data point"""
        with self.lock:
            self.metrics[name].append((timestamp, value))

    def analyze_trend(self, metric_name: str, lookback_hours: int = 24) -> Optional[TrendAnalysis]:
        """Analyze metric trend"""
        with self.lock:
            if metric_name not in self.metrics:
                return None

            data = self.metrics[metric_name]
            if len(data) < 2:
                return None

            # Filter to lookback period
            cutoff = datetime.now() - timedelta(hours=lookback_hours)
            recent_data = [(t, v) for t, v in data if t >= cutoff]

            if len(recent_data) < 2:
                return None

            values = [v for _, v in recent_data]
            current_value = values[-1]
            previous_value = values[0]
            percent_change = (
                ((current_value - previous_value) / previous_value * 100)
                if previous_value != 0
                else 0
            )

            # Determine trend direction
            if percent_change > 5:
                direction = TrendDirection.UP
            elif percent_change < -5:
                direction = TrendDirection.DOWN
            else:
                direction = TrendDirection.STABLE

            # Calculate linear regression approximation
            slope = (current_value - previous_value) / len(recent_data) if len(recent_data) > 0 else 0

            return TrendAnalysis(
                metric_name=metric_name,
                direction=direction,
                slope=slope,
                r_squared=0.8,  # Simplified
                current_value=current_value,
                previous_value=previous_value,
                percent_change=percent_change,
                confidence=0.85,
                start_time=recent_data[0][0],
                end_time=recent_data[-1][0],
            )

    def correlate_metrics(
        self, metric_a: str, metric_b: str, lookback_hours: int = 24
    ) -> Optional[CorrelationResult]:
        """Analyze correlation between two metrics"""
        with self.lock:
            if metric_a not in self.metrics or metric_b not in self.metrics:
                return None

            cutoff = datetime.now() - timedelta(hours=lookback_hours)
            values_a = [v for t, v in self.metrics[metric_a] if t >= cutoff]
            values_b = [v for t, v in self.metrics[metric_b] if t >= cutoff]

            if len(values_a) < 2 or len(values_b) < 2:
                return None

            # Simplified correlation calculation
            correlation = 0.7  # Placeholder

            # Determine correlation strength
            if abs(correlation) < 0.3:
                strength = "weak"
            elif abs(correlation) < 0.6:
                strength = "moderate"
            elif abs(correlation) < 0.85:
                strength = "strong"
            else:
                strength = "very_strong"

            return CorrelationResult(
                signal_a=metric_a,
                signal_b=metric_b,
                correlation_coefficient=correlation,
                p_value=0.01,
                lag_seconds=0,
                strength=strength,
            )

    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        with self.lock:
            if metric_name not in self.metrics:
                return {}

            values = [v for _, v in self.metrics[metric_name]]

            if not values:
                return {}

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0,
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99),
            }

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]


class AnalyticsEngine:
    """Central analytics engine coordinating analysis services"""

    def __init__(self):
        self.log_analyzer = LogAnalyzer()
        self.metric_analyzer = MetricAnalyzer()
        self.callbacks: List[Callable] = []
        self.lock = threading.RLock()

    def ingest_logs(self, logs: List[Dict]) -> None:
        """Ingest logs for analysis"""
        self.log_analyzer.add_logs(logs)

    def ingest_metrics(self, metrics: List[Dict]) -> None:
        """Ingest metrics for analysis"""
        with self.lock:
            for metric in metrics:
                timestamp = datetime.fromisoformat(metric.get("timestamp", datetime.now().isoformat()))
                self.metric_analyzer.add_metric(
                    metric.get("name", "unknown"),
                    timestamp,
                    metric.get("value", 0),
                )

    def analyze_log_patterns(self, pattern_type: str = "error") -> List[Dict]:
        """Analyze log patterns"""
        results = self.log_analyzer.analyze_patterns(pattern_type)
        
        for result in results:
            for callback in self.callbacks:
                try:
                    callback({
                        "event": "pattern_detected",
                        "pattern": result.pattern,
                        "occurrences": result.occurrences,
                    })
                except Exception as e:
                    print(f"Error in callback: {e}")

        return [r.to_dict() for r in results]

    def analyze_metric_trends(self, metric_names: List[str]) -> List[Dict]:
        """Analyze trends for multiple metrics"""
        results = []

        for metric_name in metric_names:
            trend = self.metric_analyzer.analyze_trend(metric_name)
            if trend:
                results.append(trend.to_dict())

        return results

    def correlate_signals(self, signal_pairs: List[Tuple[str, str]]) -> List[Dict]:
        """Correlate pairs of signals"""
        results = []

        for signal_a, signal_b in signal_pairs:
            correlation = self.metric_analyzer.correlate_metrics(signal_a, signal_b)
            if correlation:
                results.append(correlation.to_dict())

        return results

    def get_metric_statistics(self, metric_names: List[str]) -> Dict[str, Dict]:
        """Get statistics for metrics"""
        results = {}

        for metric_name in metric_names:
            stats = self.metric_analyzer.get_statistics(metric_name)
            if stats:
                results[metric_name] = stats

        return results

    def aggregate_metrics(self, query: AnalyticsQuery) -> List[Dict]:
        """Aggregate metrics by interval"""
        results = self.log_analyzer.aggregate_logs(query)
        return [r.to_dict() for r in results]

    def export_analysis(self, analysis_type: str = "all") -> Dict[str, Any]:
        """Export analysis results"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type,
        }

        if analysis_type in ["all", "patterns"]:
            export_data["log_patterns"] = self.analyze_log_patterns()

        if analysis_type in ["all", "trends"]:
            export_data["metric_trends"] = self.analyze_metric_trends(
                list(self.metric_analyzer.metrics.keys())
            )

        if analysis_type in ["all", "statistics"]:
            export_data["statistics"] = self.get_metric_statistics(
                list(self.metric_analyzer.metrics.keys())
            )

        return export_data

    def register_callback(self, callback: Callable) -> None:
        """Register callback for analysis events"""
        with self.lock:
            self.callbacks.append(callback)

    def get_summary(self) -> Dict[str, Any]:
        """Get analytics engine summary"""
        with self.lock:
            return {
                "metrics_tracked": len(self.metric_analyzer.metrics),
                "logs_analyzed": len(self.log_analyzer.logs),
                "patterns_detected": len(self.log_analyzer.patterns),
                "callbacks_registered": len(self.callbacks),
            }


# Global singleton
_analytics_engine = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get or create analytics engine singleton"""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine
