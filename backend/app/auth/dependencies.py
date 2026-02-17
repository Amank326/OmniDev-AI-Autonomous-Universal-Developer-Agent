"""Authentication dependencies for FastAPI endpoints.

Re-exports from app.core.security to avoid circular imports.
Also provides the `require_admin` dependency.
"""

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user, get_current_active_user  # noqa: F401
from app.models.user import User, UserRole


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require admin role.

    Returns:
        User model instance (guaranteed to be admin).

    Raises:
        HTTPException: If user is not admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required.",
        )
    return current_user
