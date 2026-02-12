"""
Unit and Integration Tests for Email and Notifications

Tests for:
- Email verification flow
- Password reset flow
- Email service
- Notification creation and delivery
- Email token generation and validation

Run with:
    pytest tests/test_email.py -v
    pytest tests/test_notifications.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.auth.tokens import EmailVerificationToken, PasswordResetToken


class TestEmailVerificationToken:
    """Test email verification token generation and validation."""
    
    @pytest.mark.unit
    def test_generate_verification_token(self):
        """Test generating email verification token."""
        user_id = 42
        email = "test@example.com"
        
        token = EmailVerificationToken.generate_token(user_id, email)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.unit
    def test_verify_valid_email_token(self):
        """Test verifying valid email verification token."""
        user_id = 42
        email = "test@example.com"
        
        token = EmailVerificationToken.generate_token(user_id, email)
        result = EmailVerificationToken.verify_token(token)
        
        assert result is not None
        verified_user_id, verified_email = result
        assert verified_user_id == user_id
        assert verified_email == email
    
    @pytest.mark.unit
    def test_verify_invalid_email_token(self):
        """Test verifying invalid email token."""
        invalid_token = "invalid.token.here"
        result = EmailVerificationToken.verify_token(invalid_token)
        
        assert result is None
    
    @pytest.mark.unit
    def test_verify_expired_email_token(self):
        """Test verifying expired email token."""
        user_id = 42
        email = "test@example.com"
        
        # Create token that expires immediately
        token = EmailVerificationToken.generate_token(user_id, email, expires_in_seconds=0)
        
        import time
        time.sleep(1)  # Wait for expiration
        
        result = EmailVerificationToken.verify_token(token)
        assert result is None


class TestPasswordResetToken:
    """Test password reset token generation and validation."""
    
    @pytest.mark.unit
    def test_generate_password_reset_token(self):
        """Test generating password reset token."""
        user_id = 42
        email = "test@example.com"
        
        token = PasswordResetToken.generate_token(user_id, email)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.unit
    def test_verify_valid_reset_token(self):
        """Test verifying valid reset token."""
        user_id = 42
        email = "test@example.com"
        
        token = PasswordResetToken.generate_token(user_id, email)
        result = PasswordResetToken.verify_token(token)
        
        assert result is not None
        verified_user_id, verified_email = result
        assert verified_user_id == user_id
        assert verified_email == email
    
    @pytest.mark.unit
    def test_verify_invalid_reset_token(self):
        """Test verifying invalid reset token."""
        invalid_token = "invalid.token.here"
        result = PasswordResetToken.verify_token(invalid_token)
        
        assert result is None


class TestEmailVerificationEndpoints:
    """Test email verification API endpoints."""
    
    @pytest.mark.integration
    def test_verify_email_invalid_token(self, client: TestClient):
        """Test email verification with invalid token."""
        response = client.post(
            "/api/email/verify",
            json={"token": "invalid_token"}
        )
        
        assert response.status_code in [400, 422]
    
    @pytest.mark.integration
    def test_resend_verification_nonexistent_email(self, client: TestClient):
        """Test resending verification to non-existent email."""
        response = client.post(
            "/api/email/resend-verification",
            json={"email": "nonexistent@example.com"}
        )
        
        # Should not reveal if email exists
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestPasswordResetEndpoints:
    """Test password reset API endpoints."""
    
    @pytest.mark.integration
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test forgot password with non-existent email."""
        response = client.post(
            "/api/password/forgot",
            json={"email": "nonexistent@example.com"}
        )
        
        # Should not reveal if email exists
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    @pytest.mark.integration
    def test_reset_password_invalid_token(self, client: TestClient):
        """Test password reset with invalid token."""
        response = client.post(
            "/api/password/reset",
            json={
                "token": "invalid_token",
                "new_password": "NewPassword123",
                "confirm_password": "NewPassword123"
            }
        )
        
        assert response.status_code == 400
    
    @pytest.mark.integration
    def test_reset_password_mismatch(self, client: TestClient):
        """Test password reset with mismatched passwords."""
        response = client.post(
            "/api/password/reset",
            json={
                "token": "some_token",
                "new_password": "NewPassword123",
                "confirm_password": "DifferentPassword456"
            }
        )
        
        assert response.status_code in [400, 422]


class TestNotificationEndpoints:
    """Test notification API endpoints."""
    
    @pytest.mark.integration
    def test_get_notifications_unauthorized(self, client: TestClient):
        """Test getting notifications without authentication."""
        response = client.get("/api/notifications")
        
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.integration
    def test_get_notifications_authenticated(self, authenticated_client: dict):
        """Test getting notifications as authenticated user."""
        response = authenticated_client["client"].get("/api/notifications")
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data or "success" in data
    
    @pytest.mark.integration
    def test_get_notifications_with_filters(self, authenticated_client: dict):
        """Test getting notifications with filters."""
        response = authenticated_client["client"].get(
            "/api/notifications?unread_only=true&limit=10&offset=0"
        )
        
        assert response.status_code == 200
    
    @pytest.mark.integration
    def test_mark_notification_read_unauthorized(self, client: TestClient):
        """Test marking notification as read without auth."""
        response = client.post("/api/notifications/1/read")
        
        assert response.status_code == 403
    
    @pytest.mark.integration
    def test_delete_notification_unauthorized(self, client: TestClient):
        """Test deleting notification without auth."""
        response = client.delete("/api/notifications/1")
        
        assert response.status_code == 403
    
    @pytest.mark.integration
    def test_clear_all_notifications_unauthorized(self, client: TestClient):
        """Test clearing all notifications without auth."""
        response = client.post("/api/notifications/clear")
        
        assert response.status_code == 403
    
    @pytest.mark.integration
    def test_clear_all_notifications_authenticated(self, authenticated_client: dict):
        """Test clearing all notifications as authenticated user."""
        response = authenticated_client["client"].post("/api/notifications/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True


class TestEmailFlow:
    """Test complete email workflows."""
    
    @pytest.mark.integration
    def test_full_registration_and_verification_flow(
        self,
        client: TestClient,
        test_user_data: dict
    ):
        """Test complete registration and email verification flow."""
        # Register user
        register_response = client.post(
            "/api/auth/register",
            json=test_user_data
        )
        assert register_response.status_code == 201
        
        # Generate verification token (simulating email send)
        user_id = register_response.json().get("id", 1)
        token = EmailVerificationToken.generate_token(
            user_id,
            test_user_data["email"]
        )
        
        # Verify email
        verify_response = client.post(
            "/api/email/verify",
            json={"token": token}
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["success"] is True
    
    @pytest.mark.integration
    def test_full_password_reset_flow(
        self,
        client: TestClient,
        test_user_data: dict
    ):
        """Test complete password reset flow."""
        # Register user
        client.post("/api/auth/register", json=test_user_data)
        
        # Request password reset
        forgot_response = client.post(
            "/api/password/forgot",
            json={"email": test_user_data["email"]}
        )
        assert forgot_response.status_code == 200
        
        # Generate reset token (simulating email send)
        user_id = 1
        token = PasswordResetToken.generate_token(
            user_id,
            test_user_data["email"]
        )
        
        # Reset password
        reset_response = client.post(
            "/api/password/reset",
            json={
                "token": token,
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            }
        )
        assert reset_response.status_code == 200
        assert reset_response.json()["success"] is True
