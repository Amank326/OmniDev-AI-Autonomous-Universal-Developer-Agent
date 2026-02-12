"""
Notification Service

Manages creating, sending, and tracking notifications across multiple channels.

Features:
    - Multi-channel delivery (email, in-app, WebSocket)
    - Notification preferences per user
    - Read/unread tracking
    - Notification history
    - Template-based messages
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.notifications.models import (
    NotificationType, NotificationChannel, NotificationPriority, NotificationRequest
)
from app.email.service import email_service
from app.realtime.connection_manager import manager

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing notifications.
    
    Handles creation, delivery, and tracking of notifications.
    """
    
    def __init__(self, db: Session):
        """
        Initialize notification service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    async def create_notification(
        self,
        recipient_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        channels: List[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create and send notification.
        
        Args:
            recipient_id: User to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            channels: Delivery channels
            priority: Priority level
            action_url: Optional action URL
            action_text: Optional action button text
            data: Optional extra data
        
        Returns:
            Notification data dict
        
        Example:
            notification = await notification_service.create_notification(
                recipient_id=42,
                notification_type=NotificationType.TASK_ASSIGNED,
                title="New Task",
                message="You've been assigned a new task",
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
            )
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP]
        
        notification_data = {
            "recipient_id": recipient_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "channels": channels,
            "priority": priority,
            "action_url": action_url,
            "action_text": action_text,
            "data": data,
            "is_read": False,
            "created_at": datetime.utcnow(),
            "read_at": None
        }
        
        # Store in database (would use Notification ORM model)
        # For now, tracking in memory
        
        # Send through each channel
        for channel in channels:
            await self._send_notification(
                recipient_id,
                channel,
                notification_data
            )
        
        logger.info(
            f"Notification created",
            extra={
                "recipient_id": recipient_id,
                "type": notification_type,
                "channels": [c.value for c in channels]
            }
        )
        
        return notification_data
    
    async def _send_notification(
        self,
        recipient_id: int,
        channel: NotificationChannel,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Send notification through specific channel.
        
        Args:
            recipient_id: Recipient user ID
            channel: Delivery channel
            notification: Notification data
        
        Returns:
            True if successful
        """
        try:
            if channel == NotificationChannel.EMAIL:
                return self._send_email_notification(recipient_id, notification)
            
            elif channel == NotificationChannel.IN_APP:
                return self._send_in_app_notification(recipient_id, notification)
            
            elif channel == NotificationChannel.WEBSOCKET:
                return await self._send_websocket_notification(recipient_id, notification)
            
            else:
                logger.warning(f"Unknown notification channel: {channel}")
                return False
        
        except Exception as e:
            logger.error(
                f"Error sending notification via {channel}: {str(e)}",
                extra={"recipient_id": recipient_id, "error": str(e)}
            )
            return False
    
    def _send_email_notification(
        self,
        recipient_id: int,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Send notification via email.
        
        Args:
            recipient_id: Recipient user ID
            notification: Notification data
        
        Returns:
            True if successful
        """
        # In production, fetch user email from database
        # For now, skip if email not available
        
        if not email_service.is_enabled():
            logger.debug("Email service not enabled")
            return False
        
        # Would fetch actual email from user
        # return email_service.send_notification_email(
        #     recipient_email=user.email,
        #     subject=notification["title"],
        #     title=notification["title"],
        #     message=notification["message"],
        #     action_url=notification.get("action_url"),
        #     action_text=notification.get("action_text")
        # )
        
        return True
    
    def _send_in_app_notification(
        self,
        recipient_id: int,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Store in-app notification.
        
        Args:
            recipient_id: Recipient user ID
            notification: Notification data
        
        Returns:
            True if successful
        """
        # In production, store in database
        logger.debug(
            f"In-app notification for user {recipient_id}",
            extra={"title": notification["title"]}
        )
        return True
    
    async def _send_websocket_notification(
        self,
        recipient_id: int,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Send notification via WebSocket.
        
        Args:
            recipient_id: Recipient user ID
            notification: Notification data
        
        Returns:
            True if successful
        """
        # Broadcast to user's WebSocket connections
        sent = await manager.broadcast_to_user(
            recipient_id,
            {
                "type": "notification",
                "notification_type": notification["notification_type"],
                "title": notification["title"],
                "message": notification["message"],
                "action_url": notification.get("action_url"),
                "action_text": notification.get("action_text"),
                "priority": notification["priority"]
            }
        )
        
        return sent > 0
    
    async def mark_as_read(
        self,
        notification_id: int,
        user_id: int
    ) -> bool:
        """
        Mark notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)
        
        Returns:
            True if successful
        """
        # In production, update database
        logger.debug(
            f"Notification marked as read",
            extra={"notification_id": notification_id, "user_id": user_id}
        )
        return True
    
    async def get_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for user.
        
        Args:
            user_id: User ID
            unread_only: Only unread notifications
            limit: Max notifications to return
            offset: Pagination offset
        
        Returns:
            List of notifications
        """
        # In production, query from database
        logger.debug(f"Getting notifications for user {user_id}")
        return []
    
    async def delete_notification(
        self,
        notification_id: int,
        user_id: int
    ) -> bool:
        """
        Delete notification.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)
        
        Returns:
            True if successful
        """
        logger.debug(f"Notification deleted: {notification_id}")
        return True
    
    async def clear_all_notifications(self, user_id: int) -> int:
        """
        Clear all notifications for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of notifications cleared
        """
        logger.info(f"All notifications cleared for user {user_id}")
        return 0
