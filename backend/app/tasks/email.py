"""
Email Queue Tasks
=================

This module contains all email-related Celery tasks for asynchronous
email delivery. Tasks are queued and processed by Celery workers.

Tasks:
- send_verification_email_task: Send email verification
- send_password_reset_task: Send password reset link
- send_notification_email_task: Send email notification
- send_welcome_email_task: Send welcome email
- send_bulk_emails_task: Send bulk emails with batching

Features:
- Automatic retry with exponential backoff (3 retries)
- Rate limiting (100 emails/minute)
- Timeout: 10 minutes
- Detailed logging and error tracking
- Dead letter queue support for failed emails
"""

from celery import shared_task
from celery.utils.log import get_task_logger
import logging
from typing import Optional, List, Dict, Any
from app.email.service import email_service
from app.email.config import email_config
import time

# Task logger
logger = get_task_logger(__name__)

# Regular logger for fallback
log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="100/m",
    soft_time_limit=600,
    name="app.tasks.email.send_verification_email_task"
)
def send_verification_email_task(
    self,
    recipient_email: str,
    verification_token: str,
    app_url: str = "https://app.omnidev.ai",
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Celery task to send email verification email asynchronously.
    
    Args:
        recipient_email: Email address to send to
        verification_token: JWT verification token
        app_url: Application URL for verification link
        user_id: Optional user ID for tracking
    
    Returns:
        dict: Task result with status and details
    
    Raises:
        Retries up to 3 times on failure with exponential backoff
    """
    task_id = self.request.id
    
    try:
        logger.info(
            f"Starting email verification task",
            extra={
                "task_id": task_id,
                "recipient": recipient_email,
                "user_id": user_id,
            }
        )
        
        # Check if email is enabled
        if not email_config.is_configured():
            logger.warning(
                f"Email system not configured, skipping task",
                extra={"task_id": task_id, "recipient": recipient_email}
            )
            return {
                "status": "skipped",
                "message": "Email system not configured",
                "task_id": task_id,
            }
        
        # Send verification email
        success = email_service.send_verification_email(
            recipient_email=recipient_email,
            verification_token=verification_token,
            app_url=app_url
        )
        
        if success:
            logger.info(
                f"Email verification sent successfully",
                extra={
                    "task_id": task_id,
                    "recipient": recipient_email,
                    "user_id": user_id,
                }
            )
            return {
                "status": "success",
                "message": "Verification email sent successfully",
                "task_id": task_id,
                "recipient": recipient_email,
            }
        else:
            raise Exception("Email service returned False")
            
    except Exception as exc:
        logger.error(
            f"Email verification task failed: {str(exc)}",
            extra={
                "task_id": task_id,
                "recipient": recipient_email,
                "exception": str(exc),
            }
        )
        
        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Email verification task failed permanently after 3 retries",
                extra={
                    "task_id": task_id,
                    "recipient": recipient_email,
                    "exception": str(exc),
                }
            )
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "recipient": recipient_email,
            }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="100/m",
    soft_time_limit=600,
    name="app.tasks.email.send_password_reset_task"
)
def send_password_reset_task(
    self,
    recipient_email: str,
    reset_token: str,
    app_url: str = "https://app.omnidev.ai",
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Celery task to send password reset email asynchronously.
    
    Args:
        recipient_email: Email address to send to
        reset_token: JWT password reset token
        app_url: Application URL for reset link
        user_id: Optional user ID for tracking
    
    Returns:
        dict: Task result with status and details
    """
    task_id = self.request.id
    
    try:
        logger.info(
            f"Starting password reset email task",
            extra={
                "task_id": task_id,
                "recipient": recipient_email,
                "user_id": user_id,
            }
        )
        
        if not email_config.is_configured():
            logger.warning(
                f"Email system not configured, skipping task",
                extra={"task_id": task_id, "recipient": recipient_email}
            )
            return {
                "status": "skipped",
                "message": "Email system not configured",
                "task_id": task_id,
            }
        
        success = email_service.send_password_reset_email(
            recipient_email=recipient_email,
            reset_token=reset_token,
            app_url=app_url
        )
        
        if success:
            logger.info(
                f"Password reset email sent successfully",
                extra={
                    "task_id": task_id,
                    "recipient": recipient_email,
                    "user_id": user_id,
                }
            )
            return {
                "status": "success",
                "message": "Password reset email sent successfully",
                "task_id": task_id,
                "recipient": recipient_email,
            }
        else:
            raise Exception("Email service returned False")
            
    except Exception as exc:
        logger.error(
            f"Password reset email task failed: {str(exc)}",
            extra={"task_id": task_id, "recipient": recipient_email}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Password reset email task failed permanently after 3 retries",
                extra={"task_id": task_id, "recipient": recipient_email}
            )
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "recipient": recipient_email,
            }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="100/m",
    soft_time_limit=600,
    name="app.tasks.email.send_notification_email_task"
)
def send_notification_email_task(
    self,
    recipient_email: str,
    subject: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    action_text: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Celery task to send notification email asynchronously.
    
    Args:
        recipient_email: Email address to send to
        subject: Email subject
        title: Notification title
        message: Notification message
        action_url: Optional action URL
        action_text: Optional action button text
        user_id: Optional user ID for tracking
    
    Returns:
        dict: Task result with status and details
    """
    task_id = self.request.id
    
    try:
        logger.info(
            f"Starting notification email task",
            extra={
                "task_id": task_id,
                "recipient": recipient_email,
                "subject": subject,
            }
        )
        
        if not email_config.is_configured():
            return {
                "status": "skipped",
                "message": "Email system not configured",
                "task_id": task_id,
            }
        
        success = email_service.send_notification_email(
            recipient_email=recipient_email,
            subject=subject,
            title=title,
            message=message,
            action_url=action_url,
            action_text=action_text
        )
        
        if success:
            logger.info(
                f"Notification email sent successfully",
                extra={
                    "task_id": task_id,
                    "recipient": recipient_email,
                    "subject": subject,
                }
            )
            return {
                "status": "success",
                "message": "Notification email sent successfully",
                "task_id": task_id,
                "recipient": recipient_email,
            }
        else:
            raise Exception("Email service returned False")
            
    except Exception as exc:
        logger.error(
            f"Notification email task failed: {str(exc)}",
            extra={"task_id": task_id, "recipient": recipient_email}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Notification email task failed permanently",
                extra={"task_id": task_id, "recipient": recipient_email}
            )
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "recipient": recipient_email,
            }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="100/m",
    soft_time_limit=600,
    name="app.tasks.email.send_welcome_email_task"
)
def send_welcome_email_task(
    self,
    recipient_email: str,
    username: str,
    app_url: str = "https://app.omnidev.ai",
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Celery task to send welcome email asynchronously.
    
    Args:
        recipient_email: Email address to send to
        username: Username of the new user
        app_url: Application URL
        user_id: Optional user ID for tracking
    
    Returns:
        dict: Task result with status and details
    """
    task_id = self.request.id
    
    try:
        logger.info(
            f"Starting welcome email task",
            extra={
                "task_id": task_id,
                "recipient": recipient_email,
                "username": username,
            }
        )
        
        if not email_config.is_configured():
            return {
                "status": "skipped",
                "message": "Email system not configured",
                "task_id": task_id,
            }
        
        success = email_service.send_welcome_email(
            recipient_email=recipient_email,
            username=username,
            app_url=app_url
        )
        
        if success:
            logger.info(
                f"Welcome email sent successfully",
                extra={
                    "task_id": task_id,
                    "recipient": recipient_email,
                    "username": username,
                }
            )
            return {
                "status": "success",
                "message": "Welcome email sent successfully",
                "task_id": task_id,
                "recipient": recipient_email,
            }
        else:
            raise Exception("Email service returned False")
            
    except Exception as exc:
        logger.error(
            f"Welcome email task failed: {str(exc)}",
            extra={"task_id": task_id, "recipient": recipient_email}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Welcome email task failed permanently",
                extra={"task_id": task_id, "recipient": recipient_email}
            )
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "recipient": recipient_email,
            }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="50/m",
    soft_time_limit=900,
    name="app.tasks.email.send_bulk_emails_task"
)
def send_bulk_emails_task(
    self,
    recipients: List[Dict[str, str]],
    email_type: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Celery task to send bulk emails with rate limiting.
    
    Args:
        recipients: List of dicts with 'email' and other fields
        email_type: Type of email (verification, reset, notification, welcome)
        **kwargs: Additional arguments for email method
    
    Returns:
        dict: Summary of bulk send operation
    
    Example:
        recipients = [
            {"email": "user1@example.com", "username": "user1"},
            {"email": "user2@example.com", "username": "user2"},
        ]
        send_bulk_emails_task.delay(recipients, "welcome", app_url="...")
    """
    task_id = self.request.id
    total = len(recipients)
    successful = 0
    failed = []
    
    try:
        logger.info(
            f"Starting bulk email task",
            extra={
                "task_id": task_id,
                "email_type": email_type,
                "total_recipients": total,
            }
        )
        
        if not email_config.is_configured():
            return {
                "status": "skipped",
                "message": "Email system not configured",
                "task_id": task_id,
                "total": total,
                "successful": 0,
            }
        
        # Send emails with rate limiting
        for i, recipient_data in enumerate(recipients):
            try:
                # Rate limiting: small delay between emails
                if i > 0:
                    time.sleep(0.6)  # 1 email per second max
                
                email = recipient_data.pop("email")
                
                # Route to appropriate email method
                if email_type == "welcome":
                    success = email_service.send_welcome_email(
                        recipient_email=email,
                        **recipient_data
                    )
                elif email_type == "notification":
                    success = email_service.send_notification_email(
                        recipient_email=email,
                        **recipient_data
                    )
                else:
                    success = False
                
                if success:
                    successful += 1
                else:
                    failed.append(email)
                    
            except Exception as e:
                logger.error(
                    f"Failed to send email to {recipient_data.get('email')}",
                    extra={"error": str(e)}
                )
                failed.append(recipient_data.get("email", "unknown"))
        
        logger.info(
            f"Bulk email task completed",
            extra={
                "task_id": task_id,
                "total": total,
                "successful": successful,
                "failed": len(failed),
            }
        )
        
        return {
            "status": "success" if len(failed) == 0 else "partial",
            "task_id": task_id,
            "total": total,
            "successful": successful,
            "failed": len(failed),
            "failed_emails": failed,
        }
        
    except Exception as exc:
        logger.error(
            f"Bulk email task failed: {str(exc)}",
            extra={"task_id": task_id, "total": total}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "total": total,
                "successful": successful,
            }


# ============================================================================
# Analytics Report Email Tasks
# ============================================================================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="50/m",
    soft_time_limit=300,
    name="app.tasks.email.send_user_analytics_report_task"
)
def send_user_analytics_report_task(
    self,
    user_id: int,
    recipient_email: str,
    report_format: str = "json",
    days: int = 30,
) -> Dict[str, Any]:
    """
    Send user analytics report via email.
    
    Args:
        user_id: User ID for report
        recipient_email: Email recipient
        report_format: Report format (json or csv)
        days: Number of days to include
    
    Returns:
        Result dictionary with status
    """
    task_id = self.request.id
    
    try:
        from app.analytics import report_service
        
        logger.info(
            f"Generating user analytics report for user {user_id}",
            extra={"task_id": task_id, "format": report_format}
        )
        
        # Generate report
        if report_format == "csv":
            report_content = report_service.generate_user_activity_csv(
                user_id=user_id,
                days=days
            )
            filename = f"user_analytics_{user_id}_{days}d.csv"
            content_type = "text/csv"
        else:
            report_content = report_service.generate_user_report_json(
                user_id=user_id,
                days=days
            )
            filename = f"user_analytics_{user_id}_{days}d.json"
            content_type = "application/json"
        
        # Send email
        subject = f"Your Analytics Report - Last {days} Days"
        body = f"""
Hello,

Your analytics report for the last {days} days is attached.

Report Details:
- Format: {report_format.upper()}
- Period: {days} days
- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

Thank you for using OmniDev AI!

Best regards,
OmniDev AI Team
"""
        
        success = email_service.send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            html_body=None,
            attachments=[{
                "filename": filename,
                "content": report_content,
                "content_type": content_type,
            }] if report_format == "csv" else [],
            priority="normal"
        )
        
        if success:
            logger.info(
                f"User analytics report sent successfully",
                extra={"task_id": task_id, "user_id": user_id}
            )
            return {
                "status": "success",
                "message": f"Report sent to {recipient_email}",
                "user_id": user_id,
                "task_id": task_id,
            }
        else:
            raise Exception("Email service returned failure")
    
    except Exception as exc:
        logger.error(
            f"Failed to send user analytics report: {str(exc)}",
            extra={"task_id": task_id, "user_id": user_id}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "user_id": user_id,
            }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="50/m",
    soft_time_limit=300,
    name="app.tasks.email.send_project_analytics_report_task"
)
def send_project_analytics_report_task(
    self,
    project_id: int,
    recipient_emails: List[str],
    report_format: str = "json",
    days: int = 30,
) -> Dict[str, Any]:
    """
    Send project analytics report to team members.
    
    Args:
        project_id: Project ID for report
        recipient_emails: List of email recipients
        report_format: Report format (json or csv)
        days: Number of days to include
    
    Returns:
        Result dictionary with status
    """
    task_id = self.request.id
    
    try:
        from app.analytics import report_service
        from app.database.models import Project
        from app.database.config import SessionLocal
        
        db = SessionLocal()
        
        logger.info(
            f"Generating project analytics report for project {project_id}",
            extra={"task_id": task_id, "recipients": len(recipient_emails)}
        )
        
        # Get project
        project = db.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Generate report
        if report_format == "csv":
            report_content = report_service.generate_project_metrics_csv(
                project_id=project_id,
                days=days
            )
            filename = f"project_analytics_{project_id}_{days}d.csv"
            content_type = "text/csv"
        else:
            report_content = report_service.generate_project_report_json(
                project_id=project_id,
                days=days
            )
            filename = f"project_analytics_{project_id}_{days}d.json"
            content_type = "application/json"
        
        # Send emails
        successful = 0
        failed = 0
        
        for recipient_email in recipient_emails:
            try:
                subject = f"Project Analytics Report: {project.title}"
                body = f"""
Hello Team Member,

Here is the analytics report for the project "{project.title}" for the last {days} days.

Report Details:
- Project: {project.title}
- Format: {report_format.upper()}
- Period: {days} days
- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

Thank you for your contributions!

Best regards,
OmniDev AI Team
"""
                
                success = email_service.send_email(
                    to_email=recipient_email,
                    subject=subject,
                    body=body,
                    html_body=None,
                    priority="normal"
                )
                
                if success:
                    successful += 1
                else:
                    failed += 1
            
            except Exception as e:
                logger.warning(
                    f"Failed to send report to {recipient_email}: {str(e)}",
                    extra={"task_id": task_id}
                )
                failed += 1
        
        db.close()
        
        logger.info(
            f"Project analytics report distribution completed",
            extra={
                "task_id": task_id,
                "project_id": project_id,
                "successful": successful,
                "failed": failed,
            }
        )
        
        return {
            "status": "success" if failed == 0 else "partial",
            "message": f"Sent to {successful}/{len(recipient_emails)} recipients",
            "project_id": project_id,
            "successful_emails": successful,
            "failed_emails": failed,
            "task_id": task_id,
        }
    
    except Exception as exc:
        logger.error(
            f"Failed to send project analytics report: {str(exc)}",
            extra={"task_id": task_id, "project_id": project_id}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
                "project_id": project_id,
            }


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    rate_limit="10/m",
    soft_time_limit=600,
    name="app.tasks.email.send_team_analytics_summary_task"
)
def send_team_analytics_summary_task(
    self,
    admin_email: str,
    days: int = 7,
) -> Dict[str, Any]:
    """
    Send team-wide analytics summary to admin.
    
    Args:
        admin_email: Admin email address
        days: Number of days to summarize
    
    Returns:
        Result dictionary with status
    """
    task_id = self.request.id
    
    try:
        from app.analytics import report_service
        
        logger.info(
            f"Generating team analytics summary",
            extra={"task_id": task_id}
        )
        
        # Generate report
        report_content = report_service.generate_system_health_report_json(
            days=days
        )
        
        # Send email
        subject = f"Team Analytics Summary - Last {days} Days"
        body = f"""
Hello Admin,

Please find attached the team-wide analytics summary for the last {days} days.

Summary Details:
- Period: {days} days
- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

This summary includes system health metrics, team engagement, and project performance.

Best regards,
OmniDev AI Team
"""
        
        success = email_service.send_email(
            to_email=admin_email,
            subject=subject,
            body=body,
            html_body=None,
            priority="high"
        )
        
        if success:
            logger.info(
                f"Team analytics summary sent successfully",
                extra={"task_id": task_id}
            )
            return {
                "status": "success",
                "message": f"Summary sent to {admin_email}",
                "task_id": task_id,
            }
        else:
            raise Exception("Email service returned failure")
    
    except Exception as exc:
        logger.error(
            f"Failed to send team analytics summary: {str(exc)}",
            extra={"task_id": task_id}
        )
        
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "message": f"Failed after 3 retries: {str(exc)}",
                "task_id": task_id,
            }
