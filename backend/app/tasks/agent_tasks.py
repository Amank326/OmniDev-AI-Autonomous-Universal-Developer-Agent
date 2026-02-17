"""Celery tasks for agent execution."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.utils.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.agent_tasks.run_agent_task",
    max_retries=3,
    default_retry_delay=60,
)
def run_agent_task(
    self,
    agent_id: int,
    task_id: int,
    agent_type: str,
    input_data: Dict[str, Any],
    user_id: int,
) -> Dict[str, Any]:
    """Execute an agent task asynchronously via Celery.

    Args:
        agent_id: The agent database ID.
        task_id: The task database ID.
        agent_type: Type of agent to run (e.g., 'code_generator').
        input_data: Input parameters for the agent.
        user_id: The ID of the user who submitted the task.

    Returns:
        dict with status, result, and timing info.
    """
    start = datetime.now(timezone.utc)
    logger.info(
        f"Running agent task {task_id} (agent={agent_id}, type={agent_type})"
    )

    try:
        # Import here to avoid circular imports
        from app.agents.executor import agent_executor

        # Execute synchronously inside the Celery worker
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                agent_executor.execute_agent(agent_type, input_data)
            )
        finally:
            loop.close()

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.info(f"Task {task_id} completed in {elapsed:.2f}s")

        return {
            "status": "completed",
            "task_id": task_id,
            "result": result,
            "elapsed_seconds": elapsed,
        }

    except Exception as exc:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.error(f"Task {task_id} failed after {elapsed:.2f}s: {exc}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(exc),
                "elapsed_seconds": elapsed,
            }


@celery_app.task(
    name="app.tasks.agent_tasks.cleanup_stale_tasks",
)
def cleanup_stale_tasks(max_age_hours: int = 24) -> Dict[str, Any]:
    """Clean up stale / orphaned tasks older than max_age_hours.

    This is meant to be called periodically via Celery Beat.
    """
    logger.info(f"Cleaning up stale tasks older than {max_age_hours}h")

    # Placeholder: implement actual DB cleanup
    return {
        "status": "completed",
        "cleaned": 0,
        "max_age_hours": max_age_hours,
    }
