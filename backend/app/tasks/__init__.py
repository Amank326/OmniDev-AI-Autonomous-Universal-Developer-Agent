"""
Tasks Package
=============

This package contains all Celery tasks for OmniDev AI.

Modules:
- email: Email delivery tasks
- notifications: Notification delivery tasks

All tasks are automatically discovered by Celery via app.celery_app
"""

from app.tasks.email import (
    send_verification_email_task,
    send_password_reset_task,
    send_notification_email_task,
    send_welcome_email_task,
    send_bulk_emails_task,
)
from app.tasks.notifications import (
    create_notification_task,
    batch_notifications_task,
    send_digest_notification_task,
)

__all__ = [
    "send_verification_email_task",
    "send_password_reset_task",
    "send_notification_email_task",
    "send_welcome_email_task",
    "send_bulk_emails_task",
    "create_notification_task",
    "batch_notifications_task",
    "send_digest_notification_task",
]
