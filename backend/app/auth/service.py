"""Authentication service - Business logic for user registration, login, and token management"""

from typing import Optional, Tuple
from datetime import timedelta
from sqlalchemy.orm import Session
from uuid import uuid4
import logging

from app.database import User, SessionLocal
from app.database.services import UserService
from .utils import hash_password, verify_password, create_access_token, verify_token, get_user_from_token
from jose import JWTError

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for handling user registration, login, and token operations"""
    
    def __init__(self, db: Session):
        """
        Initialize auth service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.user_service = UserService(db=db)
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = ""
    ) -> Tuple[User, str]:
        """
        Register a new user with email and password.
        
        Args:
            username: Unique username
            email: User email address
            password: Plain text password to hash
            full_name: Optional full name
            
        Returns:
            Tuple of (User object, message)
            
        Raises:
            ValueError: If user already exists or validation fails
        """
        # Validate input
        if not username or not email or not password:
            raise ValueError("Username, email, and password are required")
        
        # Check if user exists
        existing_user = self.user_service.get_user_by_username(username)
        if existing_user:
            raise ValueError(f"Username '{username}' is already taken")
        
        existing_email = self.user_service.get_user_by_email(email)
        if existing_email:
            raise ValueError(f"Email '{email}' is already registered")
        
        # Hash password
        try:
            hashed_password = hash_password(password)
        except ValueError as e:
            raise ValueError(f"Password validation failed: {str(e)}")
        
        # Create user
        try:
            user = self.user_service.create_user(
                username=username,
                email=email,
                password=hashed_password,
                full_name=full_name
            )
            logger.info(f"User registered: {username} ({email})")
            return user, f"User '{username}' registered successfully"
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise ValueError(f"Failed to register user: {str(e)}")
    
    def login_user(
        self,
        username: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Authenticate user with username/email and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            Tuple of (User object, access_token, refresh_token)
            
        Raises:
            ValueError: If credentials are invalid
        """
        if not username or not password:
            raise ValueError("Username and password are required")
        
        # Try to get user by username or email
        user = self.user_service.get_user_by_username(username)
        if not user:
            user = self.user_service.get_user_by_email(username)
        
        if not user:
            logger.warning(f"Login attempt with non-existent user: {username}")
            raise ValueError("Invalid username or password")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt by inactive user: {username}")
            raise ValueError("User account is inactive")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {username}")
            raise ValueError("Invalid username or password")
        
        # Create tokens
        try:
            access_token = create_access_token(
                data={"sub": str(user.id)},
                expires_delta=timedelta(minutes=30)
            )
            
            # Create longer-lived refresh token
            refresh_token = create_access_token(
                data={"sub": str(user.id), "type": "refresh"},
                expires_delta=timedelta(days=7)
            )
            
            logger.info(f"User logged in: {username}")
            return user, access_token, refresh_token
        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            raise ValueError(f"Login failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate a new access token from a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            ValueError: If refresh token is invalid or expired
        """
        if not refresh_token:
            raise ValueError("Refresh token is required")
        
        try:
            # Verify refresh token
            payload = verify_token(refresh_token)
            
            # Check token type
            if payload.get("type") != "refresh":
                raise ValueError("Invalid refresh token")
            
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid refresh token payload")
            
            # Create new access token
            new_access_token = create_access_token(
                data={"sub": user_id},
                expires_delta=timedelta(minutes=30)
            )
            
            logger.info(f"Access token refreshed for user: {user_id}")
            return new_access_token
        except JWTError as e:
            logger.warning(f"Refresh token verification failed: {str(e)}")
            raise ValueError(f"Invalid or expired refresh token: {str(e)}")
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise ValueError(f"Failed to refresh token: {str(e)}")
    
    def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.
        
        Args:
            token: JWT access token
            
        Returns:
            User object
            
        Raises:
            ValueError: If token is invalid or user not found
        """
        if not token:
            raise ValueError("Token is required")
        
        try:
            user_id = get_user_from_token(token)
            if not user_id:
                raise ValueError("Invalid token payload")
            
            user = self.user_service.get_user(user_id=user_id)
            if not user:
                raise ValueError("User not found")
            
            if not user.is_active:
                raise ValueError("User account is inactive")
            
            return user
        except JWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise ValueError(f"Invalid or expired token: {str(e)}")
        except Exception as e:
            logger.error(f"User lookup failed: {str(e)}")
            raise ValueError(f"Failed to get current user: {str(e)}")
    
    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, message)
            
        Raises:
            ValueError: If validation fails
        """
        if not old_password or not new_password:
            raise ValueError("Both passwords are required")
        
        if old_password == new_password:
            raise ValueError("New password must be different from current password")
        
        # Get user
        user = self.user_service.get_user(user_id=user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Hash new password
        try:
            hashed_password = hash_password(new_password)
            user.hashed_password = hashed_password
            self.db.commit()
            
            logger.info(f"Password changed for user: {user.username}")
            return True, "Password changed successfully"
        except Exception as e:
            self.db.rollback()
            logger.error(f"Password change failed: {str(e)}")
            raise ValueError(f"Failed to change password: {str(e)}")
    
    @staticmethod
    def create_auth_service(db: Optional[Session] = None) -> "AuthService":
        """
        Factory method to create AuthService with database session.
        
        Args:
            db: Optional database session (creates new if not provided)
            
        Returns:
            AuthService instance
        """
        if db is None:
            db = SessionLocal()
        
        return AuthService(db=db)
