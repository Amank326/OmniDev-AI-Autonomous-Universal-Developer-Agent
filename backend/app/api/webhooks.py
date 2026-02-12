"""
Stripe Webhook Handler

Processes Stripe events:
- Subscription created/updated/deleted
- Payment succeeded/failed
- Invoice paid/failed
- Customer updates
"""

from fastapi import APIRouter, Request, status, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import stripe
from typing import Optional

from app.database.config import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.models.payment_models import (
    StripeCustomer,
    Subscription,
    Invoice,
    PaymentMethod,
    SubscriptionStatus,
    PaymentTransaction,
    PaymentStatus,
)
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ============================================================================
# Webhook Event Handlers
# ============================================================================


def handle_customer_created(event: dict, db: Session):
    """Handle customer.created event"""
    customer_data = event["data"]["object"]
    logger.info(f"Customer created: {customer_data['id']}")
    # Customers are created through our checkout flow, so this is informational


def handle_customer_updated(event: dict, db: Session):
    """Handle customer.updated event"""
    customer_data = event["data"]["object"]
    logger.info(f"Customer updated: {customer_data['id']}")

    stripe_customer = db.query(StripeCustomer).filter(
        StripeCustomer.stripe_customer_id == customer_data["id"]
    ).first()

    if stripe_customer:
        stripe_customer.email = customer_data.get("email") or stripe_customer.email
        stripe_customer.name = customer_data.get("name") or stripe_customer.name
        stripe_customer.updated_at = datetime.utcnow()
        db.commit()


def handle_customer_deleted(event: dict, db: Session):
    """Handle customer.deleted event"""
    customer_data = event["data"]["object"]
    logger.info(f"Customer deleted: {customer_data['id']}")

    stripe_customer = db.query(StripeCustomer).filter(
        StripeCustomer.stripe_customer_id == customer_data["id"]
    ).first()

    if stripe_customer:
        stripe_customer.is_active = False
        stripe_customer.updated_at = datetime.utcnow()
        db.commit()


def handle_checkout_session_completed(event: dict, db: Session):
    """Handle checkout.session.completed event"""
    session = event["data"]["object"]
    logger.info(f"Checkout session completed: {session['id']}")

    # Link subscription to customer
    if session.get("subscription"):
        # Subscription will be created via subscription.created event
        logger.info(f"Subscription to be created: {session['subscription']}")


def handle_payment_intent_succeeded(event: dict, db: Session):
    """Handle payment_intent.succeeded event"""
    payment_intent = event["data"]["object"]
    logger.info(f"Payment intent succeeded: {payment_intent['id']}")

    # Record transaction
    customer_id = payment_intent.get("customer")
    if customer_id:
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.stripe_customer_id == customer_id
        ).first()

        if stripe_customer:
            transaction = PaymentTransaction(
                id=f"{payment_intent['id'][:8]}-{datetime.utcnow().timestamp()}",
                customer_id=stripe_customer.id,
                stripe_payment_intent_id=payment_intent["id"],
                stripe_charge_id=payment_intent.get("charges", {}).get("data", [{}])[0].get("id"),
                amount=payment_intent.get("amount"),
                currency=payment_intent.get("currency", "usd"),
                status=PaymentStatus.SUCCEEDED,
                description=payment_intent.get("description"),
                receipt_url=payment_intent.get("charges", {}).get("data", [{}])[0].get("receipt_url"),
            )
            db.add(transaction)
            db.commit()


def handle_payment_intent_payment_failed(event: dict, db: Session):
    """Handle payment_intent.payment_failed event"""
    payment_intent = event["data"]["object"]
    logger.warning(f"Payment intent failed: {payment_intent['id']}")

    customer_id = payment_intent.get("customer")
    if customer_id:
        stripe_customer = db.query(StripeCustomer).filter(
            StripeCustomer.stripe_customer_id == customer_id
        ).first()

        if stripe_customer:
            transaction = PaymentTransaction(
                id=f"{payment_intent['id'][:8]}-{datetime.utcnow().timestamp()}",
                customer_id=stripe_customer.id,
                stripe_payment_intent_id=payment_intent["id"],
                amount=payment_intent.get("amount"),
                currency=payment_intent.get("currency", "usd"),
                status=PaymentStatus.FAILED,
                description=payment_intent.get("description"),
            )
            db.add(transaction)
            db.commit()


