# Phase 6 Quick Reference

## 🚀 Setup (5 minutes)

```bash
# 1. Install dependencies
pip install celery>=5.3.0 redis>=5.0.0 apscheduler>=3.10.0

# 2. Start Redis
docker run -d -p 6379:6379 redis:latest
# OR: redis-server

# 3. Start Celery worker (new terminal)
celery -A app.celery_app worker -Q default,email,notifications,scheduled --loglevel=info

# 4. Start main app (your terminal)
python -m uvicorn app.main:app --reload

# Done! Ready to queue tasks
```

---

## 📧 Email Tasks

### Queue Verification Email
```python
from app.tasks.email import send_verification_email_task

task_id = send_verification_email_task.delay(
    recipient_email="user@example.com",
    verification_token="jwt_token_24hr",
    app_url="https://yourapp.com",
    user_id=1
)
```

### Queue Password Reset Email
```python
from app.tasks.email import send_password_reset_task

task_id = send_password_reset_task.delay(
    recipient_email="user@example.com",
    reset_token="jwt_token_1hr",
    app_url="https://yourapp.com",
    user_id=1
)
```

### Queue Generic Notification Email
```python
from app.tasks.email import send_notification_email_task

task_id = send_notification_email_task.delay(
    recipient_email="user@example.com",
    subject="Subject Line",
    title="Email Title",
    message="Email body text",
    action_url="https://yourapp.com/action",
    action_text="Click Here",
    user_id=1
)
```

### Queue Welcome Email
```python
from app.tasks.email import send_welcome_email_task

task_id = send_welcome_email_task.delay(
    recipient_email="newuser@example.com",
    username="John Doe",
    app_url="https://yourapp.com",
    user_id=1
)
```

### Queue Bulk Emails
```python
from app.tasks.email import send_bulk_emails_task

recipients = [
    {"email": "user1@example.com", "name": "User 1"},
    {"email": "user2@example.com", "name": "User 2"},
]

task_id = send_bulk_emails_task.delay(
    recipients=recipients,
    email_type="newsletter",
    subject="Our Newsletter"
)
```

---

## 🔔 Notification Tasks

### Queue Single Notification
```python
from app.tasks.notifications import create_notification_task

task_id = create_notification_task.delay(
    recipient_id=1,
    notification_type="task_assigned",
    title="New Task",
    message="You have been assigned a task",
    channels=["IN_APP", "EMAIL"],
    action_url="https://yourapp.com/tasks/123",
    action_text="View Task",
    priority="high"
)
```

### Queue Batch Notifications
```python
from app.tasks.notifications import batch_notifications_task

task_id = batch_notifications_task.delay(
    recipient_ids=[1, 2, 3, 4, 5],
    notification_type="announcement",
    title="Team Announcement",
    message="Important announcement",
    channels=["IN_APP", "EMAIL"],
    priority="normal"
)
```

### Queue Digest Notification
```python
from app.tasks.notifications import send_digest_notification_task

# Daily
task_id = send_digest_notification_task.delay(
    recipient_id=1,
    digest_type="daily"  # or "weekly", "monthly"
)
```

---

## 📊 Monitor Tasks

### Get Task Status
```python
from app.tasks.monitoring import monitoring_service

status = monitoring_service.get_task_status("task-id")
print(status)
# {'task_id': '...', 'status': 'SUCCESS', 'result': {...}}
```

### Get Active Tasks
```python
active = monitoring_service.get_active_tasks()
# {'worker1': [{'id': 'task-1', 'name': 'app.tasks.email...'}]}
```

### Get Worker Stats
```python
stats = monitoring_service.get_worker_stats()
# {'status': 'ok', 'workers': 3, 'worker_stats': {...}}
```

### Get System Health
```python
health = monitoring_service.get_health_status()
# {'status': 'healthy', 'workers': 3, 'active_tasks': 12}
```

### Retry Failed Task
```python
result = monitoring_service.retry_task("failed-task-id")
# {'status': 'success', 'message': 'Task marked for retry'}
```

### Revoke Task
```python
result = monitoring_service.revoke_task("task-id", terminate=True)
# {'status': 'success', 'message': 'Task revoked'}
```

---

## 🌐 API Endpoints

### Health & Stats
```bash
GET  /api/workers/health           # System health
GET  /api/workers/stats            # Worker statistics
GET  /api/queues                   # Queue stats
```

### Task Management
```bash
GET  /api/tasks                    # List tasks (active by default)
GET  /api/tasks?task_type=scheduled # List scheduled tasks
GET  /api/tasks/{task_id}          # Get task status
GET  /api/tasks/{task_id}/info     # Detailed task info
POST /api/tasks/{task_id}/retry    # Retry failed task
POST /api/tasks/{task_id}/revoke   # Revoke task
GET  /api/failed-tasks             # Dead letter queue
POST /api/tasks/purge              # Purge queue ⚠️
```

---

## ⏰ Schedule Periodic Tasks

