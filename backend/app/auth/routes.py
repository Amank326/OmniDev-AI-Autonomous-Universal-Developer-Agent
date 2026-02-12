"""Authentication routes - Register, Login, Refresh Token endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from .schemas import (
    UserRegister, UserLogin, Token, UserResponse, 
    RefreshTokenRequest, ChangePasswordRequest, AuthError
)
from .service import AuthService
from .dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": AuthError, "description": "Validation error"},
        409: {"model": AuthError, "description": "User already exists"},
    }
)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user.
    
    - **username**: Unique username (3-50 chars)
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: Optional full name
    
    Returns registered user information.
    """
    try:
        auth_service = AuthService(db=db)
        user, message = auth_service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        logger.info(f"New user registered: {user.username}")
        return UserResponse.model_validate(user)
    except ValueError as e:
        logger.warning(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": AuthError, "description": "Invalid credentials"},
    }
)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
) -> Token:
    """
    Login user and receive access token.
    
    - **username**: Username or email
    - **password**: User password
    
    Returns JWT tokens and user information.
    """
    try:
        auth_service = AuthService(db=db)
        user, access_token, refresh_token = auth_service.login_user(
            username=credentials.username,
            password=credentials.password
        )
        
        logger.info(f"User logged in: {user.username}")
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user_id=str(user.id),
            username=user.username
        )
    except ValueError as e:
        logger.warning(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": AuthError, "description": "Invalid or expired refresh token"},
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token.
    """
    try:
        auth_service = AuthService(db=db)
        new_access_token = auth_service.refresh_access_token(request.refresh_token)
        
        logger.info("Token refreshed successfully")
        return Token(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=1800,
            user_id="unknown",  # Would need to extract from token in production
            username="unknown"
        )
    except ValueError as e:
        logger.warning(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": AuthError, "description": "Not authenticated"},
    }
)
async def get_current_user_info(
    current_user = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user information.
    
    Requires valid JWT access token in Authorization header.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": AuthError, "description": "Invalid password"},
        401: {"model": AuthError, "description": "Not authenticated"},
    }
)
async def change_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Change user password.
    
    Requires valid JWT access token.
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    try:
        auth_service = AuthService(db=db)
        success, message = auth_service.change_password(
            user_id=str(current_user.id),
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        logger.info(f"Password changed for user: {current_user.username}")
        return {"success": success, "message": message}
    except ValueError as e:
        logger.warning(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during password change: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post(
    "/logout",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def logout(current_user = Depends(get_current_user)) -> dict:
    """
    Logout user (client-side token removal).
    
    Note: JWT tokens are stateless. The client should remove the token.
    In production, consider maintaining a token blacklist for revocation.
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Logged out successfully"}
