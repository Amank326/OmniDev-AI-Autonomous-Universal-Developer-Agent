"""Subscription and payment endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.subscription import Subscription
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
)

router = APIRouter()


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new subscription."""
    new_subscription = Subscription(**subscription_data.model_dump())
    db.add(new_subscription)
    await db.commit()
    await db.refresh(new_subscription)
    return new_subscription


@router.get("/user/{user_id}", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get subscriptions for a specific user."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscriptions = result.scalars().all()
    return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get subscription by ID."""
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a subscription."""
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    subscription.cancel_at_period_end = True
    await db.commit()
    return None
