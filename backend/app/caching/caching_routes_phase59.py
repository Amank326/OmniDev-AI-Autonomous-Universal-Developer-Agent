"""
Phase 59: Advanced Caching API Routes
REST API endpoints for cache management, invalidation, and warming.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from caching.caching_service_phase59 import (
    get_cache_manager,
    get_cache_warmer,
    reset_cache_manager,
    reset_cache_warmer,
    CacheConfig,
    CacheStrategy,
    CachePattern,
    InvalidationType,
    InvalidationRule,
    WarmupStrategy,
    CacheKeyBuilder
)

router = APIRouter(prefix="/api/v1", tags=["caching"])


# ===================== REQUEST/RESPONSE MODELS =====================

class CacheSetRequest(BaseModel):
    """Set cache entry."""
    key: str = Field(..., description="Cache key")
    value: Any = Field(..., description="Value to cache")
    ttl_seconds: Optional[int] = Field(None, description="Time to live in seconds")
    tags: List[str] = Field(default_factory=list, description="Cache tags")


class CacheGetRequest(BaseModel):
    """Get cache entry."""
    key: str = Field(..., description="Cache key")


class CacheDeleteRequest(BaseModel):
    """Delete cache entry."""
    key: str = Field(..., description="Cache key")


class CacheConfigRequest(BaseModel):
    """Configure cache."""
    max_size_mb: int = Field(default=100, ge=1, description="Max cache size in MB")
    max_entries: int = Field(default=10000, ge=1, description="Max cache entries")
    default_ttl_seconds: int = Field(default=3600, ge=1, description="Default TTL in seconds")
    strategy: str = Field(default="lru", description="Eviction strategy")
    pattern: str = Field(default="cache_aside", description="Cache pattern")


class InvalidationRuleRequest(BaseModel):
    """Create invalidation rule."""
    rule_id: str = Field(..., description="Rule ID")
    rule_type: str = Field(..., description="Invalidation type (ttl/tag_based/pattern_based)")
    target_keys: List[str] = Field(default_factory=list, description="Keys to target")
    target_tags: List[str] = Field(default_factory=list, description="Tags to target")
    pattern: Optional[str] = Field(None, description="Regex pattern")
    ttl_seconds: Optional[int] = Field(None, description="TTL in seconds")


class WarmupStrategyRequest(BaseModel):
    """Create warmup strategy."""
    strategy_id: str = Field(..., description="Strategy ID")
    data_source: str = Field(..., description="Data source type")
    keys_to_load: List[str] = Field(..., description="Keys to load")
    batch_size: int = Field(default=100, ge=1, description="Batch size")


class CacheKeyBuildRequest(BaseModel):
    """Build cache key."""
    namespace: str = Field(..., description="Key namespace")
    args: List[str] = Field(default_factory=list, description="Key components")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Keyword components")


class InvalidateByTagRequest(BaseModel):
    """Invalidate by tag."""
    tag: str = Field(..., description="Tag to invalidate")


class InvalidateByPatternRequest(BaseModel):
    """Invalidate by pattern."""
    pattern: str = Field(..., description="Regex pattern to match")


class PrefetchKeysRequest(BaseModel):
    """Prefetch keys."""
    keys: List[str] = Field(..., description="Keys to prefetch")


# ===================== CACHE OPERATIONS =====================

@router.post("/cache/set")
async def set_cache(request: CacheSetRequest):
    """Set value in cache."""
    try:
        manager = get_cache_manager()
        tags = set(request.tags) if request.tags else None
        manager.set(request.key, request.value, request.ttl_seconds, tags)
        
        return {
            "status": "set",
            "key": request.key,
            "ttl_seconds": request.ttl_seconds or "default"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cache/get")
async def get_cache(request: CacheGetRequest):
    """Get value from cache."""
    manager = get_cache_manager()
    found, value = manager.get(request.key)
    
    if not found:
        raise HTTPException(status_code=404, detail="Cache miss")
    
    return {
        "key": request.key,
        "found": True,
        "value": value
    }


@router.get("/cache/{key}")
async def get_cache_by_path(key: str):
    """Get value from cache by path."""
    manager = get_cache_manager()
    found, value = manager.get(key)
    
    if not found:
        raise HTTPException(status_code=404, detail="Cache miss")
    
    return {
        "key": key,
        "found": True,
        "value": value
    }


@router.delete("/cache/{key}")
async def delete_cache(key: str):
    """Delete from cache."""
    manager = get_cache_manager()
    deleted = manager.delete(key)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {
        "status": "deleted",
        "key": key
    }


@router.post("/cache/delete")
async def delete_cache_request(request: CacheDeleteRequest):
    """Delete from cache."""
    manager = get_cache_manager()
    deleted = manager.delete(request.key)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {
        "status": "deleted",
        "key": request.key
    }


@router.post("/cache/invalidate/tag")
async def invalidate_by_tag(request: InvalidateByTagRequest):
    """Invalidate all entries with tag."""
    manager = get_cache_manager()
    count = manager.l1_cache.invalidate_by_tag(request.tag)
    
    return {
        "status": "invalidated",
        "tag": request.tag,
        "count": count
    }


@router.post("/cache/invalidate/pattern")
async def invalidate_by_pattern(request: InvalidateByPatternRequest):
    """Invalidate entries matching pattern."""
    try:
        manager = get_cache_manager()
        count = manager.l1_cache.invalidate_by_pattern(request.pattern)
        
        return {
            "status": "invalidated",
            "pattern": request.pattern,
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """Clear all cache."""
    manager = get_cache_manager()
    count = manager.clear_all()
    
    return {
        "status": "cleared",
        "entries_cleared": count
    }


# ===================== CACHE CONFIGURATION =====================

@router.post("/cache/configure")
async def configure_cache(request: CacheConfigRequest):
    """Configure cache."""
    try:
        reset_cache_manager()
        config = CacheConfig(
            max_size_mb=request.max_size_mb,
            max_entries=request.max_entries,
            default_ttl_seconds=request.default_ttl_seconds,
            strategy=CacheStrategy(request.strategy),
            pattern=CachePattern(request.pattern)
        )
        manager = get_cache_manager(config)
        
        return {
            "status": "configured",
            "config": config.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cache/config")
async def get_cache_config():
    """Get current cache configuration."""
    manager = get_cache_manager()
    summary = manager.get_cache_stat_summary()
    
    return {
        "config": summary["config"],
        "metrics": summary["l1_metrics"]
    }


# ===================== INVALIDATION RULES =====================

@router.post("/cache/rules/add")
async def add_invalidation_rule(request: InvalidationRuleRequest):
    """Add cache invalidation rule."""
    try:
        manager = get_cache_manager()
        rule = InvalidationRule(
            rule_id=request.rule_id,
            rule_type=InvalidationType(request.rule_type),
            target_keys=set(request.target_keys),
            target_tags=set(request.target_tags),
            pattern=request.pattern,
            ttl_seconds=request.ttl_seconds
        )
        manager.add_invalidation_rule(rule)
        
        return {
            "status": "added",
            "rule_id": request.rule_id,
            "rule": rule.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cache/rules/remove/{rule_id}")
async def remove_invalidation_rule(rule_id: str):
    """Remove invalidation rule."""
    manager = get_cache_manager()
    removed = manager.remove_invalidation_rule(rule_id)
    
    if not removed:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {
        "status": "removed",
        "rule_id": rule_id
    }


@router.post("/cache/rules/apply")
async def apply_invalidation_rules():
    """Apply all active invalidation rules."""
    manager = get_cache_manager()
    count = manager.apply_invalidation_rules()
    
    return {
        "status": "applied",
        "entries_invalidated": count
    }


# ===================== WARMUP STRATEGIES =====================

@router.post("/cache/warmup/add")
async def add_warmup_strategy(request: WarmupStrategyRequest):
    """Add cache warmup strategy."""
    try:
        manager = get_cache_manager()
        strategy = WarmupStrategy(
            strategy_id=request.strategy_id,
            data_source=request.data_source,
            keys_to_load=request.keys_to_load,
            batch_size=request.batch_size
        )
        manager.add_warmup_strategy(strategy)
        
        return {
            "status": "added",
            "strategy_id": request.strategy_id,
            "strategy": strategy.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cache/warmup/run/{strategy_id}")
async def run_warmup_strategy(strategy_id: str):
    """Run specific warmup strategy."""
    warmer = get_cache_warmer()
    
    # Example: simple warmup with identity function
    def simple_loader(key: str):
        return f"data_for_{key}"
    
    count = warmer.run_warmup(strategy_id)
    
    if count == 0:
        raise HTTPException(status_code=404, detail="Strategy not found or not runnable")
    
    return {
        "status": "warmed",
        "strategy_id": strategy_id,
        "keys_loaded": count
    }


@router.post("/cache/warmup/run-all")
async def run_all_warmup_strategies():
    """Run all due warmup strategies."""
    warmer = get_cache_warmer()
    count = warmer.run_all_due_jobs()
    
    return {
        "status": "warmed",
        "total_keys_loaded": count
    }


# ===================== PREFETCH =====================

@router.post("/cache/prefetch")
async def prefetch_keys(request: PrefetchKeysRequest):
    """Prefetch multiple keys."""
    manager = get_cache_manager()
    
    def simple_loader(key: str):
        return f"data_for_{key}"
    
    count = manager.prefetch_keys(request.keys, simple_loader)
    
    return {
        "status": "prefetched",
        "keys_requested": len(request.keys),
        "keys_loaded": count
    }


# ===================== KEY BUILDING =====================

@router.post("/cache/key/build")
async def build_cache_key(request: CacheKeyBuildRequest):
    """Build cache key."""
    try:
        args = request.args if request.args else tuple()
        key = CacheKeyBuilder.build_key(request.namespace, *args, **request.kwargs)
        
        return {
            "key": key,
            "namespace": request.namespace,
            "length": len(key)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cache/key/pattern")
async def build_pattern_key(request: CacheKeyBuildRequest):
    """Build pattern key for invalidation."""
    try:
        args = request.args if request.args else tuple()
        pattern = CacheKeyBuilder.build_pattern_key(request.namespace, *args)
        
        return {
            "pattern": pattern,
            "namespace": request.namespace
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== STATISTICS & MONITORING =====================

@router.get("/cache/stats")
async def get_cache_statistics():
    """Get cache statistics."""
    manager = get_cache_manager()
    summary = manager.get_cache_stat_summary()
    
    return {
        "statistics": summary
    }


@router.get("/cache/entries")
async def get_cache_entries(limit: int = Query(100, ge=1, le=1000)):
    """Get cache entries (for inspection)."""
    manager = get_cache_manager()
    entries = manager.l1_cache.get_entries(limit)
    
    return {
        "count": len(entries),
        "entries": entries
    }


@router.get("/cache/health")
async def get_cache_health():
    """Get cache health status."""
    manager = get_cache_manager()
    summary = manager.get_cache_stat_summary()
    metrics = summary["l1_metrics"]
    
    # Calculate health score
    hit_rate = metrics["hit_rate"]
    eviction_count = metrics["evictions"]
    
    if hit_rate >= 80:
        health = "excellent"
    elif hit_rate >= 60:
        health = "good"
    elif hit_rate >= 40:
        health = "fair"
    else:
        health = "poor"
    
    return {
        "health_status": health,
        "hit_rate": hit_rate,
        "metrics": metrics
    }


# ===================== TESTING ENDPOINTS =====================

@router.post("/test/reset")
async def reset_all_services():
    """Reset all caching services (testing only)."""
    reset_cache_manager()
    reset_cache_warmer()
    
    return {
        "status": "reset",
        "services": ["cache_manager", "cache_warmer"]
    }
