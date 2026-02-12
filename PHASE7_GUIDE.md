# Phase 7: Analytics & Reporting Guide

## Overview

Phase 7 implements comprehensive analytics, reporting, and metrics tracking for OmniDev AI. This phase provides:

- **Activity Tracking**: Log all user actions with context and metadata
- **Metrics Collection**: Track task, project, and system-level metrics
- **Engagement Scoring**: Dynamic user engagement calculation (0-100)
- **Dashboard Aggregation**: User, project, and team-wide insights
- **Report Generation**: CSV and JSON export capabilities
- **Real-Time Streaming**: WebSocket support for live dashboard updates
- **Email Distribution**: Automated report delivery via task queue
- **Audit Logging**: Compliance-ready audit trail with before/after values

## Architecture

### Database Models

#### 1. UserActivity
Tracks all user actions in the system.

```python
from app.analytics import UserActivity, ActivityType

# Log activity
activity = UserActivity(
    user_id=1,
    activity_type=ActivityType.LOGIN,
    description="User logged in",
    project_id=None,
    task_id=None,
    success=True,
    duration_ms=250,
    metadata={"browser": "Chrome"},
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
)
db.add(activity)
db.commit()
```

**Activity Types** (20 types):
- `LOGIN` - User login
- `LOGOUT` - User logout
- `CREATE_PROJECT` - Project creation
- `UPDATE_PROJECT` - Project update
- `DELETE_PROJECT` - Project deletion
- `CREATE_TASK` - Task creation
- `UPDATE_TASK` - Task update
- `COMPLETE_TASK` - Task completion
- `DELETE_TASK` - Task deletion
- `RUN_AGENT` - Agent execution
- `AGENT_SUCCESS` - Agent success
- `AGENT_ERROR` - Agent error
- `API_CALL` - API call
- `API_ERROR` - API error
- `COMMENT` - User comment
- `MENTION` - User mention
- `SHARE` - Resource share
- `DOWNLOAD` - File download
- `UPLOAD` - File upload
- `EXPORT` - Data export

#### 2. TaskMetrics
Records per-task metrics over time.

```python
from app.analytics import TaskMetrics, MetricType

metric = TaskMetrics(
    task_id=1,
    project_id=1,
    metric_type=MetricType.TASK_COMPLETION_TIME,
    value=3600,  # in seconds
    unit="seconds",
    period_start=datetime.utcnow() - timedelta(hours=1),
    period_end=datetime.utcnow(),
)
db.add(metric)
db.commit()
```

**Metric Types** (10 types):
- `TASK_COMPLETION_TIME` - Time to complete task
- `ERROR_RATE` - Error percentage
- `SUCCESS_RATE` - Success percentage
- `API_RESPONSE_TIME` - API latency
- `DATABASE_QUERY_TIME` - Query duration
- `AGENT_EXECUTION_TIME` - Agent runtime
- `MEMORY_USAGE` - Memory consumption
- `CPU_USAGE` - CPU utilization
- `THROUGHPUT` - Tasks per second
- `QUEUE_DEPTH` - Pending tasks

#### 3. ProjectMetrics
Aggregated metrics for a project.

```python
from app.analytics import ProjectMetrics

metrics = ProjectMetrics(
    project_id=1,
    total_tasks=100,
    completed_tasks=75,
    completion_rate=75.0,
    success_rate=95.5,
    contributor_count=5,
    avg_completion_time_hours=2.5,
)
db.add(metrics)
db.commit()
```

#### 4. SystemMetrics
System health snapshot.

```python
from app.analytics import SystemMetrics

metrics = SystemMetrics(
    uptime_percentage=99.99,
    error_rate=0.01,
    api_response_time_ms=245,
    database_query_time_ms=50,
    queue_depth=5,
    active_workers=3,
    total_requests=1000000,
    failed_requests=100,
)
db.add(metrics)
db.commit()
```

#### 5. EngagementMetrics
User engagement scoring.

