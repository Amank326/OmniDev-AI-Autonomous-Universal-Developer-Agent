"""
Phase 12: Access Control Middleware
FastAPI middleware for RBAC enforcement and audit logging
"""

import logging
from typing import Callable, Optional, List
from functools import wraps
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

from .rbac_service import RBACService
from .audit_logger import AuditLogger, AuditEventType

logger = logging.getLogger(__name__)


class AccessControlMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for access control and audit logging
    """

    def __init__(self, app, rbac_service: RBACService, audit_logger: AuditLogger):
        super().__init__(app)
        self.rbac_service = rbac_service
        self.audit_logger = audit_logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercept requests and apply access control
        """
        start_time = time.time()

        # Extract user info from request
        user_id = self._get_user_id(request)
        tenant_id = self._get_tenant_id(request)
        ip_address = self._get_ip_address(request)
        user_agent = request.headers.get("user-agent", "")

        # Skip audit for health checks and public endpoints
        if request.url.path in ["/health", "/status"]:
            return await call_next(request)

        # Log API call
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log successful API call
            if user_id and tenant_id:
                self.audit_logger.log_api_call(
                    endpoint=request.url.path,
                    method=request.method,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    status_code=response.status_code,
                    response_time=duration,
                    ip_address=ip_address,
                )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log failed API call
            if user_id and tenant_id:
                self.audit_logger.log_api_call(
                    endpoint=request.url.path,
                    method=request.method,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    status_code=500,
                    response_time=duration,
                    ip_address=ip_address,
                )

            raise

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try multiple header names
        for header in ["x-user-id", "user-id", "authorization"]:
            value = request.headers.get(header)
            if value:
                if header == "authorization" and value.startswith("Bearer "):
                    return value[7:]  # Extract token
                return value

        return None

    def _get_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        return request.headers.get("x-tenant-id") or request.headers.get("tenant-id")

    def _get_ip_address(self, request: Request) -> str:
        """Extract IP address from request"""
        # Check X-Forwarded-For header (for proxies)
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.client.host if request.client else "unknown"


class PermissionDecorator:
    """
    Decorator for endpoint-level permission checking
    """

    def __init__(self, rbac_service: RBACService, audit_logger: AuditLogger):
        self.rbac_service = rbac_service
        self.audit_logger = audit_logger

    def require_permission(self, *permissions: str):
        """
        Decorator to require specific permission(s)
        Usage: @require_permission("workflow:create")
               @require_permission("workflow:create", "workflow:share")  # OR logic
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = self._get_request(*args, **kwargs)
                user_id = self._get_user_id(request)
                tenant_id = self._get_tenant_id(request)

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not authenticated"
                    )

                # Check if user has ANY of the required permissions
                has_permission = self.rbac_service.has_any_permission(
                    user_id, list(permissions), tenant_id
                )

                if not has_permission:
                    # Log unauthorized attempt
                    self.audit_logger.log_user_action(
                        event_type="access_denied",
                        user_id=user_id,
                        tenant_id=tenant_id,
                        description=f"Unauthorized access attempt: {', '.join(permissions)}",
                        details={"required_permissions": list(permissions)},
                    )

                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required permission: {', '.join(permissions)}"
                    )

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def require_all_permissions(self, *permissions: str):
        """
        Decorator to require ALL specified permissions (AND logic)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = self._get_request(*args, **kwargs)
                user_id = self._get_user_id(request)
                tenant_id = self._get_tenant_id(request)

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not authenticated"
                    )

                # Check if user has ALL required permissions
                has_all = self.rbac_service.has_all_permissions(
                    user_id, list(permissions), tenant_id
                )

                if not has_all:
                    self.audit_logger.log_user_action(
                        event_type="access_denied",
                        user_id=user_id,
                        tenant_id=tenant_id,
                        description=f"Unauthorized access (all required): {', '.join(permissions)}",
                    )

                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required permissions: {', '.join(permissions)}"
                    )

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def require_role(self, *roles: str):
        """
        Decorator to require specific role(s)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = self._get_request(*args, **kwargs)
                user_id = self._get_user_id(request)
                tenant_id = self._get_tenant_id(request)

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not authenticated"
                    )

                # Check if user has one of the required roles
                user_roles = self.rbac_service.get_user_roles(user_id, tenant_id)
                has_role = any(role in roles for role in user_roles)

                if not has_role:
                    self.audit_logger.log_user_action(
                        event_type="access_denied",
                        user_id=user_id,
                        tenant_id=tenant_id,
                        description=f"Role check failed: {', '.join(roles)}",
                    )

                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required role not found: {', '.join(roles)}"
                    )

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def audit_action(self, event_type: str, resource_type: str = None):
        """
        Decorator to automatically audit endpoint calls
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = self._get_request(*args, **kwargs)
                user_id = self._get_user_id(request)
                tenant_id = self._get_tenant_id(request)

                # Execute function
                result = await func(*args, **kwargs)

                # Log action
                if user_id and tenant_id:
                    self.audit_logger.log_user_action(
                        event_type=event_type,
                        user_id=user_id,
                        tenant_id=tenant_id,
                        description=f"{event_type} via {request.method} {request.url.path}",
                        details={
                            "method": request.method,
                            "endpoint": request.url.path,
                            "resource_type": resource_type,
                        },
                    )

                return result

            return wrapper
        return decorator

    def _get_request(self, *args, **kwargs) -> Request:
        """Extract Request object from function arguments"""
        for arg in args:
            if isinstance(arg, Request):
                return arg

        raise ValueError("Request object not found in function arguments")

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        for header in ["x-user-id", "user-id"]:
            value = request.headers.get(header)
            if value:
                return value

        return None

    def _get_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        return request.headers.get("x-tenant-id") or request.headers.get("tenant-id")


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce tenant isolation
    Prevents users from accessing data from other tenants
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Verify user's tenant matches request's tenant
        """
        # Skip for public endpoints
        if request.url.path in ["/health", "/status", "/api/v1/auth/login"]:
            return await call_next(request)

        user_tenant_id = request.headers.get("x-user-tenant-id")
        request_tenant_id = request.headers.get("x-tenant-id")

        # If both tenant IDs are present, verify they match
        if user_tenant_id and request_tenant_id and user_tenant_id != request_tenant_id:
            logger.warning(
                f"Tenant mismatch: user_tenant={user_tenant_id}, request_tenant={request_tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant access denied"
            )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Basic rate limiting middleware
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = {}  # user_id -> list of timestamps

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Track and limit requests per user
        """
        user_id = request.headers.get("x-user-id")

        if user_id:
            current_time = time.time()

            # Get user's request history
            if user_id not in self.request_history:
                self.request_history[user_id] = []

            # Remove old entries (older than 1 minute)
            self.request_history[user_id] = [
                ts for ts in self.request_history[user_id]
                if current_time - ts < 60
            ]

            # Check if user exceeded limit
            if len(self.request_history[user_id]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            # Add current request
            self.request_history[user_id].append(current_time)

        return await call_next(request)
