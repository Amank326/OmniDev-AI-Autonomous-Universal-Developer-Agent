"""
Phase 50: Advanced API Gateway & Rate Limiting Routes

REST API endpoints for:
- API gateway management
- Rate limiting configuration
- Circuit breaker management
- Request transformation
- API versioning
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Optional, Any, List
from datetime import datetime
from ..services.api_gateway_service import (
    get_phase50_service,
    RateLimitConfig,
    CircuitBreakerConfig,
    TransformationRule,
    APIVersion,
    RouteConfig,
    RateLimitType
)

router = APIRouter(prefix="/api/v1/gateway", tags=["api-gateway"])
phase50_service = get_phase50_service()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RateLimitConfigRequest(BaseModel):
    """Rate limit configuration request"""
    identifier: str
    request_limit: int
    time_window: int
    burst_limit: int
    enabled: bool = True


class RateLimitCheckRequest(BaseModel):
    """Rate limit check request"""
    identifier: str


class CircuitBreakerConfigRequest(BaseModel):
    """Circuit breaker configuration request"""
    name: str
    failure_threshold: int
    recovery_timeout: int
    success_threshold: int


class CircuitBreakerRecordRequest(BaseModel):
    """Record circuit breaker event"""
    breaker_name: str
    event: str  # "success" or "failure"


class TransformationRuleRequest(BaseModel):
    """Transformation rule request"""
    rule_id: str
    source_header: str
    target_header: str
    enabled: bool = True


class RouteRegistrationRequest(BaseModel):
    """Route registration request"""
    path: str
    method: str
    target_service: str
    rate_limit: Optional[str] = None
    circuit_breaker: Optional[str] = None
    requires_auth: bool = True
    version: str = "v1"


class APIVersionRequest(BaseModel):
    """API version registration request"""
    version: str
    deprecated: bool = False
    migration_guide: str = ""


class RequestCheckRequest(BaseModel):
    """Check if request can be processed"""
    identifier: str
    method: str
    path: str


# ============================================================================
# RATE LIMITING ENDPOINTS
# ============================================================================

@router.post("/rate-limit/configure")
async def configure_rate_limit(request: RateLimitConfigRequest) -> Dict[str, Any]:
    """Configure rate limit"""
    try:
        config = RateLimitConfig(
            request_limit=request.request_limit,
            time_window=request.time_window,
            burst_limit=request.burst_limit,
            enabled=request.enabled
        )
        
        success = phase50_service.rate_limiter.configure_limit(request.identifier, config)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to configure rate limit")
        
        return {
            "status": "success",
            "identifier": request.identifier,
            "request_limit": request.request_limit,
            "time_window": request.time_window
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limit/check")
async def check_rate_limit(request: RateLimitCheckRequest) -> Dict[str, Any]:
    """Check rate limit status"""
    try:
        status = phase50_service.rate_limiter.get_status(request.identifier)
        if not status:
            raise HTTPException(status_code=404, detail="Rate limit not found")
        
        return {
            "identifier": status.identifier,
            "remaining_requests": status.remaining_requests,
            "reset_time": status.reset_time.isoformat(),
            "limit_exceeded": status.limit_exceeded,
            "requests_in_window": status.requests_in_window
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limit/{identifier}/reset")
async def reset_rate_limit(identifier: str) -> Dict[str, Any]:
    """Reset rate limit"""
    try:
        success = phase50_service.rate_limiter.reset_limit(identifier)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reset")
        
        return {
            "status": "success",
            "identifier": identifier,
            "message": "Rate limit reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CIRCUIT BREAKER ENDPOINTS
# ============================================================================

@router.post("/circuit-breaker/register")
async def register_circuit_breaker(request: CircuitBreakerConfigRequest) -> Dict[str, Any]:
    """Register circuit breaker"""
    try:
        config = CircuitBreakerConfig(
            name=request.name,
            failure_threshold=request.failure_threshold,
            recovery_timeout=request.recovery_timeout,
            success_threshold=request.success_threshold
        )
        
        success = phase50_service.circuit_breaker.register_breaker(request.name, config)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to register")
        
        return {
            "status": "success",
            "breaker_name": request.name,
            "state": "closed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/circuit-breaker/record")
async def record_circuit_breaker_event(request: CircuitBreakerRecordRequest) -> Dict[str, Any]:
    """Record circuit breaker event"""
    try:
        if request.event == "success":
            success = phase50_service.circuit_breaker.record_success(request.breaker_name)
        elif request.event == "failure":
            success = phase50_service.circuit_breaker.record_failure(request.breaker_name)
        else:
            raise HTTPException(status_code=400, detail="Invalid event type")
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to record event")
        
        status = phase50_service.circuit_breaker.get_breaker_status(request.breaker_name)
        return {
            "status": "success",
            "breaker": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/circuit-breaker/{breaker_name}/status")
async def get_circuit_breaker_status(breaker_name: str) -> Dict[str, Any]:
    """Get circuit breaker status"""
    try:
        status = phase50_service.circuit_breaker.get_breaker_status(breaker_name)
        if not status:
            raise HTTPException(status_code=404, detail="Circuit breaker not found")
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REQUEST TRANSFORMATION ENDPOINTS
# ============================================================================

@router.post("/transform/rule/add")
async def add_transformation_rule(request: TransformationRuleRequest) -> Dict[str, Any]:
    """Add transformation rule"""
    try:
        rule = TransformationRule(
            rule_id=request.rule_id,
            source_header=request.source_header,
            target_header=request.target_header,
            enabled=request.enabled
        )
        
        success = phase50_service.transformer.add_rule(rule)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add rule")
        
        return {
            "status": "success",
            "rule_id": request.rule_id,
            "message": "Rule added"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transform/rules")
async def get_transformation_rules() -> Dict[str, Any]:
    """Get all transformation rules"""
    try:
        rules = phase50_service.transformer.get_rules()
        return {
            "total_rules": len(rules),
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "source_header": r.source_header,
                    "target_header": r.target_header,
                    "enabled": r.enabled
                }
                for r in rules.values()
            ],
            "transformations_applied": phase50_service.transformer.transformations_applied
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform/request")
async def transform_request_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    """Transform request headers"""
    try:
        transformed = phase50_service.transformer.transform_request(headers)
        return {
            "original_headers": len(headers),
            "transformed_headers": transformed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# API VERSIONING ENDPOINTS
# ============================================================================

@router.post("/version/register")
async def register_api_version(request: APIVersionRequest) -> Dict[str, Any]:
    """Register API version"""
    try:
        version = APIVersion(
            version=request.version,
            release_date=datetime.utcnow(),
            deprecated=request.deprecated,
            migration_guide=request.migration_guide
        )
        
        success = phase50_service.versioning.register_version(version)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to register version")
        
        return {
            "status": "success",
            "version": request.version,
            "deprecated": request.deprecated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version/{version}/status")
async def check_version_status(version: str) -> Dict[str, Any]:
    """Check API version status"""
    try:
        status = phase50_service.versioning.check_version_status(version)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/version/{version}/deprecate")
async def deprecate_version(version: str, migration_guide: str = "") -> Dict[str, Any]:
    """Deprecate API version"""
    try:
        success = phase50_service.versioning.deprecate_version(version, migration_guide)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to deprecate version")
        
        return {
            "status": "success",
            "version": version,
            "deprecated": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions")
async def list_all_versions() -> Dict[str, Any]:
    """List all API versions"""
    try:
        active = phase50_service.versioning.get_active_versions()
        all_versions = phase50_service.versioning.get_all_versions()
        
        return {
            "total_versions": len(all_versions),
            "active_versions": len(active),
            "active": active,
            "all_versions": all_versions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/routes/register")
async def register_route(request: RouteRegistrationRequest) -> Dict[str, Any]:
    """Register API route"""
    try:
        route = RouteConfig(
            path=request.path,
            method=request.method,
            target_service=request.target_service,
            rate_limit=request.rate_limit,
            circuit_breaker=request.circuit_breaker,
            requires_auth=request.requires_auth,
            version=request.version
        )
        
        success = phase50_service.gateway.register_route(route)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to register route")
        
        return {
            "status": "success",
            "path": request.path,
            "method": request.method,
            "target_service": request.target_service
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes")
async def list_routes() -> Dict[str, Any]:
    """List all routes"""
    try:
        routes = phase50_service.gateway.get_all_routes()
        return {
            "total_routes": len(routes),
            "routes": [
                {
                    "path": r.path,
                    "method": r.method,
                    "target_service": r.target_service,
                    "version": r.version,
                    "requires_auth": r.requires_auth
                }
                for r in routes.values()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes/{method}/{path}")
async def get_route(method: str, path: str) -> Dict[str, Any]:
    """Get specific route"""
    try:
        route = phase50_service.gateway.get_route(method, path)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return {
            "path": route.path,
            "method": route.method,
            "target_service": route.target_service,
            "rate_limit": route.rate_limit,
            "circuit_breaker": route.circuit_breaker,
            "requires_auth": route.requires_auth,
            "version": route.version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REQUEST PROCESSING ENDPOINTS
# ============================================================================

@router.post("/request/check")
async def check_request_allowed(request: RequestCheckRequest) -> Dict[str, Any]:
    """Check if request can be processed"""
    try:
        route_key = f"{request.method}:{request.path}"
        allowed, message = phase50_service.gateway.can_process_request(request.identifier, route_key)
        
        return {
            "allowed": allowed,
            "identifier": request.identifier,
            "method": request.method,
            "path": request.path,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GATEWAY STATUS ENDPOINTS
# ============================================================================

@router.get("/health")
async def gateway_health() -> Dict[str, Any]:
    """Gateway health check"""
    return {
        "service": "api-gateway",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status")
async def gateway_status() -> Dict[str, Any]:
    """Get Phase 50 status"""
    return phase50_service.get_status()


@router.get("/metrics")
async def gateway_metrics() -> Dict[str, Any]:
    """Get gateway metrics"""
    try:
        gw_status = phase50_service.gateway.get_gateway_status()
        status = phase50_service.get_status()
        
        return {
            "requests_processed": gw_status["requests_processed"],
            "requests_rejected": gw_status["requests_rejected"],
            "rejection_rate": gw_status["rejection_rate"],
            "routes_registered": status["metrics"]["routes_registered"],
            "transformations_applied": status["metrics"]["transformations_applied"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
