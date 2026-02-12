"""
Distributed tracing service for comprehensive request flow visibility.
Handles span creation, context propagation, trace collection, and performance analysis.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json
import uuid
from collections import defaultdict
import threading
import time


class SpanKind(Enum):
    """Types of spans."""
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(Enum):
    """Span completion status."""
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


@dataclass
class SpanAttribute:
    """Span attribute with type."""
    key: str
    value: Any
    attribute_type: str = "string"


@dataclass
class SpanEvent:
    """Event within a span."""
    name: str
    timestamp: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanLink:
    """Link to another span."""
    trace_id: str
    span_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Represents a single span in a trace."""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    status: SpanStatus
    workspace_id: str
    service_name: str
    resource: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    links: List[SpanLink] = field(default_factory=list)
    instrument_name: Optional[str] = None
    error_message: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self):
        """Convert to dictionary."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['kind'] = self.kind.value
        data['status'] = self.status.value
        return data


@dataclass
class Trace:
    """Represents a complete trace with all spans."""
    trace_id: str
    workspace_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    root_span_name: str
    root_service: str
    spans: List[Span] = field(default_factory=list)
    service_count: int = 0
    span_count: int = 0
    error_count: int = 0
    status: SpanStatus = SpanStatus.OK
    critical_path_duration_ms: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'trace_id': self.trace_id,
            'workspace_id': self.workspace_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'root_span_name': self.root_span_name,
            'root_service': self.root_service,
            'span_count': self.span_count,
            'service_count': self.service_count,
            'error_count': self.error_count,
            'status': self.status.value,
            'critical_path_duration_ms': self.critical_path_duration_ms,
            'attributes': self.attributes,
        }


@dataclass
class TraceFilter:
    """Trace filtering criteria."""
    workspace_id: Optional[str] = None
    service_name: Optional[str] = None
    operation_name: Optional[str] = None
    min_duration_ms: Optional[float] = None
    max_duration_ms: Optional[float] = None
    has_errors: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Optional[List[str]] = None
    status: Optional[SpanStatus] = None


@dataclass
class TraceMetrics:
    """Aggregated trace metrics."""
    trace_count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    p999_duration_ms: float
    error_rate: float
    error_count: int
    services_involved: List[str]
    operations: Dict[str, int]
    slowest_traces: List[Dict[str, Any]]


class TraceContext:
    """Context for distributed tracing."""

    def __init__(self, trace_id: str, span_id: str, parent_span_id: Optional[str] = None):
        self.trace_id = trace_id
        span_id = span_id
        self.parent_span_id = parent_span_id
        self.baggage = {}

    def with_baggage(self, key: str, value: str) -> 'TraceContext':
        """Add baggage to context."""
        self.baggage[key] = value
        return self


class DistributedTracingService:
    """
    Distributed tracing service for request flow analysis.

    Features:
    - Span creation and tracking
    - Context propagation across services
    - Trace collection and aggregation
    - Performance analysis
    - Critical path analysis
    - Service dependency mapping
    - Error tracking
    - Custom attributes and events
    - Trace sampling
    - Real-time trace streaming
    """

    def __init__(self, max_traces: int = 10000, sampling_rate: float = 1.0):
        """Initialize tracing service."""
        self.max_traces = max_traces
        self.sampling_rate = sampling_rate

        # Storage
        self.traces: Dict[str, Trace] = {}
        self.spans: Dict[str, List[Span]] = defaultdict(list)  # trace_id -> spans
        self.active_spans: Dict[str, Span] = {}  # span_id -> span

        # Tracking
        self.service_graph: Dict[str, set] = defaultdict(set)  # from_service -> to_services
        self.operation_timeline: List[Dict[str, Any]] = []

        # Threading
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.running = False

        # Callbacks
        self.trace_callbacks: List[callable] = []

    def start(self):
        """Start tracing service."""
        with self.lock:
            if self.running:
                return
            self.running = True

    def stop(self):
        """Stop tracing service."""
        with self.lock:
            self.running = False

    def start_trace(self,
                   workspace_id: str,
                   root_span_name: str,
                   root_service: str,
                   attributes: Optional[Dict[str, Any]] = None,
                   trace_id: Optional[str] = None,
                   tags: Optional[List[str]] = None) -> Trace:
        """Start a new trace."""
        # Check sampling
        import random
        if random.random() > self.sampling_rate:
            return None

        trace_id = trace_id or str(uuid.uuid4())

        with self.lock:
            trace = Trace(
                trace_id=trace_id,
                workspace_id=workspace_id,
                start_time=datetime.utcnow(),
                end_time=None,
                duration_ms=None,
                root_span_name=root_span_name,
                root_service=root_service,
                attributes=attributes or {},
            )
            self.traces[trace_id] = trace
            return trace

    def start_span(self,
                  trace_id: str,
                  workspace_id: str,
                  operation_name: str,
                  service_name: str,
                  span_kind: SpanKind = SpanKind.INTERNAL,
                  parent_span_id: Optional[str] = None,
                  attributes: Optional[Dict[str, Any]] = None,
                  tags: Optional[List[str]] = None,
                  instrument_name: Optional[str] = None) -> Span:
        """Start a new span in a trace."""
        span_id = str(uuid.uuid4())

        with self.lock:
            span = Span(
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                name=operation_name,
                kind=span_kind,
                start_time=datetime.utcnow(),
                end_time=None,
                duration_ms=None,
                status=SpanStatus.UNSET,
                workspace_id=workspace_id,
                service_name=service_name,
                attributes=attributes or {},
                instrument_name=instrument_name,
                tags=tags or [],
            )

            # Store span
            self.spans[trace_id].append(span)
            self.active_spans[span_id] = span

            # Update service graph
            if parent_span_id:
                parent = self.active_spans.get(parent_span_id)
                if parent:
                    self.service_graph[parent.service_name].add(service_name)

            # Update trace
            if trace_id in self.traces:
                self.traces[trace_id].span_count += 1

            return span

    def end_span(self,
                span_id: str,
                status: SpanStatus = SpanStatus.OK,
                error_message: Optional[str] = None,
                attributes: Optional[Dict[str, Any]] = None):
        """End a span."""
        with self.lock:
            if span_id not in self.active_spans:
                return

            span = self.active_spans[span_id]
            span.end_time = datetime.utcnow()
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            span.status = status
            span.error_message = error_message

            if attributes:
                span.attributes.update(attributes)

            # Update trace
            trace = self.traces.get(span.trace_id)
            if trace:
                if status == SpanStatus.ERROR:
                    trace.error_count += 1
                    trace.status = SpanStatus.ERROR

            del self.active_spans[span_id]

    def add_span_event(self, span_id: str, event_name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to a span."""
        with self.lock:
            if span_id not in self.active_spans:
                return

            span = self.active_spans[span_id]
            event = SpanEvent(
                name=event_name,
                timestamp=datetime.utcnow(),
                attributes=attributes or {},
            )
            span.events.append(event)

    def add_span_attribute(self, span_id: str, key: str, value: Any):
        """Add an attribute to a span."""
        with self.lock:
            if span_id in self.active_spans:
                self.active_spans[span_id].attributes[key] = value
            else:
                # Try to find in completed spans
                for spans_list in self.spans.values():
                    for span in spans_list:
                        if span.span_id == span_id:
                            span.attributes[key] = value
                            return

    def add_span_link(self,
                     span_id: str,
                     linked_trace_id: str,
                     linked_span_id: str,
                     attributes: Optional[Dict[str, Any]] = None):
        """Add a link to another span."""
        with self.lock:
            span = self.active_spans.get(span_id)
            if span:
                link = SpanLink(
                    trace_id=linked_trace_id,
                    span_id=linked_span_id,
                    attributes=attributes or {},
                )
                span.links.append(link)

    def end_trace(self, trace_id: str):
        """Complete a trace."""
        with self.lock:
            if trace_id not in self.traces:
                return

            trace = self.traces[trace_id]
            trace.end_time = datetime.utcnow()
            trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000

            # Calculate metrics
            trace.service_count = len(set(span.service_name for span in self.spans[trace_id]))
            trace.critical_path_duration_ms = self._calculate_critical_path(trace_id)

            # Invoke callbacks
            for callback in self.trace_callbacks:
                try:
                    callback(trace)
                except Exception:
                    pass

            # Enforce size limit
            if len(self.traces) > self.max_traces:
                oldest_id = min(self.traces.keys(), key=lambda x: self.traces[x].start_time)
                del self.traces[oldest_id]
                if oldest_id in self.spans:
                    del self.spans[oldest_id]

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Retrieve a trace with all its spans."""
        with self.lock:
            trace = self.traces.get(trace_id)
            if trace:
                trace.spans = self.spans[trace_id]
            return trace

    def search_traces(self, filter: TraceFilter, limit: int = 100) -> List[Trace]:
        """Search traces by criteria."""
        with self.lock:
            results = []

            for trace_id, trace in self.traces.items():
                # Workspace filter
                if filter.workspace_id and trace.workspace_id != filter.workspace_id:
                    continue

                # Service filter
                if filter.service_name and filter.service_name not in [trace.root_service] + list(self.service_graph.get(trace.root_service, [])):
                    continue

                # Operation filter
                if filter.operation_name and trace.root_span_name != filter.operation_name:
                    continue

                # Duration filter
                if filter.min_duration_ms and trace.duration_ms < filter.min_duration_ms:
                    continue
                if filter.max_duration_ms and trace.duration_ms > filter.max_duration_ms:
                    continue

                # Error filter
                if filter.has_errors is not None:
                    has_errors = trace.error_count > 0
                    if has_errors != filter.has_errors:
                        continue

                # Time filter
                if filter.start_time and trace.start_time < filter.start_time:
                    continue
                if filter.end_time and trace.end_time and trace.end_time > filter.end_time:
                    continue

                # Status filter
                if filter.status and trace.status != filter.status:
                    continue

                results.append(trace)
                if len(results) >= limit:
                    break

            return results

    def get_trace_metrics(self, filter: Optional[TraceFilter] = None) -> TraceMetrics:
        """Get aggregated trace metrics."""
        with self.lock:
            traces = self.search_traces(filter or TraceFilter(), limit=10000)

            if not traces:
                return TraceMetrics(
                    trace_count=0,
                    total_duration_ms=0,
                    avg_duration_ms=0,
                    min_duration_ms=0,
                    max_duration_ms=0,
                    p50_duration_ms=0,
                    p95_duration_ms=0,
                    p99_duration_ms=0,
                    p999_duration_ms=0,
                    error_rate=0,
                    error_count=0,
                    services_involved=[],
                    operations={},
                    slowest_traces=[],
                )

            durations = [t.duration_ms for t in traces if t.duration_ms]
            sorted_durations = sorted(durations)

            # Calculate percentiles
            p50 = sorted_durations[int(len(sorted_durations) * 0.50)] if sorted_durations else 0
            p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if sorted_durations else 0
            p99 = sorted_durations[int(len(sorted_durations) * 0.99)] if sorted_durations else 0
            p999 = sorted_durations[int(len(sorted_durations) * 0.999)] if sorted_durations else 0

            # Services
            services = set()
            for trace in traces:
                services.add(trace.root_service)
                services.update(self.service_graph.get(trace.root_service, []))

            # Operations
            operations = {}
            for trace in traces:
                op = trace.root_span_name
                operations[op] = operations.get(op, 0) + 1

            # Slowest traces
            slowest = sorted(traces, key=lambda t: t.duration_ms or 0, reverse=True)[:5]

            error_count = sum(1 for t in traces if t.error_count > 0)

            return TraceMetrics(
                trace_count=len(traces),
                total_duration_ms=sum(durations),
                avg_duration_ms=sum(durations) / len(durations) if durations else 0,
                min_duration_ms=min(sorted_durations) if sorted_durations else 0,
                max_duration_ms=max(sorted_durations) if sorted_durations else 0,
                p50_duration_ms=p50,
                p95_duration_ms=p95,
                p99_duration_ms=p99,
                p999_duration_ms=p999,
                error_rate=error_count / len(traces) if traces else 0,
                error_count=error_count,
                services_involved=list(services),
                operations=operations,
                slowest_traces=[
                    {
                        'trace_id': t.trace_id,
                        'operation': t.root_span_name,
                        'duration_ms': t.duration_ms,
                        'error_count': t.error_count,
                    }
                    for t in slowest
                ],
            )

    def get_service_dependencies(self, workspace_id: Optional[str] = None) -> Dict[str, List[str]]:
        """Get service dependency graph."""
        with self.lock:
            return dict(self.service_graph)

    def get_critical_path(self, trace_id: str) -> List[Span]:
        """Get critical path (longest chain of dependent spans)."""
        with self.lock:
            if trace_id not in self.spans:
                return []

            spans = self.spans[trace_id]
            if not spans:
                return []

            # Build dependency graph
            children: Dict[Optional[str], List[Span]] = defaultdict(list)
            for span in spans:
                children[span.parent_span_id].append(span)

            # Find critical path from root
            def find_path(parent_id):
                if parent_id not in children:
                    return []

                max_path = []
                for child in children[parent_id]:
                    path = [child] + find_path(child.span_id)
                    if sum(s.duration_ms or 0 for s in path) > sum(s.duration_ms or 0 for s in max_path):
                        max_path = path

                return max_path

            return find_path(None)

    def _calculate_critical_path(self, trace_id: str) -> Optional[float]:
        """Calculate critical path duration."""
        path = self.get_critical_path(trace_id)
        if path:
            return sum(s.duration_ms for s in path if s.duration_ms)
        return None

    def add_trace_callback(self, callback: callable):
        """Add callback for completed traces."""
        with self.lock:
            self.trace_callbacks.append(callback)

    def remove_trace_callback(self, callback: callable):
        """Remove trace callback."""
        with self.lock:
            if callback in self.trace_callbacks:
                self.trace_callbacks.remove(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Get tracing service statistics."""
        with self.lock:
            return {
                'total_traces': len(self.traces),
                'total_spans': sum(len(spans) for spans in self.spans.values()),
                'active_spans': len(self.active_spans),
                'services_count': len(self.service_graph),
                'pending_traces': len([t for t in self.traces.values() if t.end_time is None]),
            }
