"""
Phase 7 Analytics Tests
=======================

Comprehensive test suite for analytics, reporting, and metrics tracking.
Tests cover models, services, API routes, and aggregation functionality.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.config import SessionLocal, Base, engine
from app.database.models import User, Project, Task
from app.analytics.models import (
    ActivityType, MetricType, UserActivity, TaskMetrics, ProjectMetrics,
    SystemMetrics, EngagementMetrics, AuditLog
)
from app.analytics.service import AnalyticsService
from app.analytics.aggregation import DashboardAggregationService
from app.analytics.reports import ReportGenerationService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def db():
    """Create a fresh test database."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user(db: Session):
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_project(db: Session, test_user: User):
    """Create test project."""
    project = Project(
        title="Test Project",
        description="Test project for analytics",
        owner_id=test_user.id,
        status="active",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture(scope="function")
def test_task(db: Session, test_project: Project):
    """Create test task."""
    task = Task(
        title="Test Task",
        description="Test task for analytics",
        project_id=test_project.id,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture(scope="function")
def analytics_service(db: Session):
    """Create analytics service instance."""
    service = AnalyticsService(db)
    return service


@pytest.fixture(scope="function")
def dashboard_service(db: Session):
    """Create dashboard service instance."""
    service = DashboardAggregationService(db)
    return service


@pytest.fixture(scope="function")
def report_service(db: Session):
    """Create report service instance."""
    service = ReportGenerationService(db)
    return service


# ============================================================================
# Model Tests
# ============================================================================

class TestUserActivityModel:
    """Test UserActivity model."""
    
    def test_create_user_activity(self, db: Session, test_user: User):
        """Test creating user activity record."""
        activity = UserActivity(
            user_id=test_user.id,
            activity_type=ActivityType.LOGIN,
            description="User logged in",
            success=True,
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        assert activity.id is not None
        assert activity.user_id == test_user.id
        assert activity.activity_type == ActivityType.LOGIN
        assert activity.success is True
    
    def test_user_activity_to_dict(self, db: Session, test_user: User):
        """Test user activity to_dict method."""
        activity = UserActivity(
            user_id=test_user.id,
            activity_type=ActivityType.CREATE_PROJECT,
            success=True,
        )
        db.add(activity)
        db.commit()
        
        result = activity.to_dict()
        assert "id" in result
        assert result["user_id"] == test_user.id
        assert result["activity_type"] == "create_project"
    
    def test_user_activity_with_metadata(self, db: Session, test_user: User):
        """Test user activity with JSON metadata."""
        metadata = {"browser": "Chrome", "version": "120"}
        activity = UserActivity(
            user_id=test_user.id,
            activity_type=ActivityType.LOGIN,
            metadata=metadata,
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        assert activity.metadata == metadata


class TestProjectMetricsModel:
    """Test ProjectMetrics model."""
    
    def test_create_project_metrics(self, db: Session, test_project: Project):
        """Test creating project metrics."""
        metrics = ProjectMetrics(
            project_id=test_project.id,
            total_tasks=10,
            completed_tasks=5,
            completion_rate=50.0,
            success_rate=95.0,
        )
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        
        assert metrics.project_id == test_project.id
        assert metrics.total_tasks == 10
        assert metrics.completion_rate == 50.0
    
    def test_project_metrics_to_dict(self, db: Session, test_project: Project):
        """Test project metrics to_dict method."""
        metrics = ProjectMetrics(
            project_id=test_project.id,
            total_tasks=5,
            completed_tasks=3,
        )
        db.add(metrics)
        db.commit()
        
        result = metrics.to_dict()
        assert "project_id" in result
        assert result["total_tasks"] == 5


class TestEngagementMetricsModel:
    """Test EngagementMetrics model."""
    
    def test_create_engagement_metrics(self, db: Session, test_user: User):
        """Test creating engagement metrics."""
        metrics = EngagementMetrics(
            user_id=test_user.id,
            login_count=10,
            tasks_completed=5,
            overall_engagement_score=42.5,
            is_active=True,
        )
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        
        assert metrics.user_id == test_user.id
        assert metrics.login_count == 10
        assert metrics.overall_engagement_score == 42.5


class TestAuditLogModel:
    """Test AuditLog model."""
    
    def test_create_audit_log(self, db: Session, test_user: User):
        """Test creating audit log."""
        log = AuditLog(
            user_id=test_user.id,
            action="UPDATE",
            resource_type="Project",
            resource_id=1,
            status="success",
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.action == "UPDATE"
        assert log.resource_type == "Project"
        assert log.status == "success"


# ============================================================================
# Service Tests
# ============================================================================

class TestAnalyticsService:
    """Test AnalyticsService."""
    
    def test_log_user_activity(
        self,
        analytics_service: AnalyticsService,
        test_user: User,
        db: Session
    ):
        """Test logging user activity."""
        analytics_service.log_user_activity(
            user_id=test_user.id,
            activity_type=ActivityType.LOGIN,
            description="User logged in",
        )
        
        activity = db.query(UserActivity).filter_by(
            user_id=test_user.id
        ).first()
        
        assert activity is not None
        assert activity.activity_type == ActivityType.LOGIN
    
    def test_log_task_metric(
        self,
        analytics_service: AnalyticsService,
        test_task: Task,
        db: Session
    ):
        """Test logging task metric."""
        analytics_service.log_task_metric(
            task_id=test_task.id,
            project_id=test_task.project_id,
            metric_type=MetricType.TASK_COMPLETION_TIME,
            value=3600,
            unit="seconds",
        )
        
        metric = db.query(TaskMetrics).filter_by(
            task_id=test_task.id
        ).first()
        
        assert metric is not None
        assert metric.value == 3600
        assert metric.unit == "seconds"
    
    def test_update_engagement_metrics(
        self,
        analytics_service: AnalyticsService,
        test_user: User,
        db: Session
    ):
        """Test updating engagement metrics."""
        # Log some activities first
        for _ in range(3):
            analytics_service.log_user_activity(
                user_id=test_user.id,
                activity_type=ActivityType.LOGIN,
            )
        
        engagement = analytics_service.update_engagement_metrics(
            user_id=test_user.id
        )
        
        assert engagement is not None
        assert engagement.user_id == test_user.id
    
    def test_get_user_activities(
        self,
        analytics_service: AnalyticsService,
        test_user: User,
        db: Session
    ):
        """Test getting user activities."""
        # Create multiple activities
        for i in range(5):
            analytics_service.log_user_activity(
                user_id=test_user.id,
                activity_type=ActivityType.LOGIN,
                description=f"Login {i}",
            )
        
        activities = analytics_service.get_user_activities(
            user_id=test_user.id,
            days=1,
            limit=10
        )
        
        assert len(activities) == 5
    
    def test_log_system_metrics(
        self,
        analytics_service: AnalyticsService,
        db: Session
    ):
        """Test logging system metrics."""
        analytics_service.log_system_metrics(
            uptime_percentage=99.9,
            error_rate=0.1,
            api_response_time_ms=250,
            queue_depth=5,
            active_workers=3,
        )
        
        metrics = db.query(SystemMetrics).first()
        assert metrics is not None
        assert metrics.uptime_percentage == 99.9
    
    def test_log_audit(
        self,
        analytics_service: AnalyticsService,
        test_user: User,
        db: Session
    ):
        """Test logging audit event."""
        analytics_service.log_audit(
            user_id=test_user.id,
            action="CREATE",
            resource_type="Project",
            resource_id=1,
            status="success",
            new_values={"title": "New Project"},
        )
        
        log = db.query(AuditLog).first()
        assert log is not None
        assert log.action == "CREATE"


class TestDashboardAggregationService:
    """Test DashboardAggregationService."""
    
    def test_get_user_dashboard(
        self,
        dashboard_service: DashboardAggregationService,
        analytics_service: AnalyticsService,
        test_user: User,
    ):
        """Test getting user dashboard."""
        # Create some activities
        for _ in range(5):
            analytics_service.log_user_activity(
                user_id=test_user.id,
                activity_type=ActivityType.LOGIN,
            )
        
        dashboard = dashboard_service.get_user_dashboard(
            user_id=test_user.id,
            days=30
        )
        
        assert "engagement_score" in dashboard
        assert "activity_summary" in dashboard
        assert "recent_activities" in dashboard
    
    def test_get_project_dashboard(
        self,
        dashboard_service: DashboardAggregationService,
        analytics_service: AnalyticsService,
        test_project: Project,
    ):
        """Test getting project dashboard."""
        dashboard = dashboard_service.get_project_dashboard(
            project_id=test_project.id,
            days=30
        )
        
        assert "metrics" in dashboard
        assert "activity_summary" in dashboard
    
    def test_get_team_dashboard(
        self,
        dashboard_service: DashboardAggregationService,
    ):
        """Test getting team dashboard."""
        dashboard = dashboard_service.get_team_dashboard(
            days=30,
            limit=10
        )
        
        assert "summary" in dashboard
        assert "top_projects" in dashboard
        assert "top_users" in dashboard


class TestReportGenerationService:
    """Test ReportGenerationService."""
    
    def test_generate_user_activity_csv(
        self,
        report_service: ReportGenerationService,
        analytics_service: AnalyticsService,
        test_user: User,
    ):
        """Test generating user activity CSV report."""
        # Create activities
        for i in range(3):
            analytics_service.log_user_activity(
                user_id=test_user.id,
                activity_type=ActivityType.LOGIN,
                description=f"Activity {i}",
            )
        
        csv_content = report_service.generate_user_activity_csv(
            user_id=test_user.id,
            days=30
        )
        
        assert isinstance(csv_content, str)
        assert "Timestamp" in csv_content
        assert "Activity Type" in csv_content
    
    def test_generate_engagement_report_csv(
        self,
        report_service: ReportGenerationService,
    ):
        """Test generating engagement report CSV."""
        csv_content = report_service.generate_engagement_report_csv(
            days=30
        )
        
        assert isinstance(csv_content, str)
        assert "User ID" in csv_content
        assert "Engagement Score" in csv_content
    
    def test_generate_audit_log_csv(
        self,
        report_service: ReportGenerationService,
        analytics_service: AnalyticsService,
        test_user: User,
    ):
        """Test generating audit log CSV."""
        # Create audit log
        analytics_service.log_audit(
            user_id=test_user.id,
            action="CREATE",
            resource_type="Project",
            resource_id=1,
            status="success",
        )
        
        csv_content = report_service.generate_audit_log_csv(
            days=30
        )
        
        assert isinstance(csv_content, str)
        assert "Timestamp" in csv_content
        assert "Action" in csv_content
    
    def test_generate_user_report_json(
        self,
        report_service: ReportGenerationService,
        analytics_service: AnalyticsService,
        test_user: User,
    ):
        """Test generating user report JSON."""
        # Create activities
        analytics_service.log_user_activity(
            user_id=test_user.id,
            activity_type=ActivityType.LOGIN,
        )
        
        json_content = report_service.generate_user_report_json(
            user_id=test_user.id,
            days=30
        )
        
        assert isinstance(json_content, str)
        assert "user_report" in json_content
        assert "activities" in json_content
    
    def test_generate_system_health_report_json(
        self,
        report_service: ReportGenerationService,
        analytics_service: AnalyticsService,
    ):
        """Test generating system health report JSON."""
        # Create system metrics
        analytics_service.log_system_metrics(
            uptime_percentage=99.9,
            error_rate=0.1,
        )
        
        json_content = report_service.generate_system_health_report_json(
            days=30
        )
        
        assert isinstance(json_content, str)
        assert "system_health_report" in json_content


# ============================================================================
# API Route Tests
# ============================================================================

class TestAnalyticsAPI:
    """Test analytics API endpoints."""
    
    def test_get_user_activities(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test GET /api/analytics/user/{user_id}/activities"""
        response = client.get(f"/api/analytics/user/{test_user.id}/activities")
        assert response.status_code in [200, 401]  # 401 if auth required
    
    def test_get_user_engagement(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test GET /api/analytics/user/{user_id}/engagement"""
        response = client.get(f"/api/analytics/user/{test_user.id}/engagement")
        assert response.status_code in [200, 401]
    
    def test_get_system_health(
        self,
        client: TestClient,
    ):
        """Test GET /api/analytics/system/health"""
        response = client.get("/api/analytics/system/health")
        assert response.status_code in [200, 401]
    
    def test_get_analytics_summary(
        self,
        client: TestClient,
    ):
        """Test GET /api/analytics/summary"""
        response = client.get("/api/analytics/summary")
        assert response.status_code in [200, 401]
    
    def test_get_top_users(
        self,
        client: TestClient,
    ):
        """Test GET /api/analytics/top-users"""
        response = client.get("/api/analytics/top-users")
        assert response.status_code in [200, 401]


# ============================================================================
# Integration Tests
# ============================================================================

class TestAnalyticsIntegration:
    """Integration tests for analytics system."""
    
    def test_full_activity_tracking_flow(
        self,
        analytics_service: AnalyticsService,
        dashboard_service: DashboardAggregationService,
        report_service: ReportGenerationService,
        test_user: User,
    ):
        """Test complete flow: log activities → aggregate → report."""
        # 1. Log activities
        for i in range(10):
            analytics_service.log_user_activity(
                user_id=test_user.id,
                activity_type=ActivityType.LOGIN if i % 2 == 0 else ActivityType.CREATE_TASK,
                success=i % 3 != 0,
            )
        
        # 2. Update engagement
        engagement = analytics_service.update_engagement_metrics(
            user_id=test_user.id
        )
        assert engagement is not None
        
        # 3. Get dashboard
        dashboard = dashboard_service.get_user_dashboard(
            user_id=test_user.id
        )
        assert dashboard["activity_summary"]["total_activities"] >= 10
        
        # 4. Generate report
        csv_report = report_service.generate_user_activity_csv(
            user_id=test_user.id
        )
        assert "Activity Type" in csv_report
    
    def test_multi_user_analytics(
        self,
        analytics_service: AnalyticsService,
        dashboard_service: DashboardAggregationService,
        test_user: User,
        db: Session,
    ):
        """Test analytics with multiple users."""
        # Create second user
        user2 = User(username="user2", email="user2@example.com")
        db.add(user2)
        db.commit()
        db.refresh(user2)
        
        # Log activities for both
        analytics_service.log_user_activity(
            user_id=test_user.id,
            activity_type=ActivityType.LOGIN,
        )
        analytics_service.log_user_activity(
            user_id=user2.id,
            activity_type=ActivityType.CREATE_PROJECT,
        )
        
        # Get team dashboard
        dashboard = dashboard_service.get_team_dashboard()
        assert "summary" in dashboard
        assert dashboard["summary"]["total_activities"] >= 2


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