```python
from app.analytics import EngagementMetrics

metrics = EngagementMetrics(
    user_id=1,
    login_count=45,
    tasks_completed=25,
    projects_created=3,
    comments_made=150,
    mentions_received=20,
    overall_engagement_score=75.5,
    is_active=True,
    last_login=datetime.utcnow(),
)
db.add(metrics)
db.commit()
```

**Engagement Score Formula**:
```
score = (login_count × 2) + (tasks_completed × 5) + (projects_created × 10) + 
        (comments_made × 1) + (mentions_received × 3)
capped at 100
is_active = score >= 30
```

#### 6. AuditLog
Compliance audit trail.

```python
from app.analytics import AuditLog

log = AuditLog(
    user_id=1,
    action="UPDATE",
    resource_type="Project",
    resource_id=1,
    status="success",
    old_values={"title": "Old Title"},
    new_values={"title": "New Title"},
    error_message=None,
)
db.add(log)
db.commit()
```

## Services

### AnalyticsService

Main service for logging activities and metrics.

```python
from app.analytics import analytics_service, ActivityType

# Log user activity
activity = analytics_service.log_user_activity(
    user_id=1,
    activity_type=ActivityType.LOGIN,
    description="User logged in",
    project_id=None,
    task_id=None,
    success=True,
    duration_ms=250,
    metadata={"browser": "Chrome"},
    ip_address="192.168.1.1",
)

# Log task metric
metric = analytics_service.log_task_metric(
    task_id=1,
    project_id=1,
    metric_type=MetricType.TASK_COMPLETION_TIME,
    value=3600,
    unit="seconds",
)

# Update engagement metrics
engagement = analytics_service.update_engagement_metrics(user_id=1)

# Log system metrics
analytics_service.log_system_metrics(
    uptime_percentage=99.9,
    error_rate=0.1,
    api_response_time_ms=250,
    queue_depth=5,
    active_workers=3,
)

# Get user activities
activities = analytics_service.get_user_activities(
    user_id=1,
    days=7,
    limit=100,
)

# Log audit event
analytics_service.log_audit(
    user_id=1,
    action="CREATE",
    resource_type="Project",
    resource_id=1,
    status="success",
    new_values={"title": "New Project"},
)
```

### DashboardAggregationService

Aggregates data for dashboard visualization.

```python
from app.analytics import dashboard_service

# User dashboard
user_dashboard = dashboard_service.get_user_dashboard(
    user_id=1,
    days=30,
)
# Returns: {
#   "engagement_score": 75.5,
#   "activity_summary": {...},
#   "recent_activities": [...],
#   "projects_created": 3,
#   "tasks_completed": 25,
#   "activity_trend": {...},
#   "last_active": "2024-01-15T10:30:00",
# }

# Project dashboard
project_dashboard = dashboard_service.get_project_dashboard(
    project_id=1,
    days=30,
)
# Returns: {
#   "metrics": {...},
#   "recent_activities": [...],
#   "top_contributors": [...],
#   "progress_trend": {...},
#   "task_metrics": [...],
# }

# Team dashboard
team_dashboard = dashboard_service.get_team_dashboard(
    days=30,
    limit=10,
)
# Returns: {
#   "summary": {
#     "total_activities": 1500,
#     "success_rate": 95.5,
#     "active_users": 25,
#     "active_projects": 8,
#   },
#   "top_projects": [...],
#   "top_users": [...],
#   "activity_trend": {...},
#   "activity_breakdown": {...},
# }
```

### ReportGenerationService

Generates reports in various formats.

```python
from app.analytics import report_service

# User activity CSV
csv_report = report_service.generate_user_activity_csv(
    user_id=1,
    days=30,
)

# Engagement report CSV
csv_report = report_service.generate_engagement_report_csv(
    days=30,
)

# Project metrics CSV
csv_report = report_service.generate_project_metrics_csv(
    project_id=1,
    days=30,
)

# Audit log CSV
csv_report = report_service.generate_audit_log_csv(
    days=30,
    limit=10000,
)

# User report JSON
json_report = report_service.generate_user_report_json(
    user_id=1,
    days=30,
)

# Project report JSON
json_report = report_service.generate_project_report_json(
    project_id=1,
    days=30,
)

# System health JSON
json_report = report_service.generate_system_health_report_json(
    days=30,
)
```

