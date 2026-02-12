"""
Payment and Billing Routes

Endpoints for:
- Subscription checkout
- Subscription management
- Invoice retrieval
- Billing portal
- Payment methods
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.config import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from app.auth.dependencies import get_current_user
# from app.models import User  # User model not available, using dict instead
from app.models.payment_models import (
    StripeCustomer,
    Subscription,
    Invoice,
    PricingPlan,
    PricingTier,
    PaymentMethod,
)
from app.services.stripe_service import StripeService
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])


# ============================================================================
# Pydantic Models
# ============================================================================


class PricingPlanResponse(BaseModel):
    """Pricing plan details"""

    id: str
    tier: str
    name: str
    description: Optional[str]
    price_monthly: float
    price_annual: Optional[float]
    trial_days: int
    features: List[str]
    max_projects: Optional[int]
    storage_gb: int

    class Config:
        from_attributes = True


class CheckoutSessionRequest(BaseModel):
    """Request to create a checkout session"""

    tier: PricingTier
    billing_cycle: str  # "monthly" or "annual"
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Checkout session response"""

    session_id: str
    session_url: str


class SubscriptionResponse(BaseModel):
    """Subscription details"""

    id: str
    status: str
    tier: str
    billing_cycle: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime]
    created_at: datetime


class InvoiceResponse(BaseModel):
    """Invoice details"""

    id: str
    invoice_number: str
    amount_total: float
    status: str
    date_created: datetime
    date_paid: Optional[datetime]
    pdf_url: Optional[str]

    class Config:
        from_attributes = True


