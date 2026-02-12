"""Pydantic schemas for authentication requests and responses"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """User registration request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str = Field(default="", max_length=100, description="Full name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePassword123",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """User login request schema"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePassword123"
            }
        }


class Token(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user_id": "12345",
                "username": "john_doe"
            }
        }


class TokenData(BaseModel):
    """Token payload data"""
    sub: str = Field(..., description="Subject (user ID)")
    exp: float = Field(..., description="Expiration timestamp")
    iat: float = Field(..., description="Issued at timestamp")
    scope: str = Field(default="access", description="Token scope")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sub": "12345",
                "exp": 1707139200,
                "iat": 1707133200,
                "scope": "access"
            }
        }


class UserResponse(BaseModel):
    """User response schema (public)"""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    is_active: bool = Field(default=True, description="Is active")
    is_admin: bool = Field(default=False, description="Is administrator")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "12345",
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_admin": False,
                "created_at": "2025-02-05T10:30:00"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldPassword123",
                "new_password": "NewPassword456",
                "confirm_password": "NewPassword456"
            }
        }


class AuthError(BaseModel):
    """Authentication error response"""
    detail: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "error_code": "INVALID_CREDENTIALS"
            }
        }
