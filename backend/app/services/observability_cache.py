"""
Observability Cache Service - Caching layer for observability data
Provides caching for metrics, logs, traces, and query results to improve performance
"""

import time
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
from enum import Enum
import json


class EvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"  # Least recently used
    FIFO = "fifo"  # First in, first out
    TTL = "ttl"  # Time-to-live only
    LFU = "lfu"  # Least frequently used


@dataclass
class CacheEntry:
    """Individual cache entry"""
    key: str
    value: Any
    timestamp: float
    ttl_seconds: int
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() - self.timestamp > self.ttl_seconds
    
    def access(self) -> None:
        """Record access"""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheStatistics:
    """Cache performance statistics"""
    total_hits: int = 0
    total_misses: int = 0
    evictions_lru: int = 0
    evictions_ttl: int = 0
    evictions_fifo: int = 0
    current_size: int = 0
    max_size: int = 0
    avg_entry_size: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage"""
        total = self.total_hits + self.total_misses
        return (self.total_hits / total * 100) if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate miss rate percentage"""
        return 100.0 - self.hit_rate


@dataclass
class CacheConfig:
    """Cache configuration"""
    max_entries: int = 10000
    default_ttl_seconds: int = 3600  # 1 hour
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    cleanup_interval_seconds: int = 300  # 5 minutes
    enable_compression: bool = False
    enable_persistence: bool = False


