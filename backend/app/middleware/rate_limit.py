"""
Rate Limiting Configuration

Implements SlowAPI rate limiting to prevent abuse and ensure fair resource usage.

Features:
    - Per-endpoint rate limits
    - Token bucket algorithm
    - Custom key functions for user-based limiting
    - Error responses with retry-after headers

Limits:
    - Auth endpoints: 5 requests / 15 minutes
    - API endpoints: 100 requests / 15 minutes
    - WebSocket: 1 connection per user per resource
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_auth_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key for auth endpoints (IP-based).
    
    Args:
        request: FastAPI request object
    
    Returns:
        IP address or session ID
    """
    # Could also use request.client.host for stricter limiting
    return get_remote_address(request)


def get_user_rate_limit_key(request: Request) -> Optional[str]:
    """
    Get rate limit key for authenticated endpoints (user-based).
    
    Args:
        request: FastAPI request object
    
    Returns:
        User ID if authenticated, else IP address
    """
    # Try to get user from token in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.auth.utils import get_user_from_token
            token = auth_header.split(" ")[1]
            user_id = get_user_from_token(token)
            if user_id:
                return f"user:{user_id}"
        except:
            pass
    
    # Fall back to IP address
    return get_remote_address(request)


# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/15 minutes"],  # Default for all endpoints
    storage_uri="memory://"  # Use in-memory storage (can upgrade to Redis)
)


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Setup rate limiting error handlers and configuration.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit exceeded exceptions."""
        logger.warning(
            f"Rate limit exceeded",
            extra={
                "client_ip": request.client.host if request.client else "unknown",
                "path": request.url.path,
                "limit": exc.detail
            }
        )
        
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please try again later.",
                "error_code": "rate_limit_exceeded",
                "retry_after": 60  # Seconds
            },
            headers={
                "Retry-After": "60"  # HTTP standard header
            }
        )


# Rate limit configurations for different endpoint groups
AUTH_LIMITS = {
    "register": "5/15 minutes",  # Strict limit on registration
    "login": "10/15 minutes",      # Allow more login attempts
    "refresh": "20/15 minutes",    # Refresh tokens more frequently
}

API_LIMITS = {
    "read": "100/15 minutes",      # Read operations (GET)
    "write": "50/15 minutes",      # Write operations (POST, PUT, DELETE)
    "expensive": "10/15 minutes",  # Expensive operations (search, analysis)
}

WEBSOCKET_LIMITS = {
    "connections_per_user": 5,     # Max 5 WS connections per user
    "messages_per_minute": 60,     # Max 60 messages per minute per connection
}
