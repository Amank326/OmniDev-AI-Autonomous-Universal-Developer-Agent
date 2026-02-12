"""
Distributed Tracing Service
OpenTelemetry integration for distributed tracing and span collection
Phase 42: Observability & Monitoring Infrastructure
"""

import logging
import time
import uuid
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from threading import RLock
import queue

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """OpenTelemetry span kind"""
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(Enum):
    """Span status"""
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


@dataclass
class SpanEvent:
    """Event within a span"""
    timestamp: datetime
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanLink:
    """Link from one span to another"""
    trace_id: str
    span_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """OpenTelemetry span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    links: List[SpanLink] = field(default_factory=list)
    resource_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span"""
        event = SpanEvent(
            timestamp=datetime.utcnow(),
            name=name,
            attributes=attributes or {}
        )
        self.events.append(event)
    
    def add_link(self, trace_id: str, span_id: str,
                attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add link to another span"""
        link = SpanLink(trace_id, span_id, attributes or {})
        self.links.append(link)
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute"""
        self.attributes[key] = value
    
    def set_status(self, status: SpanStatus, description: Optional[str] = None) -> None:
        """Set span status"""
        self.status = status
        if description:
            self.attributes['status.description'] = description
    
    def end(self) -> None:
        """End span"""
        self.end_time = datetime.utcnow()
    
    def get_duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'name': self.name,
            'kind': self.kind.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.get_duration_ms(),
            'status': self.status.value,
            'attributes': self.attributes,
            'events': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'name': e.name,
                    'attributes': e.attributes
                }
                for e in self.events
            ],
            'resource_attributes': self.resource_attributes
        }


@dataclass
class Trace:
    """Collection of spans forming a trace"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    def add_span(self, span: Span) -> None:
        """Add span to trace"""
        self.spans.append(span)
    
    def get_root_span(self) -> Optional[Span]:
        """Get root span (no parent)"""
        for span in self.spans:
            if span.parent_span_id is None:
                return span
        return None
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Get span by ID"""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None
    
    def get_child_spans(self, parent_span_id: str) -> List[Span]:
        """Get child spans of given parent"""
        return [s for s in self.spans if s.parent_span_id == parent_span_id]
    
    def get_total_duration_ms(self) -> Optional[float]:
        """Get total trace duration"""
        root = self.get_root_span()
        if root and root.end_time:
            return (root.end_time - root.start_time).total_seconds() * 1000
        return None
    
    def finalize(self) -> None:
        """Finalize trace"""
        self.end_time = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'trace_id': self.trace_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'span_count': len(self.spans),
            'duration_ms': self.get_total_duration_ms(),
            'spans': [s.to_dict() for s in self.spans]
        }


class TraceContext:
    """Current trace context (thread-local style)"""
    
    def __init__(self):
        self.trace_id: Optional[str] = None
        self.span_id: Optional[str] = None
        self.parent_span_id: Optional[str] = None
        self.baggage: Dict[str, str] = {}
    
    def start_trace(self) -> str:
        """Start new trace"""
        self.trace_id = str(uuid.uuid4())
        self.span_id = str(uuid.uuid4())
        self.parent_span_id = None
        return self.trace_id
    
    def start_span(self, parent_span_id: Optional[str] = None) -> str:
        """Start new span"""
        self.parent_span_id = parent_span_id or self.span_id
        self.span_id = str(uuid.uuid4())
        return self.span_id
    
    def get_trace_context(self) -> Dict[str, str]:
        """Get trace context for propagation"""
        return {
            'trace_id': self.trace_id or '',
            'span_id': self.span_id or '',
            'parent_span_id': self.parent_span_id or '',
            'baggage': json.dumps(self.baggage)
        }
    
    def set_from_propagation(self, context: Dict[str, str]) -> None:
        """Set context from propagated values"""
        self.trace_id = context.get('trace_id')
        self.span_id = context.get('span_id')
        self.parent_span_id = context.get('parent_span_id')
        
        if 'baggage' in context:
            try:
                self.baggage = json.loads(context['baggage'])
            except json.JSONDecodeError:
                pass


