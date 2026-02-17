"""Rate limiting middleware."""

import time
import logging
from collections import defaultdict
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware.

    For production, use Redis-backed rate limiting.
    """

    def __init__(self, app, authenticated_limit: int = 100, unauthenticated_limit: int = 20, **kwargs):
        super().__init__(app)
        # Dict[client_key] -> (request_count, window_start_time)
        self._requests: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self._window_seconds = 60  # 1 minute window
        self._authenticated_limit = authenticated_limit
        self._unauthenticated_limit = unauthenticated_limit

    def _get_client_key(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request has an auth token."""
        auth_header = request.headers.get("authorization", "")
        return auth_header.startswith("Bearer ")

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and docs
        if request.url.path in ("/health", "/", f"{settings.API_V1_STR}/docs", f"{settings.API_V1_STR}/redoc"):
            return await call_next(request)

        client_key = self._get_client_key(request)
        is_authenticated = self._is_authenticated(request)
        max_requests = (
            self._authenticated_limit
            if is_authenticated
            else self._unauthenticated_limit
        )

        now = time.time()
        count, window_start = self._requests[client_key]

        # Reset window if expired
        if now - window_start > self._window_seconds:
            count = 0
            window_start = now

        count += 1
        self._requests[client_key] = (count, window_start)

        if count > max_requests:
            retry_after = int(self._window_seconds - (now - window_start))
            logger.warning(
                f"Rate limit exceeded for {client_key}: {count}/{max_requests}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - count))
        return response
