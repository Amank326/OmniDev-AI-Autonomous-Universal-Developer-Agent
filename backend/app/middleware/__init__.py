"""Middleware module for FastAPI application."""

from app.middleware.rate_limit import (
    limiter,
    setup_rate_limiting,
    AUTH_LIMITS,
    API_LIMITS,
    WEBSOCKET_LIMITS
)

__all__ = [
    "limiter",
    "setup_rate_limiting",
    "AUTH_LIMITS",
    "API_LIMITS",
    "WEBSOCKET_LIMITS"
]
