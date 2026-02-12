"""
Phase 51: Metrics Collection Service
Unified metrics collection and reporting
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Categories of metrics"""
    CACHE = "cache"
    PERFORMANCE = "performance"
    REQUEST = "request"
    COMPRESSION = "compression"
    SYSTEM = "system"


@dataclass
class MetricDataPoint:
    """Individual metric data point"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    value: float = 0
    unit: str = ""
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricsSnapshot:
    """Complete metrics snapshot at a point in time"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cache_metrics: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    request_metrics: Dict[str, Any] = field(default_factory=dict)
    compression_metrics: Dict[str, Any] = field(default_factory=dict)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cache": self.cache_metrics,
            "performance": self.performance_metrics,
            "request": self.request_metrics,
            "compression": self.compression_metrics,
            "system": self.system_metrics
        }


class MetricsCollector:
    """Central metrics collection service"""
    
    def __init__(self, max_snapshots: int = 100):
        self.max_snapshots = max_snapshots
        self.snapshots: List[MetricsSnapshot] = []
        self.current_metrics: Dict[str, Any] = {}
        self.start_time = datetime.utcnow()
    
    def collect_cache_metrics(self, cache_stats: Dict[str, Any]) -> None:
        """Collect cache metrics"""
        self.current_metrics["cache"] = cache_stats
        logger.debug(f"Collected cache metrics: {cache_stats}")
    
    def collect_performance_metrics(self, perf_stats: Dict[str, Any]) -> None:
        """Collect performance metrics"""
        self.current_metrics["performance"] = perf_stats
        logger.debug(f"Collected performance metrics")
    
    def collect_request_metrics(self, req_stats: Dict[str, Any]) -> None:
        """Collect request metrics"""
        self.current_metrics["request"] = req_stats
        logger.debug(f"Collected request metrics: {req_stats['total_requests']} requests")
    
    def collect_compression_metrics(self, comp_stats: Dict[str, Any]) -> None:
        """Collect compression metrics"""
        self.current_metrics["compression"] = comp_stats
        logger.debug(f"Collected compression metrics")
    
    def collect_system_metrics(self, sys_stats: Dict[str, Any]) -> None:
        """Collect system metrics"""
        self.current_metrics["system"] = sys_stats
        logger.debug(f"Collected system metrics")
    
    def take_snapshot(self) -> MetricsSnapshot:
        """Take a metrics snapshot"""
        snapshot = MetricsSnapshot(
            cache_metrics=self.current_metrics.get("cache", {}),
            performance_metrics=self.current_metrics.get("performance", {}),
            request_metrics=self.current_metrics.get("request", {}),
            compression_metrics=self.current_metrics.get("compression", {}),
            system_metrics=self.current_metrics.get("system", {})
        )
        
        # Keep snapshots limited
        self.snapshots.append(snapshot)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)
        
        logger.info(f"Took metrics snapshot ({len(self.snapshots)} total)")
        
        return snapshot
    
    def get_latest_snapshot(self) -> Optional[MetricsSnapshot]:
        """Get latest metrics snapshot"""
        return self.snapshots[-1] if self.snapshots else None
    
    def get_snapshot_range(self, start_index: int = 0, 
                          end_index: Optional[int] = None) -> List[MetricsSnapshot]:
        """Get range of snapshots"""
        if not self.snapshots:
            return []
        
        end_index = end_index or len(self.snapshots)
        return self.snapshots[start_index:end_index]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            **self.current_metrics
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        summary = {
            "uptime_seconds": uptime,
            "total_snapshots": len(self.snapshots),
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.utcnow().isoformat(),
            "metrics_available": list(self.current_metrics.keys())
        }
        
        # Add summary stats from latest snapshot
        if self.snapshots:
            latest = self.snapshots[-1]
            summary["latest_cache_hit_rate"] = latest.cache_metrics.get("hit_rate", "N/A")
            summary["latest_request_count"] = latest.request_metrics.get("total_requests", 0)
            summary["latest_error_rate"] = latest.request_metrics.get("error_rate", 0)
        
        return summary
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        if format == "json":
            import json
            snapshots_data = [snap.to_dict() for snap in self.snapshots]
            return json.dumps({
                "summary": self.get_summary(),
                "snapshots": snapshots_data
            }, indent=2)
        
        # Default to summary text
        return str(self.get_summary())
    
    def reset(self) -> None:
        """Reset metrics collector"""
        self.snapshots.clear()
        self.current_metrics.clear()
        self.start_time = datetime.utcnow()
        logger.info("Metrics collector reset")


class MetricsAggregator:
    """Aggregate metrics across multiple collectors"""
    
    def __init__(self):
        self.collectors: Dict[str, MetricsCollector] = {}
    
    def register_collector(self, name: str, 
                          collector: MetricsCollector) -> None:
        """Register a metrics collector"""
        self.collectors[name] = collector
        logger.info(f"Registered metrics collector: {name}")
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all collectors"""
        aggregated = {
            "collectors": list(self.collectors.keys()),
            "timestamp": datetime.utcnow().isoformat(),
            "collector_metrics": {}
        }
        
        for name, collector in self.collectors.items():
            aggregated["collector_metrics"][name] = collector.get_current_metrics()
        
        return aggregated
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status based on metrics"""
        status = {
            "overall": "healthy",
            "components": {}
        }
        
        for name, collector in self.collectors.items():
            snapshot = collector.get_latest_snapshot()
            if not snapshot:
                status["components"][name] = "no_data"
                continue
            
            # Simple health check based on error rates
            error_rate = snapshot.request_metrics.get("error_rate", 0)
            if error_rate > 10:
                status["components"][name] = "degraded"
                status["overall"] = "degraded"
            elif error_rate > 5:
                status["components"][name] = "warning"
            else:
                status["components"][name] = "healthy"
        
        return status


# Global instances
_metrics_collector: Optional[MetricsCollector] = None
_metrics_aggregator: Optional[MetricsAggregator] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_metrics_aggregator() -> MetricsAggregator:
    """Get or create metrics aggregator"""
    global _metrics_aggregator
    if _metrics_aggregator is None:
        _metrics_aggregator = MetricsAggregator()
    return _metrics_aggregator


def reset_metrics_collection() -> None:
    """Reset metrics collection (for testing)"""
    global _metrics_collector, _metrics_aggregator
    _metrics_collector = None
    _metrics_aggregator = None
