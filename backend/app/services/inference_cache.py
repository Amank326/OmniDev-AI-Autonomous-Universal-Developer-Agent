"""
Inference Cache Service - Cache predictions for fast retrieval and cost reduction.

Implements multi-level caching (in-memory, local, distributed) with TTL, LRU eviction,
and cache invalidation strategies for real-time inference optimization.
"""

import time
import hashlib
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from threading import RLock
from collections import OrderedDict, deque
import threading


class CacheLevel(Enum):
    """Cache levels."""
    L1_MEMORY = "l1_memory"  # In-process memory
    L2_LOCAL = "l2_local"  # Local disk/file
    L3_DISTRIBUTED = "l3_distributed"  # Distributed cache (Redis)


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    FIFO = "fifo"  # First in first out
    TTL = "ttl"  # Time to live


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""
    TTL = "ttl"  # Time-based expiration
    MANUAL = "manual"  # Manual invalidation
    FEATURE_CHANGE = "feature_change"  # Invalidate on feature changes
    MODEL_UPDATE = "model_update"  # Invalidate on model update


@dataclass
class CacheEntry:
    """Single cache entry."""
    key: str
    value: Any
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 3600
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheConfig:
    """Cache configuration."""
    max_entries: int = 100000
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    invalidation_strategy: InvalidationStrategy = InvalidationStrategy.TTL
    ttl_seconds: int = 3600
    enable_compression: bool = False
    enable_distributed: bool = False
    distributed_backend: str = ""  # redis, memcached


