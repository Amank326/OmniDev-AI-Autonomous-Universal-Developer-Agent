"""
Unit Tests for Authentication System

Tests for:
- Password hashing and verification
- JWT token generation and validation
- User registration with validation
- User login and token generation
- Token refresh
- Current user retrieval
- Password change functionality
- Error handling and edge cases

Run with:
    pytest tests/test_auth.py -v
    pytest tests/test_auth.py::test_register_user -v
"""

import pytest
from fastapi.testclient import TestClient
from app.auth.utils import hash_password, verify_password, create_access_token, verify_token
from app.auth.service import AuthService
from app.database.config import SessionLocal
from datetime import timedelta
import time


class TestPasswordHashing:
    """Test password hashing utilities."""
    
    @pytest.mark.unit
    def test_hash_password_creates_different_hashes(self):
        """Same password should create different hashes (due to salt)."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different due to random salt
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    @pytest.mark.unit
    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    @pytest.mark.unit
    def test_verify_password_failure(self):
        """Test failed password verification with wrong password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)
        
        assert not verify_password(wrong_password, hashed)
    
    @pytest.mark.unit
    def test_hash_password_too_short(self):
        """Test that short passwords raise ValueError."""
        password = "short"  # Less than 8 characters
        
        with pytest.raises(ValueError):
            hash_password(password)


class TestJWTTokens:
    """Test JWT token generation and validation."""
    
    @pytest.mark.unit
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "123"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.unit
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "123", "scope": "admin"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "123"
        assert payload.get("scope") == "admin"
    
    @pytest.mark.unit
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        
        with pytest.raises(Exception):  # JWT decoding error
            verify_token(invalid_token)
    
    @pytest.mark.unit
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))  # Already expired
        
        with pytest.raises(Exception):  # Token expired error
            verify_token(token)
    
    @pytest.mark.unit
    def test_token_expiration(self):
        """Test that token has expiration claim."""
        data = {"sub": "123"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert "exp" in payload  # Expiration claim exists


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""
    
    @pytest.mark.integration
    def test_register_user_success(self, client: TestClient, test_user_data: dict):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json=test_user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.integration
    def test_register_duplicate_username(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate username."""
        # First registration
        response1 = client.post("/api/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Second registration with same username
        response2 = client.post("/api/auth/register", json=test_user_data)
        assert response2.status_code == 409  # Conflict
    
    @pytest.mark.integration
    def test_register_invalid_password(self, client: TestClient, test_user_data: dict):
        """Test registration with invalid password."""
        invalid_data = {
            **test_user_data,
            "password": "short"  # Too short
        }
        
        response = client.post("/api/auth/register", json=invalid_data)
        assert response.status_code == 400  # Bad request
    
    @pytest.mark.integration
    def test_login_success(self, client: TestClient, test_user_data: dict):
        """Test successful login."""
        # Register first
        client.post("/api/auth/register", json=test_user_data)
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] is not None
    
    @pytest.mark.integration
    def test_login_wrong_password(self, client: TestClient, test_user_data: dict):
        """Test login with wrong password."""
        # Register first
        client.post("/api/auth/register", json=test_user_data)
        
        # Login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["username"],
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.integration
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.integration
    def test_get_current_user(self, authenticated_client: dict):
        """Test getting current user information."""
        response = authenticated_client["client"].get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["is_active"] is True
    
    @pytest.mark.integration
    def test_get_current_user_without_token(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.integration
    def test_refresh_token_success(self, authenticated_client: dict):
        """Test token refresh."""
        response = authenticated_client["client"].post(
            "/api/auth/refresh",
            json={"refresh_token": authenticated_client["refresh_token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != authenticated_client["token"]  # New token
    
    @pytest.mark.integration
    def test_change_password_success(self, authenticated_client: dict, test_user_data: dict):
        """Test successful password change."""
        new_password = "NewPassword456!"
        
        response = authenticated_client["client"].post(
            "/api/auth/change-password",
            json={
                "old_password": test_user_data["password"],
                "new_password": new_password,
                "confirm_password": new_password
            }
        )
        
        assert response.status_code == 200
    
    @pytest.mark.integration
    def test_change_password_wrong_old_password(self, authenticated_client: dict):
        """Test password change with wrong old password."""
        response = authenticated_client["client"].post(
            "/api/auth/change-password",
            json={
                "old_password": "WrongPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!"
            }
        )
        
        assert response.status_code == 400  # Bad request
    
    @pytest.mark.integration
    def test_change_password_passwords_dont_match(self, authenticated_client: dict):
        """Test password change with mismatched new passwords."""
        response = authenticated_client["client"].post(
            "/api/auth/change-password",
            json={
                "old_password": "TestPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "DifferentPassword789!"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    def test_logout(self, authenticated_client: dict):
        """Test logout endpoint."""
        response = authenticated_client["client"].post("/api/auth/logout")
        
        assert response.status_code == 200
        assert "message" in response.json()


class TestAuthService:
    """Test AuthService business logic."""
    
    @pytest.mark.unit
    def test_create_auth_service(self):
        """Test AuthService instantiation."""
        db = SessionLocal()
        try:
            service = AuthService(db)
            assert service is not None
            assert service.db == db
        finally:
            db.close()
    
    @pytest.mark.unit
    def test_register_user_validation(self):
        """Test user registration validation."""
        db = SessionLocal()
        try:
            service = AuthService(db)
            
            # Test with too short password
            with pytest.raises(ValueError):
                service.register_user("testuser", "test@example.com", "short", None)
        finally:
            db.close()


class TestAuthErrors:
    """Test error handling in authentication."""
    
    @pytest.mark.integration
    def test_missing_required_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser"}  # Missing email and password
        )
        
        assert response.status_code == 422  # Validation error
