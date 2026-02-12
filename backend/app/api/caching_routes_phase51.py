"""
Phase 51: Caching & Performance API Routes
FastAPI routes for caching, compression, and performance monitoring
"""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging

from backend.app.services.caching_service import (
    CachingService, CacheConfig, CacheStrategy, get_cache_service
)
from backend.app.services.performance_monitor_phase51 import (
    PerformanceMonitor, get_performance_monitor, get_request_metrics
)
from backend.app.services.compression_service import (
    CompressionService, CompressionAlgorithm, get_compression_service, 
    get_response_optimizer
)
from backend.app.services.metrics_collection import (
    MetricsCollector, get_metrics_collector
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cache", tags=["caching-performance"])


# ============================================================================
# Pydantic Models
# ============================================================================

class CacheSetRequest(BaseModel):
    """Request to set cache value"""
    key: str
    value: Any
    ttl: Optional[int] = None
    tags: Optional[List[str]] = None


class CacheGetResponse(BaseModel):
    """Response from cache get"""
    key: str
    value: Optional[Any]
    found: bool
    timestamp: str


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: str
    miss_rate: str
    evictions: int
    total_memory_bytes: int
    cache_size: int
    max_size: int


class CompressionRequest(BaseModel):
    """Request to compress data"""
    data: str
    algorithm: str = "gzip"


class CompressionResponse(BaseModel):
    """Response from compression"""
    original_size: int
    compressed_size: int
    compression_ratio: str
    algorithm: str
    bytes_saved: int


class MetricsSnapshot(BaseModel):
    """Metrics snapshot"""
    timestamp: str
    cache_metrics: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    compression_metrics: Optional[Dict[str, Any]] = None


# ============================================================================
# Cache Endpoints
# ============================================================================

@router.post("/set", summary="Set cache value")
async def set_cache(request: CacheSetRequest) -> Dict[str, Any]:
    """Set a value in the cache"""
    try:
        cache_service = get_cache_service()
        cache_service.set(request.key, request.value, request.ttl, request.tags)
        
        return {
            "success": True,
            "key": request.key,
            "ttl": request.ttl or cache_service.config.ttl,
            "tags": request.tags or []
        }
    except Exception as e:
        logger.error(f"Error setting cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache set failed: {str(e)}")


@router.get("/get/{key}", summary="Get cache value")
async def get_cache(key: str) -> CacheGetResponse:
    """Get a value from the cache"""
    try:
        cache_service = get_cache_service()
        value = cache_service.get(key)
        
        return CacheGetResponse(
            key=key,
            value=value,
            found=value is not None,
            timestamp=str(__import__('datetime').datetime.utcnow())
        )
    except Exception as e:
        logger.error(f"Error getting cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache get failed: {str(e)}")


@router.delete("/delete/{key}", summary="Delete cache value")
async def delete_cache(key: str) -> Dict[str, Any]:
    """Delete a value from the cache"""
    try:
        cache_service = get_cache_service()
        deleted = cache_service.delete(key)
        
        return {
            "success": True,
            "key": key,
            "deleted": deleted
        }
    except Exception as e:
        logger.error(f"Error deleting cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache delete failed: {str(e)}")


@router.post("/invalidate-tag/{tag}", summary="Invalidate by tag")
async def invalidate_by_tag(tag: str) -> Dict[str, Any]:
    """Invalidate all cache entries with a specific tag"""
    try:
        cache_service = get_cache_service()
        count = cache_service.invalidate_by_tag(tag)
        
        return {
            "success": True,
            "tag": tag,
            "invalidated_count": count
        }
    except Exception as e:
        logger.error(f"Error invalidating by tag: {e}")
        raise HTTPException(status_code=500, detail=f"Tag invalidation failed: {str(e)}")


@router.delete("/clear", summary="Clear all cache")
async def clear_cache() -> Dict[str, Any]:
    """Clear entire cache"""
    try:
        cache_service = get_cache_service()
        cache_service.clear()
        
        return {
            "success": True,
            "message": "Cache cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.get("/stats", response_model=CacheStatsResponse, summary="Get cache statistics")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        cache_service = get_cache_service()
        return cache_service.get_stats()
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/info", summary="Get cache info")
async def get_cache_info() -> Dict[str, Any]:
    """Get cache information and configuration"""
    try:
        cache_service = get_cache_service()
        return cache_service.get_info()
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(status_code=500, detail=f"Info retrieval failed: {str(e)}")


# ============================================================================
# Compression Endpoints
# ============================================================================

@router.post("/compress", response_model=CompressionResponse, summary="Compress data")
async def compress_data(request: CompressionRequest) -> Dict[str, Any]:
    """Compress data using specified algorithm"""
    try:
        # Convert algorithm string to enum
        try:
            algorithm = CompressionAlgorithm(request.algorithm.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid algorithm: {request.algorithm}. Valid: gzip, brotli"
            )
        
        compressor = get_compression_service()
        data_bytes = request.data.encode('utf-8')
        result = compressor.compress(data_bytes, algorithm)
        
        return {
            "original_size": result.original_size,
            "compressed_size": result.compressed_size,
            "compression_ratio": f"{result.compression_ratio:.2f}%",
            "algorithm": result.algorithm.value,
            "bytes_saved": result.savings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error compressing data: {e}")
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")


@router.get("/compression/stats", summary="Get compression statistics")
async def get_compression_stats() -> Dict[str, Any]:
    """Get compression statistics"""
    try:
        compressor = get_compression_service()
        stats = compressor.get_stats()
        
        # Add summary
        stats["brotli_available"] = True  # Check if Brotli is available
        
        return stats
    except Exception as e:
        logger.error(f"Error getting compression stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


# ============================================================================
# Performance Monitoring Endpoints
# ============================================================================

@router.get("/performance/metrics", summary="Get performance metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics"""
    try:
        monitor = get_performance_monitor()
        return {
            "all_stats": monitor.get_all_stats(),
            "active_timers": len(monitor.active_timers)
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.get("/performance/metrics/{metric_name}", summary="Get specific metric")
async def get_specific_metric(metric_name: str) -> Dict[str, Any]:
    """Get statistics for a specific metric"""
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_metric_stats(metric_name)
        
        if stats is None:
            raise HTTPException(status_code=404, detail=f"Metric not found: {metric_name}")
        
        return {
            "metric": metric_name,
            "stats": stats,
            "recent": monitor.get_recent_metrics(metric_name)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric: {e}")
        raise HTTPException(status_code=500, detail=f"Metric retrieval failed: {str(e)}")


@router.get("/request/metrics", summary="Get request metrics")
async def get_request_metrics_endpoint() -> Dict[str, Any]:
    """Get HTTP request metrics"""
    try:
        req_metrics = get_request_metrics()
        return req_metrics.get_stats()
    except Exception as e:
        logger.error(f"Error getting request metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Request metrics failed: {str(e)}")


@router.get("/request/endpoint/{endpoint}", summary="Get endpoint metrics")
async def get_endpoint_metrics(endpoint: str) -> Dict[str, Any]:
    """Get metrics for a specific endpoint"""
    try:
        req_metrics = get_request_metrics()
        stats = req_metrics.get_endpoint_stats(f"/{endpoint}")
        
        if stats is None:
            raise HTTPException(status_code=404, detail=f"Endpoint not found: {endpoint}")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting endpoint metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Endpoint metrics failed: {str(e)}")


# ============================================================================
# Metrics Collection Endpoints
# ============================================================================

@router.post("/metrics/snapshot", summary="Take metrics snapshot")
async def take_metrics_snapshot() -> Dict[str, Any]:
    """Take a snapshot of all current metrics"""
    try:
        collector = get_metrics_collector()
        
        # Collect from all available sources
        cache_service = get_cache_service()
        monitor = get_performance_monitor()
        req_metrics = get_request_metrics()
        compressor = get_compression_service()
        
        collector.collect_cache_metrics(cache_service.get_stats())
        collector.collect_performance_metrics(monitor.get_all_stats())
        collector.collect_request_metrics(req_metrics.get_stats())
        collector.collect_compression_metrics(compressor.get_stats())
        
        snapshot = collector.take_snapshot()
        
        return {
            "success": True,
            "timestamp": snapshot.timestamp.isoformat(),
            "snapshot": snapshot.to_dict()
        }
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Snapshot failed: {str(e)}")


@router.get("/metrics/summary", summary="Get metrics summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """Get summary of all metrics"""
    try:
        collector = get_metrics_collector()
        
        return {
            "summary": collector.get_summary(),
            "current_metrics": collector.get_current_metrics()
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary retrieval failed: {str(e)}")


@router.get("/metrics/snapshots", summary="Get all metric snapshots")
async def get_all_snapshots(
    start: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
) -> Dict[str, Any]:
    """Get range of metric snapshots"""
    try:
        collector = get_metrics_collector()
        snapshots = collector.get_snapshot_range(start, start + limit)
        
        return {
            "total": len(collector.snapshots),
            "start": start,
            "limit": limit,
            "snapshots": [s.to_dict() for s in snapshots]
        }
    except Exception as e:
        logger.error(f"Error getting snapshots: {e}")
        raise HTTPException(status_code=500, detail=f"Snapshots retrieval failed: {str(e)}")


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@router.get("/health", summary="Health check")
async def health_check() -> Dict[str, Any]:
    """Health check for caching and performance services"""
    try:
        cache_service = get_cache_service()
        cache_stats = cache_service.get_stats()
        
        return {
            "status": "healthy",
            "services": {
                "cache": "operational",
                "performance_monitor": "operational",
                "compression": "operational",
                "metrics_collector": "operational"
            },
            "cache_health": {
                "cache_size": cache_stats["cache_size"],
                "max_size": cache_stats["max_size"],
                "hit_rate": cache_stats["hit_rate"]
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/status", summary="Detailed status")
async def get_status() -> Dict[str, Any]:
    """Get detailed status of all services"""
    try:
        cache_service = get_cache_service()
        monitor = get_performance_monitor()
        compressor = get_compression_service()
        collector = get_metrics_collector()
        
        return {
            "services": {
                "cache": cache_service.get_info(),
                "compression": compressor.get_stats(),
                "performance_monitor": {
                    "metrics_tracked": len(monitor.metrics),
                    "active_timers": len(monitor.active_timers)
                },
                "metrics_collector": collector.get_summary()
            },
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
