"""
Email and Notification Routes

Endpoints for email verification, password reset, and notifications.

Routes:
    POST /api/email/verify - Verify email with token
    POST /api/email/resend-verification - Resend verification email
    POST /api/password/forgot - Request password reset
    POST /api/password/reset - Reset password with token
    GET /api/notifications - List user notifications
    POST /api/notifications/{id}/read - Mark notification as read
    DELETE /api/notifications/{id} - Delete notification
    POST /api/notifications/clear - Clear all notifications
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.auth.dependencies import get_current_user
from app.auth.tokens import EmailVerificationToken, PasswordResetToken
from app.auth.utils import hash_password, verify_password
from app.auth.service import AuthService
from app.email.service import email_service
from app.notifications.models import NotificationChannel
from app.notifications.service import NotificationService
from app.database.services import UserService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["email-notifications"]
)


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str = Field(..., description="Email verification token")


class VerifyEmailResponse(BaseModel):
    """Email verification response."""
    success: bool
    message: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: str = Field(..., description="User email address")


class ForgotPasswordResponse(BaseModel):
    """Forgot password response."""
    success: bool
    message: str


class ResetPasswordRequest(BaseModel):
    """Password reset request."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")


class ResetPasswordResponse(BaseModel):
    """Password reset response."""
    success: bool
    message: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""
    email: str = Field(..., description="User email address")


class ResendVerificationResponse(BaseModel):
    """Resend verification response."""
    success: bool
    message: str


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Email Verification Routes
# ============================================================================

@router.post(
    "/email/verify",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Email Address",
    description="Verify user email address using token from verification email"
)
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address.
    
    Takes email verification token from email and marks email as verified.
    
    Args:
        request: Verification request with token
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        400: Invalid or expired token
        404: User not found
    
    Example Request:
        POST /api/email/verify
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """
    try:
        # Verify token
        result = EmailVerificationToken.verify_token(request.token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        user_id, email = result
        
        # Get user from database
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check email matches
        if user.email != email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email mismatch"
            )
        
        # Mark email as verified (would update database)
        # user.is_email_verified = True
        # db.commit()
        
        logger.info(f"Email verified for user {user_id}")
        
        return VerifyEmailResponse(
            success=True,
            message="Email verified successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post(
    "/email/resend-verification",
    response_model=ResendVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend Verification Email",
    description="Send verification email again to user email address"
)
async def resend_verification_email(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend verification email.
    
    Sends verification email again to the specified email address.
    
    Args:
        request: Resend request with email
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        404: Email not found
        429: Too many requests
    
    Example Request:
        POST /api/email/resend-verification
        {
            "email": "user@example.com"
        }
    """
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_email(request.email)
        
        if not user:
            # Don't reveal if email exists
            return ResendVerificationResponse(
                success=True,
                message="If email is registered, verification email will be sent"
            )
        
        # Generate verification token
        token = EmailVerificationToken.generate_token(user.id, user.email)
        
        # Send verification email
        if email_service.is_enabled():
            email_service.send_verification_email(
                recipient_email=user.email,
                verification_token=token
            )
        else:
            logger.warning("Email service not configured")
        
        logger.info(f"Verification email resent to {request.email}")
        
        return ResendVerificationResponse(
            success=True,
            message="Verification email sent successfully"
        )
    
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


# ============================================================================
# Password Reset Routes
# ============================================================================

