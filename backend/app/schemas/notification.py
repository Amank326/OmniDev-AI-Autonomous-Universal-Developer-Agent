"""Notification schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationStatus


class NotificationBase(BaseModel):
    """Base notification schema."""

    title: str
    message: str
    channel: NotificationChannel


class NotificationCreate(NotificationBase):
    """Notification creation schema."""

    data: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Notification response schema."""

    id: int
    user_id: int
    status: NotificationStatus
    is_read: bool
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