### Schedule Daily Digest
```python
from app.scheduler.config import schedule_daily_digest

schedule_daily_digest(
    user_id=1,
    hour=9,        # 9 AM UTC
    minute=0
)
```

### Schedule Weekly Digest
```python
from app.scheduler.config import schedule_weekly_digest

schedule_weekly_digest(
    user_id=1,
    day_of_week=0,  # 0=Monday, 6=Sunday
    hour=9
)
```

### Schedule Monthly Digest
```python
from app.scheduler.config import schedule_monthly_digest

schedule_monthly_digest(
    user_id=1,
    day_of_month=1,
    hour=9
)
```

### Remove Schedule
```python
from app.scheduler.config import unschedule_digest

unschedule_digest(user_id=1, digest_type="daily")
```

---

## 🛠️ Common Commands

### Worker Management
```bash
# Start worker for all queues
celery -A app.celery_app worker --loglevel=info

# Start worker for specific queue
celery -A app.celery_app worker -Q email --loglevel=info

# Start multiple workers with auto-restart
supervisor # see supervisord config

# Start with debug logging
celery -A app.celery_app worker --loglevel=debug

# Check active tasks
celery -A app.celery_app inspect active

# Check worker stats
celery -A app.celery_app inspect stats

# Revoke all tasks
celery -A app.celery_app control shutdown
```

### Redis Commands
```bash
# Check Redis
redis-cli ping

# View keys
redis-cli keys '*'

# Flush all data (development only!)
redis-cli FLUSHALL

# Monitor activity
redis-cli MONITOR
```

---

## 🐛 Quick Troubleshooting

### Worker Not Processing Tasks
```bash
# Check if worker is running
celery -A app.celery_app inspect active

# Check worker health
celery -A app.celery_app inspect stats

# Check if Redis is connected
redis-cli ping

# Restart worker with debug logging
celery -A app.celery_app worker --loglevel=debug
```

### Task Stuck in PENDING
```python
# Check task exists
from app.tasks.monitoring import monitoring_service
status = monitoring_service.get_task_status("task-id")

# Revoke if stuck
monitoring_service.revoke_task("task-id", terminate=True)

# Check workers exist
stats = monitoring_service.get_worker_stats()
print(stats["workers"])  # Should be > 0
```

### Email Not Sending
```python
# Test email service
from app.email.service import email_service
result = email_service.send_verification_email(
    "test@example.com",
    "token",
    "http://localhost:3000"
)
print(result)  # Should be True
```

### High Memory Usage
```bash
# Reduce concurrency
celery -A app.celery_app worker --concurrency=2

# Enable task cleanup
celery -A app.celery_app worker --max-tasks-per-child=100
```

---

## 📁 File Structure

```
backend/
├── app/
│   ├── celery_app.py                  # Celery configuration
│   ├── tasks/
│   │   ├── __init__.py               # Task exports
│   │   ├── email.py                  # Email tasks (5 tasks)
│   │   ├── notifications.py          # Notification tasks (3 tasks)
│   │   └── monitoring.py             # Monitoring service
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── config.py                 # APScheduler setup
│   ├── api/
│   │   ├── routes.py                 # Existing routes
│   │   └── worker_routes.py          # Worker management (9 endpoints)
│   └── main.py                       # Updated for scheduler & routes
├── requirements.txt                  # +3 dependencies
└── tests/
    └── test_phase6_tasks.py          # 40+ tests
```

---

## 🎯 Quick Stats

| Metric | Count |
|--------|-------|
| Total Tasks | 8 (5 email + 3 notification) |
| API Endpoints | 9 |
| Monitoring Methods | 10+ |
| Test Cases | 40+ |
| Documentation Lines | 2,000+ |
| Total Phase 6 LOC | 3,000+ |

---

## 📚 Key Facts

- **Max Retries:** 3 (email/notifications)
- **Retry Backoff:** Exponential (60s, 120s, 240s)
- **Email Rate Limit:** 100/min
- **Notification Rate Limit:** 100/min
- **Bulk Rate Limit:** 50/min
- **Task Timeout:** 10 minutes (soft), 15 minutes (hard)
- **Result Expiry:** 1 hour
- **Queues:** 4 (default, email, notifications, scheduled)

---

## ✅ Checklist for Production

- [ ] Redis instance deployed
- [ ] Celery workers auto-restart configured
- [ ] Multiple workers for load distribution
- [ ] Logging aggregated to central system
- [ ] Monitoring and alerting setup
- [ ] Rate limits appropriate for scale
- [ ] Worker heartbeat monitoring enabled
- [ ] Dead letter queue inspection setup
- [ ] Backup for failed tasks
- [ ] Documentation accessible to team

---

## 🎓 Learn More

- Read `PHASE6_GUIDE.md` for comprehensive documentation
- Check `tests/test_phase6_tasks.py` for usage examples
- Review `app/celery_app.py` for configuration details

---

**Phase 6 Complete!** 🎉

