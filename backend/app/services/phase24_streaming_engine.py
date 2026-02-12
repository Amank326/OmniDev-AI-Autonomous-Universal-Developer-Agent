"""
Phase 24: Streaming Engine
Real-time data stream processing with buffering, batching, and transformations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json
import uuid


class StreamStatus(Enum):
    """Stream status states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class WindowType(Enum):
    """Stream window types"""
    TUMBLING = "tumbling"  # Fixed non-overlapping
    SLIDING = "sliding"    # Overlapping with stride
    SESSION = "session"    # Based on activity
    GLOBAL = "global"      # All events


@dataclass
class StreamEvent:
    """Represents a single event in the stream"""
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    event_type: str = "data"

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())


@dataclass
class StreamWindow:
    """Stream window for aggregation"""
    window_id: str
    window_type: WindowType
    start_time: datetime
    end_time: datetime
    events: List[StreamEvent] = field(default_factory=list)
    aggregations: Dict = field(default_factory=dict)
    is_closed: bool = False

    def add_event(self, event: StreamEvent) -> bool:
        """Add event to window"""
        if event.timestamp >= self.start_time and event.timestamp < self.end_time:
            self.events.append(event)
            return True
        return False

    def get_event_count(self) -> int:
        """Get number of events in window"""
        return len(self.events)


@dataclass
class StreamMetrics:
    """Stream processing metrics"""
    stream_id: str
    events_processed: int = 0
    events_failed: int = 0
    events_buffered: int = 0
    batches_processed: int = 0
    avg_latency_ms: float = 0.0
    throughput_events_per_sec: float = 0.0
    backpressure_triggered: int = 0
    last_event_timestamp: Optional[datetime] = None
    start_time: Optional[datetime] = None
    error_count: int = 0


