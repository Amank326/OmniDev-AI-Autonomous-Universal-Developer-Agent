"""Notifications module for system and user notifications."""

from app.notifications.service import NotificationService
from app.notifications.models import NotificationType

__all__ = ["NotificationService", "NotificationType"]
