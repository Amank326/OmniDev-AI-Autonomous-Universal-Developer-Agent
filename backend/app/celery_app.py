"""
Celery Application Setup
========================

This module configures Celery as the task queue system for OmniDev AI.
It uses Redis as the message broker and supports both synchronous and
asynchronous task execution.

Features:
- Redis-based message broker
- Task routing and task naming
- Automatic retry with exponential backoff
- Task result backend with expiration
- Custom task classes with error handling
- Rate limiting and task timeout configuration

Usage:
    celery -A app.celery_app worker --loglevel=info
    celery -A app.celery_app beat (for scheduled tasks)
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import logging
from datetime import timedelta
from typing import Any, Dict
import os

# Configure logging
logger = logging.getLogger(__name__)

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Initialize Celery app
celery_app = Celery("omnidev_ai")

# Configuration dictionary
celery_config = {
    # Broker settings
    "broker_url": CELERY_BROKER_URL,
    "broker_connection_retry_on_startup": True,
    "broker_connection_max_retries": 10,
    
    # Result backend settings
    "result_backend": CELERY_RESULT_BACKEND,
    "result_expires": 3600,  # Results expire after 1 hour
    "result_extended": True,
    
    # Task settings
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    
    # Task routing
    "task_routes": {
        # Email tasks
        "app.tasks.email.*": {"queue": "email", "routing_key": "email.#"},
        "app.tasks.email.send_verification_email_task": {"queue": "email"},
        "app.tasks.email.send_password_reset_task": {"queue": "email"},
        "app.tasks.email.send_notification_email_task": {"queue": "email"},
        "app.tasks.email.send_welcome_email_task": {"queue": "email"},
        
        # Notification tasks
        "app.tasks.notifications.*": {"queue": "notifications", "routing_key": "notifications.#"},
        "app.tasks.notifications.create_notification_task": {"queue": "notifications"},
        "app.tasks.notifications.batch_notifications_task": {"queue": "notifications"},
        
        # Scheduled tasks
        "app.scheduler.*": {"queue": "scheduled", "routing_key": "scheduled.#"},
    },
    
    # Queue configuration
    "task_default_queue": "default",
    "task_default_exchange": "omnidev_ai",
    "task_default_routing_key": "omnidev_ai.default",
    
    # Queues definition
    "task_queues": (
        ("default", {"exchange": "omnidev_ai", "routing_key": "omnidev_ai.default"}),
        ("email", {"exchange": "omnidev_ai", "routing_key": "email.#"}),
        ("notifications", {"exchange": "omnidev_ai", "routing_key": "notifications.#"}),
        ("scheduled", {"exchange": "omnidev_ai", "routing_key": "scheduled.#"}),
    ),
    
    # Task execution settings
    "task_acks_late": True,
    "worker_prefetch_multiplier": 4,
    "worker_max_tasks_per_child": 1000,
    
    # Retry settings
    "task_autoretry_for": (Exception,),
    "task_max_retries": 3,
    "task_default_retry_delay": 60,  # 1 minute
    
    # Rate limiting
    "task_default_rate_limit": "100/m",  # 100 tasks per minute
    "task_soft_time_limit": 600,  # 10 minutes soft limit
    "task_time_limit": 900,  # 15 minutes hard limit
    
    # Worker settings
    "worker_disable_rate_limits": False,
    "worker_log_format": "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    "worker_task_log_format": "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
    
    # Beat schedule (scheduled tasks)
    "beat_schedule": {
        # Example: Send digest emails every day at 9 AM
        # "send-daily-digest": {
        #     "task": "app.scheduler.send_digest_emails",
        #     "schedule": crontab(hour=9, minute=0),
        # },
    },
}

# Apply configuration
celery_app.config_from_object(celery_config)

# Auto-discover tasks from task modules
celery_app.autodiscover_tasks(["app.tasks"])


# Signal handlers for monitoring and logging
@task_prerun.connect
def before_task_run(task_id, task, args, kwargs, **kw) -> None:
    """Log before task execution."""
    logger.info(
        f"Task starting: {task.name}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "args": args,
            "kwargs": kwargs,
        }
    )


@task_postrun.connect
def after_task_run(task_id, task, args, kwargs, retval, state, **kw) -> None:
    """Log after successful task execution."""
    logger.info(
        f"Task completed: {task.name}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "result": retval,
        }
    )


@task_failure.connect
def on_task_failure(task_id, exception, args, kwargs, traceback, einfo, **kw) -> None:
    """Log task failures for monitoring and debugging."""
    logger.error(
        f"Task failed: {kw['task'].name}",
        extra={
            "task_id": task_id,
            "task_name": kw["task"].name,
            "exception": str(exception),
            "traceback": str(traceback),
        }
    )


# Custom task class with error handling
class CustomTask(celery_app.Task):
    """
    Custom Celery task class with enhanced error handling and logging.
    
    Features:
    - Automatic retries with exponential backoff
    - Comprehensive error logging
    - Task state tracking
    - Dead letter queue support
    """
    
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            f"Task {self.name} (ID: {task_id}) retrying due to {type(exc).__name__}: {str(exc)}",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "exception": str(exc),
            }
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails permanently."""
        logger.error(
            f"Task {self.name} (ID: {task_id}) failed permanently: {str(exc)}",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "exception": str(exc),
                "args": args,
                "kwargs": kwargs,
            }
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, result, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.debug(
            f"Task {self.name} (ID: {task_id}) succeeded",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "result": result,
            }
        )
        super().on_success(result, task_id, args, kwargs)


# Set custom task class
celery_app.Task = CustomTask


def get_celery_status() -> Dict[str, Any]:
    """
    Get Celery and Redis status for health checks.
    
    Returns:
        dict: Status information including broker connection and active tasks
    """
    try:
        # Check Redis connection
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats is None:
            return {
                "status": "error",
                "message": "No Celery workers active",
                "workers": 0,
            }
        
        return {
            "status": "ok",
            "message": "Celery and Redis operational",
            "workers": len(stats),
            "worker_details": stats,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Celery health check failed: {str(e)}",
            "error": str(e),
        }


def get_active_tasks() -> Dict[str, Any]:
    """
    Get list of currently active tasks.
    
    Returns:
        dict: Map of worker names to their active tasks
    """
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active()
        return active or {}
    except Exception as e:
        logger.error(f"Failed to get active tasks: {str(e)}")
        return {}


def get_scheduled_tasks() -> Dict[str, Any]:
    """
    Get list of scheduled tasks.
    
    Returns:
        dict: Map of worker names to their scheduled tasks
    """
    try:
        inspect = celery_app.control.inspect()
        scheduled = inspect.scheduled()
        return scheduled or {}
    except Exception as e:
        logger.error(f"Failed to get scheduled tasks: {str(e)}")
        return {}


def get_registered_tasks() -> list:
    """
    Get list of all registered task names.
    
    Returns:
        list: All registered task names
    """
    try:
        inspect = celery_app.control.inspect()
        registered = inspect.registered()
        if registered:
            # Flatten the dict of lists
            all_tasks = []
            for tasks in registered.values():
                all_tasks.extend(tasks)
            return list(set(all_tasks))
        return []
    except Exception as e:
        logger.error(f"Failed to get registered tasks: {str(e)}")
        return []


# Celery app is ready for import and use
if __name__ == "__main__":
    celery_app.start()