class StreamingEngine:
    """
    Real-time data stream processing engine
    Handles event buffering, batching, windowing, and transformations
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.streams: Dict[str, Dict] = {}
        self.stream_buffers: Dict[str, deque] = {}
        self.stream_windows: Dict[str, List[StreamWindow]] = {}
        self.stream_metrics: Dict[str, StreamMetrics] = {}
        self.transform_functions: Dict[str, Callable] = {}
        self.aggregate_functions: Dict[str, Callable] = {}
        self.backpressure_threshold = 10000
        self.batch_size = 100
        self.window_duration_seconds = 60

    # ========================================================================
    # STREAM LIFECYCLE
    # ========================================================================

    def create_stream(
        self,
        stream_name: str,
        source: str,
        event_schema: Dict = None,
        metadata: Dict = None,
    ) -> Dict:
        """
        Create new data stream
        
        Args:
            stream_name: Stream name
            source: Data source (database, api, kafka, etc)
            event_schema: Schema for validation
            metadata: Additional metadata
        
        Returns:
            Stream configuration dict
        """
        stream_id = str(uuid.uuid4())
        now = datetime.utcnow()

        stream_config = {
            "stream_id": stream_id,
            "name": stream_name,
            "source": source,
            "created_at": now,
            "status": StreamStatus.IDLE.value,
            "event_schema": event_schema or {},
            "metadata": metadata or {},
        }

        self.streams[stream_id] = stream_config
        self.stream_buffers[stream_id] = deque(maxlen=self.backpressure_threshold)
        self.stream_windows[stream_id] = []
        self.stream_metrics[stream_id] = StreamMetrics(stream_id=stream_id, start_time=now)

        return stream_config

    def start_stream(self, stream_id: str) -> bool:
        """
        Start stream processing
        
        Args:
            stream_id: Stream ID
        
        Returns:
            Success status
        """
        if stream_id not in self.streams:
            return False

        self.streams[stream_id]["status"] = StreamStatus.RUNNING.value
        self.stream_metrics[stream_id].start_time = datetime.utcnow()

        return True

    def stop_stream(self, stream_id: str) -> bool:
        """
        Stop stream processing
        
        Args:
            stream_id: Stream ID
        
        Returns:
            Success status
        """
        if stream_id not in self.streams:
            return False

        self.streams[stream_id]["status"] = StreamStatus.STOPPED.value

        return True

    def pause_stream(self, stream_id: str) -> bool:
        """Pause stream temporarily"""
        if stream_id not in self.streams:
            return False

        self.streams[stream_id]["status"] = StreamStatus.PAUSED.value

        return True

    def resume_stream(self, stream_id: str) -> bool:
        """Resume paused stream"""
        if stream_id not in self.streams:
            return False

        self.streams[stream_id]["status"] = StreamStatus.RUNNING.value

        return True

    # ========================================================================
    # EVENT PROCESSING
    # ========================================================================

    def add_event(self, stream_id: str, event: StreamEvent) -> bool:
        """
        Add event to stream
        
        Args:
            stream_id: Stream ID
            event: StreamEvent
        
        Returns:
            Success status
        """
        if stream_id not in self.streams:
            return False

        stream_status = self.streams[stream_id]["status"]
        if stream_status not in [StreamStatus.RUNNING.value]:
            return False

        try:
            self.stream_buffers[stream_id].append(event)
            metrics = self.stream_metrics[stream_id]
            metrics.events_buffered = len(self.stream_buffers[stream_id])
            metrics.last_event_timestamp = event.timestamp

            # Check backpressure
            if metrics.events_buffered >= self.backpressure_threshold:
                metrics.backpressure_triggered += 1
                return False

            return True
        except Exception as e:
            self.stream_metrics[stream_id].error_count += 1
            return False

    def add_events_batch(self, stream_id: str, events: List[StreamEvent]) -> int:
        """
        Add batch of events to stream
        
        Args:
            stream_id: Stream ID
            events: List of StreamEvents
        
        Returns:
            Number of events added
        """
        added_count = 0

        for event in events:
            if self.add_event(stream_id, event):
                added_count += 1

        return added_count

    def process_batch(self, stream_id: str, batch_size: int = None) -> List[StreamEvent]:
        """
        Process batch of events from stream
        
        Args:
            stream_id: Stream ID
            batch_size: Number of events to process
        
        Returns:
            List of processed events
        """
        if stream_id not in self.stream_buffers:
            return []

        size = batch_size or self.batch_size
        buffer = self.stream_buffers[stream_id]
        batch = []

        for _ in range(min(size, len(buffer))):
            event = buffer.popleft()
            batch.append(event)

        metrics = self.stream_metrics[stream_id]
        metrics.events_processed += len(batch)
        metrics.batches_processed += 1
        metrics.events_buffered = len(buffer)

        return batch

    def get_buffer_size(self, stream_id: str) -> int:
        """Get current buffer size"""
        if stream_id not in self.stream_buffers:
            return 0

        return len(self.stream_buffers[stream_id])

    # ========================================================================
    # TRANSFORMATIONS
    # ========================================================================

    def register_transform(self, transform_name: str, func: Callable):
        """
        Register transformation function
        
        Args:
            transform_name: Transformation name
            func: Callable that transforms event data
        """
        self.transform_functions[transform_name] = func

    def apply_transform(self, transform_name: str, event: StreamEvent) -> Optional[StreamEvent]:
        """
        Apply transformation to event
        
        Args:
            transform_name: Transformation name
            event: StreamEvent
        
        Returns:
            Transformed event or None if transform failed
        """
        if transform_name not in self.transform_functions:
            return None

        try:
            func = self.transform_functions[transform_name]
            transformed_data = func(event.data)

            return StreamEvent(
                event_id=event.event_id,
                timestamp=event.timestamp,
                data=transformed_data,
                source=event.source,
                event_type=event.event_type,
            )
        except Exception:
            return None

    def apply_transforms_pipeline(
        self,
        event: StreamEvent,
        transforms: List[str],
    ) -> Optional[StreamEvent]:
        """
        Apply multiple transformations in sequence
        
        Args:
            event: StreamEvent
            transforms: List of transformation names
        
        Returns:
            Final transformed event or None
        """
        current_event = event

        for transform_name in transforms:
            current_event = self.apply_transform(transform_name, current_event)
            if current_event is None:
                return None

        return current_event

    # ========================================================================
    # WINDOWING & AGGREGATION
    # ========================================================================

    def create_window(
        self,
        stream_id: str,
        window_type: WindowType,
        duration_seconds: int = None,
    ) -> StreamWindow:
        """
        Create stream window for aggregation
        
        Args:
            stream_id: Stream ID
            window_type: Type of window
            duration_seconds: Window duration (for tumbling/sliding)
        
        Returns:
            StreamWindow object
        """
        now = datetime.utcnow()
        duration = duration_seconds or self.window_duration_seconds

        window = StreamWindow(
            window_id=str(uuid.uuid4()),
            window_type=window_type,
            start_time=now,
            end_time=now + timedelta(seconds=duration),
        )

        self.stream_windows[stream_id].append(window)

        return window

    def register_aggregation(self, agg_name: str, func: Callable):
        """
        Register aggregation function
        
        Args:
            agg_name: Aggregation name
            func: Callable that aggregates event data
        """
        self.aggregate_functions[agg_name] = func

    def aggregate_window(
        self,
        window: StreamWindow,
        agg_name: str,
    ) -> Optional[Dict]:
        """
        Apply aggregation to window
        
        Args:
            window: StreamWindow
            agg_name: Aggregation name
        
        Returns:
            Aggregation result dict
        """
        if agg_name not in self.aggregate_functions:
            return None

        try:
            func = self.aggregate_functions[agg_name]
            result = func([e.data for e in window.events])

            window.aggregations[agg_name] = result

            return result
        except Exception:
            return None

    def close_window(self, stream_id: str, window: StreamWindow) -> bool:
        """
        Close window and finalize aggregations
        
        Args:
            stream_id: Stream ID
            window: StreamWindow
        
        Returns:
            Success status
        """
        window.is_closed = True

        return True

    def get_open_windows(self, stream_id: str) -> List[StreamWindow]:
        """Get all open windows for stream"""
        if stream_id not in self.stream_windows:
            return []

        return [w for w in self.stream_windows[stream_id] if not w.is_closed]

    def get_closed_windows(self, stream_id: str) -> List[StreamWindow]:
        """Get all closed windows for stream"""
        if stream_id not in self.stream_windows:
            return []

        return [w for w in self.stream_windows[stream_id] if w.is_closed]

    # ========================================================================
    # FILTERING & SELECTION
    # ========================================================================

    def filter_events(
        self,
        events: List[StreamEvent],
        predicate: Callable,
    ) -> List[StreamEvent]:
        """
        Filter events based on predicate
        
        Args:
            events: List of events
            predicate: Callable that returns True for events to keep
        
        Returns:
            Filtered event list
        """
        return [e for e in events if predicate(e.data)]

    def select_fields(
        self,
        events: List[StreamEvent],
        fields: List[str],
    ) -> List[Dict]:
        """
        Select specific fields from events
        
        Args:
            events: List of events
            fields: Field names to select
        
        Returns:
            List of dicts with selected fields
        """
        result = []

        for event in events:
            selected = {f: event.data.get(f) for f in fields}
            result.append(selected)

        return result

    def group_events(
        self,
        events: List[StreamEvent],
        key_func: Callable,
    ) -> Dict[Any, List[StreamEvent]]:
        """
        Group events by key
        
        Args:
            events: List of events
            key_func: Function to extract group key
        
        Returns:
            Dict mapping keys to event lists
        """
        groups = {}

        for event in events:
            key = key_func(event.data)
            if key not in groups:
                groups[key] = []
            groups[key].append(event)

        return groups

    # ========================================================================
    # BACKPRESSURE HANDLING
    # ========================================================================

    def check_backpressure(self, stream_id: str) -> bool:
        """
        Check if stream has backpressure
        
        Args:
            stream_id: Stream ID
        
        Returns:
            True if backpressure active
        """
        if stream_id not in self.stream_buffers:
            return False

        buffer_size = len(self.stream_buffers[stream_id])

        return buffer_size >= (self.backpressure_threshold * 0.8)

    def set_backpressure_threshold(self, stream_id: str, threshold: int) -> bool:
        """
        Set custom backpressure threshold
        
        Args:
            stream_id: Stream ID
            threshold: Event count threshold
        
        Returns:
            Success status
        """
        if stream_id not in self.streams:
            return False

        self.backpressure_threshold = threshold

        return True

    def drain_buffer(self, stream_id: str) -> int:
        """
        Drain all events from buffer
        
        Args:
            stream_id: Stream ID
        
        Returns:
            Number of events drained
        """
        if stream_id not in self.stream_buffers:
            return 0

        buffer = self.stream_buffers[stream_id]
        count = len(buffer)
        buffer.clear()

        return count

    # ========================================================================
    # REPLAY & TIME TRAVEL
    # ========================================================================

    def replay_events(
        self,
        stream_id: str,
        start_time: datetime,
        end_time: datetime = None,
    ) -> List[StreamEvent]:
        """
        Replay events within time range
        
        Args:
            stream_id: Stream ID
            start_time: Start timestamp
            end_time: End timestamp (default: now)
        
        Returns:
            List of replayed events
        """
        if end_time is None:
            end_time = datetime.utcnow()

        # Retrieve historical events (from database)
        # This is a placeholder for database query
        replayed_events = []

        return replayed_events

    # ========================================================================
    # STATISTICS & METRICS
    # ========================================================================

    def get_stream_metrics(self, stream_id: str) -> Optional[Dict]:
        """
        Get stream processing metrics
        
        Args:
            stream_id: Stream ID
        
        Returns:
            Metrics dict
        """
        if stream_id not in self.stream_metrics:
            return None

        metrics = self.stream_metrics[stream_id]
        duration = (datetime.utcnow() - metrics.start_time).total_seconds()
        throughput = (
            metrics.events_processed / duration if duration > 0 else 0
        )

        return {
            "stream_id": stream_id,
            "events_processed": metrics.events_processed,
            "events_failed": metrics.events_failed,
            "events_buffered": metrics.events_buffered,
            "batches_processed": metrics.batches_processed,
            "avg_latency_ms": metrics.avg_latency_ms,
            "throughput_events_per_sec": throughput,
            "backpressure_triggered": metrics.backpressure_triggered,
            "error_count": metrics.error_count,
            "last_event_timestamp": (
                metrics.last_event_timestamp.isoformat()
                if metrics.last_event_timestamp
                else None
            ),
        }

    def reset_metrics(self, stream_id: str) -> bool:
        """Reset stream metrics"""
        if stream_id not in self.stream_metrics:
            return False

        self.stream_metrics[stream_id] = StreamMetrics(
            stream_id=stream_id,
            start_time=datetime.utcnow(),
        )

        return True

    # ========================================================================
    # CLEANUP & MANAGEMENT
    # ========================================================================

    def delete_stream(self, stream_id: str) -> bool:
        """
        Delete stream and all associated data
        
        Args:
            stream_id: Stream ID
        
        Returns:
            Success status
        """
        if stream_id not in self.streams:
            return False

        del self.streams[stream_id]
        del self.stream_buffers[stream_id]
        del self.stream_windows[stream_id]
        del self.stream_metrics[stream_id]

        return True

    def get_all_streams(self) -> List[Dict]:
        """Get all stream configurations"""
        return list(self.streams.values())

    def get_stream_count(self) -> int:
        """Get number of active streams"""
        return len(self.streams)