def handle_subscription_created(event: dict, db: Session):
    """Handle customer.subscription.created event"""
    subscription_data = event["data"]["object"]
    logger.info(f"Subscription created: {subscription_data['id']}")

    stripe_customer = db.query(StripeCustomer).filter(
        StripeCustomer.stripe_customer_id == subscription_data["customer"]
    ).first()

    if stripe_customer:
        # Get tier from metadata
        tier = subscription_data.get("metadata", {}).get("tier", "starter")
        billing_cycle = subscription_data.get("metadata", {}).get("billing_cycle", "monthly")

        subscription = Subscription(
            id=f"sub-{subscription_data['id'][:8]}",
            customer_id=stripe_customer.id,
            stripe_subscription_id=subscription_data["id"],
            status=SubscriptionStatus[subscription_data["status"].upper()] if subscription_data["status"].upper() in SubscriptionStatus.__members__ else SubscriptionStatus.TRIALING,
            tier=tier,
            billing_cycle=billing_cycle,
            current_period_start=datetime.fromtimestamp(subscription_data["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription_data["current_period_end"]),
            trial_start=datetime.fromtimestamp(subscription_data["trial_start"]) if subscription_data.get("trial_start") else None,
            trial_end=datetime.fromtimestamp(subscription_data["trial_end"]) if subscription_data.get("trial_end") else None,
        )
        db.add(subscription)
        db.commit()
        logger.info(f"Subscription record created for customer {stripe_customer.id}")


def handle_subscription_updated(event: dict, db: Session):
    """Handle customer.subscription.updated event"""
    subscription_data = event["data"]["object"]
    logger.info(f"Subscription updated: {subscription_data['id']}")

    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_data["id"]
    ).first()

    if subscription:
        subscription.status = SubscriptionStatus[subscription_data["status"].upper()] if subscription_data["status"].upper() in SubscriptionStatus.__members__ else subscription.status
        subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
        subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])
        subscription.updated_at = datetime.utcnow()
        db.commit()


def handle_subscription_deleted(event: dict, db: Session):
    """Handle customer.subscription.deleted event"""
    subscription_data = event["data"]["object"]
    logger.info(f"Subscription deleted: {subscription_data['id']}")

    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_data["id"]
    ).first()

    if subscription:
        subscription.status = SubscriptionStatus.ENDED
        subscription.ends_at = datetime.utcnow()
        subscription.canceled_at = datetime.fromtimestamp(subscription_data.get("canceled_at", 0)) if subscription_data.get("canceled_at") else datetime.utcnow()
        subscription.updated_at = datetime.utcnow()
        db.commit()


def handle_invoice_created(event: dict, db: Session):
    """Handle invoice.created event"""
    invoice_data = event["data"]["object"]
    logger.info(f"Invoice created: {invoice_data['id']}")

    stripe_customer = db.query(StripeCustomer).filter(
        StripeCustomer.stripe_customer_id == invoice_data["customer"]
    ).first()

    if stripe_customer:
        subscription = None
        if invoice_data.get("subscription"):
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == invoice_data["subscription"]
            ).first()

        invoice = Invoice(
            id=f"inv-{invoice_data['id'][:8]}",
            customer_id=stripe_customer.id,
            subscription_id=subscription.id if subscription else None,
            stripe_invoice_id=invoice_data["id"],
            invoice_number=invoice_data.get("number", ""),
            description=invoice_data.get("description"),
            amount_subtotal=invoice_data.get("subtotal", 0),
            amount_tax=invoice_data.get("tax", 0),
            amount_total=invoice_data.get("total", 0),
            date_created=datetime.fromtimestamp(invoice_data["created"]),
            date_due=datetime.fromtimestamp(invoice_data["due_date"]) if invoice_data.get("due_date") else None,
            status=invoice_data.get("status", "draft"),
            pdf_url=invoice_data.get("pdf"),
        )
        db.add(invoice)
        db.commit()


