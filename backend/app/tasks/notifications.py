"""
Notification Queue Tasks
========================

This module contains Celery tasks for asynchronous notification delivery.
Supports multi-channel notifications (email, in-app, WebSocket).

Tasks:
- create_notification_task: Create and deliver notification
- batch_notifications_task: Send notifications to multiple users
- send_digest_notification_task: Send digest notifications

Features:
- Multi-channel delivery coordination
- Rate limiting (100 notifications/minute)
- Timeout: 10 minutes
- Automatic retries
- Failed notification tracking
"""

from celery import shared_task
from celery.utils.log import get_task_logger
import logging
from typing import Optional, List, Dict, Any
from app.notifications.service import NotificationService
from app.notifications.models import NotificationType, NotificationChannel, NotificationPriority
from app.database import SessionLocal
import json

# Task logger
logger = get_task_logger(__name__)

# Regular logger
log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="100/m",
    soft_time_limit=600,
    name="app.tasks.notifications.create_notification_task"
)
def create_notification_task(
    self,
    recipient_id: int,
    notification_type: str,
    title: str,
    message: str,
    channels: Optional[List[str]] = None,
    action_url: Optional[str] = None,
    action_text: Optional[str] = None,
    priority: str = "normal"
) -> Dict[str, Any]:
    """
    Celery task to create and deliver notification asynchronously.
    
    Args:
        recipient_id: User ID to send notification to
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        channels: List of delivery channels (email, in_app, websocket)
        action_url: Optional action URL
        action_text: Optional action button text
        priority: Notification priority level
    
    Returns:
        dict: Task result with notification details
    """
    task_id = self.request.id
    db = SessionLocal()
    
    try:
        logger.info(
            f"Creating notification",
            extra={
                "task_id": task_id,
                "recipient_id": recipient_id,
                "type": notification_type,
                "channels": channels,
            }
        )
        
        # Default channels
        if channels is None:
            channels = [NotificationChannel.IN_APP.value]
        
        # Convert string channels to enum
        channel_enums = [
            NotificationChannel(ch) if isinstance(ch, str) else ch
            for ch in channels
        ]
        
        # Create notification service
        notification_service = NotificationService(db)
        
        # Create notification (this will handle delivery)
        notification = notification_service.create_notification(
            recipient_id=recipient_id,
            notification_type=NotificationType(notification_type),
            title=title,
            message=message,
            channels=channel_enums,
            action_url=action_url,
            action_text=action_text,
            priority=NotificationPriority(priority)
        )
        
        logger.info(
            f"Notification created and delivered",
            extra={
                "task_id": task_id,
                "recipient_id": recipient_id,
                "notification_id": getattr(notification, "id", "unknown"),
                "channels": channels,
            }
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "recipient_id": recipient_id,
            "notification_id": getattr(notification, "id", None),
            "channels": channels,
        }
        
    except Exception as exc:
        logger.error(
            f"Notification creation task failed: {str(exc)}",
            extra={
                "task_id": task_id,
                "recipient_id": recipient_id,
                "exception": str(exc),
            }
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Notification creation failed permanently after 3 retries",
                extra={"task_id": task_id, "recipient_id": recipient_id}
            )
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "recipient_id": recipient_id,
            }
    finally:
        db.close()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="50/m",
    soft_time_limit=900,
    name="app.tasks.notifications.batch_notifications_task"
)
def batch_notifications_task(
    self,
    recipient_ids: List[int],
    notification_type: str,
    title: str,
    message: str,
    channels: Optional[List[str]] = None,
    action_url: Optional[str] = None,
    action_text: Optional[str] = None,
    priority: str = "normal"
) -> Dict[str, Any]:
    """
    Celery task to send notifications to multiple users.
    
    Args:
        recipient_ids: List of user IDs
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        channels: List of delivery channels
        action_url: Optional action URL
        action_text: Optional action button text
        priority: Notification priority level
    
    Returns:
        dict: Summary of batch notification operation
    
    Example:
        recipient_ids = [1, 2, 3, 4, 5]
        batch_notifications_task.delay(
            recipient_ids,
            "task_assigned",
            "New Task",
            "You have been assigned a task",
            channels=["email", "websocket"]
        )
    """
    task_id = self.request.id
    db = SessionLocal()
    total = len(recipient_ids)
    successful = 0
    failed = []
    
    try:
        logger.info(
            f"Starting batch notification task",
            extra={
                "task_id": task_id,
                "notification_type": notification_type,
                "total_recipients": total,
            }
        )
        
        # Default channels
        if channels is None:
            channels = [NotificationChannel.IN_APP.value]
        
        # Convert channels
        channel_enums = [
            NotificationChannel(ch) if isinstance(ch, str) else ch
            for ch in channels
        ]
        
        notification_service = NotificationService(db)
        
        # Send to each recipient
        for i, recipient_id in enumerate(recipient_ids):
            try:
                notification = notification_service.create_notification(
                    recipient_id=recipient_id,
                    notification_type=NotificationType(notification_type),
                    title=title,
                    message=message,
                    channels=channel_enums,
                    action_url=action_url,
                    action_text=action_text,
                    priority=NotificationPriority(priority)
                )
                successful += 1
                
            except Exception as e:
                logger.error(
                    f"Failed to create notification for user {recipient_id}",
                    extra={"error": str(e)}
                )
                failed.append(recipient_id)
        
        logger.info(
            f"Batch notification task completed",
            extra={
                "task_id": task_id,
                "total": total,
                "successful": successful,
                "failed": len(failed),
            }
        )
        
        return {
            "status": "success" if len(failed) == 0 else "partial",
            "task_id": task_id,
            "total": total,
            "successful": successful,
            "failed": len(failed),
            "failed_recipients": failed,
        }
        
    except Exception as exc:
        logger.error(
            f"Batch notification task failed: {str(exc)}",
            extra={"task_id": task_id, "total": total}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Batch notification task failed permanently",
                extra={"task_id": task_id, "total": total}
            )
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "total": total,
                "successful": successful,
            }
    finally:
        db.close()


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    rate_limit="20/m",
    soft_time_limit=1800,
    name="app.tasks.notifications.send_digest_notification_task"
)
def send_digest_notification_task(
    self,
    recipient_id: int,
    digest_type: str = "daily"
) -> Dict[str, Any]:
    """
    Celery task to send digest notifications (daily, weekly, monthly).
    
    Args:
        recipient_id: User ID to send digest to
        digest_type: Type of digest (daily, weekly, monthly)
    
    Returns:
        dict: Task result
    
    Note:
        This task can be scheduled using Celery Beat.
        It collects unread notifications and sends them in a digest format.
    """
    task_id = self.request.id
    db = SessionLocal()
    
    try:
        logger.info(
            f"Generating {digest_type} digest notification",
            extra={
                "task_id": task_id,
                "recipient_id": recipient_id,
                "digest_type": digest_type,
            }
        )
        
        notification_service = NotificationService(db)
        
        # Get unread notifications for user
        notifications = notification_service.get_notifications(
            user_id=recipient_id,
            unread_only=True,
            limit=1000
        )
        
        if not notifications:
            logger.info(
                f"No unread notifications for digest",
                extra={"task_id": task_id, "recipient_id": recipient_id}
            )
            return {
                "status": "skipped",
                "message": "No unread notifications",
                "task_id": task_id,
                "recipient_id": recipient_id,
            }
        
        # Create digest title and message
        count = len(notifications)
        title = f"{digest_type.capitalize()} Digest: {count} New Notifications"
        message = f"You have {count} unread notifications."
        
        # Send digest as notification
        notification = notification_service.create_notification(
            recipient_id=recipient_id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title=title,
            message=message,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            priority=NotificationPriority.NORMAL
        )
        
        logger.info(
            f"Digest notification sent",
            extra={
                "task_id": task_id,
                "recipient_id": recipient_id,
                "notification_count": count,
            }
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "recipient_id": recipient_id,
            "notifications_in_digest": count,
            "digest_type": digest_type,
        }
        
    except Exception as exc:
        logger.error(
            f"Digest notification task failed: {str(exc)}",
            extra={"task_id": task_id, "recipient_id": recipient_id}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Digest notification task failed permanently",
                extra={"task_id": task_id, "recipient_id": recipient_id}
            )
            return {
                "status": "failed",
                "message": f"Failed after retries: {str(exc)}",
                "task_id": task_id,
                "recipient_id": recipient_id,
            }
    finally:
        db.close()
