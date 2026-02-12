# Phase 6: Background Jobs & Task Queue
## Complete Implementation Guide

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Task Queue System](#task-queue-system)
5. [Email Tasks](#email-tasks)
6. [Notification Tasks](#notification-tasks)
7. [Task Monitoring](#task-monitoring)
8. [Scheduler Configuration](#scheduler-configuration)
9. [Worker Management](#worker-management)
10. [API Endpoints](#api-endpoints)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)
13. [Performance Tuning](#performance-tuning)

---

## 🎯 Overview

Phase 6 implements a complete background job and task queue system using Celery with Redis as the message broker. This enables asynchronous processing of long-running tasks such as email sending, notifications, and scheduled operations.

### Key Features

- **Asynchronous Task Processing**: Queue and process tasks in the background
- **Multiple Task Queues**: Separate queues for email, notifications, and scheduled tasks
- **Automatic Retries**: Configurable retry logic with exponential backoff
- **Rate Limiting**: Per-queue rate limits to prevent service overload
- **Task Monitoring**: Real-time monitoring of task status and worker health
- **Periodic Scheduling**: APScheduler integration for recurring tasks
- **Dead Letter Queue**: Failed tasks are logged for recovery
- **Comprehensive Logging**: Full audit trail of task execution

### Components Created

| File | Purpose | Status |
|------|---------|--------|
| `app/celery_app.py` | Celery configuration and initialization | ✅ |
| `app/tasks/email.py` | Email queue tasks (5 tasks) | ✅ |
| `app/tasks/notifications.py` | Notification queue tasks (3 tasks) | ✅ |
| `app/tasks/monitoring.py` | Task monitoring service | ✅ |
| `app/scheduler/config.py` | APScheduler configuration | ✅ |
| `app/api/worker_routes.py` | Worker management API endpoints | ✅ |
| `tests/test_phase6_tasks.py` | Comprehensive test suite | ✅ |

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Application                    │
│  ┌────────────────┐  ┌──────────────────────────┐  │
│  │ Email Routes   │  │ Notification Routes      │  │
│  │ (queue tasks)  │  │ (queue tasks)            │  │
│  └────────────────┘  └──────────────────────────┘  │
└──────────────┬────────────────────────┬─────────────┘
               │                        │
               ▼                        ▼
         ┌──────────────────────────────────┐
         │      Celery Task Queue           │
         │  ┌──────────┐  ┌──────────────┐ │
         │  │  Email   │  │ Notifications│ │
         │  │  Queue   │  │  Queue       │ │
         │  └──────────┘  └──────────────┘ │
         │  ┌──────────────────────────┐   │
         │  │     Scheduled Queue      │   │
         │  └──────────────────────────┘   │
         └──────────────┬───────────────────┘
                        │
          ┌─────────────┴──────────────┐
          ▼                            ▼
    ┌──────────────┐          ┌──────────────────┐
    │   Redis      │          │  Celery Workers  │
    │   Broker     │◄────────►│  (Process tasks) │
    └──────────────┘          └──────────────────┘
          │                            │
          │                            ▼
          │                   ┌──────────────┐
          │                   │ Email Service│
          │                   │ Notification │
          │                   │ Service      │
          │                   └──────────────┘
          │
          ▼
    ┌──────────────┐
    │ Task Status  │
    │ Result Cache │
    └──────────────┘
```

### Queue Types

1. **Default Queue**: General-purpose tasks
2. **Email Queue**: Email delivery tasks (100/min rate limit)
3. **Notifications Queue**: Real-time notifications (100/min rate limit)
4. **Scheduled Queue**: Periodic and scheduled tasks

### Retry Strategy

```
Task Execution
    ▼
Success? ──[Yes]──► Task Completed
    │
    [No] ──► Retry?
             │
             [Yes] ──► Wait (Exponential Backoff)
             │              │
             │              └─► Attempt Retry (max 3)
             │
             [No] ──► Log Error ──► Dead Letter Queue
```

**Backoff Configuration:**
- Initial delay: 60 seconds
- Exponential multiplier: 2x
- Max retries: 3
- Max delay: ~8 minutes

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install celery>=5.3.0 redis>=5.0.0 apscheduler>=3.10.0

# Start Redis server (required for Celery)
# Option A: Using Docker
docker run -d -p 6379:6379 redis:latest

# Option B: Using system Redis
redis-server
```

### 2. Start Celery Worker

```bash
# In a separate terminal, from project root
celery -A app.celery_app worker --loglevel=info

# Or with multiple queues
celery -A app.celery_app worker -Q default,email,notifications,scheduled --loglevel=info

# Or with multiple workers
celery -A app.celery_app worker -Q email --loglevel=info &
celery -A app.celery_app worker -Q notifications --loglevel=info &
celery -A app.celery_app worker -Q scheduled --loglevel=info &
```

### 3. Start Celery Beat (Scheduler)

```bash
# In another terminal
celery -A app.celery_app beat --loglevel=info
```

### 4. Run Application

```bash
# In main terminal
python -m uvicorn app.main:app --reload
```

### 5. Queue a Task

```python
from app.tasks.email import send_verification_email_task

# Queue task (returns immediately with task ID)
task_id = send_verification_email_task.delay(
    recipient_email="user@example.com",
    verification_token="token_abc123",
    app_url="http://localhost:3000",
    user_id=1
)

print(f"Task queued with ID: {task_id}")

# Check task status
from app.tasks.monitoring import monitoring_service

status = monitoring_service.get_task_status(str(task_id))
print(f"Status: {status}")
```

---

## 📧 Task Queue System

### Configuration (app/celery_app.py)

```python
from celery import Celery
import os

# Create Celery app
celery_app = Celery("omnidev_ai")

# Load configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Configure queues
celery_app.conf.task_routes = {
    'app.tasks.email.*': {'queue': 'email'},
    'app.tasks.notifications.*': {'queue': 'notifications'},
    'app.tasks.scheduler.*': {'queue': 'scheduled'},
}
```

### Custom Task Class

All tasks inherit from `CustomTask` which provides:

```python
class CustomTask(celery_app.Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.info(f"Task {task_id} retrying due to: {exc}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed permanently: {exc}")
    
    def on_success(self, result, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully")
```

### Environment Variables

```bash
# .env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 📧 Email Tasks

### Available Email Tasks

#### 1. send_verification_email_task

Queue a verification email with time-limited token.

```python
from app.tasks.email import send_verification_email_task

# Queue the task
task_id = send_verification_email_task.delay(
    recipient_email="user@example.com",
    verification_token="jwt_token_24hr",
    app_url="https://yourapp.com",
    user_id=1
)

# Parameters
# - recipient_email (str): User email address
# - verification_token (str): JWT token (24-hour expiry)
# - app_url (str): Application base URL
# - user_id (int): User ID for tracking

# Rate Limit: 100 emails/minute
# Max Retries: 3
# Timeout: 10 minutes
```

#### 2. send_password_reset_task

Queue a password reset email with secure token.

```python
from app.tasks.email import send_password_reset_task

task_id = send_password_reset_task.delay(
    recipient_email="user@example.com",
    reset_token="jwt_token_1hr",
    app_url="https://yourapp.com",
    user_id=1
)

# Parameters
# - recipient_email (str): User email address
# - reset_token (str): JWT token (1-hour expiry)
# - app_url (str): Application base URL
# - user_id (int): User ID for tracking

# Rate Limit: 100 emails/minute
# Max Retries: 3
# Timeout: 10 minutes
```

#### 3. send_notification_email_task

Queue a generic notification email.

```python
from app.tasks.email import send_notification_email_task

task_id = send_notification_email_task.delay(
    recipient_email="user@example.com",
    subject="Your Subject",
    title="Email Title",
    message="Email message content",
    action_url="https://yourapp.com/action",
    action_text="Click Here",
    user_id=1
)

# Rate Limit: 100 emails/minute
# Max Retries: 3
# Timeout: 10 minutes
```

#### 4. send_welcome_email_task

Queue a welcome email for new users.

```python
from app.tasks.email import send_welcome_email_task

task_id = send_welcome_email_task.delay(
    recipient_email="newuser@example.com",
    username="John Doe",
    app_url="https://yourapp.com",
    user_id=1
)

# Rate Limit: 100 emails/minute
# Max Retries: 3
# Timeout: 10 minutes
```

#### 5. send_bulk_emails_task

Queue bulk email delivery with progress tracking.

```python
from app.tasks.email import send_bulk_emails_task

recipients = [
    {"email": "user1@example.com", "name": "User 1"},
    {"email": "user2@example.com", "name": "User 2"},
    {"email": "user3@example.com", "name": "User 3"},
]

task_id = send_bulk_emails_task.delay(
    recipients=recipients,
    email_type="newsletter",
    subject="Our Newsletter",
    template_name="newsletter"
)

# Returns dict with:
# {
#   "successful": 3,
#   "failed": 0,
#   "total": 3,
#   "failed_recipients": []
# }

# Rate Limit: 50 batches/minute
# Max Retries: 3
# Timeout: 15 minutes
```

### Monitoring Email Tasks

```python
from app.tasks.monitoring import monitoring_service

# Get task status
status = monitoring_service.get_task_status("email-task-id")
print(status)
# {
#   "task_id": "abc123",
#   "status": "SUCCESS",
#   "result": {"sent": True},
#   "ready": True,
#   "successful": True
# }

# Get active email tasks
active = monitoring_service.get_active_tasks()
if "worker1" in active:
    email_tasks = [t for t in active["worker1"] 
                   if "email" in t.get("name", "")]
```

---

## 🔔 Notification Tasks

### Available Notification Tasks

#### 1. create_notification_task

Queue a notification for a single user with multi-channel delivery.

```python
from app.tasks.notifications import create_notification_task
from app.database.models import NotificationChannel

task_id = create_notification_task.delay(
    recipient_id=1,
    notification_type="task_assigned",
    title="New Task Assigned",
    message="You have been assigned a new task",
    channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
    action_url="https://yourapp.com/tasks/123",
    action_text="View Task",
    priority="high"
)

# Parameters
# - recipient_id (int): User ID
# - notification_type (str): Type of notification
# - title (str): Notification title
# - message (str): Notification message
# - channels (list): Delivery channels (IN_APP, EMAIL, SMS, PUSH)
# - action_url (str, optional): URL for action button
# - action_text (str, optional): Text for action button
# - priority (str): Priority level (low, normal, high, critical)

# Rate Limit: 100 notifications/minute
# Max Retries: 3
# Timeout: 10 minutes
```

#### 2. batch_notifications_task

Queue notifications for multiple users.

```python
from app.tasks.notifications import batch_notifications_task

task_id = batch_notifications_task.delay(
    recipient_ids=[1, 2, 3, 4, 5],
    notification_type="team_announcement",
    title="Team Meeting Today",
    message="Don't forget about the team meeting at 2 PM",
    channels=["IN_APP", "EMAIL"],
    action_url="https://yourapp.com/meetings/456",
    action_text="Join Meeting",
    priority="high"
)

# Returns dict with:
# {
#   "successful_recipients": [1, 2, 3, 4, 5],
#   "failed_recipients": [],
#   "total": 5,
#   "successful": 5,
#   "failed": 0
# }

# Rate Limit: 50 batches/minute
# Max Retries: 3
# Timeout: 15 minutes
```

#### 3. send_digest_notification_task

Queue a periodic digest notification.

```python
from app.tasks.notifications import send_digest_notification_task

# Daily digest
task_id = send_digest_notification_task.delay(
    recipient_id=1,
    digest_type="daily"  # or "weekly", "monthly"
)

# This task:
# 1. Collects unread notifications since last digest
# 2. Groups by category
# 3. Creates summary notification
# 4. Clears unread flag
# 5. Sends via configured channels

# Rate Limit: 20 digests/minute
# Max Retries: 2
# Timeout: 30 minutes
```

### Monitoring Notification Tasks

```python
from app.tasks.monitoring import monitoring_service

# Get scheduled digests
scheduled = monitoring_service.get_scheduled_tasks()

# Get all task info
info = monitoring_service.get_task_info("notification-task-id")
```

---

## 📊 Task Monitoring

### Monitoring Service (app/tasks/monitoring.py)

The `TaskMonitoringService` provides comprehensive task status tracking.

```python
from app.tasks.monitoring import monitoring_service

# Get task status
status = monitoring_service.get_task_status("task_id")

# Get active tasks
active = monitoring_service.get_active_tasks()
# Returns: {"worker_name": [{"id": "task_1", "name": "task.name", ...}]}

# Get scheduled tasks
scheduled = monitoring_service.get_scheduled_tasks()

# Get reserved tasks (pre-fetched by worker)
reserved = monitoring_service.get_reserved_tasks()

# Get worker statistics
stats = monitoring_service.get_worker_stats()
# {
#   "status": "ok",
#   "workers": 3,
#   "worker_stats": {
#     "worker1": {
#       "pool": {"max-concurrency": 4},
#       "total": 1000,
#       "completed": 950,
#       "failed": 50
#     }
#   }
# }

# Get queue statistics
queues = monitoring_service.get_queue_stats()

# Retry a failed task
result = monitoring_service.retry_task("failed_task_id")

# Revoke a task (stop execution)
result = monitoring_service.revoke_task("task_id", terminate=True)

# Get comprehensive task information
info = monitoring_service.get_task_info("task_id")

# Get overall system health
health = monitoring_service.get_health_status()
# {
#   "status": "healthy",
#   "workers": 3,
#   "active_tasks": 12,
#   "scheduled_tasks": 45,
#   "timestamp": "2024-01-15T10:30:00Z"
# }
```

### Task Status States

```
PENDING
    ▼
STARTED
    ▼
PROGRESS (optional)
    ▼
SUCCESS or FAILURE or RETRY or REVOKED
```

| Status | Meaning |
|--------|---------|
| PENDING | Task is queued, waiting for execution |
| STARTED | Task is currently executing |
| SUCCESS | Task completed successfully |
| FAILURE | Task failed permanently (after retries) |
| RETRY | Task is being retried |
| REVOKED | Task was manually revoked |

---

## ⏰ Scheduler Configuration

### APScheduler Setup (app/scheduler/config.py)

```python
from app.scheduler.config import (
    scheduler,
    schedule_daily_digest,
    schedule_weekly_digest,
    schedule_monthly_digest,
    start_scheduler,
    stop_scheduler
)

# Schedule daily digest for user
schedule_daily_digest(
    user_id=1,
    hour=9,      # 9 AM UTC
    minute=0
)

# Schedule weekly digest (Monday at 9 AM)
schedule_weekly_digest(
    user_id=1,
    day_of_week=0,  # 0=Monday, 6=Sunday
    hour=9
)

# Schedule monthly digest (1st of month at 9 AM)
schedule_monthly_digest(
    user_id=1,
    day_of_month=1,
    hour=9
)

# Get all scheduled jobs
jobs = scheduler.get_jobs()

# Remove schedule
unschedule_digest(user_id=1, digest_type="daily")
```

### Integration with User Preferences

```python
# In user preferences model
class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Email preferences
    send_daily_digest = Column(Boolean, default=True)
    send_weekly_digest = Column(Boolean, default=False)
    send_monthly_digest = Column(Boolean, default=False)
    
    # Digest time preferences
    digest_time_hour = Column(Integer, default=9)
    digest_time_minute = Column(Integer, default=0)
    digest_day_of_week = Column(Integer, default=0)  # For weekly
    digest_day_of_month = Column(Integer, default=1)  # For monthly

# In user update handler
def update_user_digests(user_id, preferences):
    from app.scheduler.config import (
        schedule_daily_digest, 
        schedule_weekly_digest,
        unschedule_digest
    )
    
    if preferences.send_daily_digest:
        schedule_daily_digest(
            user_id,
            hour=preferences.digest_time_hour,
            minute=preferences.digest_time_minute
        )
    else:
        unschedule_digest(user_id, "daily")
    
    if preferences.send_weekly_digest:
        schedule_weekly_digest(
            user_id,
            day_of_week=preferences.digest_day_of_week,
            hour=preferences.digest_time_hour
        )
    else:
        unschedule_digest(user_id, "weekly")
```

---

## 🛠️ Worker Management

### API Endpoints

Base URL: `/api`

#### Get System Health

```http
GET /api/workers/health
```

Response:
```json
{
  "status": "healthy",
  "workers": 3,
  "active_tasks": 12,
  "scheduled_tasks": 45,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Get Worker Statistics

```http
GET /api/workers/stats
```

Response:
```json
{
  "status": "ok",
  "workers": 3,
  "worker_stats": {
    "worker1@hostname": {
      "pool": {
        "max-concurrency": 4,
        "processes": 2
      },
      "total": 1000,
      "completed": 950,
      "failed": 50
    }
  }
}
```

#### List Tasks

```http
GET /api/tasks?task_type=active
```

Query Parameters:
- `task_type`: `active` | `scheduled` | `reserved` | `all` (default: active)

Response (for active):
```json
{
  "type": "active",
  "tasks": {
    "worker1@hostname": [
      {
        "id": "abc-123",
        "name": "app.tasks.email.send_verification_email_task",
        "args": ["user@example.com"],
        "kwargs": {}
      }
    ]
  }
}
```

#### Get Task Status

```http
GET /api/tasks/{task_id}
```

Response:
```json
{
  "task_id": "abc-123",
  "status": "SUCCESS",
  "result": {"sent": true},
  "error": null,
  "ready": true,
  "successful": true,
  "failed": false
}
```

#### Get Task Info

```http
GET /api/tasks/{task_id}/info
```

Response:
```json
{
  "task_id": "abc-123",
  "status": "SUCCESS",
  "ready": true,
  "successful": true,
  "failed": false,
  "result": {"sent": true},
  "info": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Retry Failed Task

```http
POST /api/tasks/{task_id}/retry
```

Response:
```json
{
  "status": "success",
  "message": "Task marked for retry",
  "task_id": "abc-123"
}
```

#### Revoke Task

```http
POST /api/tasks/{task_id}/revoke?terminate=false
```

Query Parameters:
- `terminate`: `true` to force-kill running task, `false` to prevent queued execution

Response:
```json
{
  "status": "success",
  "message": "Task revoked (terminate=false)",
  "task_id": "abc-123"
}
```

#### Get Queue Statistics

```http
GET /api/queues
```

Response:
```json
{
  "queues": {
    "default": 5,
    "email": 120,
    "notifications": 45,
    "scheduled": 2
  }
}
```

#### Get Failed Tasks

```http
GET /api/failed-tasks?limit=100
```

Response:
```json
{
  "failed_tasks": [
    {
      "task_id": "failed-1",
      "task_name": "app.tasks.email.send_bulk_emails_task",
      "error": "SMTPException: Connection refused",
      "timestamp": "2024-01-15T10:20:00Z"
    }
  ],
  "count": 1
}
```

#### Purge Queue

```http
POST /api/tasks/purge?queue_name=default
```

⚠️ **WARNING**: This is destructive - all queued tasks will be deleted.

---

## 📤 Deployment

### Docker Deployment

#### Dockerfile for Celery Worker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run Celery worker
CMD ["celery", "-A", "app.celery_app", "worker", \
     "-Q", "default,email,notifications,scheduled", \
     "--loglevel=info", \
     "--concurrency=4"]
```

#### Docker Compose (with Redis)

```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  worker_email:
    build: .
    command: celery -A app.celery_app worker -Q email --loglevel=info
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app

  worker_notifications:
    build: .
    command: celery -A app.celery_app worker -Q notifications --loglevel=info
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app

volumes:
  redis_data:
```

### Production Checklist

- [ ] Redis instance deployed and secured
- [ ] Multiple Celery workers configured
- [ ] Worker auto-restart configured (supervisor/systemd)
- [ ] Logging aggregated to central system
- [ ] Monitoring and alerts configured
- [ ] Task TTL configured (task results expire)
- [ ] Worker heartbeat monitoring enabled
- [ ] Dead letter queue inspection setup
- [ ] Rate limits appropriate for scale
- [ ] Retry logic tested under load

---

## 🐛 Troubleshooting

### Redis Connection Issues

```python
# Check Redis connectivity
import redis
r = redis.from_url("redis://localhost:6379/0")
r.ping()  # Should return True

# In Celery
celery_app.broker_connection().connect()
```

### Worker Not Processing Tasks

```bash
# Check worker status
celery -A app.celery_app inspect active

# Check worker health
celery -A app.celery_app inspect stats

# Look for error logs
celery -A app.celery_app worker --loglevel=debug
```

### Task Stuck in PENDING

```python
from app.tasks.monitoring import monitoring_service

# Get task status
status = monitoring_service.get_task_status("task_id")
print(status)  # Check if task exists

# If task is stuck, revoke it
monitoring_service.revoke_task("task_id", terminate=True)

# Check if workers are running
stats = monitoring_service.get_worker_stats()
print(stats["workers"])  # Should be > 0
```

### High Memory Usage

```bash
# Reduce worker concurrency
celery -A app.celery_app worker --concurrency=2

# Enable worker max-tasks-per-child
celery -A app.celery_app worker --max-tasks-per-child=100

# Monitor memory
celery -A app.celery_app inspect active
```

### Email Not Sending

```python
# Check email task logs
# 1. Verify email service is configured
# 2. Check email_service.send_*() methods exist
# 3. Verify SMTP credentials

# Test email service
from app.email.service import email_service
result = email_service.send_verification_email(
    "test@example.com",
    "token",
    "http://localhost:3000"
)
print(result)  # Should be True
```

### Tasks Timing Out

```python
# Increase timeout for long-running tasks
@celery_app.task(soft_time_limit=300, time_limit=600)
def long_running_task():
    # 5 minutes soft limit, 10 minutes hard limit
    pass

# Or adjust in task definition
send_bulk_emails_task.apply_async(
    args=(recipients,),
    time_limit=600,  # 10 minutes
    soft_time_limit=300  # 5 minutes
)
```

---

## ⚙️ Performance Tuning

### Worker Configuration

```bash
# Optimal for I/O-bound tasks (email, notifications)
celery -A app.celery_app worker \
  --concurrency=8 \
  --prefetch-multiplier=4 \
  --max-tasks-per-child=1000 \
  --pool=prefork

# Optimal for CPU-bound tasks
celery -A app.celery_app worker \
  --concurrency=4 \
  --prefetch-multiplier=1 \
  --max-tasks-per-child=100 \
  --pool=prefork
```

### Redis Configuration

```python
# app/celery_app.py

# Connection pooling
broker_pool_limit = 10
broker_connection_max_retries = 10

# Result backend tuning
result_expires = 3600  # 1 hour
result_backend_transport_options = {
    'master_name': 'mymaster',
    'retry_on_timeout': True,
}

# Task time limits
task_soft_time_limit = 600  # 10 minutes
task_time_limit = 900  # 15 minutes
```

### Rate Limiting Tuning

```python
# Adjust in task definitions
@celery_app.task(
    rate_limit="100/m",  # 100 per minute
    time_limit=600,
    soft_time_limit=300,
)
def rate_limited_task():
    pass
```

### Monitoring Queue Depths

```python
from app.tasks.monitoring import monitoring_service
import time

def monitor_queue_health():
    while True:
        stats = monitoring_service.get_queue_stats()
        
        for queue_name, depth in stats.items():
            if depth > 1000:
                logger.warning(f"Queue {queue_name} depth: {depth}")
        
        time.sleep(60)  # Check every minute
```

---

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryproject.io/)
- [Redis Documentation](https://redis.io/documentation)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Flower - Celery Monitoring UI](https://flower.readthedocs.io/)

---

## ✅ Phase 6 Completion

Phase 6 is now complete with:

✅ Celery + Redis task queue infrastructure
✅ Email queue tasks (5 tasks)
✅ Notification queue tasks (3 tasks)
✅ Task monitoring service
✅ Worker management API endpoints
✅ APScheduler for periodic tasks
✅ Comprehensive error handling
✅ Complete documentation
✅ Full test suite

**Next Phase:** Phase 7 - Analytics & Reporting