### RealtimeMetricsService

Streams real-time metrics via WebSocket.

```python
from app.realtime.metrics import (
    realtime_metrics_service,
    MetricsStreamType,
    MetricsStreamFilter,
)

# Register connection
realtime_metrics_service.register_connection(connection_id="client-1")

# Subscribe to stream
filter = MetricsStreamFilter(
    stream_type=MetricsStreamType.SYSTEM_HEALTH,
    interval_seconds=5,
)
realtime_metrics_service.subscribe(connection_id="client-1", stream_filter=filter)

# Stream metrics (async)
await realtime_metrics_service.stream_metrics(
    connection_id="client-1",
    stream_filter=filter,
    send_callback=websocket.send_text,
)

# Unsubscribe
realtime_metrics_service.unsubscribe(
    connection_id="client-1",
    stream_type=MetricsStreamType.SYSTEM_HEALTH,
)

# Unregister connection
realtime_metrics_service.unregister_connection(connection_id="client-1")
```

## API Endpoints

### GET /api/analytics/user/{user_id}/activities
Get user activity history.

**Query Parameters**:
- `days`: 1-365 (default: 30)
- `limit`: 1-1000 (default: 100)

**Response**:
```json
{
  "user_id": 1,
  "period_days": 30,
  "total_activities": 150,
  "activities": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:00",
      "activity_type": "login",
      "description": "User logged in",
      "success": true,
      "duration_ms": 250
    }
  ]
}
```

### GET /api/analytics/project/{project_id}/activities
Get project activity history.

**Query Parameters**:
- `days`: 1-365 (default: 30)
- `limit`: 1-1000 (default: 100)

**Response**: Similar to user activities endpoint.

### GET /api/analytics/user/{user_id}/engagement
Get user engagement metrics.

**Response**:
```json
{
  "user_id": 1,
  "engagement_score": 75.5,
  "is_active": true,
  "login_count": 45,
  "tasks_completed": 25,
  "projects_created": 3,
  "comments_made": 150,
  "mentions_received": 20,
  "last_login": "2024-01-15T10:30:00"
}
```

### GET /api/analytics/project/{project_id}/metrics
Get project performance metrics.

**Response**:
```json
{
  "project_id": 1,
  "total_tasks": 100,
  "completed_tasks": 75,
  "completion_rate": 75.0,
  "success_rate": 95.5,
  "contributor_count": 5,
  "avg_completion_time_hours": 2.5
}
```

### GET /api/analytics/system/health
Get current system health.

**Response**:
```json
{
  "uptime_percentage": 99.99,
  "error_rate": 0.01,
  "api_response_time_ms": 245,
  "database_query_time_ms": 50,
  "queue_depth": 5,
  "active_workers": 3,
  "timestamp": "2024-01-15T10:30:00"
}
```

### GET /api/analytics/summary
Get overall system summary.

**Query Parameters**:
- `days`: 1-365 (default: 7)

**Response**:
```json
{
  "period_days": 7,
  "total_activities": 1500,
  "success_rate": 95.5,
  "active_users": 25,
  "active_projects": 8,
  "top_projects": [...],
  "top_users": [...]
}
```

### GET /api/analytics/audit-log
Get audit log with filtering.

**Query Parameters**:
- `days`: 1-365 (default: 30)
- `limit`: 1-1000 (default: 100)
- `action`: Filter by action (optional)
- `user_id`: Filter by user (optional)
- `status`: Filter by status (optional)

**Response**:
```json
{
  "period_days": 30,
  "total_entries": 500,
  "logs": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:00",
      "user_id": 1,
      "action": "UPDATE",
      "resource_type": "Project",
      "resource_id": 1,
      "status": "success"
    }
  ]
}
```

### GET /api/analytics/top-users
Get top users by engagement.

**Query Parameters**:
- `limit`: 10-100 (default: 10)

**Response**:
```json
{
  "period_days": 30,
  "total_users": 25,
  "top_users": [
    {
      "user_id": 1,
      "username": "alice",
      "engagement_score": 85.5,
      "activities_count": 250
    }
  ]
}
```

