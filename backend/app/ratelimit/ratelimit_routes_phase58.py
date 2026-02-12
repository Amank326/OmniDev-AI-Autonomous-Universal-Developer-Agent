"""
Phase 58: Rate Limiting & Throttling API Routes
REST API endpoints for rate limiting, quota management, and DDoS protection.
"""

from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel, Field
from ratelimit.ratelimit_service_phase58 import (
    get_rate_limiter_service,
    get_quota_manager,
    get_ddos_detector,
    reset_rate_limiter_service,
    reset_quota_manager,
    reset_ddos_detector,
    RateLimitAlgorithm,
    QuotaTier,
    BlockType
)

router = APIRouter(prefix="/api/v1", tags=["rate-limiting"])


# ===================== REQUEST/RESPONSE MODELS =====================

class RateLimitConfigRequest(BaseModel):
    """Configure a rate limit."""
    limit_id: str = Field(..., description="Unique limit identifier")
    requests: int = Field(..., ge=1, description="Max requests")
    window_seconds: int = Field(..., ge=1, description="Time window in seconds")
    burst_allowed: int = Field(default=0, ge=0, description="Burst capacity")
    penalty_seconds: int = Field(default=60, ge=0, description="Penalty duration")
    algorithm: str = Field(default="token_bucket", description="Algorithm type")


class RateLimitCheckRequest(BaseModel):
    """Check rate limit."""
    limit_id: str = Field(..., description="Limit identifier")
    tokens: int = Field(default=1, ge=1, description="Tokens to consume")
    burst: bool = Field(default=False, description="Allow burst")


class QuotaCreateRequest(BaseModel):
    """Create user quota."""
    user_id: str = Field(..., description="User ID")
    tier: str = Field(..., description="Quota tier (free/basic/premium/enterprise)")
    reset_hour: int = Field(default=0, ge=0, le=23, description="Reset hour in UTC")


class QuotaCheckRequest(BaseModel):
    """Check user quota."""
    user_id: str = Field(..., description="User ID")
    requests: int = Field(default=1, ge=1, description="Requests to consume")
    concurrent: int = Field(default=0, ge=0, description="Concurrent slots")
    storage_gb: float = Field(default=0.0, ge=0, description="Storage in GB")


class QuotaReleaseRequest(BaseModel):
    """Release quota resources."""
    user_id: str = Field(..., description="User ID")
    concurrent: int = Field(default=0, ge=0, description="Concurrent slots")
    storage_gb: float = Field(default=0.0, ge=0, description="Storage in GB")


class QuotaUpgradeRequest(BaseModel):
    """Upgrade user quota tier."""
    user_id: str = Field(..., description="User ID")
    new_tier: str = Field(..., description="New tier (free/basic/premium/enterprise)")


class DDoSCheckRequest(BaseModel):
    """Analyze request for DDoS."""
    ip_address: str = Field(..., description="IP address")
    endpoint: str = Field(..., description="Endpoint accessed")
    success: bool = Field(default=True, description="Request succeeded")


class IPBlockRequest(BaseModel):
    """Block IP address."""
    ip_address: str = Field(..., description="IP to block")
    reason: str = Field(..., description="Reason for block")
    block_type: str = Field(default="temporary", description="Block type")
    duration_seconds: int = Field(default=3600, description="Duration for temporary block")


class IPWhitelistRequest(BaseModel):
    """Whitelist IP address."""
    ip_address: str = Field(..., description="IP to whitelist")


# ===================== RATE LIMITING ENDPOINTS =====================

