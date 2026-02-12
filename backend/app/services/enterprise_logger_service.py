"""
Enterprise-grade logging service for comprehensive system observability.
Handles structured logging, multiple sinks, log aggregation, and retention policies.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
import json
import uuid
from collections import defaultdict
import threading
import time


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __str__(self):
        return self.name


class LogSinkType(Enum):
    """Types of log sinks."""
    CONSOLE = "console"
    FILE = "file"
    MEMORY = "memory"
    REMOTE = "remote"


class LogCategory(Enum):
    """Log categories for organization."""
    SYSTEM = "system"
    AGENT = "agent"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    AUDIT = "audit"

    def __str__(self):
        return self.name


@dataclass
class LogEntry:
    """Represents a single log entry."""
    log_id: str
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    workspace_id: str
    source_component: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'level': str(self.level),
            'category': str(self.category),
        }

    def to_json(self):
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class LogFilter:
    """Log filtering criteria."""
    levels: Optional[List[LogLevel]] = None
    categories: Optional[List[LogCategory]] = None
    workspace_id: Optional[str] = None
    source_component: Optional[str] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_duration_ms: Optional[float] = None
    search_text: Optional[str] = None


@dataclass
class LogAggregation:
    """Aggregated log statistics."""
    total_count: int
    by_level: Dict[str, int]
    by_category: Dict[str, int]
    by_component: Dict[str, int]
    error_count: int
    warning_count: int
    avg_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    top_errors: List[Dict[str, Any]]


@dataclass
class LogRetentionPolicy:
    """Log retention configuration."""
    max_entries: int = 100000
    max_days: int = 90
    cleanup_interval_hours: int = 24
    error_logs_days: int = 180
    audit_logs_days: int = 365


@dataclass
class LogSinkConfig:
    """Configuration for a log sink."""
    sink_id: str
    sink_type: LogSinkType
    enabled: bool = True
    min_level: LogLevel = LogLevel.DEBUG
    categories: Optional[List[LogCategory]] = None
    batch_size: int = 100
    flush_interval_seconds: int = 5
    max_queue_size: int = 10000
    config: Dict[str, Any] = field(default_factory=dict)


class EnterpriseLoggerService:
    """
    Enterprise-grade logging service for system observability.
    
    Features:
    - Structured logging with metadata
    - Multiple sink types (console, file, memory, remote)
    - Log level and category filtering
    - Request/session tracking
    - Error context capture
    - Performance metrics logging
    - Log aggregation and statistics
    - Retention policies
    - Search and filtering
    - Real-time log streaming
    """

    def __init__(self,
                 retention_policy: Optional[LogRetentionPolicy] = None,
                 max_in_memory_logs: int = 50000):
        """Initialize logger service."""
        self.retention_policy = retention_policy or LogRetentionPolicy()
        self.max_in_memory_logs = max_in_memory_logs

        # Storage
        self.logs: Dict[str, List[LogEntry]] = defaultdict(list)  # workspace_id -> logs
        self.sinks: Dict[str, LogSinkConfig] = {}
        self.sink_queues: Dict[str, List[LogEntry]] = defaultdict(list)

        # Tracking
        self.log_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Threading
        self.lock = threading.RLock()
        self.flush_thread = None
        self.running = False

        # Callbacks
        self.log_callbacks: List[Callable] = []

    def start(self):
        """Start the logger service."""
        with self.lock:
            if self.running:
                return
            self.running = True
            self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
            self.flush_thread.start()

    def stop(self):
        """Stop the logger service."""
        with self.lock:
            self.running = False
            self._flush_all_sinks()

    def log(self,
            workspace_id: str,
            level: LogLevel,
            category: LogCategory,
            message: str,
            source_component: str,
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            request_id: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None,
            error_details: Optional[Dict[str, Any]] = None,
            tags: Optional[List[str]] = None,
            duration_ms: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None) -> LogEntry:
        """
        Log a message.

        Args:
            workspace_id: Workspace identifier
            level: Log level
            category: Log category
            message: Log message
            source_component: Source component name
            user_id: Optional user identifier
            session_id: Optional session identifier
            request_id: Optional request identifier
            context: Optional context data
            error_details: Optional error information
            tags: Optional tags
            duration_ms: Optional operation duration
            metadata: Optional metadata

        Returns:
            LogEntry: Created log entry
        """
        # Create log entry
        entry = LogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            level=level,
            category=category,
            message=message,
            workspace_id=workspace_id,
            source_component=source_component,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            context=context or {},
            error_details=error_details,
            tags=tags or [],
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        with self.lock:
            # Store in memory
            self.logs[workspace_id].append(entry)

            # Update counters
            self.log_counters[workspace_id][f"level_{level.name}"] += 1
            self.log_counters[workspace_id][f"category_{category.name}"] += 1

            # Track performance metrics
            if duration_ms is not None:
                self.performance_metrics[f"{workspace_id}_{source_component}"].append(duration_ms)

            # Enforce size limit
            if len(self.logs[workspace_id]) > self.max_in_memory_logs:
                self.logs[workspace_id] = self.logs[workspace_id][-self.max_in_memory_logs:]

            # Queue to sinks
            self._queue_to_sinks(entry)

            # Invoke callbacks
            for callback in self.log_callbacks:
                try:
                    callback(entry)
                except Exception:
                    pass

        return entry

    def debug(self, workspace_id: str, message: str, **kwargs) -> LogEntry:
        """Log debug message."""
        return self.log(workspace_id, LogLevel.DEBUG, LogCategory.SYSTEM, message, **kwargs)

    def info(self, workspace_id: str, message: str, **kwargs) -> LogEntry:
        """Log info message."""
        return self.log(workspace_id, LogLevel.INFO, LogCategory.SYSTEM, message, **kwargs)

    def warning(self, workspace_id: str, message: str, **kwargs) -> LogEntry:
        """Log warning message."""
        return self.log(workspace_id, LogLevel.WARNING, LogCategory.SYSTEM, message, **kwargs)

    def error(self, workspace_id: str, message: str, **kwargs) -> LogEntry:
        """Log error message."""
        return self.log(workspace_id, LogLevel.ERROR, LogCategory.SYSTEM, message, **kwargs)

    def critical(self, workspace_id: str, message: str, **kwargs) -> LogEntry:
        """Log critical message."""
        return self.log(workspace_id, LogLevel.CRITICAL, LogCategory.SYSTEM, message, **kwargs)

    def log_api_request(self,
                       workspace_id: str,
                       request_id: str,
                       method: str,
                       endpoint: str,
                       user_id: Optional[str] = None,
                       query_params: Optional[Dict] = None,
                       request_size: Optional[int] = None) -> LogEntry:
        """Log API request."""
        return self.log(
            workspace_id,
            LogLevel.INFO,
            LogCategory.API,
            f"{method} {endpoint}",
            "api_gateway",
            user_id=user_id,
            request_id=request_id,
            context={
                "method": method,
                "endpoint": endpoint,
                "query_params": query_params,
                "request_size": request_size,
            },
            tags=["api_request"],
        )

    def log_api_response(self,
                        workspace_id: str,
                        request_id: str,
                        status_code: int,
                        response_time_ms: float,
                        response_size: Optional[int] = None,
                        error: Optional[str] = None) -> LogEntry:
        """Log API response."""
        level = LogLevel.INFO if status_code < 400 else LogLevel.WARNING if status_code < 500 else LogLevel.ERROR
        category = LogCategory.API

        return self.log(
            workspace_id,
            level,
            category,
            f"API Response: {status_code}",
            "api_gateway",
            request_id=request_id,
            context={
                "status_code": status_code,
                "response_size": response_size,
            },
            error_details={"error": error} if error else None,
            duration_ms=response_time_ms,
            tags=["api_response"],
        )

    def log_security_event(self,
                          workspace_id: str,
                          event_type: str,
                          severity: str,
                          user_id: Optional[str] = None,
                          resource: Optional[str] = None,
                          action: Optional[str] = None,
                          result: Optional[str] = None,
                          reason: Optional[str] = None) -> LogEntry:
        """Log security-related event."""
        level_map = {
            "critical": LogLevel.CRITICAL,
            "high": LogLevel.ERROR,
            "medium": LogLevel.WARNING,
            "low": LogLevel.INFO,
        }

        return self.log(
            workspace_id,
            level_map.get(severity, LogLevel.WARNING),
            LogCategory.SECURITY,
            f"Security Event: {event_type}",
            "security_monitor",
            user_id=user_id,
            context={
                "event_type": event_type,
                "severity": severity,
                "resource": resource,
                "action": action,
                "result": result,
                "reason": reason,
            },
            tags=["security", event_type.lower()],
        )

    def log_audit_event(self,
                       workspace_id: str,
                       action: str,
                       resource_type: str,
                       resource_id: str,
                       user_id: str,
                       changes: Optional[Dict[str, Any]] = None,
                       result: str = "success") -> LogEntry:
        """Log audit event."""
        level = LogLevel.INFO if result == "success" else LogLevel.WARNING

        return self.log(
            workspace_id,
            level,
            LogCategory.AUDIT,
            f"Audit: {action} on {resource_type}",
            "audit_log",
            user_id=user_id,
            context={
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "changes": changes,
                "result": result,
            },
            tags=["audit", action.lower()],
        )

    def log_error_with_context(self,
                              workspace_id: str,
                              error: Exception,
                              source_component: str,
                              context: Optional[Dict[str, Any]] = None,
                              user_id: Optional[str] = None):
        """Log error with full context."""
        return self.log(
            workspace_id,
            LogLevel.ERROR,
            LogCategory.SYSTEM,
            f"Exception: {type(error).__name__}",
            source_component,
            user_id=user_id,
            context=context or {},
            error_details={
                "type": type(error).__name__,
                "message": str(error),
                "args": str(error.args),
            },
            tags=["exception"],
        )

    def search(self, workspace_id: str, filter: LogFilter) -> List[LogEntry]:
        """Search logs by filter criteria."""
        with self.lock:
            results = []

            for entry in self.logs[workspace_id]:
                # Level filter
                if filter.levels and entry.level not in filter.levels:
                    continue

                # Category filter
                if filter.categories and entry.category not in filter.categories:
                    continue

                # Component filter
                if filter.source_component and entry.source_component != filter.source_component:
                    continue

                # User filter
                if filter.user_id and entry.user_id != filter.user_id:
                    continue

                # Tags filter
                if filter.tags and not any(tag in entry.tags for tag in filter.tags):
                    continue

                # Time filter
                if filter.start_time and entry.timestamp < filter.start_time:
                    continue
                if filter.end_time and entry.timestamp > filter.end_time:
                    continue

                # Duration filter
                if filter.min_duration_ms and (entry.duration_ms is None or entry.duration_ms < filter.min_duration_ms):
                    continue

                # Text search
                if filter.search_text:
                    search_lower = filter.search_text.lower()
                    if search_lower not in entry.message.lower() and search_lower not in json.dumps(entry.context).lower():
                        continue

                results.append(entry)

            return results

    def get_logs_paginated(self,
                          workspace_id: str,
                          limit: int = 100,
                          offset: int = 0,
                          reverse: bool = True) -> tuple:
        """Get logs with pagination."""
        with self.lock:
            logs = self.logs[workspace_id]
            if reverse:
                logs = list(reversed(logs))

            total = len(logs)
            page = logs[offset:offset + limit]

            return page, total

    def aggregate(self, workspace_id: str, filter: Optional[LogFilter] = None) -> LogAggregation:
        """Get aggregated log statistics."""
        with self.lock:
            logs = self.search(workspace_id, filter or LogFilter())

            by_level = defaultdict(int)
            by_category = defaultdict(int)
            by_component = defaultdict(int)
            durations = []
            errors = defaultdict(int)

            for log in logs:
                by_level[log.level.name] += 1
                by_category[log.category.name] += 1
                by_component[log.source_component] += 1

                if log.duration_ms:
                    durations.append(log.duration_ms)

                if log.level in (LogLevel.ERROR, LogLevel.CRITICAL):
                    errors[log.message] += 1

            # Calculate percentiles
            sorted_durations = sorted(durations) if durations else []
            p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if len(sorted_durations) > 0 else 0
            p99 = sorted_durations[int(len(sorted_durations) * 0.99)] if len(sorted_durations) > 0 else 0
            avg = sum(durations) / len(durations) if durations else 0

            # Top errors
            top_errors = sorted(
                [{"message": msg, "count": count} for msg, count in errors.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:5]

            return LogAggregation(
                total_count=len(logs),
                by_level=dict(by_level),
                by_category=dict(by_category),
                by_component=dict(by_component),
                error_count=sum(1 for log in logs if log.level == LogLevel.ERROR),
                warning_count=sum(1 for log in logs if log.level == LogLevel.WARNING),
                avg_duration_ms=avg,
                p95_duration_ms=p95,
                p99_duration_ms=p99,
                top_errors=top_errors,
            )

    def register_sink(self, sink_config: LogSinkConfig):
        """Register a log sink."""
        with self.lock:
            self.sinks[sink_config.sink_id] = sink_config
            self.sink_queues[sink_config.sink_id] = []

    def remove_sink(self, sink_id: str):
        """Remove a log sink."""
        with self.lock:
            self._flush_sink(sink_id)
            if sink_id in self.sinks:
                del self.sinks[sink_id]
            if sink_id in self.sink_queues:
                del self.sink_queues[sink_id]

    def add_log_callback(self, callback: Callable[[LogEntry], None]):
        """Add a callback for new log entries."""
        with self.lock:
            self.log_callbacks.append(callback)

    def remove_log_callback(self, callback: Callable):
        """Remove a callback."""
        with self.lock:
            if callback in self.log_callbacks:
                self.log_callbacks.remove(callback)

    def cleanup_old_logs(self, workspace_id: str):
        """Clean up logs older than retention policy."""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(days=self.retention_policy.max_days)
            self.logs[workspace_id] = [
                log for log in self.logs[workspace_id]
                if log.timestamp > cutoff_time
            ]

    def get_session_logs(self, workspace_id: str, session_id: str) -> List[LogEntry]:
        """Get all logs for a session."""
        with self.lock:
            return [log for log in self.logs[workspace_id] if log.session_id == session_id]

    def get_request_logs(self, workspace_id: str, request_id: str) -> List[LogEntry]:
        """Get all logs for a request."""
        with self.lock:
            return [log for log in self.logs[workspace_id] if log.request_id == request_id]

    def _queue_to_sinks(self, entry: LogEntry):
        """Queue log entry to appropriate sinks."""
        for sink_id, sink in self.sinks.items():
            if not sink.enabled:
                continue

            # Check level
            if entry.level.value < sink.min_level.value:
                continue

            # Check categories
            if sink.categories and entry.category not in sink.categories:
                continue

            # Queue entry
            if len(self.sink_queues[sink_id]) < sink.max_queue_size:
                self.sink_queues[sink_id].append(entry)

            # Auto flush if batch size reached
            if len(self.sink_queues[sink_id]) >= sink.batch_size:
                self._flush_sink(sink_id)

    def _flush_sink(self, sink_id: str):
        """Flush a sink's queue."""
        if sink_id not in self.sinks:
            return

        queue = self.sink_queues[sink_id]
        sink = self.sinks[sink_id]

        if not queue:
            return

        # Implementation would depend on sink type
        # For now, just clear the queue
        queue.clear()

    def _flush_all_sinks(self):
        """Flush all sinks."""
        for sink_id in self.sinks:
            self._flush_sink(sink_id)

    def _flush_loop(self):
        """Background thread for periodic flushing."""
        while self.running:
            time.sleep(1)

            with self.lock:
                for sink_id, sink in self.sinks.items():
                    if len(self.sink_queues[sink_id]) > 0:
                        # Check if interval elapsed
                        self._flush_sink(sink_id)

    def get_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get logger service statistics."""
        with self.lock:
            return {
                "total_logs": len(self.logs[workspace_id]),
                "log_levels": dict(self.log_counters[workspace_id]),
                "active_sessions": len(self.active_sessions),
                "sinks_count": len(self.sinks),
                "pending_queue_size": sum(len(q) for q in self.sink_queues.values()),
            }