### GET /api/analytics/activity-types
Get activity summary by type.

**Query Parameters**:
- `days`: 1-365 (default: 30)

**Response**:
```json
{
  "period_days": 30,
  "total_activities": 1500,
  "breakdown": {
    "login": 300,
    "create_project": 50,
    "create_task": 600,
    "complete_task": 550
  }
}
```

## Email Tasks

### send_user_analytics_report_task
Send user analytics report via email.

```python
from app.tasks.email import send_user_analytics_report_task

task_result = send_user_analytics_report_task.delay(
    user_id=1,
    recipient_email="user@example.com",
    report_format="json",  # or "csv"
    days=30,
)
```

### send_project_analytics_report_task
Send project analytics report to team members.

```python
from app.tasks.email import send_project_analytics_report_task

task_result = send_project_analytics_report_task.delay(
    project_id=1,
    recipient_emails=["user1@example.com", "user2@example.com"],
    report_format="csv",
    days=30,
)
```

### send_team_analytics_summary_task
Send team-wide analytics summary to admin.

```python
from app.tasks.email import send_team_analytics_summary_task

task_result = send_team_analytics_summary_task.delay(
    admin_email="admin@example.com",
    days=7,
)
```

## WebSocket Streaming

### Real-Time Metrics via WebSocket

Connect to WebSocket endpoint: `/ws/metrics/{connection_id}`

**Subscribe to System Health**:
```json
{
  "action": "subscribe",
  "stream_type": "system_health",
  "interval_seconds": 5
}
```

**Subscribe to User Activity**:
```json
{
  "action": "subscribe",
  "stream_type": "user_activity",
  "user_id": 1,
  "interval_seconds": 10
}
```

**Received Metrics**:
```json
{
  "stream_type": "system_health",
  "timestamp": "2024-01-15T10:30:00",
  "metrics": {
    "uptime_percentage": 99.99,
    "error_rate": 0.01,
    "api_response_time_ms": 245
  }
}
```

## Usage Examples

### Complete Analytics Flow

```python
from app.analytics import (
    analytics_service, dashboard_service, 
    report_service, ActivityType
)
from app.tasks.email import send_user_analytics_report_task

# 1. Log user activities
analytics_service.log_user_activity(
    user_id=1,
    activity_type=ActivityType.LOGIN,
    description="User logged in",
    success=True,
)

# 2. Log task metric
analytics_service.log_task_metric(
    task_id=1,
    project_id=1,
    metric_type=MetricType.TASK_COMPLETION_TIME,
    value=3600,
    unit="seconds",
)

# 3. Update engagement metrics
engagement = analytics_service.update_engagement_metrics(user_id=1)
print(f"User engagement score: {engagement.overall_engagement_score}")

# 4. Get user dashboard
dashboard = dashboard_service.get_user_dashboard(user_id=1)
print(f"Recent activities: {dashboard['recent_activities']}")

# 5. Generate report
json_report = report_service.generate_user_report_json(user_id=1)

# 6. Send report via email
task_result = send_user_analytics_report_task.delay(
    user_id=1,
    recipient_email="user@example.com",
    report_format="json",
    days=30,
)
```

### Dashboard Updates

```python
from app.analytics import dashboard_service

# Get team overview
team_dashboard = dashboard_service.get_team_dashboard(days=30, limit=10)

# Extract key metrics
summary = team_dashboard['summary']
print(f"Team size: {summary['active_users']}")
print(f"Success rate: {summary['success_rate']}%")
print(f"Active projects: {summary['active_projects']}")

# Show top performers
for user in team_dashboard['top_users']:
    print(f"{user['username']}: {user['engagement_score']} score")
```

### Compliance Audit

```python
from app.analytics import report_service

# Generate audit log
audit_csv = report_service.generate_audit_log_csv(days=90, limit=50000)

# Save to file
with open("audit_log.csv", "w") as f:
    f.write(audit_csv)

# Send to compliance team
send_email_task.delay(
    to_email="compliance@company.com",
    subject="Q1 Audit Log",
    attachment=audit_csv,
)
```

## Metrics Collection Patterns