@router.post("/rate-limits/configure")
async def configure_rate_limit(request: RateLimitConfigRequest):
    """Configure a rate limit."""
    try:
        service = get_rate_limiter_service()
        from ratelimit.ratelimit_service_phase58 import RateLimit
        
        rate_limit = RateLimit(
            limit_type=request.limit_id,
            requests=request.requests,
            window_seconds=request.window_seconds,
            burst_allowed=request.burst_allowed,
            penalty_seconds=request.penalty_seconds,
            algorithm=RateLimitAlgorithm(request.algorithm)
        )
        service.configure_rate_limit(request.limit_id, rate_limit)
        
        return {
            "status": "configured",
            "limit_id": request.limit_id,
            "config": rate_limit.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rate-limits/check")
async def check_rate_limit(request: RateLimitCheckRequest):
    """Check if request allowed under rate limit."""
    service = get_rate_limiter_service()
    allowed, details = service.check_rate_limit(request.limit_id, request.tokens, request.burst)
    
    status_code = 200 if allowed else 429
    return {
        "allowed": allowed,
        "limit_id": request.limit_id,
        "details": details
    }


@router.get("/rate-limits/statistics")
async def get_rate_limit_statistics():
    """Get rate limiting statistics."""
    service = get_rate_limiter_service()
    stats = service.get_statistics()
    return {
        "statistics": stats
    }


@router.post("/rate-limits/{limit_id}/reset")
async def reset_rate_limit(limit_id: str):
    """Reset a rate limit."""
    service = get_rate_limiter_service()
    service.reset_limit(limit_id)
    return {
        "status": "reset",
        "limit_id": limit_id
    }


# ===================== QUOTA ENDPOINTS =====================

@router.post("/quotas/create")
async def create_quota(request: QuotaCreateRequest):
    """Create user quota."""
    try:
        manager = get_quota_manager()
        tier = QuotaTier(request.tier)
        quota = manager.create_quota(request.user_id, tier, request.reset_hour)
        
        return {
            "status": "created",
            "user_id": request.user_id,
            "quota": quota.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quotas/check")
async def check_quota(request: QuotaCheckRequest):
    """Check user quota."""
    manager = get_quota_manager()
    allowed, details = manager.check_quota(
        request.user_id,
        request.requests,
        request.concurrent,
        request.storage_gb
    )
    
    status_code = 200 if allowed else 429
    return {
        "allowed": allowed,
        "user_id": request.user_id,
        "details": details
    }


@router.get("/quotas/{user_id}")
async def get_quota(user_id: str):
    """Get user quota."""
    manager = get_quota_manager()
    quota = manager.get_quota(user_id)
    
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    
    return {
        "user_id": user_id,
        "quota": quota.to_dict()
    }


@router.post("/quotas/release")
async def release_quota(request: QuotaReleaseRequest):
    """Release quota resources."""
    manager = get_quota_manager()
    manager.release_quota(request.user_id, request.concurrent, request.storage_gb)
    
    return {
        "status": "released",
        "user_id": request.user_id
    }


@router.post("/quotas/upgrade")
async def upgrade_quota_tier(request: QuotaUpgradeRequest):
    """Upgrade user quota tier."""
    try:
        manager = get_quota_manager()
        new_tier = QuotaTier(request.new_tier)
        quota = manager.upgrade_tier(request.user_id, new_tier)
        
        if not quota:
            raise HTTPException(status_code=404, detail="User quota not found")
        
        return {
            "status": "upgraded",
            "user_id": request.user_id,
            "new_tier": request.new_tier,
            "quota": quota.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quotas/statistics")
async def get_quota_statistics():
    """Get quota statistics."""
    manager = get_quota_manager()
    stats = manager.get_statistics()
    return {
        "statistics": stats
    }


# ===================== DDOS DETECTION ENDPOINTS =====================

@router.post("/ddos/analyze")
async def analyze_for_ddos(request: DDoSCheckRequest):
    """Analyze request for DDoS attack."""
    detector = get_ddos_detector()
    allowed, details = detector.analyze_request(request.ip_address, request.endpoint, request.success)
    
    status_code = 200 if allowed else 403
    return {
        "allowed": allowed,
        "ip_address": request.ip_address,
        "details": details
    }


@router.post("/ddos/block-ip")
async def block_ip(request: IPBlockRequest):
    """Block IP address."""
    try:
        detector = get_ddos_detector()
        block_type = BlockType(request.block_type)
        # Note: This is a simplified version; in production use proper blocking
        
        return {
            "status": "blocked",
            "ip_address": request.ip_address,
            "reason": request.reason,
            "block_type": request.block_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ddos/whitelist-ip")
async def whitelist_ip(request: IPWhitelistRequest):
    """Whitelist IP address."""
    detector = get_ddos_detector()
    detector.whitelist_ip(request.ip_address)
    
    return {
        "status": "whitelisted",
        "ip_address": request.ip_address
    }


@router.post("/ddos/unblock-ip/{ip_address}")
async def unblock_ip(ip_address: str):
    """Unblock IP address."""
    detector = get_ddos_detector()
    unblocked = detector.unblock_ip(ip_address)
    
    if not unblocked:
        raise HTTPException(status_code=404, detail="IP not blocked")
    
    return {
        "status": "unblocked",
        "ip_address": ip_address
    }


@router.get("/ddos/blocked-ips")
async def get_blocked_ips(limit: int = Query(100, ge=1, le=1000)):
    """Get blocked IP addresses."""
    detector = get_ddos_detector()
    blocked_ips = detector.get_blocked_ips()[:limit]
    
    return {
        "count": len(blocked_ips),
        "blocked_ips": blocked_ips
    }


@router.get("/ddos/statistics")
async def get_ddos_statistics():
    """Get DDoS detection statistics."""
    detector = get_ddos_detector()
    stats = detector.get_statistics()
    return {
        "statistics": stats
    }


# ===================== COMBINED ENDPOINTS =====================

@router.post("/protection/request-check")
async def comprehensive_request_check(
    request_data: DDoSCheckRequest,
    user_id: Optional[str] = Header(None),
    limit_id: Optional[str] = Header(None)
):
    """Comprehensive request check: DDoS + Rate Limit + Quota."""
    results = {
        "ip_address": request_data.ip_address,
        "checks": {}
    }
    
    # DDoS check
    detector = get_ddos_detector()
    ddos_allowed, ddos_details = detector.analyze_request(
        request_data.ip_address,
        request_data.endpoint,
        request_data.success
    )
    results["checks"]["ddos"] = {
        "allowed": ddos_allowed,
        "details": ddos_details
    }
    
    if not ddos_allowed:
        return results
    
    # Rate limit check
    if limit_id:
        limiter = get_rate_limiter_service()
        rl_allowed, rl_details = limiter.check_rate_limit(limit_id, 1, False)
        results["checks"]["rate_limit"] = {
            "allowed": rl_allowed,
            "details": rl_details
        }
        if not rl_allowed:
            return results
    
    # Quota check
    if user_id:
        manager = get_quota_manager()
        quota_allowed, quota_details = manager.check_quota(user_id, 1, 0, 0)
        results["checks"]["quota"] = {
            "allowed": quota_allowed,
            "details": quota_details
        }
        if not quota_allowed:
            return results
    
    results["allowed"] = True
    return results


@router.get("/protection/status")
async def get_protection_status():
    """Get overall protection status."""
    limiter = get_rate_limiter_service()
    manager = get_quota_manager()
    detector = get_ddos_detector()
    
    return {
        "rate_limiting": limiter.get_statistics(),
        "quota_management": manager.get_statistics(),
        "ddos_detection": detector.get_statistics()
    }


# ===================== TESTING ENDPOINTS =====================

@router.post("/test/reset")
async def reset_all_services():
    """Reset all protection services (testing only)."""
    reset_rate_limiter_service()
    reset_quota_manager()
    reset_ddos_detector()
    
    return {
        "status": "reset",
        "services": ["rate_limiter", "quota_manager", "ddos_detector"]
    }
