"""
Stripe Service Layer

Handles all interactions with Stripe API:
- Customer management
- Subscription creation/update
- Payment processing
- Invoice management
- Webhook handling
"""

import stripe
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


class StripeService:
    """Service for managing Stripe operations"""

    @staticmethod
    def create_customer(email: str, name: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """Create a new Stripe customer"""
        try:
            customer_data = {
                "email": email,
                "name": name or email,
            }
            if metadata:
                customer_data["metadata"] = metadata

            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Created Stripe customer: {customer.id}")
            return {
                "success": True,
                "stripe_customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    def get_customer(stripe_customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer details from Stripe"""
        try:
            customer = stripe.Customer.retrieve(stripe_customer_id)
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created,
                "metadata": customer.metadata,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer: {str(e)}")
            return None

    @staticmethod
    def create_checkout_session(
        stripe_customer_id: str,
        stripe_price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session"""
        try:
            session_data = {
                "customer": stripe_customer_id,
                "mode": "subscription",
                "line_items": [{"price": stripe_price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "subscription_data": {},
            }

            if trial_days:
                session_data["subscription_data"]["trial_settings"] = {
                    "end_behavior": {"missing_payment_method": "cancel"}
                }
                session_data["subscription_data"]["trial_period_days"] = trial_days

            if metadata:
                session_data["client_reference_id"] = metadata.get("user_id")
                session_data["subscription_data"]["metadata"] = metadata

            session = stripe.checkout.Session.create(**session_data)
            logger.info(f"Created checkout session: {session.id}")
            return {
                "success": True,
                "session_id": session.id,
                "session_url": session.url,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_checkout_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve checkout session details"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "customer": session.customer,
                "subscription": session.subscription,
                "payment_status": session.payment_status,
                "status": session.status,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve session: {str(e)}")
            return None

    @staticmethod
    def create_subscription(
        stripe_customer_id: str,
        stripe_price_id: str,
        trial_days: int = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create a new subscription for a customer"""
        try:
            subscription_data = {
                "customer": stripe_customer_id,
                "items": [{"price": stripe_price_id}],
            }

            if trial_days:
                subscription_data["trial_period_days"] = trial_days

            if metadata:
                subscription_data["metadata"] = metadata

            subscription = stripe.Subscription.create(**subscription_data)
            logger.info(f"Created subscription: {subscription.id}")
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "trial_end": (
                    datetime.fromtimestamp(subscription.trial_end)
                    if subscription.trial_end
                    else None
                ),
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "customer": subscription.customer,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "trial_end": (
                    datetime.fromtimestamp(subscription.trial_end)
                    if subscription.trial_end
                    else None
                ),
                "items": subscription.items.data,
                "metadata": subscription.metadata,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {str(e)}")
            return None

    @staticmethod
    def update_subscription(
        subscription_id: str,
        stripe_price_id: str = None,
        trial_settings: Dict = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Update an existing subscription"""
        try:
            update_data = {}

            if stripe_price_id:
                update_data["items"] = [{"id": stripe.Subscription.retrieve(subscription_id).items.data[0].id, "price": stripe_price_id}]

            if metadata:
                update_data["metadata"] = metadata

            subscription = stripe.Subscription.modify(subscription_id, **update_data)
            logger.info(f"Updated subscription: {subscription.id}")
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def cancel_subscription(
        subscription_id: str, at_period_end: bool = True
    ) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            logger.info(f"Cancelled subscription: {subscription_id}")
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_payment_intent(
        stripe_customer_id: str,
        amount: int,  # in cents
        description: str = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time payments"""
        try:
            intent_data = {
                "amount": amount,
                "currency": "usd",
                "customer": stripe_customer_id,
            }

            if description:
                intent_data["description"] = description

            if metadata:
                intent_data["metadata"] = metadata

            intent = stripe.PaymentIntent.create(**intent_data)
            logger.info(f"Created payment intent: {intent.id}")
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "status": intent.status,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_payment_intent(payment_intent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve payment intent details"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "id": intent.id,
                "amount": intent.amount,
                "status": intent.status,
                "customer": intent.customer,
                "client_secret": intent.client_secret,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment intent: {str(e)}")
            return None

    @staticmethod
    def get_invoices(stripe_customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of invoices for a customer"""
        try:
            invoices = stripe.Invoice.list(customer=stripe_customer_id, limit=limit)
            return [
                {
                    "id": inv.id,
                    "number": inv.number,
                    "amount_due": inv.amount_due,
                    "amount_paid": inv.amount_paid,
                    "status": inv.status,
                    "created": datetime.fromtimestamp(inv.created),
                    "due_date": datetime.fromtimestamp(inv.due_date) if inv.due_date else None,
                    "paid_at": datetime.fromtimestamp(inv.paid_at) if inv.paid_at else None,
                    "pdf_url": inv.pdf,
                }
                for inv in invoices.data
            ]
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoices: {str(e)}")
            return []

    @staticmethod
    def get_invoice(invoice_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve invoice details"""
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return {
                "id": invoice.id,
                "number": invoice.number,
                "customer": invoice.customer,
                "amount_subtotal": invoice.subtotal,
                "amount_tax": invoice.tax,
                "amount_total": invoice.total,
                "status": invoice.status,
                "created": datetime.fromtimestamp(invoice.created),
                "due_date": datetime.fromtimestamp(invoice.due_date) if invoice.due_date else None,
                "paid_at": datetime.fromtimestamp(invoice.paid_at) if invoice.paid_at else None,
                "pdf_url": invoice.pdf,
                "lines": invoice.lines.data,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoice: {str(e)}")
            return None

    @staticmethod
    def create_product(
        name: str,
        description: str = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create a product in Stripe"""
        try:
            product_data = {"name": name}
            if description:
                product_data["description"] = description
            if metadata:
                product_data["metadata"] = metadata

            product = stripe.Product.create(**product_data)
            logger.info(f"Created product: {product.id}")
            return {
                "success": True,
                "product_id": product.id,
                "name": product.name,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create product: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_price(
        product_id: str,
        amount: int,  # in cents
        currency: str = "usd",
        recurring_interval: str = None,  # "month" or "year"
        recurring_interval_count: int = 1,
    ) -> Dict[str, Any]:
        """Create a price for a product"""
        try:
            price_data = {
                "product": product_id,
                "currency": currency,
                "unit_amount": amount,
            }

            if recurring_interval:
                price_data["recurring"] = {
                    "interval": recurring_interval,
                    "interval_count": recurring_interval_count,
                }

            price = stripe.Price.create(**price_data)
            logger.info(f"Created price: {price.id}")
            return {
                "success": True,
                "price_id": price.id,
                "amount": price.unit_amount,
                "currency": price.currency,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create price: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """Verify and construct a webhook event from Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                WEBHOOK_SECRET,
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            return None