class TraceCollector:
    """Collects and manages distributed traces"""
    
    def __init__(self, service_name: str = "omnidev",
                 retention_hours: int = 24):
        self.service_name = service_name
        self.retention_hours = retention_hours
        self.traces: Dict[str, Trace] = {}
        self.current_spans: Dict[str, Span] = {}
        self.lock = RLock()
        self.callbacks: List[Callable] = []
        self.export_queue = queue.Queue()
    
    def start_trace(self, name: str = "request",
                   attributes: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace"""
        trace_id = str(uuid.uuid4())
        trace = Trace(trace_id=trace_id)
        
        # Create root span
        span_id = str(uuid.uuid4())
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            name=name,
            kind=SpanKind.INTERNAL,
            start_time=datetime.utcnow(),
            resource_attributes={'service.name': self.service_name}
        )
        
        if attributes:
            span.attributes.update(attributes)
        
        with self.lock:
            trace.add_span(span)
            self.traces[trace_id] = trace
            self.current_spans[span_id] = span
        
        logger.debug(f"Started trace {trace_id} with root span {span_id}")
        return trace_id
    
    def start_span(self, trace_id: str, name: str,
                  kind: SpanKind = SpanKind.INTERNAL,
                  parent_span_id: Optional[str] = None,
                  attributes: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Start a new span in trace"""
        with self.lock:
            trace = self.traces.get(trace_id)
            if not trace:
                logger.warning(f"Trace {trace_id} not found")
                return None
        
        span_id = str(uuid.uuid4())
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time=datetime.utcnow(),
            resource_attributes={'service.name': self.service_name}
        )
        
        if attributes:
            span.attributes.update(attributes)
        
        with self.lock:
            trace.add_span(span)
            self.current_spans[span_id] = span
        
        logger.debug(f"Started span {span_id} in trace {trace_id}")
        return span_id
    
    def end_span(self, span_id: str, status: SpanStatus = SpanStatus.OK) -> None:
        """End a span"""
        with self.lock:
            span = self.current_spans.get(span_id)
            if span:
                span.end()
                span.set_status(status)
                del self.current_spans[span_id]
                logger.debug(f"Ended span {span_id}")
    
    def end_trace(self, trace_id: str) -> None:
        """End a trace"""
        with self.lock:
            trace = self.traces.get(trace_id)
            if trace:
                trace.finalize()
                
                # End any unclosed spans
                for span in trace.spans:
                    if span.end_time is None:
                        span.end()
                
                # Queue for export
                self.export_queue.put(trace)
                self._trigger_callbacks(trace)
                
                logger.debug(f"Ended trace {trace_id}")
    
    def add_event_to_span(self, span_id: str, event_name: str,
                         attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span"""
        with self.lock:
            span = self.current_spans.get(span_id)
            if span:
                span.add_event(event_name, attributes)
    
    def set_span_attribute(self, span_id: str, key: str, value: Any) -> None:
        """Set attribute on span"""
        with self.lock:
            span = self.current_spans.get(span_id)
            if span:
                span.set_attribute(key, value)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID"""
        with self.lock:
            return self.traces.get(trace_id)
    
    def get_traces_by_service(self, service_name: str) -> List[Trace]:
        """Get traces for a service"""
        with self.lock:
            results = []
            for trace in self.traces.values():
                for span in trace.spans:
                    if span.resource_attributes.get('service.name') == service_name:
                        results.append(trace)
                        break
            return results
    
    def get_traces_by_duration(self, min_ms: float = None, max_ms: float = None) -> List[Trace]:
        """Get traces by duration"""
        results = []
        
        with self.lock:
            for trace in self.traces.values():
                duration = trace.get_total_duration_ms()
                if duration is None:
                    continue
                
                if min_ms and duration < min_ms:
                    continue
                if max_ms and duration > max_ms:
                    continue
                
                results.append(trace)
        
        return results
    
    def find_slow_traces(self, threshold_ms: float = 1000) -> List[Trace]:
        """Find traces exceeding duration threshold"""
        return self.get_traces_by_duration(min_ms=threshold_ms)
    
    def export_traces(self, exporter: Callable[[Trace], None]) -> None:
        """Export collected traces"""
        while not self.export_queue.empty():
            try:
                trace = self.export_queue.get_nowait()
                exporter(trace)
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Export error: {e}")
    
    def cleanup_old_traces(self) -> None:
        """Remove old traces beyond retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        with self.lock:
            to_delete = [
                trace_id for trace_id, trace in self.traces.items()
                if trace.start_time < cutoff_time
            ]
            
            for trace_id in to_delete:
                del self.traces[trace_id]
                logger.debug(f"Cleaned up trace {trace_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        with self.lock:
            total_traces = len(self.traces)
            total_spans = sum(len(t.spans) for t in self.traces.values())
            
            # Find slow traces
            slow_traces = [
                t for t in self.traces.values()
                if t.get_total_duration_ms() and t.get_total_duration_ms() > 1000
            ]
            
            return {
                'total_traces': total_traces,
                'total_spans': total_spans,
                'active_spans': len(self.current_spans),
                'slow_traces': len(slow_traces),
                'avg_spans_per_trace': total_spans / max(total_traces, 1)
            }
    
    def register_callback(self, callback: Callable[[Trace], None]) -> None:
        """Register callback for trace completion"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callbacks(self, trace: Trace) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(trace)
            except Exception as e:
                logger.error(f"Callback error: {e}")


@dataclass
class SpanContextPropagation:
    """SpanContext for W3C Trace Context propagation"""
    trace_id: str
    span_id: str
    trace_flags: int = 0x01  # sampled
    
    def to_header(self) -> str:
        """Convert to traceparent header"""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags:02x}"
    
    @staticmethod
    def from_header(header: str) -> Optional['SpanContextPropagation']:
        """Parse from traceparent header"""
        try:
            parts = header.split('-')
            if len(parts) >= 4:
                return SpanContextPropagation(
                    trace_id=parts[1],
                    span_id=parts[2],
                    trace_flags=int(parts[3], 16)
                )
        except Exception as e:
            logger.error(f"Error parsing trace header: {e}")
        
        return None


# Global trace collector
_trace_collector: Optional[TraceCollector] = None


def get_trace_collector(service_name: str = "omnidev",
                       retention_hours: int = 24) -> TraceCollector:
    """Get or create trace collector"""
    global _trace_collector
    if _trace_collector is None:
        _trace_collector = TraceCollector(service_name, retention_hours)
    return _trace_collector
