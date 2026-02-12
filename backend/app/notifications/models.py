"""
Notification Models and Types

Defines notification types, channels, and data structures.

Types:
    - User registration
    - Email verification
    - Password reset
    - Project updates
    - Task assignments
    - Team invitations
    - System alerts

Channels:
    - Email
    - In-app
    - WebSocket
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class NotificationType(str, Enum):
    """Notification type enumeration."""
    
    # Account notifications
    ACCOUNT_REGISTERED = "account_registered"
    EMAIL_VERIFIED = "email_verified"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGED = "password_changed"
    
    # Project notifications
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    PROJECT_SHARED = "project_shared"
    
    # Task notifications
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"
    
    # Collaboration notifications
    TEAM_INVITED = "team_invited"
    TEAM_ACCEPTED = "team_accepted"
    COMMENT_ADDED = "comment_added"
    MENTIONED = "mentioned"
    
    # System notifications
    SYSTEM_ALERT = "system_alert"
    MAINTENANCE = "maintenance"
    UPDATE_AVAILABLE = "update_available"


class NotificationChannel(str, Enum):
    """Notification delivery channel."""
    EMAIL = "email"
    IN_APP = "in_app"
    WEBSOCKET = "websocket"
    SMS = "sms"
    PUSH = "push"


class NotificationPriority(str, Enum):
    """Notification priority level."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationRequest(BaseModel):
    """Request to create a notification."""
    
    recipient_id: int
    notification_type: NotificationType
    title: str
    message: str
    channels: list[NotificationChannel] = [NotificationChannel.IN_APP]
    priority: NotificationPriority = NotificationPriority.NORMAL
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Response with notification data."""
    
    id: int
    recipient_id: int
    notification_type: NotificationType
    title: str
    message: str
    channels: list[NotificationChannel]
    priority: NotificationPriority
    action_url: Optional[str]
    action_text: Optional[str]
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]
    data: Optional[Dict[str, Any]]
