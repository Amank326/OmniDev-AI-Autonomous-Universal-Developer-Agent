"""
Phase 13: Distributed Tracer
Request tracing across distributed services
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class SpanStatus(str, Enum):
    """Span execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"


class Span:
    """Individual operation within a trace"""

    def __init__(self, span_id: str, operation_name: str, 
                 trace_id: str, parent_span_id: Optional[str] = None):
        self.span_id = span_id
        self.trace_id = trace_id
        self.operation_name = operation_name
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = SpanStatus.PENDING
        self.error_message: Optional[str] = None
        self.tags: Dict[str, Any] = {}
        self.metrics: Dict[str, float] = {}
        self.logs: List[Dict[str, Any]] = []

    @property
    def duration(self) -> float:
        """Duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0

    def set_tag(self, key: str, value: Any) -> None:
        """Add tag to span"""
        self.tags[key] = value

    def record_metric(self, name: str, value: float) -> None:
        """Record metric in span"""
        self.metrics[name] = value

    def add_log(self, message: str, level: str = "info", **fields) -> None:
        """Add log entry to span"""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "level": level,
            **fields
        })

    def finish(self, status: SpanStatus = SpanStatus.SUCCESS, 
              error: Optional[str] = None) -> None:
        """Mark span as finished"""
        self.end_time = time.time()
        self.status = status
        self.error_message = error
        logger.debug(f"Span finished: {self.operation_name} ({self.duration}ms)")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "operation_name": self.operation_name,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration,
            "status": self.status.value,
            "error_message": self.error_message,
            "tags": self.tags,
            "metrics": self.metrics,
            "logs": self.logs,
        }


class Trace:
    """Complete distributed trace"""

    def __init__(self, trace_id: str, user_id: str, tenant_id: str,
                 request_id: str, request_method: str, request_path: str):
        self.trace_id = trace_id
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.request_id = request_id
        self.request_method = request_method
        self.request_path = request_path
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.spans: Dict[str, Span] = {}
        self.root_span_id: Optional[str] = None
        self.status = SpanStatus.PENDING
        self.error_message: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    @property
    def duration(self) -> float:
        """Total trace duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0

    @property
    def span_count(self) -> int:
        """Number of spans in trace"""
        return len(self.spans)

    def add_span(self, span: Span) -> None:
        """Add span to trace"""
        self.spans[span.span_id] = span
        if span.parent_span_id is None:
            self.root_span_id = span.span_id

    def get_critical_path(self) -> List[Span]:
        """Get longest path through trace (critical path)"""
        if not self.root_span_id:
            return []

        def traverse(span_id: str) -> tuple[List[Span], float]:
            span = self.spans[span_id]
            children = [s for s in self.spans.values() if s.parent_span_id == span_id]

            if not children:
                return [span], span.duration

            longest_path = []
            max_duration = 0

            for child in children:
                path, duration = traverse(child.span_id)
                total = span.duration + duration
                if total > max_duration:
                    max_duration = total
                    longest_path = [span] + path

            return longest_path, max_duration

        path, _ = traverse(self.root_span_id)
        return path

    def get_service_dependencies(self) -> List[tuple[str, str]]:
        """Get service call chain"""
        dependencies = []

        for span in self.spans.values():
            if "service" in span.tags:
                parent = None
                if span.parent_span_id and span.parent_span_id in self.spans:
                    parent = self.spans[span.parent_span_id].tags.get("service")

                if parent:
                    dependencies.append((parent, span.tags["service"]))

        return dependencies

    def finish(self, status: SpanStatus = SpanStatus.SUCCESS,
              error: Optional[str] = None) -> None:
        """Mark trace as finished"""
        self.end_time = time.time()
        self.status = status
        self.error_message = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration,
            "status": self.status.value,
            "error_message": self.error_message,
            "span_count": self.span_count,
            "spans": [s.to_dict() for s in self.spans.values()],
            "critical_path": [s.span_id for s in self.get_critical_path()],
            "metadata": self.metadata,
        }


