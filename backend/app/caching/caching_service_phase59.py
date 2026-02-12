"""
Phase 59: Advanced Caching & Cache Management
Multi-tier caching, Redis integration, invalidation strategies, and cache patterns.
"""

import time
import threading
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set, Callable, Tuple
from enum import Enum
from collections import OrderedDict
import pickle


# ===================== ENUMS =====================

class CacheStrategy(Enum):
    """Cache replacement strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    MRU = "mru"  # Most Recently Used
    ARC = "arc"  # Adaptive Replacement Cache


class CachePattern(Enum):
    """Cache design patterns."""
    CACHE_ASIDE = "cache_aside"  # Check cache first, fetch from DB if miss
    WRITE_THROUGH = "write_through"  # Write to cache and DB simultaneously
    WRITE_BEHIND = "write_behind"  # Write to cache, async DB
    REFRESH_AHEAD = "refresh_ahead"  # Proactively refresh before expiry


class CacheTier(Enum):
    """Cache hierarchy tiers."""
    L1 = "l1"  # In-memory local cache
    L2 = "l2"  # Redis distributed cache
    L3 = "l3"  # Database


class InvalidationType(Enum):
    """Cache invalidation types."""
    TTL = "ttl"  # Time-to-live expiration
    LRU_EVICTION = "lru_eviction"  # Evict least recently used
    TAG_BASED = "tag_based"  # Invalidate by tag
    PATTERN_BASED = "pattern_based"  # Invalidate by pattern
    EVENT_BASED = "event_based"  # Invalidate on event
    MANUAL = "manual"  # Manual invalidation


class CacheHitType(Enum):
    """Cache hit classification."""
    HIT = "hit"
    MISS = "miss"
    STALE = "stale"
    PARTIAL = "partial"


# ===================== DATA CLASSES =====================

@dataclass
class CacheEntry:
    """Individual cache entry."""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    accessed_count: int = 0
    ttl_seconds: Optional[int] = None
    tags: Set[str] = field(default_factory=set)
    size_bytes: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds
    
    def to_dict(self):
        return {
            "key": self.key,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "accessed_count": self.accessed_count,
            "ttl_seconds": self.ttl_seconds,
            "tags": list(self.tags),
            "size_bytes": self.size_bytes
        }


@dataclass
class CacheConfig:
    """Cache configuration."""
    max_size_mb: int = 100
    max_entries: int = 10000
    default_ttl_seconds: int = 3600
    strategy: CacheStrategy = CacheStrategy.LRU
    pattern: CachePattern = CachePattern.CACHE_ASIDE
    enable_compression: bool = False
    enable_encryption: bool = False
    persistence_enabled: bool = False
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "max_size_mb": self.max_size_mb,
            "max_entries": self.max_entries,
            "default_ttl_seconds": self.default_ttl_seconds,
            "strategy": self.strategy.value,
            "pattern": self.pattern.value,
            "enable_compression": self.enable_compression,
            "enable_encryption": self.enable_encryption,
            "persistence_enabled": self.persistence_enabled
        }


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    writes: int = 0
    deletes: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    avg_entry_size_bytes: float = 0.0
    last_updated: float = field(default_factory=time.time)
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self):
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate, 2),
            "evictions": self.evictions,
            "invalidations": self.invalidations,
            "writes": self.writes,
            "deletes": self.deletes,
            "total_size_bytes": self.total_size_bytes,
            "entry_count": self.entry_count,
            "avg_entry_size_bytes": round(self.avg_entry_size_bytes, 2)
        }


@dataclass
class InvalidationRule:
    """Cache invalidation rule."""
    rule_id: str
    rule_type: InvalidationType
    target_keys: Set[str] = field(default_factory=set)
    target_tags: Set[str] = field(default_factory=set)
    pattern: Optional[str] = None  # Regex pattern
    ttl_seconds: Optional[int] = None
    created_at: float = field(default_factory=time.time)
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "target_keys": list(self.target_keys),
            "target_tags": list(self.target_tags),
            "pattern": self.pattern,
            "ttl_seconds": self.ttl_seconds,
            "created_at": self.created_at,
            "enabled": self.enabled
        }


@dataclass
class WarmupStrategy:
    """Cache warmup configuration."""
    strategy_id: str
    data_source: str  # "function", "database", "api"
    source_config: Dict = field(default_factory=dict)
    keys_to_load: List[str] = field(default_factory=list)
    batch_size: int = 100
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "strategy_id": self.strategy_id,
            "data_source": self.data_source,
            "batch_size": self.batch_size,
            "keys_count": len(self.keys_to_load),
            "enabled": self.enabled,
            "created_at": self.created_at
        }


# ===================== CACHE SERVICES =====================

class L1MemoryCache:
    """In-memory L1 cache with LRU/LFU/FIFO strategies."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, CacheEntry] = OrderedDict()
        self._metrics = CacheMetrics()
        self._lock = threading.Lock()
        self._access_freq: Dict[str, int] = {}  # For LFU
    
    def get(self, key: str) -> Tuple[bool, Optional[Any]]:
        """Get value from cache. Returns (found, value)."""
        with self._lock:
            if key not in self._cache:
                self._metrics.misses += 1
                return False, None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._metrics.misses += 1
                return False, None
            
            # Update access metrics
            entry.last_accessed = time.time()
            entry.accessed_count += 1
            self._access_freq[key] = self._access_freq.get(key, 0) + 1
            
            # Move to end for LRU (OrderedDict)
            if self.config.strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)
            
            self._metrics.hits += 1
            return True, entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, tags: Set[str] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            ttl = ttl_seconds or self.config.default_ttl_seconds
            size_bytes = len(pickle.dumps(value))
            
            # Check size limits
            if self._metrics.total_size_bytes + size_bytes > self.config.max_size_mb * 1024 * 1024:
                self._evict_entries(size_bytes)
            
            if len(self._cache) >= self.config.max_entries:
                self._evict_entry()
            
            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl,
                tags=tags or set(),
                size_bytes=size_bytes
            )
            
            # Update existing entry size
            if key in self._cache:
                self._metrics.total_size_bytes -= self._cache[key].size_bytes
            
            self._cache[key] = entry
            self._metrics.total_size_bytes += size_bytes
            self._metrics.writes += 1
            self._update_avg_size()
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete from cache."""
        with self._lock:
            if key in self._cache:
                self._metrics.total_size_bytes -= self._cache[key].size_bytes
                del self._cache[key]
                self._access_freq.pop(key, None)
                self._metrics.deletes += 1
                self._update_avg_size()
                return True
            return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with tag. Returns count invalidated."""
        with self._lock:
            keys_to_delete = [k for k, v in self._cache.items() if tag in v.tags]
            
            for key in keys_to_delete:
                self._metrics.total_size_bytes -= self._cache[key].size_bytes
                del self._cache[key]
                self._access_freq.pop(key, None)
            
            self._metrics.invalidations += len(keys_to_delete)
            self._update_avg_size()
            return len(keys_to_delete)
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate entries matching key pattern. Returns count."""
        import re
        with self._lock:
            regex = re.compile(pattern)
            keys_to_delete = [k for k in self._cache.keys() if regex.match(k)]
            
            for key in keys_to_delete:
                self._metrics.total_size_bytes -= self._cache[key].size_bytes
                del self._cache[key]
                self._access_freq.pop(key, None)
            
            self._metrics.invalidations += len(keys_to_delete)
            self._update_avg_size()
            return len(keys_to_delete)
    
    def clear(self) -> int:
        """Clear all cache. Returns count cleared."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._access_freq.clear()
            self._metrics.total_size_bytes = 0
            self._metrics.invalidations += count
            self._update_avg_size()
            return count
    
    def _evict_entry(self) -> Optional[str]:
        """Evict single entry based on strategy."""
        if not self._cache:
            return None
        
        if self.config.strategy == CacheStrategy.LRU:
            key = next(iter(self._cache))  # First item (least recently used)
        elif self.config.strategy == CacheStrategy.LFU:
            key = min(self._access_freq, key=self._access_freq.get)
        elif self.config.strategy == CacheStrategy.FIFO:
            key = min(self._cache, key=lambda k: self._cache[k].created_at)
        else:
            key = next(iter(self._cache))
        
        self._metrics.total_size_bytes -= self._cache[key].size_bytes
        del self._cache[key]
        self._access_freq.pop(key, None)
        self._metrics.evictions += 1
        self._update_avg_size()
        return key
    
    def _evict_entries(self, needed_bytes: int) -> int:
        """Evict multiple entries to free space."""
        freed = 0
        while freed < needed_bytes and self._cache:
            self._evict_entry()
            freed += needed_bytes // len(self._cache) if self._cache else needed_bytes
        return freed
    
    def _update_avg_size(self):
        """Update average entry size."""
        if self._cache:
            self._metrics.avg_entry_size_bytes = self._metrics.total_size_bytes / len(self._cache)
        self._metrics.entry_count = len(self._cache)
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics."""
        with self._lock:
            return self._metrics
    
    def get_entries(self, limit: int = 100) -> List[Dict]:
        """Get cache entries (for inspection)."""
        with self._lock:
            return [v.to_dict() for v in list(self._cache.values())[:limit]]


class CacheManager:
    """Multi-tier cache manager with L1 and L2 support."""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.l1_cache = L1MemoryCache(self.config)
        self._invalidation_rules: Dict[str, InvalidationRule] = {}
        self._warmup_strategies: Dict[str, WarmupStrategy] = {}
        self._lock = threading.Lock()
        self._statistics = {
            "total_gets": 0,
            "total_sets": 0,
            "total_deletes": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "cache_misses": 0
        }
    
    def get(self, key: str, fetch_func: Optional[Callable] = None) -> Tuple[bool, Any]:
        """Get value with fallback to fetch function."""
        with self._lock:
            self._statistics["total_gets"] += 1
        
        # Try L1 cache
        found, value = self.l1_cache.get(key)
        if found:
            self._statistics["l1_hits"] += 1
            return True, value
        
        # Try fetch function
        if fetch_func:
            try:
                value = fetch_func(key)
                self.set(key, value)
                return True, value
            except Exception:
                pass
        
        self._statistics["cache_misses"] += 1
        return False, None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, tags: Set[str] = None) -> None:
        """Set value in all tiers."""
        with self._lock:
            self._statistics["total_sets"] += 1
        
        # Set in L1
        self.l1_cache.set(key, value, ttl_seconds, tags)
    
    def delete(self, key: str) -> bool:
        """Delete from all tiers."""
        with self._lock:
            self._statistics["total_deletes"] += 1
        
        return self.l1_cache.delete(key)
    
    def add_invalidation_rule(self, rule: InvalidationRule) -> None:
        """Add cache invalidation rule."""
        with self._lock:
            self._invalidation_rules[rule.rule_id] = rule
    
    def remove_invalidation_rule(self, rule_id: str) -> bool:
        """Remove invalidation rule."""
        with self._lock:
            if rule_id in self._invalidation_rules:
                del self._invalidation_rules[rule_id]
                return True
            return False
    
    def apply_invalidation_rules(self) -> int:
        """Apply active invalidation rules. Returns count invalidated."""
        total_invalidated = 0
        rules = list(self._invalidation_rules.values())
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if rule.rule_type == InvalidationType.TAG_BASED:
                for tag in rule.target_tags:
                    total_invalidated += self.l1_cache.invalidate_by_tag(tag)
            
            elif rule.rule_type == InvalidationType.PATTERN_BASED:
                if rule.pattern:
                    total_invalidated += self.l1_cache.invalidate_by_pattern(rule.pattern)
            
            elif rule.rule_type == InvalidationType.TTL:
                pass  # TTL handled at entry level
        
        return total_invalidated
    
    def add_warmup_strategy(self, strategy: WarmupStrategy) -> None:
        """Add cache warmup strategy."""
        with self._lock:
            self._warmup_strategies[strategy.strategy_id] = strategy
    
    def warmup_cache(self, strategy_id: str, data_loader: Callable) -> int:
        """Warmup cache using strategy. Returns count loaded."""
        with self._lock:
            if strategy_id not in self._warmup_strategies:
                return 0
            
            strategy = self._warmup_strategies[strategy_id]
            if not strategy.enabled:
                return 0
            
            loaded = 0
            try:
                for key in strategy.keys_to_load:
                    value = data_loader(key)
                    self.l1_cache.set(key, value)
                    loaded += 1
            except Exception:
                pass
            
            return loaded
    
    def prefetch_keys(self, keys: List[str], fetch_func: Callable) -> int:
        """Prefetch multiple keys. Returns count prefetched."""
        prefetched = 0
        for key in keys:
            try:
                found, _ = self.get(key)
                if not found:
                    value = fetch_func(key)
                    self.set(key, value)
                    prefetched += 1
            except Exception:
                pass
        
        return prefetched
    
    def get_cache_stat_summary(self) -> Dict:
        """Get overall cache statistics."""
        l1_metrics = self.l1_cache.get_metrics()
        
        with self._lock:
            return {
                "l1_metrics": l1_metrics.to_dict(),
                "l1_l2_hit_rate": l1_metrics.hit_rate,
                "total_gets": self._statistics["total_gets"],
                "total_sets": self._statistics["total_sets"],
                "total_deletes": self._statistics["total_deletes"],
                "cache_misses": self._statistics["cache_misses"],
                "invalidation_rules_count": len(self._invalidation_rules),
                "warmup_strategies_count": len(self._warmup_strategies),
                "config": self.config.to_dict()
            }
    
    def clear_all(self) -> int:
        """Clear all cache."""
        return self.l1_cache.clear()


class CacheKeyBuilder:
    """Utility for generating consistent cache keys."""
    
    @staticmethod
    def build_key(namespace: str, *args, **kwargs) -> str:
        """Build cache key from components."""
        parts = [namespace]
        parts.extend(str(arg) for arg in args)
        
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            parts.append("|".join(f"{k}={v}" for k, v in sorted_kwargs))
        
        key_str = ":".join(parts)
        
        # Hash if too long
        if len(key_str) > 255:
            return f"{namespace}:{hashlib.md5(key_str.encode()).hexdigest()}"
        
        return key_str
    
    @staticmethod
    def build_pattern_key(namespace: str, *args) -> str:
        """Build pattern key for invalidation."""
        parts = [namespace]
        parts.extend(str(arg) if arg != "*" else ".*" for arg in args)
        return ":".join(parts).replace(":", ".*")


class CacheWarmer:
    """Cache warming service for preloading data."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._warmup_jobs: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def schedule_warmup(
        self,
        job_id: str,
        keys: List[str],
        fetch_func: Callable,
        interval_seconds: int = 3600
    ) -> None:
        """Schedule cache warmup job."""
        with self._lock:
            self._warmup_jobs[job_id] = {
                "keys": keys,
                "fetch_func": fetch_func,
                "interval_seconds": interval_seconds,
                "last_run": 0,
                "run_count": 0
            }
    
    def run_warmup(self, job_id: str) -> int:
        """Run warmup job. Returns count loaded."""
        with self._lock:
            if job_id not in self._warmup_jobs:
                return 0
            
            job = self._warmup_jobs[job_id]
            loaded = 0
            
            try:
                for key in job["keys"]:
                    value = job["fetch_func"](key)
                    self.cache_manager.set(key, value)
                    loaded += 1
            except Exception:
                pass
            
            job["last_run"] = time.time()
            job["run_count"] += 1
            
            return loaded
    
    def run_all_due_jobs(self, current_time: float = None) -> int:
        """Run all jobs that are due. Returns total count loaded."""
        current_time = current_time or time.time()
        total_loaded = 0
        
        for job_id in list(self._warmup_jobs.keys()):
            with self._lock:
                if job_id not in self._warmup_jobs:
                    continue
                
                job = self._warmup_jobs[job_id]
                if current_time - job["last_run"] >= job["interval_seconds"]:
                    total_loaded += self.run_warmup(job_id)
        
        return total_loaded


# ===================== SINGLETON SERVICES =====================

_cache_manager_instance: Optional[CacheManager] = None
_cache_warmer_instance: Optional[CacheWarmer] = None


def get_cache_manager(config: CacheConfig = None) -> CacheManager:
    """Get cache manager singleton."""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(config)
    return _cache_manager_instance


def get_cache_warmer() -> CacheWarmer:
    """Get cache warmer singleton."""
    global _cache_warmer_instance
    if _cache_warmer_instance is None:
        manager = get_cache_manager()
        _cache_warmer_instance = CacheWarmer(manager)
    return _cache_warmer_instance


def reset_cache_manager() -> None:
    """Reset cache manager for testing."""
    global _cache_manager_instance
    _cache_manager_instance = CacheManager()


def reset_cache_warmer() -> None:
    """Reset cache warmer for testing."""
    global _cache_warmer_instance
    manager = get_cache_manager()
    _cache_warmer_instance = CacheWarmer(manager)