class CacheStatistics:
    """Tracks cache performance statistics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.invalidations = 0
        self.lock = RLock()
    
    def record_hit(self) -> None:
        """Record cache hit."""
        with self.lock:
            self.hits += 1
    
    def record_miss(self) -> None:
        """Record cache miss."""
        with self.lock:
            self.misses += 1
    
    def record_eviction(self) -> None:
        """Record eviction."""
        with self.lock:
            self.evictions += 1
    
    def record_invalidation(self) -> None:
        """Record invalidation."""
        with self.lock:
            self.invalidations += 1
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        with self.lock:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        with self.lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": self.get_hit_rate(),
                "evictions": self.evictions,
                "invalidations": self.invalidations
            }


class InferenceCache:
    """Multi-level inference cache."""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.l2_cache: Dict[str, CacheEntry] = {}  # Local disk simulation
        self.statistics = CacheStatistics()
        self.lock = RLock()
        self.callbacks: Dict[str, List] = {}
        self.cleanup_thread = None
        self._start_cleanup_worker()
    
    def get(self, key: str, cache_level: CacheLevel = CacheLevel.L1_MEMORY) -> Optional[Any]:
        """Get value from cache."""
        if cache_level == CacheLevel.L1_MEMORY:
            return self._get_from_l1(key)
        elif cache_level == CacheLevel.L2_LOCAL:
            return self._get_from_l2(key)
        elif cache_level == CacheLevel.L3_DISTRIBUTED:
            # Mock distributed cache
            return None
        
        return None
    
    def _get_from_l1(self, key: str) -> Optional[Any]:
        """Get from L1 memory cache."""
        with self.lock:
            if key not in self.l1_cache:
                self.statistics.record_miss()
                return None
            
            entry = self.l1_cache[key]
            
            # Check TTL
            if time.time() - entry.created_at > entry.ttl_seconds:
                del self.l1_cache[key]
                self.statistics.record_miss()
                self._trigger_callback("entry_expired", key)
                return None
            
            # Update LRU
            entry.last_accessed = time.time()
            entry.hit_count += 1
            self.l1_cache.move_to_end(key)
            
            self.statistics.record_hit()
            return entry.value
    
    def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get from L2 local cache."""
        with self.lock:
            if key not in self.l2_cache:
                self.statistics.record_miss()
                return None
            
            entry = self.l2_cache[key]
            
            # Check TTL
            if time.time() - entry.created_at > entry.ttl_seconds:
                del self.l2_cache[key]
                self.statistics.record_miss()
                return None
            
            entry.last_accessed = time.time()
            entry.hit_count += 1
            
            self.statistics.record_hit()
            return entry.value
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
            metadata: Optional[Dict] = None, cache_level: CacheLevel = CacheLevel.L1_MEMORY) -> None:
        """Store value in cache."""
        if ttl_seconds is None:
            ttl_seconds = self.config.ttl_seconds
        
        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            metadata=metadata or {}
        )
        
        if cache_level == CacheLevel.L1_MEMORY:
            self._put_in_l1(entry)
        elif cache_level == CacheLevel.L2_LOCAL:
            self._put_in_l2(entry)
        elif cache_level == CacheLevel.L3_DISTRIBUTED:
            pass  # Mock distributed
    
    def _put_in_l1(self, entry: CacheEntry) -> None:
        """Store in L1 memory cache."""
        with self.lock:
            # Check if we need to evict
            if len(self.l1_cache) >= self.config.max_entries:
                self._evict_from_l1()
            
            self.l1_cache[entry.key] = entry
            self.l1_cache.move_to_end(entry.key)
        
        self._trigger_callback("entry_cached", entry.key)
    
    def _put_in_l2(self, entry: CacheEntry) -> None:
        """Store in L2 local cache (simulated)."""
        with self.lock:
            if len(self.l2_cache) >= self.config.max_entries * 10:
                self._evict_from_l2()
            
            self.l2_cache[entry.key] = entry
    
    def _evict_from_l1(self) -> None:
        """Evict entry from L1 cache based on policy."""
        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Remove least recently used (first item since OrderedDict)
            key, entry = self.l1_cache.popitem(last=False)
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used
            lfu_key = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k].hit_count)
            key = lfu_key
            del self.l1_cache[lfu_key]
        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # Remove oldest
            key, entry = self.l1_cache.popitem(last=False)
        else:
            return
        
        self.statistics.record_eviction()
        self._trigger_callback("entry_evicted", key)
    
    def _evict_from_l2(self) -> None:
        """Evict entry from L2 cache."""
        if not self.l2_cache:
            return
        
        if self.config.eviction_policy == EvictionPolicy.LRU:
            lru_key = min(self.l2_cache.keys(), key=lambda k: self.l2_cache[k].last_accessed)
            del self.l2_cache[lru_key]
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            lfu_key = min(self.l2_cache.keys(), key=lambda k: self.l2_cache[k].hit_count)
            del self.l2_cache[lfu_key]
        
        self.statistics.record_eviction()
    
    def invalidate(self, key: str) -> bool:
        """Invalidate cache entry."""
        with self.lock:
            removed_l1 = False
            removed_l2 = False
            
            if key in self.l1_cache:
                del self.l1_cache[key]
                removed_l1 = True
            
            if key in self.l2_cache:
                del self.l2_cache[key]
                removed_l2 = True
            
            if removed_l1 or removed_l2:
                self.statistics.record_invalidation()
                self._trigger_callback("entry_invalidated", key)
                return True
        
        return False
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        count = 0
        with self.lock:
            keys_to_remove = [k for k in self.l1_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.l1_cache[key]
                count += 1
            
            keys_to_remove = [k for k in self.l2_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.l2_cache[key]
                count += 1
        
        if count > 0:
            self.statistics.record_invalidation()
        
        return count
    
    def invalidate_by_model(self, model_version: str) -> int:
        """Invalidate cache for model version."""
        # Cache keys typically include model version
        return self.invalidate_by_pattern(model_version)
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self.lock:
            self.l1_cache.clear()
            self.l2_cache.clear()
    
    def get_size(self) -> Dict[str, int]:
        """Get cache size."""
        with self.lock:
            return {
                "l1_entries": len(self.l1_cache),
                "l2_entries": len(self.l2_cache),
                "total": len(self.l1_cache) + len(self.l2_cache)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        size = self.get_size()
        stats = self.statistics.to_dict()
        
        return {
            **stats,
            **size,
            "max_entries": self.config.max_entries,
            "eviction_policy": self.config.eviction_policy.value,
            "ttl_seconds": self.config.ttl_seconds
        }
    
    def _start_cleanup_worker(self) -> None:
        """Start background cleanup worker."""
        def cleanup():
            while True:
                time.sleep(60)  # Cleanup every 60 seconds
                self._cleanup_expired_entries()
        
        self.cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_thread.start()
    
    def _cleanup_expired_entries(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        removed_count = 0
        
        with self.lock:
            # L1 cleanup
            expired_keys = []
            for key, entry in self.l1_cache.items():
                if current_time - entry.created_at > entry.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.l1_cache[key]
                removed_count += 1
            
            # L2 cleanup
            expired_keys = []
            for key, entry in self.l2_cache.items():
                if current_time - entry.created_at > entry.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.l2_cache[key]
                removed_count += 1
        
        if removed_count > 0:
            self._trigger_callback("cleanup_completed", removed_count)
    
    def warm_cache(self, keys_and_values: Dict[str, Any], cache_level: CacheLevel = CacheLevel.L1_MEMORY) -> None:
        """Pre-populate cache with values."""
        for key, value in keys_and_values.items():
            self.put(key, value, cache_level=cache_level)
    
    def register_callback(self, event: str, callback) -> None:
        """Register callback."""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, *args) -> None:
        """Trigger callbacks."""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args)
            except:
                pass


class CacheKey:
    """Utility for creating consistent cache keys."""
    
    @staticmethod
    def for_prediction(model_version: str, input_features: Dict[str, Any]) -> str:
        """Create cache key for prediction."""
        feature_json = json.dumps(input_features, sort_keys=True)
        feature_hash = hashlib.md5(feature_json.encode()).hexdigest()
        return f"pred:{model_version}:{feature_hash}"
    
    @staticmethod
    def for_feature_vector(entity_id: str, feature_set: str) -> str:
        """Create cache key for feature vector."""
        return f"feat:{feature_set}:{entity_id}"
    
    @staticmethod
    def for_evaluation(model_version: str, dataset_name: str) -> str:
        """Create cache key for evaluation."""
        return f"eval:{model_version}:{dataset_name}"


# Singleton instance
_inference_cache: Optional[InferenceCache] = None


def get_inference_cache(config: Optional[CacheConfig] = None) -> InferenceCache:
    """Get or create inference cache instance."""
    global _inference_cache
    if _inference_cache is None:
        _inference_cache = InferenceCache(config)
    return _inference_cache
