"""
Phase 51: Advanced Caching Service
Multi-level caching with in-memory and Redis support
"""

import json
import hashlib
import time
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategies"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    FIFO = "fifo"


class InvalidationStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"
    TAG_BASED = "tag_based"
    EVENT_BASED = "event_based"
    MANUAL = "manual"
    LRU = "lru"


@dataclass
class CacheEntry:
    """Represents a single cache entry"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    ttl: Optional[int] = None  # seconds
    tags: List[str] = field(default_factory=list)
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl
    
    def update_access(self) -> None:
        """Update last access time"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


@dataclass
class CacheConfig:
    """Cache configuration"""
    max_size: int = 1000
    ttl: int = 3600  # 1 hour
    strategy: CacheStrategy = CacheStrategy.LRU
    invalidation: InvalidationStrategy = InvalidationStrategy.TTL
    enable_redis: bool = False
    redis_url: str = "redis://localhost:6379"
    enable_compression: bool = False
    compression_threshold: int = 1024  # bytes


@dataclass
class CacheStats:
    """Cache statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_memory: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    @property
    def miss_rate(self) -> float:
        """Calculate miss rate"""
        return 100 - self.hit_rate


class CacheBackend(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear entire cache"""
        pass
    
    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        pass


class InMemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self.tag_index: Dict[str, set] = {}  # For tag-based invalidation
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        self.stats.total_requests += 1
        
        if key not in self.cache:
            self.stats.cache_misses += 1
            logger.debug(f"Cache miss: {key}")
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            del self.cache[key]
            self.stats.cache_misses += 1
            logger.debug(f"Cache expired: {key}")
            return None
        
        # Update access info
        entry.update_access()
        self.stats.cache_hits += 1
        logger.debug(f"Cache hit: {key}")
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            tags: List[str] = None) -> None:
        """Set value in cache"""
        # Handle LRU eviction if needed
        if len(self.cache) >= self.config.max_size and key not in self.cache:
            self._evict_lru()
        
        ttl = ttl or self.config.ttl
        entry = CacheEntry(key=key, value=value, ttl=ttl, tags=tags or [])
        self.cache[key] = entry
        
        # Update tag index
        for tag in (tags or []):
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(key)
        
        # Update memory stats
        self._update_memory_stats()
        logger.debug(f"Cache set: {key} (ttl={ttl}s)")
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            # Remove from tag index
            for tag in entry.tags:
                if tag in self.tag_index:
                    self.tag_index[tag].discard(key)
            del self.cache[key]
            self._update_memory_stats()
            logger.debug(f"Cache delete: {key}")
            return True
        return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with a specific tag"""
        keys_to_delete = self.tag_index.get(tag, set()).copy()
        for key in keys_to_delete:
            self.delete(key)
        logger.info(f"Invalidated {len(keys_to_delete)} entries with tag: {tag}")
        return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear entire cache"""
        size = len(self.cache)
        self.cache.clear()
        self.tag_index.clear()
        self._update_memory_stats()
        logger.info(f"Cleared cache ({size} entries)")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].accessed_at)
        self.delete(lru_key)
        self.stats.evictions += 1
        logger.debug(f"Cache eviction (LRU): {lru_key}")
    
    def _update_memory_stats(self) -> None:
        """Update memory statistics"""
        total_memory = 0
        for entry in self.cache.values():
            try:
                total_memory += len(json.dumps(entry.value))
            except:
                total_memory += len(str(entry.value))
        self.stats.total_memory = total_memory


class CachingService:
    """Advanced caching service with multiple backends"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.backend = InMemoryCacheBackend(self.config)
        self.decorators: Dict[str, Callable] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self.backend.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            tags: List[str] = None) -> None:
        """Set value in cache"""
        self.backend.set(key, value, ttl, tags)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        return self.backend.delete(key)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate entries by tag"""
        if hasattr(self.backend, 'invalidate_by_tag'):
            return self.backend.invalidate_by_tag(tag)
        return 0
    
    def clear(self) -> None:
        """Clear entire cache"""
        self.backend.clear()
    
    def get_or_set(self, key: str, func: Callable, ttl: Optional[int] = None,
                   tags: List[str] = None) -> Any:
        """Get from cache or compute and cache"""
        # Try to get from cache
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Compute value
        value = func()
        
        # Cache it
        self.set(key, value, ttl, tags)
        
        return value
    
    def cache_function(self, ttl: Optional[int] = None, 
                      tags: List[str] = None):
        """Decorator for function result caching"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # Try cached result
                cached = self.get(cache_key)
                if cached is not None:
                    return cached
                
                # Compute and cache
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl, tags)
                
                return result
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.backend.get_stats()
        return {
            "total_requests": stats.total_requests,
            "cache_hits": stats.cache_hits,
            "cache_misses": stats.cache_misses,
            "hit_rate": f"{stats.hit_rate:.2f}%",
            "miss_rate": f"{stats.miss_rate:.2f}%",
            "evictions": stats.evictions,
            "total_memory_bytes": stats.total_memory,
            "cache_size": len(self.backend.cache),
            "max_size": self.config.max_size
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get cache info"""
        return {
            "strategy": self.config.strategy.value,
            "invalidation": self.config.invalidation.value,
            "max_size": self.config.max_size,
            "default_ttl": self.config.ttl,
            "stats": self.get_stats()
        }
    
    def _generate_cache_key(self, func_name: str, args: tuple, 
                           kwargs: dict) -> str:
        """Generate cache key from function and arguments"""
        key_data = f"{func_name}_{str(args)}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()


# Global caching service instance
_cache_service: Optional[CachingService] = None


def get_cache_service(config: CacheConfig = None) -> CachingService:
    """Get or create cache service"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CachingService(config)
    return _cache_service


def reset_cache_service() -> None:
    """Reset cache service (for testing)"""
    global _cache_service
    _cache_service = None
