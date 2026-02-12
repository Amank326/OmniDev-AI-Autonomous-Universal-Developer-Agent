"""
Notification Service - Multi-channel notification delivery management
Phase 27: Advanced Notifications & Real-time Alerts System
"""

import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationType(Enum):
    """Types of notifications"""
    ALERT = "alert"
    MENTION = "mention"
    UPDATE = "update"
    SYSTEM = "system"
    REMINDER = "reminder"
    COLLABORATION = "collaboration"


class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"


@dataclass
class NotificationContent:
    """Notification message content"""
    title: str
    body: str
    action_url: Optional[str] = None
    icon_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Notification:
    """Notification instance"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    notification_type: NotificationType = NotificationType.SYSTEM
    content: NotificationContent = field(default_factory=lambda: NotificationContent("", ""))
    channels: List[NotificationChannel] = field(default_factory=list)
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_channels: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationTemplate:
    """Reusable notification template"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    notification_type: NotificationType = NotificationType.SYSTEM
    title_template: str = ""
    body_template: str = ""
    default_channels: List[NotificationChannel] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class NotificationService:
    """Service for managing notification delivery across multiple channels"""

    def __init__(self):
        self.notifications: Dict[str, Notification] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.notification_history: Dict[str, List[Notification]] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        """Initialize default notification templates"""
        templates = [
            NotificationTemplate(
                name="alert_warning",
                notification_type=NotificationType.ALERT,
                title_template="Alert: {alert_name}",
                body_template="{alert_description}",
                default_channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
            ),
            NotificationTemplate(
                name="mention_notification",
                notification_type=NotificationType.MENTION,
                title_template="{user_name} mentioned you",
                body_template="in {context}",
                default_channels=[NotificationChannel.IN_APP]
            ),
            NotificationTemplate(
                name="system_update",
                notification_type=NotificationType.SYSTEM,
                title_template="System Update",
                body_template="{update_message}",
                default_channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
            ),
            NotificationTemplate(
                name="collaboration_update",
                notification_type=NotificationType.COLLABORATION,
                title_template="{action} in {workspace}",
                body_template="{details}",
                default_channels=[NotificationChannel.IN_APP]
            ),
            NotificationTemplate(
                name="reminder",
                notification_type=NotificationType.REMINDER,
                title_template="Reminder: {reminder_title}",
                body_template="{reminder_description}",
                default_channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH]
            ),
        ]
        for template in templates:
            self.templates[template.id] = template

    def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        content: NotificationContent,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            content=content,
            channels=channels or [NotificationChannel.IN_APP],
            metadata=metadata or {}
        )
        self.notifications[notification.id] = notification

        # Add to user history
        if user_id not in self.notification_history:
            self.notification_history[user_id] = []
        self.notification_history[user_id].append(notification)

        return notification

    def send_notification(self, notification_id: str) -> Dict[str, bool]:
        """Send notification across configured channels"""
        notification = self.notifications.get(notification_id)
        if not notification:
            return {}

        results = {}
        for channel in notification.channels:
            try:
                success = self._send_via_channel(notification, channel)
                results[channel.value] = success
                if not success:
                    notification.failed_channels[channel.value] = "Channel send failed"
            except Exception as e:
                results[channel.value] = False
                notification.failed_channels[channel.value] = str(e)

        notification.sent_at = datetime.utcnow()
        notification.status = NotificationStatus.SENT if any(results.values()) else NotificationStatus.FAILED

        return results

    def _send_via_channel(self, notification: Notification, channel: NotificationChannel) -> bool:
        """Send notification via specific channel"""
        channel_handlers = {
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.SMS: self._send_sms,
            NotificationChannel.PUSH: self._send_push,
            NotificationChannel.IN_APP: self._store_in_app,
        }
        handler = channel_handlers.get(channel)
        return handler(notification) if handler else False

    def _send_email(self, notification: Notification) -> bool:
        """Send email notification"""
        # Email sending implementation
        return True

    def _send_sms(self, notification: Notification) -> bool:
        """Send SMS notification"""
        # SMS sending implementation
        return True

    def _send_push(self, notification: Notification) -> bool:
        """Send push notification"""
        # Push notification implementation
        return True

    def _store_in_app(self, notification: Notification) -> bool:
        """Store in-app notification"""
        # Already stored in creation
        return True

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        notification = self.notifications.get(notification_id)
        if notification:
            notification.read_at = datetime.utcnow()
            notification.status = NotificationStatus.READ
            return True
        return False

    def mark_as_delivered(self, notification_id: str) -> bool:
        """Mark notification as delivered"""
        notification = self.notifications.get(notification_id)
        if notification:
            notification.status = NotificationStatus.DELIVERED
            return True
        return False

    def get_user_notifications(
        self,
        user_id: str,
        notification_type: Optional[NotificationType] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get user notifications with filtering"""
        notifications = self.notification_history.get(user_id, [])

        # Filter by type
        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]

        # Filter unread
        if unread_only:
            notifications = [n for n in notifications if n.status != NotificationStatus.READ]

        # Sort by creation time (newest first) and limit
        return sorted(notifications, key=lambda n: n.created_at, reverse=True)[:limit]

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get specific notification"""
        return self.notifications.get(notification_id)

    def delete_notification(self, notification_id: str) -> bool:
        """Delete notification"""
        if notification_id in self.notifications:
            del self.notifications[notification_id]
            return True
        return False

    def search_notifications(
        self,
        user_id: str,
        query: str,
        notification_type: Optional[NotificationType] = None
    ) -> List[Notification]:
        """Search notifications by content"""
        notifications = self.notification_history.get(user_id, [])

        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]

        # Search in title and body
        query_lower = query.lower()
        return [
            n for n in notifications
            if query_lower in n.content.title.lower() or query_lower in n.content.body.lower()
        ]

    def retry_failed_notification(self, notification_id: str) -> bool:
        """Retry sending failed notification"""
        notification = self.notifications.get(notification_id)
        if not notification or notification.retry_count >= notification.max_retries:
            return False

        notification.retry_count += 1
        notification.failed_channels.clear()
        self.send_notification(notification_id)
        return True

    def get_notification_stats(self, user_id: str) -> Dict[str, int]:
        """Get notification statistics for user"""
        notifications = self.notification_history.get(user_id, [])

        stats = {
            "total": len(notifications),
            "unread": len([n for n in notifications if n.status != NotificationStatus.READ]),
            "sent": len([n for n in notifications if n.status == NotificationStatus.SENT]),
            "failed": len([n for n in notifications if n.status == NotificationStatus.FAILED]),
        }

        # Count by type
        for notif_type in NotificationType:
            stats[f"type_{notif_type.value}"] = len([
                n for n in notifications if n.notification_type == notif_type
            ])

        return stats

    def bulk_mark_read(self, user_id: str, notification_ids: List[str]) -> int:
        """Mark multiple notifications as read"""
        count = 0
        for notif_id in notification_ids:
            if self.mark_as_read(notif_id):
                count += 1
        return count

    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """Get notification template"""
        return self.templates.get(template_id)

    def create_custom_template(
        self,
        name: str,
        notification_type: NotificationType,
        title_template: str,
        body_template: str,
        default_channels: List[NotificationChannel]
    ) -> NotificationTemplate:
        """Create custom notification template"""
        template = NotificationTemplate(
            name=name,
            notification_type=notification_type,
            title_template=title_template,
            body_template=body_template,
            default_channels=default_channels
        )
        self.templates[template.id] = template
        return template

    def cleanup_old_notifications(self, days: int = 90) -> int:
        """Remove notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_notifications = [
            notif_id for notif_id, notif in self.notifications.items()
            if notif.created_at < cutoff_date and notif.status == NotificationStatus.READ
        ]

        for notif_id in old_notifications:
            del self.notifications[notif_id]

        return len(old_notifications)
