"""Stripe payment service."""

import logging
from typing import Optional, Dict, Any
import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for Stripe payment processing."""

    async def create_customer(self, email: str, name: Optional[str] = None) -> Optional[str]:
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
            )
            return customer.id
        except stripe.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Create a Stripe subscription."""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
            )
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
            }
        except stripe.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            return None

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a Stripe subscription."""
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
            )
            return True
        except stripe.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a payment intent."""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
            )
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
            }
        except stripe.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None


stripe_service = StripeService()
