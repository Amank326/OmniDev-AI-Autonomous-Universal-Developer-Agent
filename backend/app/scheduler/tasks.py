"""
Celery tasks for background job processing.
"""

import os
from celery import Celery, shared_task

# Initialize Celery app
celery_app = Celery(
    'omnidev',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)


@shared_task
def send_notification(user_id: int, message: str):
    """Send a notification to a user."""
    print(f"Sending notification to user {user_id}: {message}")
    return f"Notification sent to user {user_id}"


@shared_task
def send_digest_notification(user_id: int):
    """Send a digest notification to a user."""
    print(f"Sending digest notification to user {user_id}")
    return f"Digest sent to user {user_id}"


@shared_task
def sync_external_data():
    """Sync data from external sources."""
    print("Syncing external data...")
    return "Data sync complete"


@shared_task
def cleanup_old_data():
    """Clean up old data from the database."""
    print("Cleaning up old data...")
    return "Cleanup complete"


@shared_task
def generate_report(report_type: str):
    """Generate a report."""
    print(f"Generating {report_type} report...")
    return f"Report generated: {report_type}"


@shared_task
def process_batch_job(job_id: int):
    """Process a batch job."""
    print(f"Processing batch job {job_id}...")
    return f"Batch job {job_id} completed"
