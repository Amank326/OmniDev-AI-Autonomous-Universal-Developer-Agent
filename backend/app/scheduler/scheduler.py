"""Simple task scheduler using asyncio.

For production use, consider APScheduler, Celery Beat, or similar.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, Optional

logger = logging.getLogger(__name__)

AsyncTask = Callable[..., Coroutine[Any, Any, Any]]


class ScheduledJob:
    """Represents a scheduled recurring job."""

    def __init__(
        self,
        name: str,
        func: AsyncTask,
        interval_seconds: float,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.args = args
        self.kwargs = kwargs or {}
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.run_count: int = 0
        self._task: Optional[asyncio.Task] = None

    async def _loop(self):
        """Internal loop that runs the job periodically."""
        self.is_running = True
        try:
            while self.is_running:
                try:
                    await self.func(*self.args, **self.kwargs)
                    self.last_run = datetime.now(timezone.utc)
                    self.run_count += 1
                except Exception as e:
                    logger.error(f"Scheduled job '{self.name}' failed: {e}")
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            pass
        finally:
            self.is_running = False

    def start(self) -> None:
        """Start the scheduled job."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())
            logger.info(
                f"Started job '{self.name}' (every {self.interval_seconds}s)"
            )

    def stop(self) -> None:
        """Stop the scheduled job."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info(f"Stopped job '{self.name}'")


class TaskScheduler:
    """Manage scheduled recurring tasks.

    Usage:
        scheduler = TaskScheduler()

        async def cleanup():
            print("Running cleanup...")

        scheduler.add_job("cleanup", cleanup, interval_seconds=3600)
        scheduler.start_all()
        # ...
        scheduler.stop_all()
    """

    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}

    def add_job(
        self,
        name: str,
        func: AsyncTask,
        interval_seconds: float,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> ScheduledJob:
        """Add a recurring job."""
        if name in self._jobs:
            raise ValueError(f"Job '{name}' already exists. Remove it first.")
        job = ScheduledJob(name, func, interval_seconds, args, kwargs)
        self._jobs[name] = job
        return job

    def remove_job(self, name: str) -> None:
        """Remove and stop a job."""
        if name in self._jobs:
            self._jobs[name].stop()
            del self._jobs[name]

    def start_all(self) -> None:
        """Start all registered jobs."""
        for job in self._jobs.values():
            job.start()

    def stop_all(self) -> None:
        """Stop all running jobs."""
        for job in self._jobs.values():
            job.stop()

    def get_status(self) -> list:
        """Return status of all jobs."""
        return [
            {
                "name": job.name,
                "running": job.is_running,
                "interval": job.interval_seconds,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "run_count": job.run_count,
            }
            for job in self._jobs.values()
        ]


# Singleton scheduler
scheduler = TaskScheduler()
