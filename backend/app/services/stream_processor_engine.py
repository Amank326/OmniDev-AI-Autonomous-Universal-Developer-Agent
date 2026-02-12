"""
Stream Processor Engine - Real-time stream processing with transformations
Provides windowing, stateful operations, time-based processing
"""

import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict
import json


class WindowType(Enum):
    """Stream window types"""
    TUMBLING = "tumbling"  # Non-overlapping, fixed-size windows
    SLIDING = "sliding"  # Overlapping windows
    SESSION = "session"  # Event-triggered windows
    GLOBAL = "global"  # All events in window


class AggregationFunction(Enum):
    """Aggregation operations"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    FIRST = "first"
    LAST = "last"
    COLLECT = "collect"


class ProcessingMode(Enum):
    """Stream processing mode"""
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"
    AT_MOST_ONCE = "at_most_once"


@dataclass
class StreamEvent:
    """Event in stream processing"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_time: float = field(default_factory=time.time)
    processing_time: float = field(default_factory=time.time)
    watermark: Optional[float] = None
    partition_key: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    is_late: bool = False
    
    def __hash__(self):
        return hash(self.event_id)
    
    def __eq__(self, other):
        if not isinstance(other, StreamEvent):
            return False
        return self.event_id == other.event_id


@dataclass
class WindowConfig:
    """Window configuration"""
    window_type: WindowType = WindowType.TUMBLING
    window_size_seconds: int = 60
    slide_size_seconds: Optional[int] = None  # For sliding windows
    grace_period_seconds: int = 10  # Late data tolerance
    allowed_lateness_seconds: int = 3600  # 1 hour


@dataclass
class ProcessorState:
    """State for stateful stream processing"""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    values: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if state has expired"""
        if self.ttl_seconds is None:
            return False
        return time.time() - self.last_updated > self.ttl_seconds


@dataclass
class ProcessingStatistics:
    """Stream processing statistics"""
    events_processed: int = 0
    events_dropped: int = 0
    events_late: int = 0
    processing_latency_ms: float = 0.0
    avg_window_size: float = 0.0
    backpressure_events: int = 0


class ProcessorFunction:
    """Base class for stream processing functions"""
    
    def process(self, event: StreamEvent) -> Optional[StreamEvent]:
        """Process single event"""
        return event
    
    def process_batch(self, events: List[StreamEvent]) -> List[StreamEvent]:
        """Process batch of events"""
        return [self.process(e) for e in events if self.process(e) is not None]


class MapFunction(ProcessorFunction):
    """Map transformation on stream"""
    
    def __init__(self, map_func: Callable[[Dict], Dict]):
        self.map_func = map_func
    
    def process(self, event: StreamEvent) -> Optional[StreamEvent]:
        try:
            event.data = self.map_func(event.data)
            return event
        except Exception:
            return None


class FilterFunction(ProcessorFunction):
    """Filter events from stream"""
    
    def __init__(self, filter_func: Callable[[Dict], bool]):
        self.filter_func = filter_func
    
    def process(self, event: StreamEvent) -> Optional[StreamEvent]:
        try:
            if self.filter_func(event.data):
                return event
            return None
        except Exception:
            return None


class FlatMapFunction(ProcessorFunction):
    """Flat map producing multiple events"""
    
    def __init__(self, flatmap_func: Callable[[Dict], List[Dict]]):
        self.flatmap_func = flatmap_func
    
    def process_batch(self, events: List[StreamEvent]) -> List[StreamEvent]:
        results = []
        for event in events:
            try:
                mapped_data = self.flatmap_func(event.data)
                for data in mapped_data:
                    new_event = StreamEvent(
                        event_time=event.event_time,
                        partition_key=event.partition_key,
                        data=data
                    )
                    results.append(new_event)
            except Exception:
                pass
        return results


class StreamWindow:
    """Window containing stream events"""
    
    def __init__(self, window_id: str, start_time: float, end_time: float, window_config: WindowConfig):
        self.window_id = window_id
        self.start_time = start_time
        self.end_time = end_time
        self.config = window_config
        self.events: List[StreamEvent] = []
        self.state_storage: Dict[str, Dict] = {}
        self.created_at = time.time()
        self.is_triggered = False
        self.is_finalized = False
    
    def add_event(self, event: StreamEvent) -> bool:
        """Add event to window"""
        if event.event_time < self.start_time or event.event_time >= self.end_time:
            # Late data
            if event.event_time < self.start_time and \
               time.time() - event.event_time <= self.config.allowed_lateness_seconds:
                event.is_late = True
                self.events.append(event)
                return True
            return False
        
        self.events.append(event)
        return True
    
    def get_events(self) -> List[StreamEvent]:
        """Get all events in window"""
        return self.events
    
    def aggregate(self, agg_func: AggregationFunction, field_name: str) -> Any:
        """Aggregate field values"""
        if not self.events:
            return None
        
        values = [e.data.get(field_name) for e in self.events if field_name in e.data]
        
        if agg_func == AggregationFunction.COUNT:
            return len(values)
        elif agg_func == AggregationFunction.SUM:
            return sum(float(v) for v in values if v is not None)
        elif agg_func == AggregationFunction.AVG:
            return sum(float(v) for v in values) / len(values) if values else 0
        elif agg_func == AggregationFunction.MIN:
            return min(values) if values else None
        elif agg_func == AggregationFunction.MAX:
            return max(values) if values else None
        elif agg_func == AggregationFunction.FIRST:
            return values[0] if values else None
        elif agg_func == AggregationFunction.LAST:
            return values[-1] if values else None
        elif agg_func == AggregationFunction.COLLECT:
            return values
        
        return None


class StateStore:
    """State storage for stateful processing"""
    
    def __init__(self, store_id: str):
        self.store_id = store_id
        self.state: Dict[str, ProcessorState] = {}
        self.lock = threading.RLock()
    
    def put(self, key: str, values: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        """Store state"""
        with self.lock:
            state = ProcessorState(
                key=key,
                values=values,
                ttl_seconds=ttl_seconds
            )
            self.state[key] = state
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve state"""
        with self.lock:
            if key not in self.state:
                return None
            
            state = self.state[key]
            if state.is_expired():
                del self.state[key]
                return None
            
            state.last_updated = time.time()
            return state.values
    
    def delete(self, key: str) -> bool:
        """Delete state"""
        with self.lock:
            if key in self.state:
                del self.state[key]
                return True
            return False
    
    def cleanup_expired(self) -> int:
        """Remove expired state entries"""
        with self.lock:
            expired_keys = [
                k for k, v in self.state.items()
                if v.is_expired()
            ]
            for k in expired_keys:
                del self.state[k]
            return len(expired_keys)


