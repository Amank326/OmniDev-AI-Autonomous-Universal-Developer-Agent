"""
Analytics Package
=================

Analytics, metrics tracking, and reporting module.
"""

from app.analytics.models import (
    ActivityType,
    MetricType,
    UserActivity,
    TaskMetrics,
    ProjectMetrics,
    SystemMetrics,
    EngagementMetrics,
    AuditLog,
)
from app.analytics.service import AnalyticsService, analytics_service
from app.analytics.aggregation import DashboardAggregationService, dashboard_service
from app.analytics.reports import ReportGenerationService, report_service

__all__ = [
    # Models
    "ActivityType",
    "MetricType",
    "UserActivity",
    "TaskMetrics",
    "ProjectMetrics",
    "SystemMetrics",
    "EngagementMetrics",
    "AuditLog",
    # Services
    "AnalyticsService",
    "analytics_service",
    "DashboardAggregationService",
    "dashboard_service",
    "ReportGenerationService",
    "report_service",
]
