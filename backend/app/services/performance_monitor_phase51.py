"""
Phase 51: Performance Monitoring Service
Track and analyze application performance metrics
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY = "memory"
    CPU = "cpu"
    CACHE_HIT = "cache_hit"
    QUEUE_SIZE = "queue_size"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.LATENCY


@dataclass
class PerformanceStats:
    """Performance statistics"""
    min_value: float = float('inf')
    max_value: float = 0
    avg_value: float = 0
    total_count: int = 0
    total_sum: float = 0
    
    def add_value(self, value: float) -> None:
        """Add a value to statistics"""
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        self.total_count += 1
        self.total_sum += value
        self.avg_value = self.total_sum / self.total_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "min": round(self.min_value, 4) if self.min_value != float('inf') else 0,
            "max": round(self.max_value, 4),
            "avg": round(self.avg_value, 4),
            "count": self.total_count
        }


class PerformanceMonitor:
    """Monitor application performance"""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.metrics: Dict[str, deque] = {}
        self.stats: Dict[str, PerformanceStats] = {}
        self.active_timers: Dict[str, float] = {}
    
    def record_metric(self, name: str, value: float, 
                     labels: Dict[str, str] = None) -> None:
        """Record a metric value"""
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.max_samples)
            self.stats[name] = PerformanceStats()
        
        # Add metric
        metric = Metric(name=name, value=value, labels=labels or {})
        self.metrics[name].append(metric)
        
        # Update stats
        self.stats[name].add_value(value)
        
        logger.debug(f"Recorded metric {name}: {value}")
    
    def start_timer(self, name: str) -> None:
        """Start a performance timer"""
        self.active_timers[name] = time.time()
    
    def end_timer(self, name: str, labels: Dict[str, str] = None) -> float:
        """End a timer and record latency"""
        if name not in self.active_timers:
            logger.warning(f"Timer {name} not started")
            return 0
        
        elapsed = time.time() - self.active_timers[name]
        del self.active_timers[name]
        
        # Record as latency metric
        metric_name = f"{name}_latency"
        self.record_metric(metric_name, elapsed * 1000, labels)  # Convert to ms
        
        return elapsed
    
    def get_metric_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a metric"""
        if name not in self.stats:
            return None
        
        return self.stats[name].to_dict()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get all metric statistics"""
        return {name: stats.to_dict() 
                for name, stats in self.stats.items()}
    
    def get_recent_metrics(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent metrics for a name"""
        if name not in self.metrics:
            return []
        
        return [
            {
                "value": m.value,
                "timestamp": m.timestamp.isoformat(),
                "labels": m.labels
            }
            for m in list(self.metrics[name])[-limit:]
        ]
    
    def clear_metrics(self, name: Optional[str] = None) -> None:
        """Clear metrics"""
        if name:
            if name in self.metrics:
                self.metrics[name].clear()
                self.stats[name] = PerformanceStats()
        else:
            self.metrics.clear()
            self.stats.clear()


class RequestMetrics:
    """Track HTTP request metrics"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.request_latencies: deque = deque(maxlen=1000)
        self.status_codes: Dict[int, int] = {}
        self.endpoints: Dict[str, Dict[str, Any]] = {}
    
    def record_request(self, endpoint: str, status_code: int, 
                      latency_ms: float) -> None:
        """Record a request"""
        self.total_requests += 1
        
        # Status tracking
        if status_code in self.status_codes:
            self.status_codes[status_code] += 1
        else:
            self.status_codes[status_code] = 1
        
        # Success/failure tracking
        if 200 <= status_code < 300:
            self.successful_requests += 1
        elif status_code >= 400:
            self.failed_requests += 1
        
        # Latency tracking
        self.request_latencies.append(latency_ms)
        
        # Endpoint tracking
        if endpoint not in self.endpoints:
            self.endpoints[endpoint] = {
                "requests": 0,
                "total_latency": 0,
                "min_latency": float('inf'),
                "max_latency": 0,
                "errors": 0
            }
        
        ep = self.endpoints[endpoint]
        ep["requests"] += 1
        ep["total_latency"] += latency_ms
        ep["min_latency"] = min(ep["min_latency"], latency_ms)
        ep["max_latency"] = max(ep["max_latency"], latency_ms)
        if status_code >= 400:
            ep["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        if not self.request_latencies:
            avg_latency = 0
            min_latency = 0
            max_latency = 0
        else:
            latencies = list(self.request_latencies)
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
        
        success_rate = (self.successful_requests / self.total_requests * 100 
                       if self.total_requests > 0 else 0)
        error_rate = (self.failed_requests / self.total_requests * 100 
                     if self.total_requests > 0 else 0)
        
        # Calculate endpoint stats
        endpoint_stats = {}
        for endpoint, data in self.endpoints.items():
            endpoint_stats[endpoint] = {
                "requests": data["requests"],
                "avg_latency_ms": round(data["total_latency"] / data["requests"], 2),
                "min_latency_ms": round(data["min_latency"], 2) if data["min_latency"] != float('inf') else 0,
                "max_latency_ms": round(data["max_latency"], 2),
                "errors": data["errors"],
                "error_rate": round(data["errors"] / data["requests"] * 100, 2) if data["requests"] > 0 else 0
            }
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(success_rate, 2),
            "error_rate": round(error_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": round(min_latency, 2),
            "max_latency_ms": round(max_latency, 2),
            "status_codes": self.status_codes,
            "endpoints": endpoint_stats
        }
    
    def get_endpoint_stats(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific endpoint"""
        if endpoint not in self.endpoints:
            return None
        
        data = self.endpoints[endpoint]
        return {
            "requests": data["requests"],
            "avg_latency_ms": round(data["total_latency"] / data["requests"], 2),
            "min_latency_ms": round(data["min_latency"], 2) if data["min_latency"] != float('inf') else 0,
            "max_latency_ms": round(data["max_latency"], 2),
            "errors": data["errors"],
            "error_rate": round(data["errors"] / data["requests"] * 100, 2)
        }


# Global monitoring instance
_performance_monitor: Optional[PerformanceMonitor] = None
_request_metrics: Optional[RequestMetrics] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_request_metrics() -> RequestMetrics:
    """Get or create request metrics"""
    global _request_metrics
    if _request_metrics is None:
        _request_metrics = RequestMetrics()
    return _request_metrics


def reset_monitoring() -> None:
    """Reset monitoring (for testing)"""
    global _performance_monitor, _request_metrics
    _performance_monitor = None
    _request_metrics = None
