"""
Payment and Subscription Models for Stripe Integration

Manages:
- Customer records (Stripe + local)
- Subscription plans and pricing
- Active subscriptions
- Invoices and billing history
- Payment methods
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.config import Base


class PricingTier(str, enum.Enum):
    """Subscription pricing tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription lifecycle states"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    ENDED = "ended"


class PaymentStatus(str, enum.Enum):
    """Payment transaction states"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class StripeCustomer(Base):
    """Stripe customer records linked to app users"""
    __tablename__ = "stripe_customers"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    stripe_customer_id = Column(String(100), nullable=False, unique=True, index=True)
    stripe_account_id = Column(String(100), nullable=True)  # For Connect
    
    # Customer details
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    user = relationship("User", backref="stripe_customer")
    subscriptions = relationship("Subscription", backref="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", backref="customer", cascade="all, delete-orphan")
    payment_methods = relationship("PaymentMethod", backref="customer", cascade="all, delete-orphan")


class PricingPlan(Base):
    """Subscription pricing plans"""
    __tablename__ = "pricing_plans"

    id = Column(String(36), primary_key=True)  # UUID
    
    # Plan details
    tier = Column(Enum(PricingTier), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    price_monthly = Column(Float, nullable=False)  # USD
    price_annual = Column(Float, nullable=True)    # USD (discount if set)
    
    # Trial
    trial_days = Column(Integer, default=14)
    
    # Features (JSON array of feature strings)
    features = Column(JSON, default=list)
    
    # Limits
    max_projects = Column(Integer, nullable=True)      # None = unlimited
    max_tasks_per_project = Column(Integer, nullable=True)
    max_agents = Column(Integer, nullable=True)
    max_api_calls_monthly = Column(Integer, nullable=True)
    storage_gb = Column(Integer, default=10)
    
    # Stripe product/price IDs
    stripe_product_id = Column(String(100), nullable=True)
    stripe_price_id_monthly = Column(String(100), nullable=True)
    stripe_price_id_annual = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    subscriptions = relationship("Subscription", backref="plan")


class Subscription(Base):
    """Active subscriptions for customers"""
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True)  # UUID
    
    # Links
    customer_id = Column(String(36), ForeignKey("stripe_customers.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("pricing_plans.id"), nullable=False)
    
    # Stripe IDs
    stripe_subscription_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Subscription details
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIALING, index=True)
    tier = Column(Enum(PricingTier), nullable=False, index=True)
    
    # Billing cycle
    billing_cycle = Column(String(10), nullable=False)  # "monthly" or "annual"
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    
    # Trial
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    
    # Cancellation
    canceled_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    invoices = relationship("Invoice", backref="subscription", cascade="all, delete-orphan")


class Invoice(Base):
    """Invoices and billing records"""
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True)  # UUID
    
    # Links
    customer_id = Column(String(36), ForeignKey("stripe_customers.id"), nullable=False, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True)
    
    # Stripe IDs
    stripe_invoice_id = Column(String(100), nullable=False, unique=True, index=True)
    stripe_payment_intent_id = Column(String(100), nullable=True)
    
    # Invoice details
    invoice_number = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Amounts (in cents)
    amount_subtotal = Column(Integer, nullable=False)  # cents
    amount_tax = Column(Integer, default=0)
    amount_total = Column(Integer, nullable=False)     # cents
    
    # Dates
    date_created = Column(DateTime, nullable=False)
    date_due = Column(DateTime, nullable=True)
    date_paid = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, index=True)  # "draft", "open", "paid", "void", "uncollectible"
    
    # PDF
    pdf_url = Column(String(500), nullable=True)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class PaymentMethod(Base):
    """Customer payment methods (credit cards, etc)"""
    __tablename__ = "payment_methods"

    id = Column(String(36), primary_key=True)  # UUID
    
    # Links
    customer_id = Column(String(36), ForeignKey("stripe_customers.id"), nullable=False, index=True)
    
    # Stripe ID
    stripe_payment_method_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Type
    type = Column(String(50), nullable=False)  # "card", "sepa_debit", etc
    
    # Card details (if card)
    card_brand = Column(String(50), nullable=True)     # "visa", "mastercard", etc
    card_last4 = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    
    # Default method
    is_default = Column(Boolean, default=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class PaymentTransaction(Base):
    """Payment transaction history"""
    __tablename__ = "payment_transactions"

    id = Column(String(36), primary_key=True)  # UUID
    
    # Links
    customer_id = Column(String(36), ForeignKey("stripe_customers.id"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True)
    
    # Stripe ID
    stripe_charge_id = Column(String(100), nullable=True, unique=True, index=True)
    stripe_payment_intent_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Amount (in cents)
    amount = Column(Integer, nullable=False)  # cents
    currency = Column(String(3), default="usd")
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    
    # Details
    description = Column(Text, nullable=True)
    receipt_url = Column(String(500), nullable=True)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class UsageRecord(Base):
    """Track API usage for billing"""
    __tablename__ = "usage_records"

    id = Column(String(36), primary_key=True)  # UUID
    
    # Links
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("stripe_customers.id"), nullable=False, index=True)
    
    # Usage details
    metric_name = Column(String(100), nullable=False)  # "api_calls", "storage_gb", etc
    quantity = Column(Float, nullable=False)
    
    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Reporting
    reported_to_stripe = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class Coupon(Base):
    """Discount coupons and promo codes"""
    __tablename__ = "coupons"

    id = Column(String(36), primary_key=True)  # UUID
    
    # Code
    code = Column(String(50), nullable=False, unique=True, index=True)
    stripe_coupon_id = Column(String(100), nullable=False, unique=True)
    stripe_promotion_code_id = Column(String(100), nullable=True)
    
    # Discount
    discount_type = Column(String(20), nullable=False)  # "percentage" or "fixed"
    discount_value = Column(Float, nullable=False)      # % or cents
    
    # Restrictions
    max_redemptions = Column(Integer, nullable=True)
    redemption_count = Column(Integer, default=0)
    applicable_tiers = Column(JSON, nullable=True)  # List of tiers this applies to
    
    # Validity
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
