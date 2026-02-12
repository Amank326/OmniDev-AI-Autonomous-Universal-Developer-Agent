"""
Centralized Logging Service
Multi-backend logging with aggregation and search capabilities
Phase 42: Observability & Monitoring Infrastructure
"""

import logging
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from threading import RLock, Thread
from pathlib import Path
import queue
import traceback

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogBackend(Enum):
    """Logging backends"""
    MEMORY = "memory"
    FILE = "file"
    ELASTICSEARCH = "elasticsearch"
    LOKI = "loki"
    CLOUDWATCH = "cloudwatch"


@dataclass
class LogEntry:
    """Individual log entry"""
    timestamp: datetime
    level: LogLevel
    logger_name: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    service: Optional[str] = None
    environment: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'logger': self.logger_name,
            'message': self.message,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'service': self.service,
            'environment': self.environment,
            'metadata': self.metadata,
        }
        
        if self.exception:
            data['exception'] = self.exception
        
        return data
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())


@dataclass
class LogQuery:
    """Query for searching logs"""
    level: Optional[LogLevel] = None
    logger_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    message_contains: Optional[str] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    limit: int = 1000


class MemoryBackend:
    """In-memory logging backend"""
    
    def __init__(self, max_entries: int = 10000):
        self.entries: List[LogEntry] = []
        self.max_entries = max_entries
        self.lock = RLock()
    
    def write(self, entry: LogEntry) -> None:
        """Write log entry"""
        with self.lock:
            self.entries.append(entry)
            
            # Trim if exceeds max
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[-self.max_entries:]
    
    def query(self, q: LogQuery) -> List[LogEntry]:
        """Query logs"""
        with self.lock:
            results = self.entries
            
            # Filter by timestamp
            if q.start_time:
                results = [e for e in results if e.timestamp >= q.start_time]
            if q.end_time:
                results = [e for e in results if e.timestamp <= q.end_time]
            
            # Filter by level
            if q.level:
                results = [e for e in results if e.level == q.level]
            
            # Filter by logger name
            if q.logger_name:
                results = [e for e in results if q.logger_name in e.logger_name]
            
            # Filter by message
            if q.message_contains:
                results = [e for e in results if q.message_contains.lower() in e.message.lower()]
            
            # Filter by trace ID
            if q.trace_id:
                results = [e for e in results if e.trace_id == q.trace_id]
            
            # Filter by metadata
            for key, value in q.metadata_filters.items():
                results = [e for e in results if e.metadata.get(key) == value]
            
            return results[-q.limit:]


class FileBackend:
    """File-based logging backend"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.lock = RLock()
        self._rotate_log()
    
    def write(self, entry: LogEntry) -> None:
        """Write log entry to file"""
        try:
            log_file = self.log_dir / f"{entry.level.value.lower()}.log"
            
            with self.lock:
                with open(log_file, 'a') as f:
                    f.write(entry.to_json() + '\n')
            
            # Check for rotation
            if log_file.stat().st_size > 100 * 1024 * 1024:  # 100MB
                self._rotate_log()
        
        except Exception as e:
            logger.error(f"File backend write error: {e}")
    
    def query(self, q: LogQuery) -> List[LogEntry]:
        """Query logs from files"""
        results = []
        
        try:
            log_levels = [q.level.value.lower()] if q.level else ['debug', 'info', 'warning', 'error', 'critical']
            
            for level in log_levels:
                log_file = self.log_dir / f"{level}.log"
                
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                entry = LogEntry(
                                    timestamp=datetime.fromisoformat(data['timestamp']),
                                    level=LogLevel[data['level']],
                                    logger_name=data['logger'],
                                    message=data['message'],
                                    trace_id=data.get('trace_id'),
                                    span_id=data.get('span_id'),
                                    service=data.get('service'),
                                    environment=data.get('environment'),
                                    metadata=data.get('metadata', {}),
                                    exception=data.get('exception')
                                )
                                
                                # Apply filters
                                if self._matches_query(entry, q):
                                    results.append(entry)
                            
                            except json.JSONDecodeError:
                                pass
        
        except Exception as e:
            logger.error(f"File backend query error: {e}")
        
        return results[-q.limit:]
    
    @staticmethod
    def _matches_query(entry: LogEntry, q: LogQuery) -> bool:
        """Check if entry matches query"""
        if q.start_time and entry.timestamp < q.start_time:
            return False
        if q.end_time and entry.timestamp > q.end_time:
            return False
        if q.logger_name and q.logger_name not in entry.logger_name:
            return False
        if q.message_contains and q.message_contains.lower() not in entry.message.lower():
            return False
        if q.trace_id and entry.trace_id != q.trace_id:
            return False
        for key, value in q.metadata_filters.items():
            if entry.metadata.get(key) != value:
                return False
        return True
    
    def _rotate_log(self) -> None:
        """Rotate log files"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            for level in ['debug', 'info', 'warning', 'error', 'critical']:
                old_file = self.log_dir / f"{level}.log"
                if old_file.exists():
                    new_file = self.log_dir / f"{level}_{timestamp}.log"
                    old_file.rename(new_file)
        
        except Exception as e:
            logger.error(f"Log rotation error: {e}")


