"""
APScheduler Configuration
=========================

Configuration and setup for scheduled tasks using APScheduler.

This module provides:
- Scheduler initialization with database backend
- Periodic task definitions
- Task scheduling utilities
- Timezone support
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
# from app.celery_app import send_digest_notification_task

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler(
    jobstores={
        'default': MemoryJobStore()
    },
    executors={
        'default': ThreadPoolExecutor(max_workers=3),
        'processpool': ProcessPoolExecutor(max_workers=1)
    },
    job_defaults={
        'coalesce': False,
        'max_instances': 1
    },
    timezone='UTC'
)


def schedule_daily_digest(user_id: int, hour: int = 9, minute: int = 0) -> str:
    """
    Schedule a daily digest notification for a user.
    
    Args:
        user_id: User ID
        hour: Hour of day (0-23) in UTC
        minute: Minute of hour (0-59)
    
    Returns:
        Job ID
    """
    try:
        job = scheduler.add_job(
            send_digest_notification_task.delay,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=(user_id, 'daily'),
            id=f"daily_digest_{user_id}",
            name=f"Daily digest for user {user_id}",
            replace_existing=True,
        )
        
        logger.info(f"Scheduled daily digest for user {user_id} at {hour}:{minute:02d} UTC")
        return job.id
        
    except Exception as e:
        logger.error(f"Failed to schedule daily digest: {str(e)}")
        raise


def schedule_weekly_digest(user_id: int, day_of_week: int = 0, hour: int = 9) -> str:
    """
    Schedule a weekly digest notification for a user.
    
    Args:
        user_id: User ID
        day_of_week: Day of week (0=Monday, 6=Sunday)
        hour: Hour of day (0-23) in UTC
    
    Returns:
        Job ID
    """
    try:
        job = scheduler.add_job(
            send_digest_notification_task.delay,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour),
            args=(user_id, 'weekly'),
            id=f"weekly_digest_{user_id}",
            name=f"Weekly digest for user {user_id}",
            replace_existing=True,
        )
        
        logger.info(f"Scheduled weekly digest for user {user_id} on day {day_of_week} at {hour}:00 UTC")
        return job.id
        
    except Exception as e:
        logger.error(f"Failed to schedule weekly digest: {str(e)}")
        raise


def schedule_monthly_digest(user_id: int, day_of_month: int = 1, hour: int = 9) -> str:
    """
    Schedule a monthly digest notification for a user.
    
    Args:
        user_id: User ID
        day_of_month: Day of month (1-31)
        hour: Hour of day (0-23) in UTC
    
    Returns:
        Job ID
    """
    try:
        job = scheduler.add_job(
            send_digest_notification_task.delay,
            trigger=CronTrigger(day=day_of_month, hour=hour),
            args=(user_id, 'monthly'),
            id=f"monthly_digest_{user_id}",
            name=f"Monthly digest for user {user_id}",
            replace_existing=True,
        )
        
        logger.info(f"Scheduled monthly digest for user {user_id} on day {day_of_month} at {hour}:00 UTC")
        return job.id
        
    except Exception as e:
        logger.error(f"Failed to schedule monthly digest: {str(e)}")
        raise


def unschedule_digest(user_id: int, digest_type: str = "daily") -> bool:
    """
    Remove a scheduled digest for a user.
    
    Args:
        user_id: User ID
        digest_type: Type of digest (daily, weekly, monthly)
    
    Returns:
        bool: True if removed, False if not found
    """
    try:
        job_id = f"{digest_type}_digest_{user_id}"
        scheduler.remove_job(job_id)
        logger.info(f"Unscheduled {digest_type} digest for user {user_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to unschedule digest: {str(e)}")
        return False


def schedule_cleanup_task(func, hours: int = 24) -> str:
    """
    Schedule a cleanup task to run periodically.
    
    Args:
        func: Function to schedule
        hours: How often to run (in hours)
    
    Returns:
        Job ID
    """
    try:
        job = scheduler.add_job(
            func,
            trigger='interval',
            hours=hours,
            id=f"cleanup_{func.__name__}",
            name=f"Cleanup: {func.__name__}",
            replace_existing=True,
        )
        
        logger.info(f"Scheduled cleanup task {func.__name__} every {hours} hours")
        return job.id
        
    except Exception as e:
        logger.error(f"Failed to schedule cleanup task: {str(e)}")
        raise


def get_scheduled_jobs() -> list:
    """
    Get all currently scheduled jobs.
    
    Returns:
        List of scheduled jobs
    """
    try:
        jobs = scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "func": str(job.func),
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Failed to get scheduled jobs: {str(e)}")
        return []


def start_scheduler():
    """Start the APScheduler instance."""
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")


def stop_scheduler():
    """Stop the APScheduler instance."""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("APScheduler stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")


def pause_scheduler():
    """Pause the APScheduler instance."""
    try:
        scheduler.pause()
        logger.info("APScheduler paused")
    except Exception as e:
        logger.error(f"Failed to pause scheduler: {str(e)}")


def resume_scheduler():
    """Resume the APScheduler instance."""
    try:
        scheduler.resume()
        logger.info("APScheduler resumed")
    except Exception as e:
        logger.error(f"Failed to resume scheduler: {str(e)}")
