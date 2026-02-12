"""Authentication dependencies for FastAPI dependency injection"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from .utils import get_user_from_token
from .service import AuthService
from jose import JWTError

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token from header
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        user_id = get_user_from_token(token)
        if not user_id:
            raise ValueError("Invalid token")
        
        auth_service = AuthService(db=db)
        user = auth_service.user_service.get_user(user_id=user_id)
        
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise ValueError("User not found")
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.username}")
            raise ValueError("User is inactive")
        
        return user
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


async def get_admin_user(
    current_user = Depends(get_current_user)
):
    """
    Get current user and verify admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object (if admin)
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user attempted admin action: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def get_optional_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current user if token provided, return None otherwise.
    
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer token
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials or not credentials.credentials:
        return None
    
    try:
        return await get_current_user(credentials=credentials, db=db)
    except HTTPException:
        return None
