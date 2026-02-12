"""
Email verification and password reset utilities.

Generates and validates tokens for email verification and password reset flows.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from app.auth.utils import create_access_token, verify_token
import secrets
import logging

logger = logging.getLogger(__name__)


class EmailVerificationToken:
    """Handles email verification token generation and validation."""
    
    @staticmethod
    def generate_token(user_id: int, email: str, expires_in_seconds: int = 86400) -> str:
        """
        Generate email verification token.
        
        Args:
            user_id: User ID
            email: User email address
            expires_in_seconds: Token expiration time (default 24 hours)
        
        Returns:
            Signed JWT token
        
        Example:
            token = EmailVerificationToken.generate_token(user_id=42, email="user@example.com")
        """
        data = {
            "sub": str(user_id),
            "email": email,
            "type": "email_verification"
        }
        
        token = create_access_token(
            data,
            expires_delta=timedelta(seconds=expires_in_seconds)
        )
        
        logger.debug(f"Email verification token generated for user {user_id}")
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Tuple[int, str]]:
        """
        Verify email verification token.
        
        Args:
            token: JWT token to verify
        
        Returns:
            Tuple of (user_id, email) if valid, None if invalid
        
        Example:
            user_id, email = EmailVerificationToken.verify_token(token)
            if user_id:
                # Token is valid
        """
        try:
            payload = verify_token(token)
            
            # Check token type
            if payload.get("type") != "email_verification":
                logger.warning("Invalid token type for email verification")
                return None
            
            user_id = int(payload.get("sub"))
            email = payload.get("email")
            
            if not email:
                logger.warning("Email missing from token")
                return None
            
            return user_id, email
        
        except Exception as e:
            logger.debug(f"Email verification token validation failed: {str(e)}")
            return None


class PasswordResetToken:
    """Handles password reset token generation and validation."""
    
    @staticmethod
    def generate_token(user_id: int, email: str, expires_in_seconds: int = 3600) -> str:
        """
        Generate password reset token.
        
        Args:
            user_id: User ID
            email: User email address
            expires_in_seconds: Token expiration time (default 1 hour)
        
        Returns:
            Signed JWT token
        
        Example:
            token = PasswordResetToken.generate_token(user_id=42, email="user@example.com")
        """
        data = {
            "sub": str(user_id),
            "email": email,
            "type": "password_reset",
            "nonce": secrets.token_urlsafe(16)
        }
        
        token = create_access_token(
            data,
            expires_delta=timedelta(seconds=expires_in_seconds)
        )
        
        logger.debug(f"Password reset token generated for user {user_id}")
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Tuple[int, str]]:
        """
        Verify password reset token.
        
        Args:
            token: JWT token to verify
        
        Returns:
            Tuple of (user_id, email) if valid, None if invalid
        
        Example:
            user_id, email = PasswordResetToken.verify_token(token)
            if user_id:
                # Token is valid, user can reset password
        """
        try:
            payload = verify_token(token)
            
            # Check token type
            if payload.get("type") != "password_reset":
                logger.warning("Invalid token type for password reset")
                return None
            
            user_id = int(payload.get("sub"))
            email = payload.get("email")
            
            if not email:
                logger.warning("Email missing from token")
                return None
            
            return user_id, email
        
        except Exception as e:
            logger.debug(f"Password reset token validation failed: {str(e)}")
            return None
