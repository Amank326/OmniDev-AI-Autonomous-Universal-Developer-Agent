"""
Analytics Service
=================

Service for logging activities, metrics, and managing analytics data.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.analytics.models import (
    UserActivity, ActivityType,
    TaskMetrics, MetricType,
    ProjectMetrics,
    SystemMetrics,
    EngagementMetrics,
    AuditLog
)
from app.database.config import SessionLocal

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for tracking analytics, activities, and metrics.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db or SessionLocal()
    
    # ========================================================================
    # User Activity Logging
    # ========================================================================
    
    def log_user_activity(
        self,
        user_id: int,
        activity_type: ActivityType,
        description: str = None,
        project_id: int = None,
        task_id: int = None,
        metadata: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True,
        error_message: str = None,
        duration_ms: int = None
    ) -> UserActivity:
        """
        Log a user activity.
        
        Args:
            user_id: User performing the action
            activity_type: Type of activity
            description: Human-readable description
            project_id: Associated project (optional)
            task_id: Associated task (optional)
            metadata: Additional metadata as dict
            ip_address: User's IP address
            user_agent: User's browser agent
            success: Whether action succeeded
            error_message: Error message if failed
            duration_ms: How long action took in milliseconds
        
        Returns:
            Created UserActivity record
        """
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                project_id=project_id,
                task_id=task_id,
                metadata=metadata,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)
            
            logger.info(
                f"Logged activity: user_id={user_id}, "
                f"activity={activity_type.value}, success={success}"
            )
            
            return activity
        
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
            self.db.rollback()
            raise
    
    # ========================================================================
    # Task Metrics
    # ========================================================================
    
    def log_task_metric(
        self,
        task_id: int,
        project_id: int,
        metric_type: MetricType,
        value: float,
        unit: str = None,
        description: str = None,
        metadata: Dict[str, Any] = None,
        period_start: datetime = None,
        period_end: datetime = None
    ) -> TaskMetrics:
        """
        Log a task metric.
        
        Args:
            task_id: Associated task
            project_id: Associated project
            metric_type: Type of metric
            value: Metric value
            unit: Unit of measurement (seconds, percentage, etc.)
            description: Description of metric
            metadata: Additional metadata
            period_start: Period start for aggregated metrics
            period_end: Period end for aggregated metrics
        
        Returns:
            Created TaskMetrics record
        """
        try:
            metric = TaskMetrics(
                task_id=task_id,
                project_id=project_id,
                metric_type=metric_type,
                value=value,
                unit=unit,
                description=description,
                metadata=metadata,
                period_start=period_start,
                period_end=period_end,
                recorded_at=datetime.utcnow()
            )
            
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            logger.info(
                f"Logged task metric: task_id={task_id}, "
                f"metric={metric_type.value}, value={value} {unit}"
            )
            
            return metric
        
        except Exception as e:
            logger.error(f"Failed to log task metric: {str(e)}")
            self.db.rollback()
            raise
    
    # ========================================================================
    # Project Metrics
    # ========================================================================
    
    def update_project_metrics(
        self,
        project_id: int
    ) -> ProjectMetrics:
        """
        Update aggregated metrics for a project.
        
        Calculates and updates all project metrics including completion rate,
        task counts, timing, and engagement data.
        
        Args:
            project_id: Project to update metrics for
        
        Returns:
            Updated ProjectMetrics record
        """
        try:
            from app.database.models import Task
            
            # Get or create project metrics
            metrics = self.db.query(ProjectMetrics).filter_by(
                project_id=project_id
            ).first()
            
            if not metrics:
                metrics = ProjectMetrics(project_id=project_id)
                self.db.add(metrics)
            
            # Get task statistics
            tasks = self.db.query(Task).filter_by(project_id=project_id).all()
            total_tasks = len(tasks)
            
            completed_tasks = sum(1 for t in tasks if t.status == "completed")
            failed_tasks = sum(1 for t in tasks if t.status == "failed")
            
            # Update metrics
            metrics.total_tasks = total_tasks
            metrics.completed_tasks = completed_tasks
            metrics.failed_tasks = failed_tasks
            metrics.completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            metrics.success_rate = ((total_tasks - failed_tasks) / total_tasks * 100) if total_tasks > 0 else 0.0
            metrics.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(metrics)
            
            logger.info(f"Updated project metrics: project_id={project_id}")
            
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to update project metrics: {str(e)}")
            self.db.rollback()
            raise
    
    # ========================================================================
    # System Metrics
    # ========================================================================
    
    def log_system_metrics(
        self,
        uptime_percentage: float = 100.0,
        error_rate: float = 0.0,
        avg_api_response_time: float = None,
        queue_depth: int = 0,
        active_workers: int = 0,
        total_workers: int = 0
    ) -> SystemMetrics:
        """
        Log system health metrics.
        
        Args:
            uptime_percentage: System uptime percentage
            error_rate: Error rate percentage
            avg_api_response_time: Average API response time in ms
            queue_depth: Current task queue depth
            active_workers: Number of active workers
            total_workers: Total configured workers
        
        Returns:
            Created SystemMetrics record
        """
        try:
            metrics = SystemMetrics(
                uptime_percentage=uptime_percentage,
                error_rate=error_rate,
                avg_api_response_time=avg_api_response_time,
                queue_depth=queue_depth,
                active_workers=active_workers,
                total_workers=total_workers,
                recorded_at=datetime.utcnow()
            )
            
            self.db.add(metrics)
            self.db.commit()
            self.db.refresh(metrics)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to log system metrics: {str(e)}")
            self.db.rollback()
            raise
    
    # ========================================================================
    # Engagement Metrics
    # ========================================================================
    
    def update_engagement_metrics(self, user_id: int) -> EngagementMetrics:
        """
        Update engagement metrics for a user.
        
        Args:
            user_id: User to update metrics for
        
        Returns:
            Updated EngagementMetrics record
        """
        try:
            # Get or create engagement metrics
            metrics = self.db.query(EngagementMetrics).filter_by(
                user_id=user_id
            ).first()
            
            if not metrics:
                metrics = EngagementMetrics(user_id=user_id)
                self.db.add(metrics)
            
            # Get activity counts
            activities = self.db.query(UserActivity).filter_by(user_id=user_id).all()
            
            metrics.login_count = sum(1 for a in activities if a.activity_type == ActivityType.LOGIN)
            metrics.logout_count = sum(1 for a in activities if a.activity_type == ActivityType.LOGOUT)
            metrics.tasks_created = sum(1 for a in activities if a.activity_type == ActivityType.CREATE_TASK)
            metrics.tasks_completed = sum(1 for a in activities if a.activity_type == ActivityType.COMPLETE_TASK)
            metrics.projects_created = sum(1 for a in activities if a.activity_type == ActivityType.CREATE_PROJECT)
            metrics.comments_made = sum(1 for a in activities if a.activity_type == ActivityType.COMMENT)
            metrics.mentions_received = sum(1 for a in activities if a.activity_type == ActivityType.MENTION)
            
            # Get last login
            login_activity = self.db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.activity_type == ActivityType.LOGIN
            ).order_by(desc(UserActivity.timestamp)).first()
            
            if login_activity:
                metrics.last_login = login_activity.timestamp
            
            # Calculate engagement score (0-100)
            score = min(100, (
                metrics.login_count * 2 +
                metrics.tasks_completed * 5 +
                metrics.projects_created * 10 +
                metrics.comments_made * 1 +
                metrics.mentions_received * 3
            ))
            metrics.overall_engagement_score = score
            metrics.is_active = score > 0
            metrics.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(metrics)
            
            logger.info(f"Updated engagement metrics: user_id={user_id}")
            
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to update engagement metrics: {str(e)}")
            self.db.rollback()
            raise
    
    # ========================================================================
    # Audit Logs
    # ========================================================================
    
    def log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: int = None,
        user_id: int = None,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None,
        changes: str = None,
        status: str = "SUCCESS",
        error_message: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            user_id: User performing action
            old_values: Old values before change
            new_values: New values after change
            changes: Description of changes
            status: Status (SUCCESS, FAILURE)
            error_message: Error message if failed
            ip_address: IP address of requester
            user_agent: User agent of requester
        
        Returns:
            Created AuditLog record
        """
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                changes=changes,
                status=status,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.utcnow()
            )
            
            self.db.add(audit)
            self.db.commit()
            self.db.refresh(audit)
            
            logger.info(f"Logged audit: action={action}, resource={resource_type}, status={status}")
            
            return audit
        
        except Exception as e:
            logger.error(f"Failed to log audit: {str(e)}")
            self.db.rollback()
            raise
    
    # ========================================================================
    # Query Methods
    # ========================================================================
    
    def get_user_activities(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 100
    ) -> List[UserActivity]:
        """
        Get recent activities for a user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of activities to return
        
        Returns:
            List of UserActivity records
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            activities = self.db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.timestamp >= cutoff_date
            ).order_by(desc(UserActivity.timestamp)).limit(limit).all()
            
            return activities
        
        except Exception as e:
            logger.error(f"Failed to get user activities: {str(e)}")
            return []
    
    def get_project_activities(
        self,
        project_id: int,
        days: int = 7,
        limit: int = 100
    ) -> List[UserActivity]:
        """
        Get recent activities for a project.
        
        Args:
            project_id: Project ID
            days: Number of days to look back
            limit: Maximum number of activities to return
        
        Returns:
            List of UserActivity records
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            activities = self.db.query(UserActivity).filter(
                UserActivity.project_id == project_id,
                UserActivity.timestamp >= cutoff_date
            ).order_by(desc(UserActivity.timestamp)).limit(limit).all()
            
            return activities
        
        except Exception as e:
            logger.error(f"Failed to get project activities: {str(e)}")
            return []
    
    def get_engagement_metrics(self, user_id: int) -> Optional[EngagementMetrics]:
        """
        Get engagement metrics for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            EngagementMetrics record or None
        """
        try:
            return self.db.query(EngagementMetrics).filter_by(
                user_id=user_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get engagement metrics: {str(e)}")
            return None
    
    def get_project_metrics(self, project_id: int) -> Optional[ProjectMetrics]:
        """
        Get metrics for a project.
        
        Args:
            project_id: Project ID
        
        Returns:
            ProjectMetrics record or None
        """
        try:
            return self.db.query(ProjectMetrics).filter_by(
                project_id=project_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get project metrics: {str(e)}")
            return None
    
    def get_latest_system_metrics(self) -> Optional[SystemMetrics]:
        """
        Get the most recent system metrics.
        
        Returns:
            Latest SystemMetrics record or None
        """
        try:
            return self.db.query(SystemMetrics).order_by(
                desc(SystemMetrics.recorded_at)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return None
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close()


# Global analytics service instance
analytics_service = AnalyticsService()