def handle_invoice_paid(event: dict, db: Session):
    """Handle invoice.paid event"""
    invoice_data = event["data"]["object"]
    logger.info(f"Invoice paid: {invoice_data['id']}")

    invoice = db.query(Invoice).filter(
        Invoice.stripe_invoice_id == invoice_data["id"]
    ).first()

    if invoice:
        invoice.status = "paid"
        invoice.date_paid = datetime.fromtimestamp(invoice_data.get("paid_at", 0)) if invoice_data.get("paid_at") else datetime.utcnow()
        invoice.updated_at = datetime.utcnow()
        db.commit()


def handle_invoice_payment_failed(event: dict, db: Session):
    """Handle invoice.payment_failed event"""
    invoice_data = event["data"]["object"]
    logger.warning(f"Invoice payment failed: {invoice_data['id']}")

    invoice = db.query(Invoice).filter(
        Invoice.stripe_invoice_id == invoice_data["id"]
    ).first()

    if invoice:
        invoice.status = "open"
        invoice.updated_at = datetime.utcnow()
        db.commit()


def handle_payment_method_attached(event: dict, db: Session):
    """Handle payment_method.attached event"""
    payment_method = event["data"]["object"]
    logger.info(f"Payment method attached: {payment_method['id']}")

    stripe_customer = db.query(StripeCustomer).filter(
        StripeCustomer.stripe_customer_id == payment_method["customer"]
    ).first()

    if stripe_customer and payment_method["type"] == "card":
        card = payment_method.get("card", {})
        db_payment_method = PaymentMethod(
            id=f"pm-{payment_method['id'][:8]}",
            customer_id=stripe_customer.id,
            stripe_payment_method_id=payment_method["id"],
            type=payment_method["type"],
            card_brand=card.get("brand"),
            card_last4=card.get("last4"),
            card_exp_month=card.get("exp_month"),
            card_exp_year=card.get("exp_year"),
        )
        db.add(db_payment_method)
        db.commit()


def handle_payment_method_detached(event: dict, db: Session):
    """Handle payment_method.detached event"""
    payment_method = event["data"]["object"]
    logger.info(f"Payment method detached: {payment_method['id']}")

    pm = db.query(PaymentMethod).filter(
        PaymentMethod.stripe_payment_method_id == payment_method["id"]
    ).first()

    if pm:
        pm.is_active = False
        db.commit()


# ============================================================================
# Event Router
# ============================================================================

EVENT_HANDLERS = {
    "customer.created": handle_customer_created,
    "customer.updated": handle_customer_updated,
    "customer.deleted": handle_customer_deleted,
    "checkout.session.completed": handle_checkout_session_completed,
    "payment_intent.succeeded": handle_payment_intent_succeeded,
    "payment_intent.payment_failed": handle_payment_intent_payment_failed,
    "customer.subscription.created": handle_subscription_created,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.created": handle_invoice_created,
    "invoice.paid": handle_invoice_paid,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "payment_method.attached": handle_payment_method_attached,
    "payment_method.detached": handle_payment_method_detached,
}


@router.post("/stripe")
async def handle_stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle incoming Stripe webhooks"""
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = StripeService.construct_webhook_event(body, sig_header)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook")

        event_type = event["type"]
        logger.info(f"Processing Stripe webhook: {event_type}")

        # Call appropriate handler
        handler = EVENT_HANDLERS.get(event_type)
        if handler:
            handler(event, db)
            logger.info(f"Successfully processed {event_type}")
        else:
            logger.warning(f"No handler for event type: {event_type}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")
