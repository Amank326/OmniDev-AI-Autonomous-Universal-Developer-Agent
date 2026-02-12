"""Role-Based Access Control (RBAC) utilities"""

from functools import wraps
from fastapi import HTTPException, status
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin role for endpoint.
    
    Usage:
        @app.get("/admin/users")
        @require_admin
        async def get_all_users(current_user = Depends(get_current_user)):
            # Only admins can access
            pass
    
    Args:
        func: Endpoint function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args, current_user=None, **kwargs):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        if not current_user.is_admin:
            logger.warning(f"Non-admin user attempted admin action: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return await func(*args, current_user=current_user, **kwargs)
    
    return wrapper


def require_active(func: Callable) -> Callable:
    """
    Decorator to require active user status.
    
    Usage:
        @app.post("/projects")
        @require_active
        async def create_project(current_user = Depends(get_current_user)):
            # Only active users can create projects
            pass
    
    Args:
        func: Endpoint function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args, current_user=None, **kwargs):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        if not current_user.is_active:
            logger.warning(f"Inactive user attempted action: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return await func(*args, current_user=current_user, **kwargs)
    
    return wrapper


class RoleCheck:
    """Class-based role checking for more complex scenarios"""
    
    def __init__(self, *required_roles):
        """
        Initialize with required roles.
        
        Args:
            required_roles: Variable number of role requirements
        """
        self.required_roles = required_roles
    
    async def __call__(self, current_user) -> bool:
        """
        Check if user has required roles.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            True if user has required role, False otherwise
        """
        if not current_user:
            return False
        
        # Simple RBAC - extend as needed
        if "admin" in self.required_roles and current_user.is_admin:
            return True
        
        if "user" in self.required_roles and current_user.is_active:
            return True
        
        return False


def check_resource_owner(user_id: str):
    """
    Decorator to verify user owns the resource.
    
    Usage:
        @app.put("/projects/{project_id}")
        @check_resource_owner("owner_id")
        async def update_project(
            project_id: str,
            current_user = Depends(get_current_user),
            db = Depends(get_db)
        ):
            # Only owner can update
            pass
    
    Args:
        owner_field: Field name that contains owner ID
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # Check if user is resource owner
            if str(current_user.id) != str(user_id) and not current_user.is_admin:
                logger.warning(
                    f"User {current_user.username} attempted unauthorized access to resource {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this resource"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    
    return decorator


# Built-in role definitions
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_MODERATOR = "moderator"
ROLE_VIEWER = "viewer"

# Permission definitions
PERMISSION_READ = "read"
PERMISSION_WRITE = "write"
PERMISSION_DELETE = "delete"
PERMISSION_ADMIN = "admin"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    ROLE_ADMIN: [PERMISSION_READ, PERMISSION_WRITE, PERMISSION_DELETE, PERMISSION_ADMIN],
    ROLE_USER: [PERMISSION_READ, PERMISSION_WRITE],
    ROLE_MODERATOR: [PERMISSION_READ, PERMISSION_WRITE, PERMISSION_DELETE],
    ROLE_VIEWER: [PERMISSION_READ],
}