class ElasticsearchBackend:
    """Elasticsearch logging backend"""
    
    def __init__(self, hosts: List[str] = None, index_prefix: str = "logs"):
        self.hosts = hosts or ["localhost:9200"]
        self.index_prefix = index_prefix
        self.buffer: List[LogEntry] = []
        self.buffer_size = 100
        self.lock = RLock()
    
    def write(self, entry: LogEntry) -> None:
        """Write log entry (to buffer)"""
        with self.lock:
            self.buffer.append(entry)
            
            if len(self.buffer) >= self.buffer_size:
                self._flush()
    
    def query(self, q: LogQuery) -> List[LogEntry]:
        """Query logs from Elasticsearch"""
        # This would implement Elasticsearch query
        # For now, return empty list
        logger.info(f"Elasticsearch query with {q.limit} limit")
        return []
    
    def _flush(self) -> None:
        """Flush buffer to Elasticsearch"""
        try:
            # This would implement actual Elasticsearch bulk insert
            logger.debug(f"Flushing {len(self.buffer)} log entries to Elasticsearch")
            self.buffer = []
        
        except Exception as e:
            logger.error(f"Elasticsearch flush error: {e}")


class LokiBackend:
    """Loki logging backend"""
    
    def __init__(self, url: str = "http://localhost:3100"):
        self.url = url
        self.buffer: List[LogEntry] = []
        self.buffer_size = 100
        self.lock = RLock()
    
    def write(self, entry: LogEntry) -> None:
        """Write log entry (to buffer)"""
        with self.lock:
            self.buffer.append(entry)
            
            if len(self.buffer) >= self.buffer_size:
                self._flush()
    
    def query(self, q: LogQuery) -> List[LogEntry]:
        """Query logs from Loki"""
        logger.info(f"Loki query with {q.limit} limit")
        return []
    
    def _flush(self) -> None:
        """Flush buffer to Loki"""
        try:
            # This would implement actual Loki API call
            logger.debug(f"Flushing {len(self.buffer)} log entries to Loki")
            self.buffer = []
        
        except Exception as e:
            logger.error(f"Loki flush error: {e}")


class LoggingService:
    """Centralized logging service with multiple backends"""
    
    def __init__(self, service_name: str = "omnidev", 
                 environment: str = "development",
                 backends: List[LogBackend] = None):
        self.service_name = service_name
        self.environment = environment
        self.backends: Dict[LogBackend, Any] = {}
        self.queue = queue.Queue()
        self.lock = RLock()
        self.callbacks: List[Callable] = []
        
        # Default to memory backend
        if not backends:
            backends = [LogBackend.MEMORY]
        
        # Initialize backends
        for backend_type in backends:
            self._init_backend(backend_type)
        
        # Start background writer
        self._start_writer()
    
    def _init_backend(self, backend_type: LogBackend) -> None:
        """Initialize a logging backend"""
        if backend_type == LogBackend.MEMORY:
            self.backends[backend_type] = MemoryBackend()
        elif backend_type == LogBackend.FILE:
            self.backends[backend_type] = FileBackend()
        elif backend_type == LogBackend.ELASTICSEARCH:
            self.backends[backend_type] = ElasticsearchBackend()
        elif backend_type == LogBackend.LOKI:
            self.backends[backend_type] = LokiBackend()
        
        logger.info(f"Initialized {backend_type.value} backend")
    
    def log(self, level: LogLevel, message: str,
            logger_name: str = "app",
            trace_id: Optional[str] = None,
            span_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            exception: Optional[Exception] = None) -> None:
        """Log a message"""
        exc_str = None
        if exception:
            exc_str = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            logger_name=logger_name,
            message=message,
            trace_id=trace_id,
            span_id=span_id,
            service=self.service_name,
            environment=self.environment,
            metadata=metadata or {},
            exception=exc_str
        )
        
        self.queue.put(entry)
        self._trigger_callbacks(entry)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, **kwargs)
    
    def search(self, **query_params) -> List[LogEntry]:
        """Search logs across backends"""
        q = LogQuery(**query_params)
        results = []
        
        # Query all backends
        for backend in self.backends.values():
            try:
                results.extend(backend.query(q))
            except Exception as e:
                logger.error(f"Backend query error: {e}")
        
        # Deduplicate and sort by timestamp
        seen = set()
        unique = []
        for entry in results:
            key = (entry.timestamp.isoformat(), entry.message)
            if key not in seen:
                seen.add(key)
                unique.append(entry)
        
        return sorted(unique, key=lambda e: e.timestamp, reverse=True)[:q.limit]
    
    def get_logs_by_trace(self, trace_id: str) -> List[LogEntry]:
        """Get all logs for a trace"""
        return self.search(trace_id=trace_id, limit=10000)
    
    def get_logs_by_level(self, level: LogLevel, hours: int = 1) -> List[LogEntry]:
        """Get logs by level"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return self.search(level=level, start_time=start_time)
    
    def register_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """Register callback for log entries"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callbacks(self, entry: LogEntry) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(entry)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _start_writer(self) -> None:
        """Start background writer thread"""
        writer_thread = Thread(target=self._writer_loop, daemon=True)
        writer_thread.start()
    
    def _writer_loop(self) -> None:
        """Background loop for writing logs"""
        while True:
            try:
                entry = self.queue.get(timeout=5)
                
                # Write to all backends
                for backend in self.backends.values():
                    try:
                        backend.write(entry)
                    except Exception as e:
                        logger.error(f"Backend write error: {e}")
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Writer error: {e}")
    
    def flush(self) -> None:
        """Flush all backends"""
        for backend in self.backends.values():
            if hasattr(backend, '_flush'):
                try:
                    backend._flush()
                except Exception as e:
                    logger.error(f"Flush error: {e}")


# Global logging service
_logging_service: Optional[LoggingService] = None


def get_logging_service(service_name: str = "omnidev",
                       environment: str = "development",
                       backends: List[LogBackend] = None) -> LoggingService:
    """Get or create logging service"""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService(service_name, environment, backends)
    return _logging_service


def setup_logging(service_name: str = "omnidev",
                 environment: str = "development",
                 backends: List[LogBackend] = None) -> LoggingService:
    """Setup centralized logging"""
    return get_logging_service(service_name, environment, backends)
