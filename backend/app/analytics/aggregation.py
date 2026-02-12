"""
Dashboard Data Aggregation
===========================

Service for aggregating analytics data into dashboard views.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.database.config import SessionLocal
from app.analytics.models import (
    UserActivity, ActivityType,
    EngagementMetrics, ProjectMetrics, SystemMetrics, TaskMetrics, MetricType
)
from app.database.models import User, Project, Task

logger = logging.getLogger(__name__)


class DashboardAggregationService:
    """
    Service for aggregating analytics data for dashboards.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db or SessionLocal()
    
    def get_user_dashboard(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive user dashboard data.
        
        Args:
            user_id: User ID
            days: Period to analyze
        
        Returns:
            User dashboard with activities, metrics, and insights
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get engagement metrics
            engagement = self.db.query(EngagementMetrics).filter_by(
                user_id=user_id
            ).first()
            
            # Get recent activities
            activities = self.db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.timestamp >= cutoff_date
            ).order_by(desc(UserActivity.timestamp)).limit(10).all()
            
            # Get projects created by user
            projects = self.db.query(Project).filter_by(
                created_by=user_id
            ).all()
            
            # Calculate activity trend
            activity_by_day = self.db.query(
                func.date(UserActivity.timestamp).label("date"),
                func.count(UserActivity.id).label("count")
            ).filter(
                UserActivity.user_id == user_id,
                UserActivity.timestamp >= cutoff_date
            ).group_by(func.date(UserActivity.timestamp)).all()
            
            activity_trend = {
                str(date): count for date, count in activity_by_day
            }
            
            return {
                "user_id": user_id,
                "period_days": days,
                "engagement_score": engagement.overall_engagement_score if engagement else 0,
                "is_active": engagement.is_active if engagement else False,
                "total_activities": len(activities),
                "projects_created": len(projects),
                "tasks_completed": engagement.tasks_completed if engagement else 0,
                "recent_activities": [a.to_dict() for a in activities],
                "activity_trend": activity_trend,
                "last_active": (
                    activities[0].timestamp.isoformat() if activities else None
                ),
                "statistics": {
                    "login_count": engagement.login_count if engagement else 0,
                    "comments_made": engagement.comments_made if engagement else 0,
                    "mentions_received": engagement.mentions_received if engagement else 0,
                },
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get user dashboard: {str(e)}")
            raise
    
    def get_project_dashboard(self, project_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive project dashboard data.
        
        Args:
            project_id: Project ID
            days: Period to analyze
        
        Returns:
            Project dashboard with metrics, activities, and progress
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get project metrics
            metrics = self.db.query(ProjectMetrics).filter_by(
                project_id=project_id
            ).first()
            
            # Get project details
            project = self.db.query(Project).filter_by(id=project_id).first()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get recent activities
            activities = self.db.query(UserActivity).filter(
                UserActivity.project_id == project_id,
                UserActivity.timestamp >= cutoff_date
            ).order_by(desc(UserActivity.timestamp)).limit(20).all()
            
            # Get top contributors
            top_contributors = self.db.query(
                UserActivity.user_id,
                func.count(UserActivity.id).label("activity_count")
            ).filter(
                UserActivity.project_id == project_id,
                UserActivity.timestamp >= cutoff_date
            ).group_by(UserActivity.user_id).order_by(
                desc("activity_count")
            ).limit(5).all()
            
            # Get task metrics
            task_metrics = self.db.query(TaskMetrics).filter(
                TaskMetrics.project_id == project_id,
                TaskMetrics.recorded_at >= cutoff_date
            ).all()
            
            # Calculate progress by day
            progress_by_day = self.db.query(
                func.date(UserActivity.timestamp).label("date"),
                func.count(UserActivity.id).label("count")
            ).filter(
                UserActivity.project_id == project_id,
                UserActivity.timestamp >= cutoff_date,
                UserActivity.activity_type == ActivityType.COMPLETE_TASK
            ).group_by(func.date(UserActivity.timestamp)).all()
            
            progress_trend = {
                str(date): count for date, count in progress_by_day
            }
            
            return {
                "project_id": project_id,
                "project_name": project.title,
                "project_status": project.status,
                "period_days": days,
                "metrics": {
                    "total_tasks": metrics.total_tasks if metrics else 0,
                    "completed_tasks": metrics.completed_tasks if metrics else 0,
                    "completion_rate": metrics.completion_rate if metrics else 0.0,
                    "success_rate": metrics.success_rate if metrics else 0.0,
                    "avg_task_duration": metrics.avg_task_duration if metrics else None,
                    "contributor_count": metrics.contributor_count if metrics else 0,
                },
                "recent_activities": [a.to_dict() for a in activities],
                "top_contributors": [
                    {
                        "user_id": user_id,
                        "activity_count": count,
                    }
                    for user_id, count in top_contributors
                ],
                "progress_trend": progress_trend,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get project dashboard: {str(e)}")
            raise
    
    def get_team_dashboard(self, days: int = 30, limit: int = 10) -> Dict[str, Any]:
        """
        Get team-wide dashboard data.
        
        Args:
            days: Period to analyze
            limit: Maximum number of items per section
        
        Returns:
            Team dashboard with overall metrics and top performers
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get overall activity
            total_activities = self.db.query(func.count(UserActivity.id)).filter(
                UserActivity.timestamp >= cutoff_date
            ).scalar() or 0
            
            successful_activities = self.db.query(func.count(UserActivity.id)).filter(
                UserActivity.timestamp >= cutoff_date,
                UserActivity.success == True
            ).scalar() or 0
            
            # Get active users
            active_users = self.db.query(func.count(func.distinct(UserActivity.user_id))).filter(
                UserActivity.timestamp >= cutoff_date
            ).scalar() or 0
            
            # Get active projects
            active_projects = self.db.query(func.count(func.distinct(UserActivity.project_id))).filter(
                UserActivity.timestamp >= cutoff_date
            ).scalar() or 0
            
            # Get top projects
            top_projects = self.db.query(
                Project.id,
                Project.title,
                func.count(UserActivity.id).label("activity_count")
            ).outerjoin(UserActivity).filter(
                UserActivity.timestamp >= cutoff_date
            ).group_by(Project.id).order_by(
                desc("activity_count")
            ).limit(limit).all()
            
            # Get top users
            top_users = self.db.query(
                User.id,
                User.username,
                func.count(UserActivity.id).label("activity_count"),
                EngagementMetrics.overall_engagement_score
            ).outerjoin(UserActivity).outerjoin(EngagementMetrics).filter(
                UserActivity.timestamp >= cutoff_date
            ).group_by(User.id).order_by(
                desc("activity_count")
            ).limit(limit).all()
            
            # Get activity trend
            activity_by_day = self.db.query(
                func.date(UserActivity.timestamp).label("date"),
                func.count(UserActivity.id).label("count")
            ).filter(
                UserActivity.timestamp >= cutoff_date
            ).group_by(func.date(UserActivity.timestamp)).all()
            
            activity_trend = {
                str(date): count for date, count in activity_by_day
            }
            
            # Get activity by type
            activity_by_type = self.db.query(
                UserActivity.activity_type,
                func.count(UserActivity.id).label("count")
            ).filter(
                UserActivity.timestamp >= cutoff_date
            ).group_by(UserActivity.activity_type).all()
            
            activity_by_type_dict = {
                activity_type.value: count
                for activity_type, count in activity_by_type
            }
            
            return {
                "period_days": days,
                "summary": {
                    "total_activities": total_activities,
                    "successful_activities": successful_activities,
                    "success_rate": (
                        (successful_activities / total_activities * 100) 
                        if total_activities else 0
                    ),
                    "active_users": active_users,
                    "active_projects": active_projects,
                },
                "top_projects": [
                    {
                        "project_id": project_id,
                        "project_name": title,
                        "activity_count": activity_count,
                    }
                    for project_id, title, activity_count in top_projects
                ],
                "top_users": [
                    {
                        "user_id": user_id,
                        "username": username,
                        "activity_count": activity_count,
                        "engagement_score": engagement_score or 0,
                    }
                    for user_id, username, activity_count, engagement_score in top_users
                ],
                "activity_trend": activity_trend,
                "activity_by_type": activity_by_type_dict,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get team dashboard: {str(e)}")
            raise
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close()


# Global service instance
dashboard_service = DashboardAggregationService()