class StreamProcessorEngine:
    """Real-time stream processing engine"""
    
    def __init__(self, processing_mode: ProcessingMode = ProcessingMode.AT_LEAST_ONCE):
        self.processing_mode = processing_mode
        self.windows: Dict[str, StreamWindow] = {}
        self.state_stores: Dict[str, StateStore] = {}
        self.processors: List[ProcessorFunction] = []
        self.output_handlers: Dict[str, Callable] = {}
        self.watermark = 0.0
        self.watermark_idle_timeout_seconds = 60
        self.last_event_time = 0.0
        self.stats = ProcessingStatistics()
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        
        # Buffering for backpressure
        self.event_buffer: deque = deque(maxlen=10000)
        self.max_buffer_size = 10000
    
    def add_processor(self, processor: ProcessorFunction) -> None:
        """Add processing function"""
        with self.lock:
            self.processors.append(processor)
    
    def create_state_store(self, store_name: str) -> StateStore:
        """Create state store for stateful processing"""
        store = StateStore(store_name)
        with self.lock:
            self.state_stores[store_name] = store
        return store
    
    def register_output_handler(self, output_name: str, handler: Callable[[StreamEvent], None]) -> None:
        """Register output handler"""
        with self.lock:
            self.output_handlers[output_name] = handler
    
    def process_event(self, event: StreamEvent) -> None:
        """Process single event"""
        # Check buffer pressure
        if len(self.event_buffer) >= self.max_buffer_size:
            self.stats.backpressure_events += 1
            self._trigger_callback("backpressure_event")
            return
        
        start_time = time.time()
        
        # Update watermark based on event time
        if event.event_time > self.last_event_time:
            self.last_event_time = event.event_time
            self.watermark = event.event_time
        
        # Apply processors
        processed_event = event
        for processor in self.processors:
            processed_event = processor.process(processed_event)
            if processed_event is None:
                self.stats.events_dropped += 1
                self._trigger_callback("event_dropped", event.event_id)
                return
        
        # Handle late events
        if processed_event.event_time < self.watermark:
            processed_event.is_late = True
            self.stats.events_late += 1
        
        self.event_buffer.append(processed_event)
        self.stats.events_processed += 1
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        self.stats.processing_latency_ms = (
            (self.stats.processing_latency_ms + latency_ms) / 2
        )
        
        # Send to output handlers
        for handler in self.output_handlers.values():
            try:
                handler(processed_event)
            except Exception:
                pass
        
        self._trigger_callback("event_processed", processed_event.event_id)
    
    def process_events_windowed(self, events: List[StreamEvent],
                               window_config: WindowConfig) -> List[Dict]:
        """Process events with windowing"""
        if not events:
            return []
        
        # Create windows
        events.sort(key=lambda e: e.event_time)
        min_time = events[0].event_time
        max_time = events[-1].event_time
        
        results = []
        current_time = min_time
        
        while current_time <= max_time:
            window_start = current_time
            window_end = current_time + window_config.window_size_seconds
            window_id = str(uuid.uuid4())
            
            window = StreamWindow(window_id, window_start, window_end, window_config)
            
            # Add events to window
            for event in events:
                if window.add_event(event):
                    pass
            
            # Emit window result
            result = {
                "window_id": window_id,
                "start_time": window_start,
                "end_time": window_end,
                "event_count": len(window.events),
                "events": window.events,
                "late_event_count": sum(1 for e in window.events if e.is_late),
            }
            results.append(result)
            
            current_time += window_config.window_size_seconds if window_config.slide_size_seconds is None \
                           else window_config.slide_size_seconds
        
        return results
    
    def join_streams(self, stream1: List[StreamEvent], stream2: List[StreamEvent],
                    join_key: str, window_config: WindowConfig) -> List[Dict]:
        """Join two streams"""
        # Index stream2
        stream2_index = defaultdict(list)
        for event in stream2:
            if join_key in event.data:
                key = event.data[join_key]
                stream2_index[key].append(event)
        
        # Join with stream1
        results = []
        for event1 in stream1:
            if join_key in event1.data:
                key = event1.data[join_key]
                if key in stream2_index:
                    for event2 in stream2_index[key]:
                        # Check time window
                        if abs(event1.event_time - event2.event_time) <= window_config.window_size_seconds:
                            joined = {
                                "event1": event1.data,
                                "event2": event2.data,
                                "join_key": key,
                            }
                            results.append(joined)
        
        return results
    
    def get_watermark(self) -> float:
        """Get current watermark"""
        return self.watermark
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        with self.lock:
            return {
                "events_processed": self.stats.events_processed,
                "events_dropped": self.stats.events_dropped,
                "events_late": self.stats.events_late,
                "processing_latency_ms": self.stats.processing_latency_ms,
                "backpressure_events": self.stats.backpressure_events,
                "buffered_events": len(self.event_buffer),
                "buffer_utilization": len(self.event_buffer) / self.max_buffer_size * 100,
                "watermark": self.watermark,
            }
    
    def checkpoint(self) -> Dict[str, Any]:
        """Create checkpoint for fault tolerance"""
        with self.lock:
            checkpoint_data = {
                "timestamp": time.time(),
                "watermark": self.watermark,
                "buffered_events": len(self.event_buffer),
                "state_stores": {
                    name: {
                        key: store.state[key].values
                        for key in store.state.keys()
                    }
                    for name, store in self.state_stores.items()
                }
            }
            self._trigger_callback("checkpoint_created", checkpoint_data)
            return checkpoint_data
    
    def register_callback(self, callback: Callable[[str, ...], None]) -> None:
        """Register event callback"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callback(self, event_type: str, *args, **kwargs) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(event_type, *args, **kwargs)
            except Exception:
                pass
    
    def flush(self) -> None:
        """Flush buffered events"""
        with self.lock:
            events_to_process = list(self.event_buffer)
            self.event_buffer.clear()
            
            for event in events_to_process:
                for handler in self.output_handlers.values():
                    try:
                        handler(event)
                    except Exception:
                        pass


# Singleton instance
_stream_processor: Optional[StreamProcessorEngine] = None


def get_stream_processor(mode: ProcessingMode = ProcessingMode.AT_LEAST_ONCE) -> StreamProcessorEngine:
    """Get or create singleton stream processor"""
    global _stream_processor
    if _stream_processor is None:
        _stream_processor = StreamProcessorEngine(mode)
    return _stream_processor


def reset_stream_processor() -> None:
    """Reset stream processor (for testing)"""
    global _stream_processor
    _stream_processor = None