class TraceContext:
    """Thread-local trace context"""

    _thread_local = {}

    @classmethod
    def set_current_trace(cls, trace_id: str) -> None:
        """Set current trace ID"""
        import threading
        thread_id = threading.get_ident()
        if thread_id not in cls._thread_local:
            cls._thread_local[thread_id] = {}
        cls._thread_local[thread_id]["trace_id"] = trace_id

    @classmethod
    def get_current_trace(cls) -> Optional[str]:
        """Get current trace ID"""
        import threading
        thread_id = threading.get_ident()
        if thread_id in cls._thread_local:
            return cls._thread_local[thread_id].get("trace_id")
        return None

    @classmethod
    def set_current_span(cls, span_id: str) -> None:
        """Set current span ID"""
        import threading
        thread_id = threading.get_ident()
        if thread_id not in cls._thread_local:
            cls._thread_local[thread_id] = {}
        cls._thread_local[thread_id]["span_id"] = span_id

    @classmethod
    def get_current_span(cls) -> Optional[str]:
        """Get current span ID"""
        import threading
        thread_id = threading.get_ident()
        if thread_id in cls._thread_local:
            return cls._thread_local[thread_id].get("span_id")
        return None


class DistributedTracer:
    """
    Central distributed tracing service
    Tracks requests across multiple services
    """

    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.trace_retention_hours = 24  # Keep 24 hours of traces
        self.max_traces = 100000  # Max traces in memory

    def start_trace(self, user_id: str, tenant_id: str,
                   request_id: str, method: str, path: str) -> str:
        """
        Start a new trace
        Returns trace_id
        """
        trace_id = f"trace_{uuid.uuid4().hex[:16]}"

        trace = Trace(
            trace_id=trace_id,
            user_id=user_id,
            tenant_id=tenant_id,
            request_id=request_id,
            request_method=method,
            request_path=path
        )

        self.traces[trace_id] = trace
        TraceContext.set_current_trace(trace_id)

        logger.debug(f"Trace started: {trace_id} ({method} {path})")

        # Cleanup old traces if needed
        if len(self.traces) > self.max_traces:
            self._cleanup_old_traces()

        return trace_id

    def start_span(self, operation_name: str, service: str = None,
                  parent_span_id: Optional[str] = None) -> str:
        """
        Start a new span
        Returns span_id
        """
        trace_id = TraceContext.get_current_trace()
        if not trace_id or trace_id not in self.traces:
            logger.warning("No active trace for span")
            return None

        span_id = f"span_{uuid.uuid4().hex[:16]}"
        span = Span(span_id, operation_name, trace_id, parent_span_id)

        if service:
            span.set_tag("service", service)

        self.traces[trace_id].add_span(span)
        TraceContext.set_current_span(span_id)

        logger.debug(f"Span started: {operation_name} ({span_id})")

        return span_id

    def end_span(self, span_id: str, status: SpanStatus = SpanStatus.SUCCESS,
                error: Optional[str] = None) -> None:
        """End a span"""
        trace_id = TraceContext.get_current_trace()
        if not trace_id or trace_id not in self.traces:
            return

        span = self.traces[trace_id].spans.get(span_id)
        if span:
            span.finish(status, error)

    def record_metric(self, span_id: str, name: str, value: float) -> None:
        """Record metric in span"""
        trace_id = TraceContext.get_current_trace()
        if not trace_id or trace_id not in self.traces:
            return

        span = self.traces[trace_id].spans.get(span_id)
        if span:
            span.record_metric(name, value)

    def add_log(self, span_id: str, message: str, level: str = "info") -> None:
        """Add log to span"""
        trace_id = TraceContext.get_current_trace()
        if not trace_id or trace_id not in self.traces:
            return

        span = self.traces[trace_id].spans.get(span_id)
        if span:
            span.add_log(message, level)

    def end_trace(self, status: SpanStatus = SpanStatus.SUCCESS,
                 error: Optional[str] = None) -> None:
        """End current trace"""
        trace_id = TraceContext.get_current_trace()
        if not trace_id or trace_id not in self.traces:
            return

        self.traces[trace_id].finish(status, error)
        logger.debug(f"Trace finished: {trace_id}")

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get trace details"""
        if trace_id in self.traces:
            return self.traces[trace_id].to_dict()
        return None

    def get_traces(self, tenant_id: str, limit: int = 100,
                  offset: int = 0, filters: Dict = None) -> List[Dict]:
        """Query traces with filtering"""
        tenant_traces = [
            t for t in self.traces.values()
            if t.tenant_id == tenant_id
        ]

        # Apply filters
        if filters:
            if "min_duration" in filters:
                tenant_traces = [
                    t for t in tenant_traces
                    if t.duration >= filters["min_duration"]
                ]

            if "status" in filters:
                tenant_traces = [
                    t for t in tenant_traces
                    if t.status.value == filters["status"]
                ]

            if "service" in filters:
                service = filters["service"]
                tenant_traces = [
                    t for t in tenant_traces
                    if any(s.tags.get("service") == service for s in t.spans.values())
                ]

            if "error_only" in filters and filters["error_only"]:
                tenant_traces = [
                    t for t in tenant_traces
                    if t.status == SpanStatus.FAILED
                ]

        # Sort by start time descending
        tenant_traces.sort(key=lambda x: x.start_time, reverse=True)

        # Paginate
        paginated = tenant_traces[offset:offset + limit]

        return [t.to_dict() for t in paginated]

    def get_service_dependencies(self, tenant_id: str) -> Dict[str, set]:
        """Get service dependency graph"""
        dependencies = {}

        for trace in self.traces.values():
            if trace.tenant_id != tenant_id:
                continue

            for source, target in trace.get_service_dependencies():
                if source not in dependencies:
                    dependencies[source] = set()
                dependencies[source].add(target)

        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in dependencies.items()}

    def get_critical_path(self, trace_id: str) -> List[Dict]:
        """Get critical path for trace"""
        if trace_id not in self.traces:
            return []

        critical_path = self.traces[trace_id].get_critical_path()
        return [s.to_dict() for s in critical_path]

    def get_slowest_services(self, tenant_id: str, limit: int = 10) -> List[tuple[str, float]]:
        """Get slowest services by average duration"""
        service_times = {}

        for trace in self.traces.values():
            if trace.tenant_id != tenant_id:
                continue

            for span in trace.spans.values():
                if "service" in span.tags:
                    service = span.tags["service"]
                    if service not in service_times:
                        service_times[service] = {"total": 0, "count": 0}
                    service_times[service]["total"] += span.duration
                    service_times[service]["count"] += 1

        # Calculate averages and sort
        service_avg = [
            (service, data["total"] / data["count"])
            for service, data in service_times.items()
        ]

        service_avg.sort(key=lambda x: x[1], reverse=True)

        return service_avg[:limit]

    def _cleanup_old_traces(self) -> None:
        """Remove traces older than retention period"""
        cutoff_time = time.time() - (self.trace_retention_hours * 3600)
        old_traces = [
            trace_id for trace_id, trace in self.traces.items()
            if trace.start_time < cutoff_time
        ]

        for trace_id in old_traces:
            del self.traces[trace_id]

        logger.info(f"Cleaned up {len(old_traces)} old traces")

    def get_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get tracing statistics"""
        tenant_traces = [t for t in self.traces.values() if t.tenant_id == tenant_id]

        if not tenant_traces:
            return {
                "total_traces": 0,
                "avg_duration": 0,
                "total_spans": 0,
                "error_count": 0,
            }

        durations = [t.duration for t in tenant_traces]
        error_count = sum(1 for t in tenant_traces if t.status == SpanStatus.FAILED)
        total_spans = sum(t.span_count for t in tenant_traces)

        return {
            "total_traces": len(tenant_traces),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_spans": total_spans,
            "error_count": error_count,
            "error_rate": error_count / len(tenant_traces) * 100,
        }
