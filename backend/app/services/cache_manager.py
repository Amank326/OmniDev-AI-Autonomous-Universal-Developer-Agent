"""
Cache Manager Service
Multi-level caching with Redis and in-memory support.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
import json
import hashlib
import threading
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache hierarchy levels."""
    L1_MEMORY = "memory"      # In-memory (fastest)
    L2_REDIS = "redis"        # Distributed cache (medium)
    L3_DATABASE = "database"  # Persistent (slowest)


class EvictionPolicy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"              # Least Recently Used
    LFU = "lfu"              # Least Frequently Used
    FIFO = "fifo"            # First In First Out
    TTL = "ttl"              # Time To Live


class CacheReason(Enum):
    """Reasons for cache operations."""
    HIT = "hit"
    MISS = "miss"
    EXPIRED = "expired"
    EVICTED = "evicted"
    INVALIDATED = "invalidated"


@dataclass
class CacheEntry:
    """Represents a single cache entry."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: Optional[int] = None
    access_count: int = 0
    size_bytes: int = 0
    tags: Set[str] = field(default_factory=set)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds is None:
            return False
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def touch(self) -> None:
        """Update last access time."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


@dataclass
class CacheStatistics:
    """Cache performance statistics."""
    total_gets: int = 0
    total_puts: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    invalidations: int = 0
    total_entries: int = 0
    memory_used_bytes: int = 0
    hit_ratio: float = 0.0
    avg_get_time_ms: float = 0.0
    avg_put_time_ms: float = 0.0
    
    def update(self, reason: CacheReason) -> None:
        """Update statistics based on operation."""
        if reason == CacheReason.HIT:
            self.hits += 1
        elif reason == CacheReason.MISS:
            self.misses += 1
        elif reason == CacheReason.EVICTED:
            self.evictions += 1
        elif reason == CacheReason.EXPIRED:
            self.expirations += 1
        elif reason == CacheReason.INVALIDATED:
            self.invalidations += 1
        
        total = self.hits + self.misses
        self.hit_ratio = (self.hits / total * 100) if total > 0 else 0.0


@dataclass
class CacheConfiguration:
    """Cache configuration."""
    max_memory_bytes: int = 1024 * 1024 * 100  # 100 MB
    max_entries: int = 100000
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    default_ttl_seconds: Optional[int] = 3600  # 1 hour
    enable_compression: bool = True
    compression_threshold_bytes: int = 1024  # Compress if >1KB
    enable_redis: bool = False
    redis_url: str = "redis://localhost:6379/0"
    cleanup_interval_seconds: int = 300  # 5 minutes
    

