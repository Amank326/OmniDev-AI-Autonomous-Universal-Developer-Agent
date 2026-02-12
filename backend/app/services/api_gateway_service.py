"""
Phase 50: Advanced API Gateway & Rate Limiting Services

Provides comprehensive API gateway functionality:
- Request routing and load balancing
- Rate limiting (token bucket algorithm)
- Circuit breaker pattern
- Request/response transformation
- API versioning and deprecation
- Authentication and authorization headers
"""

import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import time
import json

logger = logging.getLogger(__name__)


# ============================================================================
# 1. RATE LIMITING SERVICE
# ============================================================================

class RateLimitType(Enum):
    """Rate limit types"""
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_API_KEY = "per_api_key"
    GLOBAL = "global"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    request_limit: int  # requests
    time_window: int  # seconds
    burst_limit: int  # maximum burst requests
    enabled: bool = True


@dataclass
class RateLimitStatus:
    """Current rate limit status"""
    identifier: str
    remaining_requests: int
    reset_time: datetime
    limit_type: str
    limit_exceeded: bool
    requests_in_window: int


class RateLimitingService:
    """Token bucket based rate limiting"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.configs: Dict[str, RateLimitConfig] = {}
        self.buckets: Dict[str, deque] = defaultdict(deque)  # Token buckets per identifier
        self.status = "limiting"
        
    def configure_limit(self, identifier: str, config: RateLimitConfig) -> bool:
        """Configure rate limit for identifier"""
        with self._lock:
            try:
                self.configs[identifier] = config
                self.buckets[identifier] = deque()
                logger.info(f"Rate limit configured: {identifier}")
                return True
            except Exception as e:
                logger.error(f"Configuration error: {e}")
                return False
    
    def check_rate_limit(self, identifier: str) -> Tuple[bool, RateLimitStatus]:
        """Check if request is allowed (token bucket algorithm)"""
        with self._lock:
            try:
                config = self.configs.get(identifier)
                if not config or not config.enabled:
                    return True, RateLimitStatus(
                        identifier=identifier,
                        remaining_requests=-1,
                        reset_time=datetime.utcnow(),
                        limit_type="unlimited",
                        limit_exceeded=False,
                        requests_in_window=0
                    )
                
                current_time = time.time()
                bucket = self.buckets[identifier]
                
                # Remove expired tokens
                while bucket and bucket[0] < current_time - config.time_window:
                    bucket.popleft()
                
                requests_in_window = len(bucket)
                
                # Check if burst limit exceeded
                if requests_in_window >= config.burst_limit:
                    return False, RateLimitStatus(
                        identifier=identifier,
                        remaining_requests=0,
                        reset_time=datetime.utcnow() + timedelta(seconds=config.time_window),
                        limit_type="burst",
                        limit_exceeded=True,
                        requests_in_window=requests_in_window
                    )
                
                # Check if request limit exceeded
                if requests_in_window >= config.request_limit:
                    return False, RateLimitStatus(
                        identifier=identifier,
                        remaining_requests=0,
                        reset_time=datetime.utcnow() + timedelta(seconds=config.time_window),
                        limit_type="standard",
                        limit_exceeded=True,
                        requests_in_window=requests_in_window
                    )
                
                # Add token (request) to bucket
                bucket.append(current_time)
                
                return True, RateLimitStatus(
                    identifier=identifier,
                    remaining_requests=config.request_limit - requests_in_window - 1,
                    reset_time=datetime.utcnow() + timedelta(seconds=config.time_window),
                    limit_type="standard",
                    limit_exceeded=False,
                    requests_in_window=requests_in_window
                )
            except Exception as e:
                logger.error(f"Rate limit check error: {e}")
                return True, RateLimitStatus(
                    identifier=identifier,
                    remaining_requests=-1,
                    reset_time=datetime.utcnow(),
                    limit_type="error",
                    limit_exceeded=False,
                    requests_in_window=0
                )
    
    def get_status(self, identifier: str) -> Optional[RateLimitStatus]:
        """Get current rate limit status"""
        allowed, status = self.check_rate_limit(identifier)
        return status
    
    def reset_limit(self, identifier: str) -> bool:
        """Reset rate limit for identifier"""
        with self._lock:
            try:
                if identifier in self.buckets:
                    self.buckets[identifier].clear()
                return True
            except Exception as e:
                logger.error(f"Reset error: {e}")
                return False


# ============================================================================
# 2. CIRCUIT BREAKER SERVICE
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int  # consecutive failures to trigger
    recovery_timeout: int  # seconds before trying recovery
    success_threshold: int  # successful calls in half-open to recover
    name: str = ""


class CircuitBreakerService:
    """Fault tolerance using circuit breaker pattern"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.breakers: Dict[str, Dict] = {}
        self.status = "protecting"
        
    def register_breaker(self, name: str, config: CircuitBreakerConfig) -> bool:
        """Register a circuit breaker"""
        with self._lock:
            try:
                self.breakers[name] = {
                    "config": config,
                    "state": CircuitState.CLOSED,
                    "failure_count": 0,
                    "success_count": 0,
                    "last_failure_time": None,
                    "last_state_change": datetime.utcnow(),
                    "total_failures": 0,
                    "total_successes": 0
                }
                logger.info(f"Circuit breaker registered: {name}")
                return True
            except Exception as e:
                logger.error(f"Registration error: {e}")
                return False
    
    def record_success(self, name: str) -> bool:
        """Record successful call"""
        with self._lock:
            try:
                if name not in self.breakers:
                    return False
                
                breaker = self.breakers[name]
                breaker["failure_count"] = 0
                breaker["total_successes"] += 1
                
                if breaker["state"] == CircuitState.HALF_OPEN:
                    breaker["success_count"] += 1
                    if breaker["success_count"] >= breaker["config"].success_threshold:
                        breaker["state"] = CircuitState.CLOSED
                        breaker["success_count"] = 0
                        logger.info(f"Circuit breaker {name} recovered to CLOSED")
                
                return True
            except Exception as e:
                logger.error(f"Success recording error: {e}")
                return False
    
    def record_failure(self, name: str) -> bool:
        """Record failed call"""
        with self._lock:
            try:
                if name not in self.breakers:
                    return False
                
                breaker = self.breakers[name]
                breaker["failure_count"] += 1
                breaker["total_failures"] += 1
                breaker["last_failure_time"] = datetime.utcnow()
                
                if breaker["state"] == CircuitState.CLOSED:
                    if breaker["failure_count"] >= breaker["config"].failure_threshold:
                        breaker["state"] = CircuitState.OPEN
                        breaker["last_state_change"] = datetime.utcnow()
                        logger.warning(f"Circuit breaker {name} opened after {breaker['failure_count']} failures")
                
                elif breaker["state"] == CircuitState.HALF_OPEN:
                    breaker["state"] = CircuitState.OPEN
                    breaker["success_count"] = 0
                    logger.warning(f"Circuit breaker {name} reopened during recovery test")
                
                return True
            except Exception as e:
                logger.error(f"Failure recording error: {e}")
                return False
    
    def can_execute(self, name: str) -> bool:
        """Check if call is allowed"""
        with self._lock:
            try:
                if name not in self.breakers:
                    return True
                
                breaker = self.breakers[name]
                
                if breaker["state"] == CircuitState.CLOSED:
                    return True
                
                elif breaker["state"] == CircuitState.OPEN:
                    time_since_failure = (datetime.utcnow() - breaker["last_state_change"]).total_seconds()
                    if time_since_failure >= breaker["config"].recovery_timeout:
                        breaker["state"] = CircuitState.HALF_OPEN
                        breaker["success_count"] = 0
                        logger.info(f"Circuit breaker {name} transitioning to HALF_OPEN")
                        return True
                    return False
                
                elif breaker["state"] == CircuitState.HALF_OPEN:
                    return True
                
                return False
            except Exception as e:
                logger.error(f"Can execute check error: {e}")
                return True
    
    def get_breaker_status(self, name: str) -> Optional[Dict]:
        """Get breaker status"""
        with self._lock:
            if name in self.breakers:
                b = self.breakers[name]
                return {
                    "name": name,
                    "state": b["state"].value,
                    "failure_count": b["failure_count"],
                    "total_failures": b["total_failures"],
                    "total_successes": b["total_successes"],
                    "last_state_change": b["last_state_change"].isoformat()
                }
            return None


