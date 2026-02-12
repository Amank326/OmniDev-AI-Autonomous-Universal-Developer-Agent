"""
Phase 6 Tests - Background Jobs & Task Queue
=============================================

Comprehensive test suite for Celery tasks, monitoring, and scheduling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from celery.result import AsyncResult
from app.tasks.email import (
    send_verification_email_task,
    send_password_reset_task,
    send_notification_email_task,
    send_welcome_email_task,
    send_bulk_emails_task,
)
from app.tasks.notifications import (
    create_notification_task,
    batch_notifications_task,
    send_digest_notification_task,
)
from app.tasks.monitoring import TaskMonitoringService
from app.celery_app import celery_app


# ============================================================================
# Email Task Tests
# ============================================================================

class TestEmailTasks:
    """Test suite for email queue tasks."""
    
    def test_send_verification_email_task_success(self):
        """Test successful verification email task."""
        with patch('app.tasks.email.email_service') as mock_email_service:
            # Arrange
            recipient = "test@example.com"
            token = "test_token_12345"
            app_url = "http://localhost:3000"
            user_id = 1
            
            # Act
            result = send_verification_email_task(recipient, token, app_url, user_id)
            
            # Assert
            mock_email_service.send_verification_email.assert_called_once_with(
                recipient, token, app_url
            )
    
    def test_send_verification_email_task_retry(self):
        """Test verification email task with retry."""
        with patch('app.tasks.email.email_service') as mock_email_service:
            # Arrange
            mock_email_service.send_verification_email.side_effect = Exception("Email service error")
            recipient = "test@example.com"
            token = "test_token_12345"
            app_url = "http://localhost:3000"
            user_id = 1
            
            # Act & Assert - Should raise exception for retry
            with pytest.raises(Exception):
                send_verification_email_task(recipient, token, app_url, user_id)
    
    def test_send_password_reset_task_success(self):
        """Test successful password reset email task."""
        with patch('app.tasks.email.email_service') as mock_email_service:
            # Arrange
            recipient = "test@example.com"
            token = "reset_token_12345"
            app_url = "http://localhost:3000"
            user_id = 1
            
            # Act
            result = send_password_reset_task(recipient, token, app_url, user_id)
            
            # Assert
            mock_email_service.send_password_reset_email.assert_called_once_with(
                recipient, token, app_url
            )
    
    def test_send_notification_email_task_success(self):
        """Test successful notification email task."""
        with patch('app.tasks.email.email_service') as mock_email_service:
            # Arrange
            recipient = "test@example.com"
            subject = "Test Subject"
            title = "Test Title"
            message = "Test message content"
            action_url = "http://localhost:3000/action"
            action_text = "Click here"
            user_id = 1
            
            # Act
            result = send_notification_email_task(
                recipient, subject, title, message, action_url, action_text, user_id
            )
            
            # Assert
            mock_email_service.send_notification_email.assert_called_once()
    
    def test_send_welcome_email_task_success(self):
        """Test successful welcome email task."""
        with patch('app.tasks.email.email_service') as mock_email_service:
            # Arrange
            recipient = "newuser@example.com"
            username = "John Doe"
            app_url = "http://localhost:3000"
            user_id = 1
            
            # Act
            result = send_welcome_email_task(recipient, username, app_url, user_id)
            
            # Assert
            mock_email_service.send_welcome_email.assert_called_once_with(
                recipient, username, app_url
            )
    
    def test_send_bulk_emails_task_success(self):
        """Test successful bulk email task."""
        with patch('app.tasks.email.email_service') as mock_email_service:
            # Arrange
            recipients = [
                {"email": "user1@example.com", "name": "User 1"},
                {"email": "user2@example.com", "name": "User 2"},
                {"email": "user3@example.com", "name": "User 3"},
            ]
            email_type = "newsletter"
            subject = "Our Latest Newsletter"
            
            # Act
            result = send_bulk_emails_task(recipients, email_type, subject=subject)
            
            # Assert - Should return summary
            assert isinstance(result, dict)
            assert "successful" in result or "failed" in result
    
    def test_send_bulk_emails_task_partial_failure(self):
        """Test bulk email task with partial failure."""
        with patch('app.tasks.email.email_service') as mock_email_service:
            # Arrange
            recipients = [
                {"email": "user1@example.com", "name": "User 1"},
                {"email": "invalid_email", "name": "User 2"},  # This should fail
            ]
            email_type = "newsletter"
            
            # Act
            result = send_bulk_emails_task(recipients, email_type)
            
            # Assert
            assert isinstance(result, dict)


# ============================================================================
# Notification Task Tests
# ============================================================================

class TestNotificationTasks:
    """Test suite for notification queue tasks."""
    
    @patch('app.tasks.notifications.SessionLocal')
    def test_create_notification_task_success(self, mock_session):
        """Test successful notification creation task."""
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        with patch('app.tasks.notifications.NotificationService') as mock_service:
            recipient_id = 1
            notification_type = "task_assigned"
            title = "New task assigned"
            message = "You have been assigned a new task"
            channels = ["IN_APP", "EMAIL"]
            
            # Act
            result = create_notification_task(
                recipient_id, notification_type, title, message, channels=channels
            )
            
            # Assert
            mock_db.close.assert_called_once()
    
    @patch('app.tasks.notifications.SessionLocal')
    def test_batch_notifications_task_success(self, mock_session):
        """Test successful batch notification task."""
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        with patch('app.tasks.notifications.NotificationService') as mock_service:
            recipient_ids = [1, 2, 3, 4, 5]
            notification_type = "team_announcement"
            title = "Team Announcement"
            message = "Important team announcement"
            
            # Act
            result = batch_notifications_task(
                recipient_ids, notification_type, title, message
            )
            
            # Assert
            assert isinstance(result, dict)
            assert "successful_recipients" in result or "failed_recipients" in result
    
    @patch('app.tasks.notifications.SessionLocal')
    def test_send_digest_notification_task_daily(self, mock_session):
        """Test daily digest notification task."""
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        with patch('app.tasks.notifications.NotificationService') as mock_service:
            user_id = 1
            digest_type = "daily"
            
            # Act
            result = send_digest_notification_task(user_id, digest_type)
            
            # Assert
            mock_db.close.assert_called_once()
    
    @patch('app.tasks.notifications.SessionLocal')
    def test_send_digest_notification_task_weekly(self, mock_session):
        """Test weekly digest notification task."""
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        with patch('app.tasks.notifications.NotificationService') as mock_service:
            user_id = 1
            digest_type = "weekly"
            
            # Act
            result = send_digest_notification_task(user_id, digest_type)
            
            # Assert
            mock_db.close.assert_called_once()


# ============================================================================
# Task Monitoring Tests
# ============================================================================

class TestTaskMonitoring:
    """Test suite for task monitoring service."""
    
    def test_get_task_status_success(self):
        """Test getting task status."""
        service = TaskMonitoringService()
        
        with patch('app.tasks.monitoring.AsyncResult') as mock_result_class:
            # Arrange
            mock_result = MagicMock()
            mock_result.status = "SUCCESS"
            mock_result.result = {"message": "Task completed"}
            mock_result.ready.return_value = True
            mock_result.successful.return_value = True
            mock_result.failed.return_value = False
            mock_result_class.return_value = mock_result
            
            # Act
            status = service.get_task_status("task_123")
            
            # Assert
            assert status["task_id"] == "task_123"
            assert status["status"] == "SUCCESS"
    
    def test_get_active_tasks(self):
        """Test getting active tasks."""
        service = TaskMonitoringService()
        
        with patch.object(service.inspect, 'active') as mock_active:
            # Arrange
            mock_active.return_value = {
                "worker1": [
                    {"id": "task_1", "name": "email.send_verification_email_task"},
                    {"id": "task_2", "name": "notifications.create_notification_task"},
                ]
            }
            
            # Act
            active = service.get_active_tasks()
            
            # Assert
            assert "worker1" in active
            assert len(active["worker1"]) == 2
    
    def test_get_worker_stats(self):
        """Test getting worker statistics."""
        service = TaskMonitoringService()
        
        with patch.object(service.inspect, 'stats') as mock_stats:
            # Arrange
            mock_stats.return_value = {
                "worker1": {
                    "pool": {"max-concurrency": 4, "processes": 2},
                    "total": 100,
                    "completed": 95,
                    "failed": 5,
                }
            }
            
            # Act
            stats = service.get_worker_stats()
            
            # Assert
            assert stats["status"] == "ok"
            assert stats["workers"] == 1
    
    def test_retry_task(self):
        """Test retrying a failed task."""
        service = TaskMonitoringService()
        
        with patch('app.tasks.monitoring.AsyncResult') as mock_result_class:
            # Arrange
            mock_result = MagicMock()
            mock_result.status = "FAILURE"
            mock_result_class.return_value = mock_result
            
            # Act
            result = service.retry_task("failed_task_123")
            
            # Assert
            assert result["status"] == "success"
            mock_result.forget.assert_called_once()
    
    def test_revoke_task(self):
        """Test revoking a task."""
        service = TaskMonitoringService()
        
        with patch.object(service.celery.control, 'revoke') as mock_revoke:
            # Act
            result = service.revoke_task("task_123", terminate=True)
            
            # Assert
            assert result["status"] == "success"
            mock_revoke.assert_called_once_with("task_123", terminate=True)
    
    def test_get_health_status(self):
        """Test getting system health status."""
        service = TaskMonitoringService()
        
        with patch.object(service, 'get_worker_stats') as mock_stats:
            with patch.object(service, 'get_active_tasks') as mock_active:
                with patch.object(service, 'get_scheduled_tasks') as mock_scheduled:
                    # Arrange
                    mock_stats.return_value = {"status": "ok", "workers": 2}
                    mock_active.return_value = {"worker1": [{"id": "task_1"}]}
                    mock_scheduled.return_value = {}
                    
                    # Act
                    health = service.get_health_status()
                    
                    # Assert
                    assert health["status"] == "healthy"
                    assert health["workers"] == 2
                    assert health["active_tasks"] == 1


# ============================================================================
# Celery Configuration Tests
# ============================================================================

class TestCeleryConfiguration:
    """Test suite for Celery configuration."""
    
    def test_celery_app_initialized(self):
        """Test that Celery app is properly initialized."""
        assert celery_app is not None
        assert celery_app.conf.broker_url is not None
    
    def test_task_routing_configured(self):
        """Test that task routing is configured."""
        # Check that task routes are defined
        routes = celery_app.conf.task_routes
        assert routes is not None
    
    def test_email_tasks_registered(self):
        """Test that email tasks are registered."""
        registered_tasks = celery_app.tasks
        
        assert 'app.tasks.email.send_verification_email_task' in registered_tasks
        assert 'app.tasks.email.send_password_reset_task' in registered_tasks
        assert 'app.tasks.email.send_notification_email_task' in registered_tasks
        assert 'app.tasks.email.send_welcome_email_task' in registered_tasks
        assert 'app.tasks.email.send_bulk_emails_task' in registered_tasks
    
    def test_notification_tasks_registered(self):
        """Test that notification tasks are registered."""
        registered_tasks = celery_app.tasks
        
        assert 'app.tasks.notifications.create_notification_task' in registered_tasks
        assert 'app.tasks.notifications.batch_notifications_task' in registered_tasks
        assert 'app.tasks.notifications.send_digest_notification_task' in registered_tasks
    
    def test_redis_broker_configured(self):
        """Test that Redis broker is configured."""
        broker_url = celery_app.conf.broker_url
        assert broker_url.startswith("redis://")
    
    def test_result_backend_configured(self):
        """Test that result backend is configured."""
        result_backend = celery_app.conf.result_backend
        assert result_backend is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase6Integration:
    """Integration tests for Phase 6 functionality."""
    
    @patch('app.tasks.email.email_service')
    def test_email_task_chain(self, mock_email_service):
        """Test email task processing chain."""
        # Arrange
        recipient = "user@example.com"
        token = "test_token"
        app_url = "http://localhost:3000"
        user_id = 1
        
        # Act - Queue verification email
        task_id = send_verification_email_task.delay(recipient, token, app_url, user_id)
        
        # Assert - Task should be queued
        assert task_id is not None
    
    @patch('app.tasks.notifications.SessionLocal')
    def test_notification_task_chain(self, mock_session):
        """Test notification task processing chain."""
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        with patch('app.tasks.notifications.NotificationService'):
            recipient_id = 1
            notification_type = "test"
            title = "Test"
            message = "Test message"
            
            # Act - Queue notification
            task_id = create_notification_task.delay(
                recipient_id, notification_type, title, message
            )
            
            # Assert
            assert task_id is not None
    
    def test_monitoring_service_lifecycle(self):
        """Test monitoring service lifecycle."""
        service = TaskMonitoringService()
        
        # Test initialization
        assert service.celery is not None
        assert service.inspect is not None
        
        # Test methods exist
        assert hasattr(service, 'get_task_status')
        assert hasattr(service, 'get_active_tasks')
        assert hasattr(service, 'get_worker_stats')
        assert hasattr(service, 'retry_task')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
