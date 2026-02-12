"""
Analytics Models
================

Database models for tracking user activity, metrics, and analytics data.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.config import Base
from datetime import datetime
import enum


class ActivityType(str, enum.Enum):
    """Types of user activities tracked."""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE_PROJECT = "create_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    COMPLETE_TASK = "complete_task"
    DELETE_TASK = "delete_task"
    INVITE_USER = "invite_user"
    REMOVE_USER = "remove_user"
    RUN_AGENT = "run_agent"
    STOP_AGENT = "stop_agent"
    SHARE_PROJECT = "share_project"
    EXPORT_DATA = "export_data"
    VIEW_DASHBOARD = "view_dashboard"
    UPLOAD_FILE = "upload_file"
    DELETE_FILE = "delete_file"
    COMMENT = "comment"
    MENTION = "mention"
    SEARCH = "search"


class MetricType(str, enum.Enum):
    """Types of metrics tracked."""
    TASK_COMPLETION_TIME = "task_completion_time"
    TASK_SUCCESS_RATE = "task_success_rate"
    AGENT_EXECUTION_TIME = "agent_execution_time"
    AGENT_SUCCESS_RATE = "agent_success_rate"
    PROJECT_PROGRESS = "project_progress"
    USER_ENGAGEMENT = "user_engagement"
    SYSTEM_UPTIME = "system_uptime"
    ERROR_RATE = "error_rate"
    API_RESPONSE_TIME = "api_response_time"
    QUEUE_DEPTH = "queue_depth"


class UserActivity(Base):
    """
    Track user actions and activities.
    
    Stores all user interactions with the system for activity logging
    and user behavior analysis.
    """
    __tablename__ = "user_activities"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Activity Details
    activity_type = Column(Enum(ActivityType), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    meta_data = Column(JSON, nullable=True)  # Additional context as JSON
    
    # IP and User Agent
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)  # How long the action took
    
    # Status
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    project = relationship("Project")
    task = relationship("Task")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "activity_type": self.activity_type.value if self.activity_type else None,
            "description": self.description,
            "meta_data": self.meta_data,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
        }


class TaskMetrics(Base):
    """
    Track metrics for individual tasks.
    
    Records task completion times, success rates, and other task-specific metrics.
    """
    __tablename__ = "task_metrics"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Metrics
    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    value = Column(Float, nullable=False)
    
    # Details
    unit = Column(String(50), nullable=True)  # seconds, milliseconds, percentage, etc.
    description = Column(String(500), nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Timing
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    period_start = Column(DateTime, nullable=True)  # For aggregated metrics
    period_end = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("Task")
    project = relationship("Project")
    
    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "metric_type": self.metric_type.value if self.metric_type else None,
            "value": self.value,
            "unit": self.unit,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class ProjectMetrics(Base):
    """
    Track metrics for projects.
    
    Aggregated metrics about project performance, progress, and health.
    """
    __tablename__ = "project_metrics"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Metrics
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # Percentage
    
    # Timing
    avg_task_duration = Column(Float, nullable=True)  # seconds
    total_hours_spent = Column(Float, default=0.0)
    
    # Engagement
    contributor_count = Column(Integer, default=1)
    total_comments = Column(Integer, default=0)
    total_mentions = Column(Integer, default=0)
    
    # Quality
    success_rate = Column(Float, default=0.0)  # Percentage
    error_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    period_start = Column(DateTime, default=datetime.utcnow, index=True)
    period_end = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "completion_rate": self.completion_rate,
            "avg_task_duration": self.avg_task_duration,
            "contributor_count": self.contributor_count,
            "success_rate": self.success_rate,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class SystemMetrics(Base):
    """
    Track system-level metrics.
    
    Records performance and health metrics for the entire system.
    """
    __tablename__ = "system_metrics"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # System Health
    uptime_percentage = Column(Float, default=100.0)
    error_rate = Column(Float, default=0.0)
    
    # Performance
    avg_api_response_time = Column(Float, nullable=True)  # milliseconds
    max_api_response_time = Column(Float, nullable=True)
    p95_api_response_time = Column(Float, nullable=True)
    p99_api_response_time = Column(Float, nullable=True)
    
    # Queue
    queue_depth = Column(Integer, default=0)
    pending_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # Workers
    active_workers = Column(Integer, default=0)
    total_workers = Column(Integer, default=0)
    
    # Database
    db_connection_pool_usage = Column(Float, default=0.0)  # Percentage
    
    # Redis/Cache
    cache_hit_rate = Column(Float, default=0.0)  # Percentage
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "uptime_percentage": self.uptime_percentage,
            "error_rate": self.error_rate,
            "avg_api_response_time": self.avg_api_response_time,
            "queue_depth": self.queue_depth,
            "active_workers": self.active_workers,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class EngagementMetrics(Base):
    """
    Track user engagement metrics.
    
    Records engagement data for analyzing user behavior and retention.
    """
    __tablename__ = "engagement_metrics"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Engagement Data
    login_count = Column(Integer, default=0)
    logout_count = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True, index=True)
    session_duration = Column(Integer, default=0)  # seconds
    
    # Activity
    actions_taken = Column(Integer, default=0)
    tasks_created = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    projects_created = Column(Integer, default=0)
    
    # Social
    comments_made = Column(Integer, default=0)
    mentions_received = Column(Integer, default=0)
    collaboration_score = Column(Float, default=0.0)  # 0-100
    
    # Engagement Score
    overall_engagement_score = Column(Float, default=0.0)  # 0-100
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    period_start = Column(DateTime, default=datetime.utcnow, index=True)
    period_end = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="engagement_metrics")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "login_count": self.login_count,
            "tasks_completed": self.tasks_completed,
            "projects_created": self.projects_created,
            "overall_engagement_score": self.overall_engagement_score,
            "is_active": self.is_active,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class AuditLog(Base):
    """
    Detailed audit logs for compliance and debugging.
    
    Records sensitive operations for audit trail and compliance.
    """
    __tablename__ = "audit_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Action Details
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Integer, nullable=True)
    
    # Before/After
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changes = Column(Text, nullable=True)  # Human-readable description
    
    # Status
    status = Column(String(50), default="SUCCESS")  # SUCCESS, FAILURE
    error_message = Column(Text, nullable=True)
    
    # IP and context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