# ============================================================================
# 3. REQUEST TRANSFORMATION SERVICE
# ============================================================================

@dataclass
class TransformationRule:
    """Request/response transformation rule"""
    rule_id: str
    source_header: str
    target_header: str
    transformation_fn: Optional[Callable] = None
    enabled: bool = True


class RequestTransformationService:
    """Transform requests and responses"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.rules: Dict[str, TransformationRule] = {}
        self.transformations_applied = 0
        self.status = "transforming"
        
    def add_rule(self, rule: TransformationRule) -> bool:
        """Add transformation rule"""
        with self._lock:
            try:
                self.rules[rule.rule_id] = rule
                logger.info(f"Transformation rule added: {rule.rule_id}")
                return True
            except Exception as e:
                logger.error(f"Rule add error: {e}")
                return False
    
    def transform_request(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply transformation rules to request headers"""
        with self._lock:
            try:
                transformed = dict(headers)
                
                for rule in self.rules.values():
                    if not rule.enabled:
                        continue
                    
                    if rule.source_header in transformed:
                        value = transformed[rule.source_header]
                        
                        if rule.transformation_fn:
                            value = rule.transformation_fn(value)
                        
                        transformed[rule.target_header] = value
                        del transformed[rule.source_header]
                        self.transformations_applied += 1
                
                return transformed
            except Exception as e:
                logger.error(f"Request transformation error: {e}")
                return headers
    
    def transform_response(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply transformation rules to response headers"""
        return self.transform_request(headers)
    
    def get_rules(self) -> Dict[str, TransformationRule]:
        """Get all rules"""
        with self._lock:
            return dict(self.rules)


# ============================================================================
# 4. API VERSIONING SERVICE
# ============================================================================

@dataclass
class APIVersion:
    """API version definition"""
    version: str  # "v1", "v2", etc.
    release_date: datetime
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    migration_guide: str = ""


class APIVersioningService:
    """Manage API versions and deprecation"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.versions: Dict[str, APIVersion] = {}
        self.deprecation_warnings = 0
        self.status = "versioning"
        
    def register_version(self, version: APIVersion) -> bool:
        """Register API version"""
        with self._lock:
            try:
                self.versions[version.version] = version
                logger.info(f"API version registered: {version.version}")
                return True
            except Exception as e:
                logger.error(f"Version registration error: {e}")
                return False
    
    def deprecate_version(self, version: str, migration_guide: str = "") -> bool:
        """Mark version as deprecated"""
        with self._lock:
            try:
                if version in self.versions:
                    self.versions[version].deprecated = True
                    self.versions[version].deprecation_date = datetime.utcnow()
                    if migration_guide:
                        self.versions[version].migration_guide = migration_guide
                    logger.info(f"API version deprecated: {version}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Deprecation error: {e}")
                return False
    
    def check_version_status(self, version: str) -> Dict[str, Any]:
        """Check if version is deprecated/sunset"""
        with self._lock:
            try:
                if version not in self.versions:
                    return {"status": "unknown", "version": version}
                
                v = self.versions[version]
                now = datetime.utcnow()
                
                if v.sunset_date and now > v.sunset_date:
                    self.deprecation_warnings += 1
                    return {
                        "status": "sunset",
                        "version": version,
                        "message": f"Version {version} is no longer supported",
                        "migration_guide": v.migration_guide
                    }
                
                if v.deprecated:
                    self.deprecation_warnings += 1
                    return {
                        "status": "deprecated",
                        "version": version,
                        "deprecation_date": v.deprecation_date.isoformat() if v.deprecation_date else None,
                        "migration_guide": v.migration_guide
                    }
                
                return {"status": "active", "version": version}
            except Exception as e:
                logger.error(f"Version check error: {e}")
                return {"status": "error", "version": version}
    
    def get_active_versions(self) -> List[str]:
        """Get all active versions"""
        with self._lock:
            return [v.version for v in self.versions.values() if not v.deprecated]
    
    def get_all_versions(self) -> Dict[str, Dict]:
        """Get all versions with status"""
        with self._lock:
            return {
                v.version: {
                    "deprecated": v.deprecated,
                    "release_date": v.release_date.isoformat(),
                    "deprecation_date": v.deprecation_date.isoformat() if v.deprecation_date else None
                }
                for v in self.versions.values()
            }


# ============================================================================
# 5. API GATEWAY SERVICE
# ============================================================================

@dataclass
class RouteConfig:
    """API route configuration"""
    path: str
    method: str
    target_service: str
    rate_limit: Optional[str] = None
    circuit_breaker: Optional[str] = None
    requires_auth: bool = True
    version: str = "v1"


class APIGatewayService:
    """Main API Gateway orchestrator"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.routes: Dict[str, RouteConfig] = {}
        self.rate_limiter = RateLimitingService()
        self.circuit_breaker = CircuitBreakerService()
        self.transformer = RequestTransformationService()
        self.versioning = APIVersioningService()
        self.requests_processed = 0
        self.requests_rejected = 0
        self.status = "operational"
        
    def register_route(self, route: RouteConfig) -> bool:
        """Register a route"""
        with self._lock:
            try:
                route_key = f"{route.method}:{route.path}"
                self.routes[route_key] = route
                logger.info(f"Route registered: {route_key}")
                return True
            except Exception as e:
                logger.error(f"Route registration error: {e}")
                return False
    
    def can_process_request(self, identifier: str, route_key: str) -> Tuple[bool, str]:
        """Check if request can be processed"""
        with self._lock:
            try:
                if route_key not in self.routes:
                    return False, "Route not found"
                
                route = self.routes[route_key]
                
                # Check rate limiting
                if route.rate_limit:
                    allowed, status = self.rate_limiter.check_rate_limit(f"{identifier}:{route_key}")
                    if not allowed:
                        self.requests_rejected += 1
                        return False, f"Rate limit exceeded: {status.remaining_requests} remaining"
                
                # Check circuit breaker
                if route.circuit_breaker:
                    if not self.circuit_breaker.can_execute(route.circuit_breaker):
                        self.requests_rejected += 1
                        return False, "Service unavailable (circuit open)"
                
                # Check API version
                version_check = self.versioning.check_version_status(route.version)
                if version_check["status"] == "sunset":
                    self.requests_rejected += 1
                    return False, f"API version {route.version} is no longer supported"
                
                self.requests_processed += 1
                return True, "Request allowed"
            except Exception as e:
                logger.error(f"Process check error: {e}")
                return False, f"Error: {str(e)}"
    
    def get_route(self, method: str, path: str) -> Optional[RouteConfig]:
        """Get route by method and path"""
        with self._lock:
            route_key = f"{method}:{path}"
            return self.routes.get(route_key)
    
    def get_all_routes(self) -> Dict[str, RouteConfig]:
        """Get all registered routes"""
        with self._lock:
            return dict(self.routes)
    
    def get_gateway_status(self) -> Dict[str, Any]:
        """Get gateway status"""
        with self._lock:
            return {
                "status": self.status,
                "routes_registered": len(self.routes),
                "requests_processed": self.requests_processed,
                "requests_rejected": self.requests_rejected,
                "rejection_rate": (self.requests_rejected / (self.requests_processed + self.requests_rejected) * 100) 
                                 if (self.requests_processed + self.requests_rejected) > 0 else 0
            }


# ============================================================================
# PHASE 50 ORCHESTRATOR
# ============================================================================

class Phase50Service:
    """Phase 50: Advanced API Gateway & Rate Limiting Orchestrator"""
    
    def __init__(self):
        self.gateway = APIGatewayService()
        self.rate_limiter = self.gateway.rate_limiter
        self.circuit_breaker = self.gateway.circuit_breaker
        self.transformer = self.gateway.transformer
        self.versioning = self.gateway.versioning
        self.status = "operational"
        
    def initialize(self) -> bool:
        """Initialize Phase 50 services"""
        try:
            logger.info("Phase 50: Advanced API Gateway & Rate Limiting initialized")
            return True
        except Exception as e:
            logger.error(f"Phase 50 initialization error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get Phase 50 status"""
        return {
            "phase": 50,
            "status": self.status,
            "services": {
                "api_gateway": self.gateway.status,
                "rate_limiter": self.rate_limiter.status,
                "circuit_breaker": self.circuit_breaker.status,
                "transformer": self.transformer.status,
                "versioning": self.versioning.status
            },
            "metrics": {
                "routes_registered": len(self.gateway.routes),
                "requests_processed": self.gateway.requests_processed,
                "requests_rejected": self.gateway.requests_rejected,
                "transformations_applied": self.transformer.transformations_applied
            }
        }


# Global singleton
_phase50_instance: Optional[Phase50Service] = None
_phase50_lock = threading.RLock()


def get_phase50_service() -> Phase50Service:
    """Get Phase 50 service instance (singleton)"""
    global _phase50_instance
    if _phase50_instance is None:
        with _phase50_lock:
            if _phase50_instance is None:
                _phase50_instance = Phase50Service()
                _phase50_instance.initialize()
    return _phase50_instance