class BillingPortalResponse(BaseModel):
    """Billing portal session"""

    url: str


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/pricing", response_model=List[PricingPlanResponse])
async def get_pricing_plans(db: Session = Depends(get_db)):
    """Get all available pricing plans"""
    try:
        plans = db.query(PricingPlan).filter(PricingPlan.is_active == True).all()
        return plans
    except Exception as e:
        logger.error(f"Failed to retrieve pricing plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pricing plans")


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe checkout session for subscription"""
    try:
        # Get or create Stripe customer
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == current_user.id
        ).first()

        if not stripe_customer:
            # Create new Stripe customer
            result = StripeService.create_customer(
                email=current_user.email,
                name=current_user.full_name,
                metadata={"user_id": current_user.id},
            )

            if not result.get("success"):
                raise HTTPException(status_code=400, detail="Failed to create Stripe customer")

            stripe_customer = StripeCustomer(
                id=current_user.id,  # Use user ID
                user_id=current_user.id,
                stripe_customer_id=result["stripe_customer_id"],
                email=current_user.email,
                name=current_user.full_name,
            )
            db.add(stripe_customer)
            db.commit()

        # Get pricing plan
        plan = db.query(PricingPlan).filter(PricingPlan.tier == request.tier).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Pricing plan not found")

        # Select price ID based on billing cycle
        stripe_price_id = (
            plan.stripe_price_id_annual
            if request.billing_cycle == "annual"
            else plan.stripe_price_id_monthly
        )

        if not stripe_price_id:
            raise HTTPException(status_code=400, detail="Price not available for this plan")

        # Create checkout session
        result = StripeService.create_checkout_session(
            stripe_customer_id=stripe_customer.stripe_customer_id,
            stripe_price_id=stripe_price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            trial_days=plan.trial_days if request.tier != PricingTier.FREE else None,
            metadata={
                "user_id": current_user.id,
                "tier": request.tier,
                "billing_cycle": request.billing_cycle,
            },
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Checkout failed"))

        return CheckoutSessionResponse(
            session_id=result["session_id"],
            session_url=result["session_url"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_user_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's active subscription"""
    try:
        subscription = db.query(Subscription).join(StripeCustomer).filter(
            StripeCustomer.user_id == current_user.id,
            Subscription.status.in_(["active", "trialing", "past_due"]),
        ).first()

        if not subscription:
            return None

        return SubscriptionResponse(
            id=subscription.id,
            status=subscription.status,
            tier=subscription.tier,
            billing_cycle=subscription.billing_cycle,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            trial_end=subscription.trial_end,
            created_at=subscription.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to retrieve subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")


@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel user's subscription at the end of billing period"""
    try:
        # Get active subscription
        subscription = db.query(Subscription).join(StripeCustomer).filter(
            StripeCustomer.user_id == current_user.id,
            Subscription.status.in_(["active", "trialing", "past_due"]),
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")

        # Cancel with Stripe
        result = StripeService.cancel_subscription(
            subscription.stripe_subscription_id,
            at_period_end=True,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Cancellation failed"))

        # Update subscription status
        subscription.status = "canceled"
        subscription.canceled_at = datetime.utcnow()
        db.commit()

        return {
            "message": "Subscription scheduled for cancellation",
            "subscription_id": subscription.id,
            "canceled_at": subscription.canceled_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_user_invoices(
    current_user: dict = Depends(get_current_user),
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get user's invoices"""
    try:
        invoices = db.query(Invoice).join(StripeCustomer).filter(
            StripeCustomer.user_id == current_user.id
        ).order_by(Invoice.date_created.desc()).limit(limit).all()

        return invoices

    except Exception as e:
        logger.error(f"Failed to retrieve invoices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve invoices")


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific invoice details"""
    try:
        invoice = db.query(Invoice).join(StripeCustomer).filter(
            Invoice.id == invoice_id,
            StripeCustomer.user_id == current_user.id,
        ).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return invoice

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve invoice: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve invoice")


@router.post("/billing-portal", response_model=BillingPortalResponse)
async def create_billing_portal_session(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe billing portal session for customer self-service"""
    try:
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == current_user.id
        ).first()

        if not stripe_customer:
            raise HTTPException(status_code=404, detail="No Stripe customer found")

        # Create billing portal session
        try:
            session = stripe.billing_portal.Session.create(
                customer=stripe_customer.stripe_customer_id,
                return_url="https://your-domain.com/account/billing",
            )

            return BillingPortalResponse(url=session.url)
        except Exception as e:
            logger.error(f"Failed to create billing portal session: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to create billing portal")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create billing portal: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create billing portal")


@router.post("/payment-methods")
async def add_payment_method(
    payment_method_id: str,
    is_default: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a payment method to customer account"""
    try:
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == current_user.id
        ).first()

        if not stripe_customer:
            raise HTTPException(status_code=404, detail="No Stripe customer found")

        # Attach payment method to customer
        try:
            import stripe

            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=stripe_customer.stripe_customer_id,
            )

            if is_default:
                stripe.Customer.modify(
                    stripe_customer.stripe_customer_id,
                    invoice_settings={"default_payment_method": payment_method_id},
                )

        except Exception as e:
            logger.error(f"Failed to attach payment method: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to add payment method")

        return {"message": "Payment method added successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add payment method: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add payment method")


@router.get("/payment-methods")
async def list_payment_methods(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List customer's payment methods"""
    try:
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.user_id == current_user.id
        ).first()

        if not stripe_customer:
            return {"payment_methods": []}

        # Get from database
        payment_methods = db.query(PaymentMethod).filter(
            PaymentMethod.customer_id == stripe_customer.id,
            PaymentMethod.is_active == True,
        ).all()

        return {
            "payment_methods": [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card_brand": pm.card_brand,
                    "card_last4": pm.card_last4,
                    "card_exp_month": pm.card_exp_month,
                    "card_exp_year": pm.card_exp_year,
                    "is_default": pm.is_default,
                }
                for pm in payment_methods
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list payment methods: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list payment methods")


@router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a payment method"""
    try:
        payment_method = db.query(PaymentMethod).filter(
            PaymentMethod.id == payment_method_id
        ).first()

        if not payment_method:
            raise HTTPException(status_code=404, detail="Payment method not found")

        # Verify ownership
        if payment_method.customer.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Detach from Stripe
        try:
            import stripe

            stripe.PaymentMethod.detach(payment_method.stripe_payment_method_id)
        except Exception as e:
            logger.error(f"Failed to detach payment method from Stripe: {str(e)}")

        # Mark as inactive
        payment_method.is_active = False
        db.commit()

        return {"message": "Payment method deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete payment method: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete payment method")
