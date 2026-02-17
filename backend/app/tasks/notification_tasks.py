"""Celery tasks for notification delivery."""

import logging
from typing import Any, Dict, List

from app.utils.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.notification_tasks.send_notification_task",
    max_retries=3,
    default_retry_delay=30,
)
def send_notification_task(
    self,
    user_id: int,
    title: str,
    message: str,
    channel: str = "email",
) -> Dict[str, Any]:
    """Send a notification via the specified channel.

    Args:
        user_id: Target user ID.
        title: Notification title.
        message: Notification body.
        channel: Delivery channel ('email', 'websocket', 'sms', 'push').

    Returns:
        dict with delivery status.
    """
    logger.info(f"Sending {channel} notification to user {user_id}: {title}")

    try:
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            if channel == "email":
                from app.notifications.handlers import email_handler

                # Would need user email; placeholder
                result = loop.run_until_complete(
                    email_handler.send(f"user_{user_id}@example.com", title, message)
                )
            elif channel == "websocket":
                from app.notifications.handlers import websocket_handler

                result = loop.run_until_complete(
                    websocket_handler.send(user_id, title, message)
                )
            else:
                logger.warning(f"Unknown channel '{channel}', skipping")
                result = False
        finally:
            loop.close()

        return {"status": "sent" if result else "skipped", "channel": channel}

    except Exception as exc:
        logger.error(f"Notification failed: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": "failed", "channel": channel, "error": str(exc)}


@celery_app.task(
    name="app.tasks.notification_tasks.send_bulk_notifications",
)
def send_bulk_notifications(
    user_ids: List[int],
    title: str,
    message: str,
    channel: str = "email",
) -> Dict[str, Any]:
    """Send a notification to multiple users."""
    results = []
    for uid in user_ids:
        result = send_notification_task.delay(uid, title, message, channel)
        results.append({"user_id": uid, "task_id": str(result.id)})

    return {
        "status": "dispatched",
        "count": len(results),
        "tasks": results,
    }
