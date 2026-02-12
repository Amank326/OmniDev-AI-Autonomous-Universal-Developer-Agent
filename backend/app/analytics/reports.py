"""
Report Generation Service
==========================

Service for generating analytics reports in various formats.
"""

import logging
import csv
import json
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime, timedelta
from io import StringIO, BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.config import SessionLocal
from app.analytics.models import (
    UserActivity, ActivityType,
    EngagementMetrics, ProjectMetrics, SystemMetrics, TaskMetrics, MetricType, AuditLog
)
from app.database.models import User, Project

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class ReportGenerationService:
    """
    Service for generating analytics reports in multiple formats.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db or SessionLocal()
    
    # ========================================================================
    # CSV Reports
    # ========================================================================
    
    def generate_user_activity_csv(
        self,
        user_id: int,
        days: int = 30
    ) -> str:
        """
        Generate user activity report as CSV.
        
        Args:
            user_id: User ID
            days: Number of days to include
        
        Returns:
            CSV content as string
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            activities = self.db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.timestamp >= cutoff_date
            ).order_by(desc(UserActivity.timestamp)).all()
            
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "Timestamp", "Activity Type", "Description", 
                "Project ID", "Task ID", "Success", "Duration (ms)"
            ])
            
            # Rows
            for activity in activities:
                writer.writerow([
                    activity.timestamp.isoformat(),
                    activity.activity_type.value if activity.activity_type else "",
                    activity.description or "",
                    activity.project_id or "",
                    activity.task_id or "",
                    "Yes" if activity.success else "No",
                    activity.duration_ms or "",
                ])
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Failed to generate user activity CSV: {str(e)}")
            raise
    
    def generate_project_metrics_csv(
        self,
        project_id: int,
        days: int = 30
    ) -> str:
        """
        Generate project metrics report as CSV.
        
        Args:
            project_id: Project ID
            days: Number of days to include
        
        Returns:
            CSV content as string
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get project metrics
            metrics = self.db.query(ProjectMetrics).filter_by(
                project_id=project_id
            ).first()
            
            # Get task metrics
            task_metrics = self.db.query(TaskMetrics).filter(
                TaskMetrics.project_id == project_id,
                TaskMetrics.recorded_at >= cutoff_date
            ).all()
            
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(["Project Metrics Report"])
            writer.writerow([])
            
            # Summary section
            writer.writerow(["Summary"])
            if metrics:
                writer.writerow(["Total Tasks", metrics.total_tasks])
                writer.writerow(["Completed Tasks", metrics.completed_tasks])
                writer.writerow(["Completion Rate (%)", f"{metrics.completion_rate:.2f}"])
                writer.writerow(["Success Rate (%)", f"{metrics.success_rate:.2f}"])
                writer.writerow(["Contributors", metrics.contributor_count])
            
            writer.writerow([])
            writer.writerow(["Task Metrics"])
            writer.writerow(["Timestamp", "Task ID", "Metric Type", "Value", "Unit"])
            
            for metric in task_metrics:
                writer.writerow([
                    metric.recorded_at.isoformat(),
                    metric.task_id,
                    metric.metric_type.value if metric.metric_type else "",
                    metric.value,
                    metric.unit or "",
                ])
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Failed to generate project metrics CSV: {str(e)}")
            raise
    
    def generate_engagement_report_csv(self, days: int = 30) -> str:
        """
        Generate team engagement report as CSV.
        
        Args:
            days: Number of days to include
        
        Returns:
            CSV content as string
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get engagement metrics
            engagements = self.db.query(EngagementMetrics).all()
            
            # Get users
            users = self.db.query(User).all()
            user_map = {u.id: u.username for u in users}
            
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "User ID", "Username", "Engagement Score", "Is Active",
                "Login Count", "Tasks Completed", "Projects Created",
                "Comments Made", "Last Login"
            ])
            
            # Rows
            for engagement in engagements:
                writer.writerow([
                    engagement.user_id,
                    user_map.get(engagement.user_id, "Unknown"),
                    f"{engagement.overall_engagement_score:.2f}",
                    "Yes" if engagement.is_active else "No",
                    engagement.login_count,
                    engagement.tasks_completed,
                    engagement.projects_created,
                    engagement.comments_made,
                    engagement.last_login.isoformat() if engagement.last_login else "",
                ])
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Failed to generate engagement report CSV: {str(e)}")
            raise
    
    def generate_audit_log_csv(
        self,
        days: int = 30,
        limit: int = 10000
    ) -> str:
        """
        Generate audit log report as CSV.
        
        Args:
            days: Number of days to include
            limit: Maximum rows to include
        
        Returns:
            CSV content as string
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            logs = self.db.query(AuditLog).filter(
                AuditLog.created_at >= cutoff_date
            ).order_by(desc(AuditLog.created_at)).limit(limit).all()
            
            # Create CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "Timestamp", "User ID", "Action", "Resource Type",
                "Resource ID", "Status", "Error Message"
            ])
            
            # Rows
            for log in logs:
                writer.writerow([
                    log.created_at.isoformat(),
                    log.user_id or "",
                    log.action,
                    log.resource_type,
                    log.resource_id or "",
                    log.status,
                    log.error_message or "",
                ])
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Failed to generate audit log CSV: {str(e)}")
            raise
    
    # ========================================================================
    # JSON Reports
    # ========================================================================
    
    def generate_user_report_json(
        self,
        user_id: int,
        days: int = 30
    ) -> str:
        """
        Generate user report as JSON.
        
        Args:
            user_id: User ID
            days: Number of days to include
        
        Returns:
            JSON content as string
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user
            user = self.db.query(User).filter_by(id=user_id).first()
            
            # Get engagement metrics
            engagement = self.db.query(EngagementMetrics).filter_by(
                user_id=user_id
            ).first()
            
            # Get activities
            activities = self.db.query(UserActivity).filter(
                UserActivity.user_id == user_id,
                UserActivity.timestamp >= cutoff_date
            ).all()
            
            # Build report
            report = {
                "report_type": "user_report",
                "generated_at": datetime.utcnow().isoformat(),
                "period_days": days,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                } if user else None,
                "engagement_metrics": engagement.to_dict() if engagement else None,
                "activity_summary": {
                    "total_activities": len(activities),
                    "successful_activities": sum(1 for a in activities if a.success),
                    "failed_activities": sum(1 for a in activities if not a.success),
                },
                "activities": [a.to_dict() for a in activities[:100]],  # Last 100
            }
            
            return json.dumps(report, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to generate user report JSON: {str(e)}")
            raise
    
    def generate_project_report_json(
        self,
        project_id: int,
        days: int = 30
    ) -> str:
        """
        Generate project report as JSON.
        
        Args:
            project_id: Project ID
            days: Number of days to include
        
        Returns:
            JSON content as string
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get project
            project = self.db.query(Project).filter_by(id=project_id).first()
            
            # Get metrics
            metrics = self.db.query(ProjectMetrics).filter_by(
                project_id=project_id
            ).first()
            
            # Get activities
            activities = self.db.query(UserActivity).filter(
                UserActivity.project_id == project_id,
                UserActivity.timestamp >= cutoff_date
            ).all()
            
            # Build report
            report = {
                "report_type": "project_report",
                "generated_at": datetime.utcnow().isoformat(),
                "period_days": days,
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "status": project.status,
                } if project else None,
                "metrics": metrics.to_dict() if metrics else None,
                "activity_summary": {
                    "total_activities": len(activities),
                    "successful_activities": sum(1 for a in activities if a.success),
                    "failed_activities": sum(1 for a in activities if not a.success),
                },
                "recent_activities": [a.to_dict() for a in activities[:50]],
            }
            
            return json.dumps(report, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to generate project report JSON: {str(e)}")
            raise
    
    def generate_system_health_report_json(
        self,
        days: int = 30
    ) -> str:
        """
        Generate system health report as JSON.
        
        Args:
            days: Number of days to include
        
        Returns:
            JSON content as string
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get system metrics
            metrics = self.db.query(SystemMetrics).filter(
                SystemMetrics.recorded_at >= cutoff_date
            ).all()
            
            # Calculate averages
            avg_uptime = sum(m.uptime_percentage for m in metrics) / len(metrics) if metrics else 0
            avg_error_rate = sum(m.error_rate for m in metrics) / len(metrics) if metrics else 0
            
            # Build report
            report = {
                "report_type": "system_health_report",
                "generated_at": datetime.utcnow().isoformat(),
                "period_days": days,
                "summary": {
                    "avg_uptime_percentage": f"{avg_uptime:.2f}",
                    "avg_error_rate": f"{avg_error_rate:.2f}",
                    "total_metrics_recorded": len(metrics),
                },
                "latest_metrics": metrics[-1].to_dict() if metrics else None,
                "metrics_history": [m.to_dict() for m in metrics[-100:]],  # Last 100
            }
            
            return json.dumps(report, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to generate system health report: {str(e)}")
            raise
    
    # ========================================================================
    # PDF Reports (if ReportLab available)
    # ========================================================================
    
    def generate_user_report_pdf(
        self,
        user_id: int,
        days: int = 30
    ) -> Optional[bytes]:
        """
        Generate user report as PDF (requires ReportLab).
        
        Args:
            user_id: User ID
            days: Number of days to include
        
        Returns:
            PDF content as bytes, or None if ReportLab not available
        """
        if not HAS_REPORTLAB:
            logger.warning("ReportLab not installed, skipping PDF generation")
            return None
        
        try:
            # This is a simplified version - full PDF generation requires more work
            # For now, return None to indicate not fully implemented
            logger.info("PDF generation requires additional implementation")
            return None
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {str(e)}")
            return None
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close()


# Global service instance
report_service = ReportGenerationService()
