"""
Structured Logging Configuration

Provides JSON logging with context, request IDs, user information, and performance metrics.

Features:
    - JSON formatted logs for easy parsing
    - Structured context logging
    - Request ID tracking
    - Performance metrics (latency, status codes)
    - User and operation context
    - Environment-aware log levels

Configuration:
    Log level can be set via LOG_LEVEL environment variable (DEBUG, INFO, WARNING, ERROR)
    Output format can be JSON or text via LOG_FORMAT environment variable

Usage:
    logger = logging.getLogger(__name__)
    logger.info("Operation completed", extra={
        "user_id": 123,
        "operation": "create_project",
        "duration_ms": 145,
        "status": "success"
    })
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Any, Dict
from pathlib import Path
import os


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Converts log records to JSON format with additional context.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                # Skip standard logging fields
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename',
                    'funcName', 'levelname', 'levelno', 'lineno',
                    'module', 'msecs', 'message', 'pathname', 'process',
                    'processName', 'relativeCreated', 'thread', 'threadName',
                    'exc_info', 'exc_text', 'stack_info', 'getMessage'
                ]:
                    log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Custom text formatter for readable logging.
    
    Provides human-readable log format with colors and context.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as readable text."""
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Base format
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        log_message = f"{timestamp} | {color}{record.levelname:8}{reset} | {record.name:30} | {record.getMessage()}"
        
        # Add extra context if present
        extra_items = []
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename',
                    'funcName', 'levelname', 'levelno', 'lineno',
                    'module', 'msecs', 'message', 'pathname', 'process',
                    'processName', 'relativeCreated', 'thread', 'threadName',
                    'exc_info', 'exc_text', 'stack_info', 'getMessage'
                ]:
                    extra_items.append(f"{key}={value}")
        
        if extra_items:
            log_message += " | " + " | ".join(extra_items)
        
        # Add exception info if present
        if record.exc_info:
            log_message += "\n" + self.formatException(record.exc_info)
        
        return log_message


def setup_logging(
    name: str = "omnidev_ai",
    level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json or text)
        log_file: Optional file path for logging
    
    Returns:
        Configured logger instance
    
    Example:
        logger = setup_logging(level="DEBUG", log_format="text")
        logger.info("Starting application")
    """
    
    # Get log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class ContextLogger:
    """
    Context-aware logger that includes request/operation context.
    
    Automatically includes context information in all log messages.
    """
    
    def __init__(self, logger: logging.Logger, context: Optional[Dict[str, Any]] = None):
        """
        Initialize context logger.
        
        Args:
            logger: Underlying logger instance
            context: Initial context dict
        """
        self.logger = logger
        self.context = context or {}
    
    def set_context(self, **kwargs) -> None:
        """Set context variables."""
        self.context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all context variables."""
        self.context.clear()
    
    def info(self, message: str, **kwargs) -> None:
        """Log info with context."""
        extra = {**self.context, **kwargs}
        self.logger.info(message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug with context."""
        extra = {**self.context, **kwargs}
        self.logger.debug(message, extra=extra)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning with context."""
        extra = {**self.context, **kwargs}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error with context."""
        extra = {**self.context, **kwargs}
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical with context."""
        extra = {**self.context, **kwargs}
        self.logger.critical(message, extra=extra)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with context."""
        extra = {**self.context, **kwargs}
        self.logger.exception(message, extra=extra)


# Global logger instance
_logger = None


def get_logger(name: str = "omnidev_ai") -> logging.Logger:
    """Get or create application logger."""
    global _logger
    if _logger is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_format = os.getenv("LOG_FORMAT", "json")
        log_file = os.getenv("LOG_FILE")
        
        _logger = setup_logging(
            name=name,
            level=log_level,
            log_format=log_format,
            log_file=log_file
        )
    
    return _logger


# Initialize on module load
def initialize_logging():
    """Initialize logging when module is imported."""
    get_logger()
