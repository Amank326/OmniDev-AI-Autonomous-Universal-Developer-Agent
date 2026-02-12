"""
Phase 13: Monitoring Middleware
Automatic request instrumentation and tracing
"""

import logging
import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic request instrumentation
    Tracks latency, errors, resource usage
    """

    def __init__(self, app, distributed_tracer=None, metrics_aggregator=None):
        super().__init__(app)
        self.distributed_tracer = distributed_tracer
        self.metrics_aggregator = metrics_aggregator

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with monitoring
        """
        # Extract request info
        method = request.method
        path = request.url.path
        user_id = request.headers.get("x-user-id", "anonymous")
        tenant_id = request.headers.get("x-tenant-id", "unknown")
        request_id = str(uuid.uuid4())

        # Start trace if tracer available
        trace_id = None
        span_id = None
        if self.distributed_tracer:
            trace_id = self.distributed_tracer.start_trace(
                user_id, tenant_id, request_id, method, path
            )
            span_id = self.distributed_tracer.start_span(
                f"{method} {path}",
                service="api_gateway"
            )

        # Record request metrics
        start_time = time.time()
        request_size = len(await request.body()) if request.method != "GET" else 0

        try:
            # Call next middleware/endpoint
            response = await call_next(request)

            # Calculate duration
            duration = (time.time() - start_time) * 1000  # Convert to ms

            # Record response metrics
            response_size = int(response.headers.get("content-length", 0))

            # Update metrics
            if self.metrics_aggregator:
                self._record_metrics(
                    tenant_id, method, path, response.status_code,
                    duration, request_size, response_size
                )

            # Update span
            if self.distributed_tracer and span_id:
                self.distributed_tracer.record_metric(span_id, "latency_ms", duration)
                self.distributed_tracer.record_metric(span_id, "response_size_bytes", response_size)

                if response.status_code >= 400:
                    self.distributed_tracer.end_span(
                        span_id,
                        status="FAILED" if response.status_code >= 500 else "SUCCESS"
                    )
                else:
                    self.distributed_tracer.end_span(span_id)

            # End trace
            if self.distributed_tracer:
                self.distributed_tracer.end_trace()

            # Log request
            logger.info(
                f"{method} {path} - {response.status_code} ({duration:.2f}ms) - "
                f"User: {user_id} - Tenant: {tenant_id}"
            )

            return response

        except Exception as e:
            # Record error
            error_time = (time.time() - start_time) * 1000

            if self.distributed_tracer and span_id:
                self.distributed_tracer.end_span(span_id, status="FAILED", error=str(e))
                self.distributed_tracer.end_trace(status="FAILED", error=str(e))

            if self.metrics_aggregator:
                self.metrics_aggregator.record_metric(
                    tenant_id, "api_errors_total", 1,
                    labels={"method": method, "path": path, "error_type": type(e).__name__}
                )

            logger.error(
                f"Error in {method} {path}: {e} ({error_time:.2f}ms)",
                exc_info=True
            )

            raise

    def _record_metrics(self, tenant_id: str, method: str, path: str,
                       status_code: int, duration: float,
                       request_size: int, response_size: int) -> None:
        """Record request metrics"""
        if not self.metrics_aggregator:
            return

        # Latency metric
        self.metrics_aggregator.record_metric(
            tenant_id, "http_request_duration_ms", duration,
            labels={"method": method, "path": path, "status": str(status_code)}
        )

        # Request/response size
        self.metrics_aggregator.record_metric(
            tenant_id, "http_request_size_bytes", request_size,
            labels={"method": method, "path": path}
        )
        self.metrics_aggregator.record_metric(
            tenant_id, "http_response_size_bytes", response_size,
            labels={"method": method, "path": path}
        )

        # Status code metrics
        if status_code >= 500:
            self.metrics_aggregator.record_metric(
                tenant_id, "http_server_errors_total", 1,
                labels={"method": method, "path": path}
            )
        elif status_code >= 400:
            self.metrics_aggregator.record_metric(
                tenant_id, "http_client_errors_total", 1,
                labels={"method": method, "path": path}
            )

        # Request counter
        self.metrics_aggregator.record_metric(
            tenant_id, "http_requests_total", 1,
            labels={"method": method, "path": path, "status": str(status_code)}
        )


class SpanDecorator:
    """Decorator for automatic span creation"""

    def __init__(self, tracer, operation_name: str, service: str = None):
        self.tracer = tracer
        self.operation_name = operation_name
        self.service = service

    def __call__(self, func: Callable) -> Callable:
        """Wrap function with automatic span"""
        async def wrapper(*args, **kwargs):
            span_id = self.tracer.start_span(
                self.operation_name,
                service=self.service
            ) if self.tracer else None

            try:
                result = await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
                if span_id and self.tracer:
                    self.tracer.end_span(span_id)
                return result
            except Exception as e:
                if span_id and self.tracer:
                    self.tracer.end_span(span_id, status="FAILED", error=str(e))
                raise

        return wrapper


class MetricsRecorder:
    """Helper class for recording metrics"""

    def __init__(self, metrics_aggregator):
        self.metrics = metrics_aggregator

    def record_operation(self, tenant_id: str, operation_name: str,
                        duration: float, success: bool = True) -> None:
        """Record operation metrics"""
        if not self.metrics:
            return

        self.metrics.record_metric(
            tenant_id, f"{operation_name}_duration_ms", duration
        )

        if not success:
            self.metrics.record_metric(
                tenant_id, f"{operation_name}_errors", 1
            )

    def record_resource_usage(self, tenant_id: str, resource_type: str,
                             usage_percent: float, limit: float) -> None:
        """Record resource usage"""
        if not self.metrics:
            return

        self.metrics.record_metric(
            tenant_id, f"resource_{resource_type}_usage_percent", usage_percent
        )

    def record_workflow_execution(self, tenant_id: str, workflow_id: str,
                                 duration: float, status: str) -> None:
        """Record workflow execution metrics"""
        if not self.metrics:
            return

        self.metrics.record_metric(
            tenant_id, "workflow_execution_duration_ms", duration,
            labels={"workflow_id": workflow_id, "status": status}
        )