class MetricCache:
    """Time-series metric caching with TTL"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, OrderedDict[float, CacheEntry]] = {}
        self.lock = threading.RLock()
        self.stats = CacheStatistics(max_size=config.max_entries)
        self.callbacks: List[Callable] = []
    
    def put_metric(self, metric_name: str, value: float, timestamp: float,
                   ttl_seconds: Optional[int] = None) -> None:
        """Store metric value"""
        with self.lock:
            ttl = ttl_seconds or self.config.default_ttl_seconds
            
            if metric_name not in self.cache:
                self.cache[metric_name] = OrderedDict()
            
            key = f"{metric_name}:{timestamp}"
            entry = CacheEntry(key, value, time.time(), ttl)
            self.cache[metric_name][timestamp] = entry
            
            # Trim old entries for memory
            if len(self.cache[metric_name]) > 1000:
                oldest = next(iter(self.cache[metric_name]))
                del self.cache[metric_name][oldest]
            
            self.stats.current_size += 1
            self._trigger_callback("metric_cached", metric_name, value)
    
    def get_metric(self, metric_name: str, start_time: float, 
                   end_time: float) -> List[Tuple[float, float]]:
        """Retrieve metric values in time range"""
        with self.lock:
            if metric_name not in self.cache:
                self.stats.total_misses += 1
                return []
            
            result = []
            expired_timestamps = []
            
            for ts, entry in self.cache[metric_name].items():
                if entry.is_expired():
                    expired_timestamps.append(ts)
                elif start_time <= ts <= end_time:
                    entry.access()
                    result.append((ts, entry.value))
                    self.stats.total_hits += 1
            
            # Clean expired entries
            for ts in expired_timestamps:
                del self.cache[metric_name][ts]
                self.stats.evictions_ttl += 1
            
            if not result:
                self.stats.total_misses += 1
            
            return result
    
    def get_latest_metric(self, metric_name: str) -> Optional[Tuple[float, float]]:
        """Get most recent value for metric"""
        with self.lock:
            if metric_name not in self.cache or not self.cache[metric_name]:
                self.stats.total_misses += 1
                return None
            
            ts, entry = next(reversed(list(self.cache[metric_name].items())))
            if entry.is_expired():
                del self.cache[metric_name][ts]
                self.stats.total_misses += 1
                return None
            
            entry.access()
            self.stats.total_hits += 1
            return (ts, entry.value)
    
    def clear_metric(self, metric_name: str) -> None:
        """Clear all values for a metric"""
        with self.lock:
            if metric_name in self.cache:
                del self.cache[metric_name]
                self._trigger_callback("metric_cleared", metric_name)


class LogCache:
    """Circular buffer cache for logs with TTL"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.logs: Dict[str, OrderedDict] = {}
        self.lock = threading.RLock()
        self.stats = CacheStatistics(max_size=config.max_entries)
        self.callbacks: List[Callable] = []
        self.max_logs_per_source = 5000
    
    def put_log(self, source: str, log_entry: Dict[str, Any],
                ttl_seconds: Optional[int] = None) -> None:
        """Add log entry"""
        with self.lock:
            ttl = ttl_seconds or self.config.default_ttl_seconds
            
            if source not in self.logs:
                self.logs[source] = OrderedDict()
            
            timestamp = log_entry.get("timestamp", time.time())
            key = f"{source}:{timestamp}:{id(log_entry)}"
            entry = CacheEntry(key, log_entry, time.time(), ttl)
            
            self.logs[source][key] = entry
            self.stats.current_size += 1
            
            # Enforce circular buffer limit
            if len(self.logs[source]) > self.max_logs_per_source:
                oldest_key = next(iter(self.logs[source]))
                del self.logs[source][oldest_key]
                self.stats.evictions_fifo += 1
            
            self._trigger_callback("log_cached", source, log_entry)
    
    def get_logs(self, source: str, start_time: float, end_time: float,
                 level: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        """Retrieve logs in time range"""
        with self.lock:
            if source not in self.logs:
                self.stats.total_misses += 1
                return []
            
            result = []
            expired_keys = []
            
            for key, entry in self.logs[source].items():
                if entry.is_expired():
                    expired_keys.append(key)
                    continue
                
                log = entry.value
                ts = log.get("timestamp", 0)
                
                if start_time <= ts <= end_time:
                    if level is None or log.get("level") == level:
                        entry.access()
                        result.append(log)
                        self.stats.total_hits += 1
                        
                        if len(result) >= limit:
                            break
            
            # Clean expired entries
            for key in expired_keys:
                del self.logs[source][key]
                self.stats.evictions_ttl += 1
            
            if not result:
                self.stats.total_misses += 1
            
            return result
    
    def get_recent_logs(self, source: str, limit: int = 100,
                       level: Optional[str] = None) -> List[Dict]:
        """Get most recent logs"""
        with self.lock:
            if source not in self.logs:
                self.stats.total_misses += 1
                return []
            
            result = []
            for key, entry in reversed(list(self.logs[source].items())):
                if entry.is_expired():
                    del self.logs[source][key]
                    self.stats.evictions_ttl += 1
                    continue
                
                log = entry.value
                if level is None or log.get("level") == level:
                    entry.access()
                    result.append(log)
                    self.stats.total_hits += 1
                    
                    if len(result) >= limit:
                        break
            
            if not result:
                self.stats.total_misses += 1
            
            return result
    
    def clear_source(self, source: str) -> None:
        """Clear all logs for a source"""
        with self.lock:
            if source in self.logs:
                del self.logs[source]
                self._trigger_callback("logs_cleared", source)


class TraceCache:
    """Distributed trace caching with span aggregation"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.traces: Dict[str, Dict] = {}
        self.spans: Dict[str, OrderedDict] = {}
        self.lock = threading.RLock()
        self.stats = CacheStatistics(max_size=config.max_entries)
        self.callbacks: List[Callable] = []
    
    def put_trace(self, trace_id: str, trace_data: Dict[str, Any],
                  ttl_seconds: Optional[int] = None) -> None:
        """Store trace information"""
        with self.lock:
            ttl = ttl_seconds or self.config.default_ttl_seconds
            
            entry = CacheEntry(trace_id, trace_data, time.time(), ttl)
            self.traces[trace_id] = entry
            self.stats.current_size += 1
            
            self._trigger_callback("trace_cached", trace_id, trace_data)
    
    def put_span(self, trace_id: str, span_id: str, span_data: Dict[str, Any],
                 ttl_seconds: Optional[int] = None) -> None:
        """Store span data for a trace"""
        with self.lock:
            ttl = ttl_seconds or self.config.default_ttl_seconds
            
            if trace_id not in self.spans:
                self.spans[trace_id] = OrderedDict()
            
            entry = CacheEntry(span_id, span_data, time.time(), ttl)
            self.spans[trace_id][span_id] = entry
            
            self._trigger_callback("span_cached", trace_id, span_id, span_data)
    
    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Retrieve complete trace with spans"""
        with self.lock:
            if trace_id not in self.traces:
                self.stats.total_misses += 1
                return None
            
            entry = self.traces[trace_id]
            if entry.is_expired():
                del self.traces[trace_id]
                self.stats.evictions_ttl += 1
                self.stats.total_misses += 1
                return None
            
            entry.access()
            self.stats.total_hits += 1
            
            trace_data = entry.value.copy()
            
            # Include spans
            if trace_id in self.spans:
                spans = []
                expired_spans = []
                
                for span_id, span_entry in self.spans[trace_id].items():
                    if span_entry.is_expired():
                        expired_spans.append(span_id)
                    else:
                        spans.append(span_entry.value)
                
                trace_data["spans"] = spans
                
                # Clean expired spans
                for span_id in expired_spans:
                    del self.spans[trace_id][span_id]
                    self.stats.evictions_ttl += 1
            
            return trace_data
    
    def get_traces(self, start_time: float, end_time: float,
                   service: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve traces in time range"""
        with self.lock:
            result = []
            expired_traces = []
            
            for trace_id, entry in self.traces.items():
                if entry.is_expired():
                    expired_traces.append(trace_id)
                    continue
                
                trace = entry.value
                ts = trace.get("timestamp", 0)
                
                if start_time <= ts <= end_time:
                    if service is None or trace.get("service") == service:
                        entry.access()
                        trace_copy = trace.copy()
                        
                        # Add spans if available
                        if trace_id in self.spans:
                            spans = []
                            for sid, sentry in self.spans[trace_id].items():
                                if not sentry.is_expired():
                                    spans.append(sentry.value)
                            trace_copy["spans"] = spans
                        
                        result.append(trace_copy)
                        self.stats.total_hits += 1
                        
                        if len(result) >= limit:
                            break
            
            # Clean expired
            for trace_id in expired_traces:
                del self.traces[trace_id]
                self.stats.evictions_ttl += 1
            
            if not result:
                self.stats.total_misses += 1
            
            return result


class QueryResultCache:
    """Cache for expensive query results"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.results: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()
        self.stats = CacheStatistics(max_size=config.max_entries)
        self.callbacks: List[Callable] = []
    
    def _query_hash(self, query_type: str, params: Dict) -> str:
        """Generate cache key from query"""
        param_str = json.dumps(params, sort_keys=True, default=str)
        return f"{query_type}:{hash(param_str)}"
    
    def put_result(self, query_type: str, params: Dict, result: Any,
                   ttl_seconds: Optional[int] = None) -> None:
        """Cache query result"""
        with self.lock:
            ttl = ttl_seconds or self.config.default_ttl_seconds
            cache_key = self._query_hash(query_type, params)
            
            entry = CacheEntry(cache_key, result, time.time(), ttl)
            self.results[cache_key] = entry
            self.stats.current_size += 1
            
            # Enforce max size
            if self.stats.current_size > self.config.max_entries:
                self._evict_lru()
            
            self._trigger_callback("query_result_cached", query_type, cache_key)
    
    def get_result(self, query_type: str, params: Dict) -> Optional[Any]:
        """Retrieve cached query result"""
        with self.lock:
            cache_key = self._query_hash(query_type, params)
            
            if cache_key not in self.results:
                self.stats.total_misses += 1
                return None
            
            entry = self.results[cache_key]
            if entry.is_expired():
                del self.results[cache_key]
                self.stats.evictions_ttl += 1
                self.stats.total_misses += 1
                return None
            
            entry.access()
            self.stats.total_hits += 1
            return entry.value
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.results:
            return
        
        lru_key = min(self.results.keys(),
                      key=lambda k: self.results[k].last_accessed)
        del self.results[lru_key]
        self.stats.evictions_lru += 1
        self.stats.current_size -= 1


class ObservabilityCacheManager:
    """Central cache manager for all observability data"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.metric_cache = MetricCache(self.config)
        self.log_cache = LogCache(self.config)
        self.trace_cache = TraceCache(self.config)
        self.query_cache = QueryResultCache(self.config)
        
        self.callbacks: List[Callable[[str, ...], None]] = []
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.running = False
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self) -> None:
        """Start background thread for cache cleanup"""
        self.running = True
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
    
    def _cleanup_loop(self) -> None:
        """Periodically cleanup expired entries"""
        while self.running:
            try:
                time.sleep(self.config.cleanup_interval_seconds)
                self._cleanup_expired_entries()
            except Exception as e:
                # Log error but continue
                pass
    
    def _cleanup_expired_entries(self) -> None:
        """Remove all expired entries from all caches"""
        with self.lock:
            # Metric cache cleanup
            for metric_name in list(self.metric_cache.cache.keys()):
                expired = []
                for ts, entry in self.metric_cache.cache[metric_name].items():
                    if entry.is_expired():
                        expired.append(ts)
                
                for ts in expired:
                    del self.metric_cache.cache[metric_name][ts]
            
            # Log cache cleanup
            for source in list(self.log_cache.logs.keys()):
                expired = []
                for key, entry in self.log_cache.logs[source].items():
                    if entry.is_expired():
                        expired.append(key)
                
                for key in expired:
                    del self.log_cache.logs[source][key]
            
            # Trace cache cleanup
            expired_traces = []
            for trace_id, entry in self.metric_cache.cache.items():
                if entry.is_expired():
                    expired_traces.append(trace_id)
            
            for trace_id in expired_traces:
                if trace_id in self.trace_cache.traces:
                    del self.trace_cache.traces[trace_id]
    
    # Metric cache delegation
    def cache_metric(self, metric_name: str, value: float, timestamp: float,
                    ttl_seconds: Optional[int] = None) -> None:
        """Cache metric value"""
        self.metric_cache.put_metric(metric_name, value, timestamp, ttl_seconds)
    
    def get_metric_range(self, metric_name: str, start_time: float,
                        end_time: float) -> List[Tuple[float, float]]:
        """Get metric values in range"""
        return self.metric_cache.get_metric(metric_name, start_time, end_time)
    
    def get_latest_metric(self, metric_name: str) -> Optional[Tuple[float, float]]:
        """Get latest metric value"""
        return self.metric_cache.get_latest_metric(metric_name)
    
    # Log cache delegation
    def cache_log(self, source: str, log_entry: Dict[str, Any],
                 ttl_seconds: Optional[int] = None) -> None:
        """Cache log entry"""
        self.log_cache.put_log(source, log_entry, ttl_seconds)
    
    def get_logs(self, source: str, start_time: float, end_time: float,
                 level: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        """Get logs in range"""
        return self.log_cache.get_logs(source, start_time, end_time, level, limit)
    
    def get_recent_logs(self, source: str, limit: int = 100,
                       level: Optional[str] = None) -> List[Dict]:
        """Get recent logs"""
        return self.log_cache.get_recent_logs(source, limit, level)
    
    # Trace cache delegation
    def cache_trace(self, trace_id: str, trace_data: Dict[str, Any],
                   ttl_seconds: Optional[int] = None) -> None:
        """Cache trace"""
        self.trace_cache.put_trace(trace_id, trace_data, ttl_seconds)
    
    def cache_span(self, trace_id: str, span_id: str, span_data: Dict[str, Any],
                  ttl_seconds: Optional[int] = None) -> None:
        """Cache span"""
        self.trace_cache.put_span(trace_id, span_id, span_data, ttl_seconds)
    
    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Get trace with spans"""
        return self.trace_cache.get_trace(trace_id)
    
    def get_traces(self, start_time: float, end_time: float,
                   service: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get traces in range"""
        return self.trace_cache.get_traces(start_time, end_time, service, limit)
    
    # Query result cache delegation
    def cache_query_result(self, query_type: str, params: Dict, result: Any,
                          ttl_seconds: Optional[int] = None) -> None:
        """Cache query result"""
        self.query_cache.put_result(query_type, params, result, ttl_seconds)
    
    def get_query_result(self, query_type: str, params: Dict) -> Optional[Any]:
        """Get cached query result"""
        return self.query_cache.get_result(query_type, params)
    
    def register_callback(self, callback: Callable[[str, ...], None]) -> None:
        """Register event callback"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callback(self, event_type: str, *args, **kwargs) -> None:
        """Trigger registered callbacks"""
        with self.lock:
            for callback in self.callbacks:
                try:
                    callback(event_type, *args, **kwargs)
                except Exception:
                    pass
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self.lock:
            return {
                "metrics": {
                    "total_Series": len(self.metric_cache.cache),
                    "hits": self.metric_cache.stats.total_hits,
                    "misses": self.metric_cache.stats.total_misses,
                    "hit_rate": self.metric_cache.stats.hit_rate,
                    "size": self.metric_cache.stats.current_size,
                },
                "logs": {
                    "total_sources": len(self.log_cache.logs),
                    "hits": self.log_cache.stats.total_hits,
                    "misses": self.log_cache.stats.total_misses,
                    "hit_rate": self.log_cache.stats.hit_rate,
                    "size": self.log_cache.stats.current_size,
                },
                "traces": {
                    "total_traces": len(self.trace_cache.traces),
                    "total_spans": sum(len(s) for s in self.trace_cache.spans.values()),
                    "hits": self.trace_cache.stats.total_hits,
                    "misses": self.trace_cache.stats.total_misses,
                    "hit_rate": self.trace_cache.stats.hit_rate,
                },
                "queries": {
                    "cached_results": len(self.query_cache.results),
                    "hits": self.query_cache.stats.total_hits,
                    "misses": self.query_cache.stats.total_misses,
                    "hit_rate": self.query_cache.stats.hit_rate,
                    "evictions_lru": self.query_cache.stats.evictions_lru,
                },
                "total_evictions": (
                    self.metric_cache.stats.evictions_ttl +
                    self.log_cache.stats.evictions_fifo +
                    self.trace_cache.stats.evictions_ttl +
                    self.query_cache.stats.evictions_lru
                ),
            }
    
    def clear_all(self) -> None:
        """Clear all caches"""
        with self.lock:
            self.metric_cache.cache.clear()
            self.log_cache.logs.clear()
            self.trace_cache.traces.clear()
            self.trace_cache.spans.clear()
            self.query_cache.results.clear()
            self._trigger_callback("all_caches_cleared")
    
    def shutdown(self) -> None:
        """Shutdown cache manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)


# Singleton instance for application
_cache_manager: Optional[ObservabilityCacheManager] = None


def get_cache_manager() -> ObservabilityCacheManager:
    """Get or create singleton cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ObservabilityCacheManager()
    return _cache_manager


def reset_cache_manager() -> None:
    """Reset cache manager (for testing)"""
    global _cache_manager
    if _cache_manager:
        _cache_manager.shutdown()
    _cache_manager = None
