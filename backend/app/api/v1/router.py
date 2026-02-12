"""Main API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, agents, notifications, subscriptions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(
    subscriptions.router, prefix="/subscriptions", tags=["subscriptions"]
)