class CacheManager:
    """Multi-level cache manager with Redis and in-memory support."""
    
    def __init__(self, config: Optional[CacheConfiguration] = None):
        """Initialize cache manager."""
        self.config = config or CacheConfiguration()
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStatistics()
        self.lock = threading.RLock()
        self.redis_client = None
        self.tag_index: Dict[str, Set[str]] = {}
        self.callbacks: Dict[str, List[Callable]] = {
            'on_eviction': [],
            'on_expiration': [],
            'on_invalidation': [],
            'on_hit': [],
            'on_miss': []
        }
        
        if self.config.enable_redis:
            try:
                import redis
                self.redis_client = redis.from_url(self.config.redis_url)
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory only")
    
    def get(self, key: str, compute_fn: Optional[Callable] = None) -> Any:
        """Get value from cache with optional compute function."""
        with self.lock:
            self.stats.total_gets += 1
            
            # Check L1 memory cache
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired():
                    self._remove_entry(key, CacheReason.EXPIRED)
                    self.stats.update(CacheReason.EXPIRED)
                    self._trigger_callbacks('on_expiration', key)
                else:
                    entry.touch()
                    self.stats.update(CacheReason.HIT)
                    self._trigger_callbacks('on_hit', key)
                    # Move to end (for LRU)
                    self.cache.move_to_end(key)
                    return entry.value
            
            # Check L2 Redis cache
            if self.redis_client:
                try:
                    value = self.redis_client.get(key)
                    if value:
                        self.stats.update(CacheReason.HIT)
                        self._trigger_callbacks('on_hit', key)
                        # Promote to L1
                        entry = CacheEntry(key=key, value=json.loads(value))
                        self.cache[key] = entry
                        self._evict_if_needed()
                        return entry.value
                except Exception as e:
                    logger.warning(f"Redis get failed for {key}: {e}")
            
            # Cache miss - compute if function provided
            self.stats.update(CacheReason.MISS)
            self._trigger_callbacks('on_miss', key)
            
            if compute_fn:
                value = compute_fn()
                self.put(key, value)
                return value
            
            return None
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            tags: Optional[Set[str]] = None) -> None:
        """Store value in cache."""
        with self.lock:
            self.stats.total_puts += 1
            
            # Create entry
            ttl = ttl_seconds or self.config.default_ttl_seconds
            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl,
                tags=tags or set()
            )
            entry.size_bytes = self._estimate_size(value)
            
            # Store in L1
            self.cache[key] = entry
            self._evict_if_needed()
            
            # Store in L2 Redis
            if self.redis_client:
                try:
                    ttl_redis = ttl if ttl else -1
                    self.redis_client.setex(
                        key,
                        ttl_redis,
                        json.dumps(value, default=str)
                    )
                except Exception as e:
                    logger.warning(f"Redis put failed for {key}: {e}")
            
            # Update tag index
            for tag in entry.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(key)
            
            # Update stats
            self.stats.total_entries = len(self.cache)
            self.stats.memory_used_bytes = sum(e.size_bytes for e in self.cache.values())
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self._remove_entry(key, CacheReason.INVALIDATED)
                self.stats.update(CacheReason.INVALIDATED)
                self._trigger_callbacks('on_invalidation', key)
                
                # Remove from Redis
                if self.redis_client:
                    try:
                        self.redis_client.delete(key)
                    except Exception as e:
                        logger.warning(f"Redis delete failed for {key}: {e}")
                
                return True
            return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with given tag."""
        with self.lock:
            keys = self.tag_index.get(tag, set()).copy()
            count = 0
            for key in keys:
                if self.delete(key):
                    count += 1
            return count
    
    def clear(self) -> None:
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
            self.tag_index.clear()
            if self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception as e:
                    logger.warning(f"Redis flush failed: {e}")
            self.stats = CacheStatistics()
    
    def warmup(self, data: Dict[str, tuple[Any, Optional[int]]]) -> None:
        """Warm up cache with initial data."""
        with self.lock:
            for key, (value, ttl) in data.items():
                self.put(key, value, ttl)
    
    def cleanup(self) -> int:
        """Remove expired entries."""
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key, CacheReason.EXPIRED)
                self.stats.update(CacheReason.EXPIRED)
            
            return len(expired_keys)
    
    def get_stats(self) -> CacheStatistics:
        """Get cache statistics."""
        with self.lock:
            stats = CacheStatistics(
                total_gets=self.stats.total_gets,
                total_puts=self.stats.total_puts,
                hits=self.stats.hits,
                misses=self.stats.misses,
                evictions=self.stats.evictions,
                expirations=self.stats.expirations,
                invalidations=self.stats.invalidations,
                total_entries=len(self.cache),
                memory_used_bytes=sum(e.size_bytes for e in self.cache.values())
            )
            total = stats.hits + stats.misses
            stats.hit_ratio = (stats.hits / total * 100) if total > 0 else 0.0
            return stats
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for cache events."""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def size(self) -> int:
        """Get cache size."""
        with self.lock:
            return len(self.cache)
    
    # Private methods
    
    def _evict_if_needed(self) -> None:
        """Evict entries if limits are exceeded."""
        # Check entry count limit
        while len(self.cache) > self.config.max_entries:
            self._evict_one()
        
        # Check memory limit
        total_memory = sum(e.size_bytes for e in self.cache.values())
        while total_memory > self.config.max_memory_bytes:
            self._evict_one()
            total_memory = sum(e.size_bytes for e in self.cache.values())
    
    def _evict_one(self) -> None:
        """Evict single entry based on policy."""
        if not self.cache:
            return
        
        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Remove least recently used (first in OrderedDict)
            key = next(iter(self.cache))
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used
            key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # Remove oldest
            key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        else:  # TTL
            key = next(iter(self.cache))
        
        self._remove_entry(key, CacheReason.EVICTED)
        self.stats.update(CacheReason.EVICTED)
        self._trigger_callbacks('on_eviction', key)
    
    def _remove_entry(self, key: str, reason: CacheReason) -> None:
        """Remove entry from cache."""
        if key in self.cache:
            entry = self.cache.pop(key)
            
            # Remove from tag index
            for tag in entry.tags:
                if tag in self.tag_index:
                    self.tag_index[tag].discard(key)
                    if not self.tag_index[tag]:
                        del self.tag_index[tag]
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes."""
        try:
            if isinstance(value, str):
                return len(value.encode())
            elif isinstance(value, bytes):
                return len(value)
            else:
                return len(json.dumps(value, default=str).encode())
        except:
            return 1024  # Default estimate
    
    def _trigger_callbacks(self, event: str, key: str) -> None:
        """Trigger registered callbacks."""
        for callback in self.callbacks.get(event, []):
            try:
                callback(key)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache_manager(config: Optional[CacheConfiguration] = None) -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(config)
    return _cache_instance


def reset_cache_manager() -> None:
    """Reset global cache instance (for testing)."""
    global _cache_instance
    _cache_instance = None