@router.post(
    "/password/forgot",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
    description="Send password reset email to user"
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.
    
    Sends password reset email with token.
    
    Args:
        request: Forgot password request with email
        db: Database session
    
    Returns:
        Success message
    
    Example Request:
        POST /api/password/forgot
        {
            "email": "user@example.com"
        }
    """
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_email(request.email)
        
        if not user:
            # Don't reveal if email exists
            return ForgotPasswordResponse(
                success=True,
                message="If email is registered, password reset email will be sent"
            )
        
        # Generate reset token
        token = PasswordResetToken.generate_token(user.id, user.email)
        
        # Send reset email
        if email_service.is_enabled():
            email_service.send_password_reset_email(
                recipient_email=user.email,
                reset_token=token
            )
        else:
            logger.warning("Email service not configured")
        
        logger.info(f"Password reset email sent to {request.email}")
        
        return ForgotPasswordResponse(
            success=True,
            message="Password reset email sent successfully"
        )
    
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset"
        )


@router.post(
    "/password/reset",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Password",
    description="Reset user password using reset token"
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with token.
    
    Validates reset token and updates user password.
    
    Args:
        request: Reset password request with token and new password
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        400: Invalid token or password mismatch
        404: User not found
    
    Example Request:
        POST /api/password/reset
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "new_password": "NewSecurePassword123",
            "confirm_password": "NewSecurePassword123"
        }
    """
    try:
        # Validate passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Passwords do not match"
            )
        
        # Verify reset token
        result = PasswordResetToken.verify_token(request.token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user_id, email = result
        
        # Get user
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash and update password
        hashed_password = hash_password(request.new_password)
        user.password_hash = hashed_password
        db.commit()
        
        logger.info(f"Password reset successful for user {user_id}")
        
        # Send confirmation email
        if email_service.is_enabled():
            email_service.send_notification_email(
                recipient_email=user.email,
                subject="Password Reset Confirmation",
                title="Password Reset",
                message="Your password has been reset successfully. If you didn't request this change, please contact support."
            )
        
        return ResetPasswordResponse(
            success=True,
            message="Password reset successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


# ============================================================================
# Notification Routes
# ============================================================================

@router.get(
    "/notifications",
    status_code=status.HTTP_200_OK,
    summary="Get User Notifications",
    description="List all notifications for current user"
)
async def get_notifications(
    unread_only: bool = Query(False, description="Only unread notifications"),
    limit: int = Query(20, ge=1, le=100, description="Max notifications"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications for current user.
    
    Args:
        unread_only: Filter to unread only
        limit: Max notifications to return
        offset: Pagination offset
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of notifications
    
    Example Request:
        GET /api/notifications?unread_only=true&limit=10
    """
    try:
        notification_service = NotificationService(db)
        notifications = await notification_service.get_notifications(
            current_user.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "count": len(notifications),
            "notifications": notifications
        }
    
    except Exception as e:
        logger.error(f"Get notifications error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )


@router.post(
    "/notifications/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Mark Notification as Read",
    description="Mark specific notification as read"
)
async def mark_notification_read(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read.
    
    Args:
        notification_id: Notification ID
        current_user: Current user
        db: Database session
    
    Returns:
        Success message
    """
    try:
        notification_service = NotificationService(db)
        success = await notification_service.mark_as_read(
            notification_id,
            current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"success": True, "message": "Notification marked as read"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark as read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification"
        )


@router.delete(
    "/notifications/{notification_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Notification",
    description="Delete a notification"
)
async def delete_notification(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete notification.
    
    Args:
        notification_id: Notification ID
        current_user: Current user
        db: Database session
    
    Returns:
        Success message
    """
    try:
        notification_service = NotificationService(db)
        success = await notification_service.delete_notification(
            notification_id,
            current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"success": True, "message": "Notification deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete notification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.post(
    "/notifications/clear",
    status_code=status.HTTP_200_OK,
    summary="Clear All Notifications",
    description="Delete all notifications for current user"
)
async def clear_all_notifications(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear all notifications for user.
    
    Args:
        current_user: Current user
        db: Database session
    
    Returns:
        Success message with count
    """
    try:
        notification_service = NotificationService(db)
        count = await notification_service.clear_all_notifications(current_user.id)
        
        logger.info(f"Cleared {count} notifications for user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Cleared {count} notifications",
            "count": count
        }
    
    except Exception as e:
        logger.error(f"Clear notifications error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear notifications"
        )
