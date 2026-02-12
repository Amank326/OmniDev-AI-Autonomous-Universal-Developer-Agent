"""Subscription schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.subscription import SubscriptionPlan, SubscriptionStatus


class SubscriptionBase(BaseModel):
    """Base subscription schema."""

    plan: SubscriptionPlan


class SubscriptionCreate(SubscriptionBase):
    """Subscription creation schema."""

    user_id: int
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None


class SubscriptionResponse(SubscriptionBase):
    """Subscription response schema."""

    id: int
    user_id: int
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """Payment creation schema."""

    amount: float
    currency: str = "usd"
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response schema."""

    id: int
    user_id: int
    stripe_payment_id: str
    amount: float
    currency: str
    status: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