### Automatic Activity Logging

In your request handlers:

```python
from fastapi import APIRouter, Request
from app.analytics import analytics_service, ActivityType

router = APIRouter()

@router.post("/projects/")
async def create_project(project: ProjectCreate, request: Request):
    # ... create project logic ...
    
    # Log activity
    analytics_service.log_user_activity(
        user_id=current_user.id,
        activity_type=ActivityType.CREATE_PROJECT,
        project_id=project.id,
        success=True,
        metadata={
            "title": project.title,
            "ip": request.client.host,
        },
    )
    
    return project
```

### Periodic System Metrics

In your scheduler:

```python
from app.scheduler.config import scheduler
from app.analytics import analytics_service
import psutil

@scheduler.scheduled_job("interval", minutes=5)
def collect_system_metrics():
    analytics_service.log_system_metrics(
        uptime_percentage=99.9,
        error_rate=0.01,
        api_response_time_ms=245,
        queue_depth=get_queue_depth(),
        active_workers=get_worker_count(),
    )
```

### Task Performance Tracking

After task completion:

```python
from app.analytics import analytics_service, MetricType
import time

start_time = time.time()
# ... execute task ...
end_time = time.time()

duration_ms = (end_time - start_time) * 1000
analytics_service.log_task_metric(
    task_id=task.id,
    project_id=task.project_id,
    metric_type=MetricType.TASK_COMPLETION_TIME,
    value=duration_ms,
    unit="milliseconds",
)
```

## Troubleshooting

### Activity Not Showing in Dashboard

1. Check that `log_user_activity()` is being called
2. Verify user_id exists in database
3. Check the `timestamp` is recent
4. Ensure metrics are within the query `days` range

### Engagement Score Not Updating

1. Verify activities are being logged
2. Check `update_engagement_metrics()` was called
3. Ensure formula calculation: (login × 2) + (tasks × 5) + (projects × 10) + (comments × 1) + (mentions × 3)
4. Score is capped at 100

### Reports Not Generating

1. Check database has data in analytics tables
2. Verify dates/days parameter is correct
3. Ensure required fields are populated
4. Check for database connection errors in logs

### WebSocket Not Streaming

1. Verify connection is registered with `register_connection()`
2. Check stream_type is valid: system_health, user_activity, engagement_metrics, dashboard_summary
3. Ensure interval_seconds is between 1-300
4. Check WebSocket connection is open

## Performance Considerations

- **Indexes**: All timestamp fields are indexed for fast queries
- **Aggregation**: Use dashboard_service for pre-aggregated data
- **Limits**: API endpoints limit results to 1000 rows
- **Archival**: Consider archiving old analytics after 90 days
- **WebSocket**: Limit concurrent connections and update intervals

## Future Enhancements

- [ ] Advanced filtering and search
- [ ] Custom dashboard widgets
- [ ] Predictive analytics
- [ ] Anomaly detection
- [ ] Scheduled report generation
- [ ] Multi-tenancy support
- [ ] Analytics data export/import
- [ ] Custom metrics definition

## Files Created

1. **app/analytics/models.py** - Database models (6 models, 2 enums)
2. **app/analytics/service.py** - Analytics service (13 methods)
3. **app/analytics/aggregation.py** - Dashboard service (3 dashboards)
4. **app/analytics/reports.py** - Report generation (CSV + JSON)
5. **app/realtime/metrics.py** - WebSocket streaming service
6. **app/api/analytics_routes.py** - REST API endpoints (11 endpoints)
7. **app/tasks/email.py** - Updated with 3 report email tasks
8. **app/main.py** - Updated to include analytics routes
9. **tests/test_phase7_analytics.py** - 50+ test cases

## Integration Checklist

- [x] Database models created and migrated
- [x] Analytics service implemented
- [x] Dashboard aggregation working
- [x] API routes registered
- [x] Report generation available
- [x] WebSocket streaming service ready
- [x] Email tasks for report distribution
- [x] Main app integration complete
- [x] Comprehensive test suite
- [x] Full documentation

---

**Phase 7 Complete**: Analytics & Reporting system fully integrated and operational.
