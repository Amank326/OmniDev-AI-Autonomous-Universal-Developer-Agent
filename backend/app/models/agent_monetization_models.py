"""
Phase 16: Agent Marketplace Monetization Models
- Pricing tiers and dynamic pricing
- Transaction tracking and billing
- Payout management and financial reporting
- Trial and free tier management
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.config import Base
from datetime import datetime
import enum


class PricingTier(Base):
    __tablename__ = "pricing_tiers"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Tier Definition
    name = Column(String(100), nullable=False)  # starter, pro, enterprise
    slug = Column(String(100))
    description = Column(Text)
    
    # Pricing
    monthly_price = Column(Float, nullable=False)  # USD
    annual_price = Column(Float)  # Discounted annual
    setup_fee = Column(Float, default=0.0)
    
    # Features & Limits
    monthly_executions = Column(Integer)  # null = unlimited
    monthly_tokens = Column(Integer)  # null = unlimited
    concurrent_deployments = Column(Integer, default=1)
    priority_support = Column(Boolean, default=False)
    custom_integration = Column(Boolean, default=False)
    sla_uptime = Column(Float, default=99.0)  # percentage
    
    # Features included
    features = Column(JSON, default=list)  # ["advanced_analytics", "priority_queue"]
    
    # Visibility
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])
    subscriptions = relationship("AgentSubscription", back_populates="tier")


class AgentPrice(Base):
    __tablename__ = "agent_prices"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Pricing Strategy
    pricing_model = Column(String(50))  # fixed, per_execution, per_token, freemium, subscription
    base_price = Column(Float, nullable=False)  # Base cost
    currency = Column(String(3), default="USD")
    
    # Per-Execution Model
    price_per_execution = Column(Float)  # If applicable
    
    # Per-Token Model
    price_per_1k_input_tokens = Column(Float)  # Input token cost
    price_per_1k_output_tokens = Column(Float)  # Output token cost
    
    # Free Tier
    has_free_tier = Column(Boolean, default=False)
    free_monthly_executions = Column(Integer, default=0)
    free_monthly_tokens = Column(Integer, default=0)
    
    # Trial
    trial_available = Column(Boolean, default=False)
    trial_days = Column(Integer, default=14)
    trial_monthly_executions = Column(Integer, default=1000)
    trial_monthly_tokens = Column(Integer, default=100000)
    
    # Discounts
    volume_discounts = Column(JSON, default=dict)  # {1000: 0.05, 10000: 0.10}
    annual_discount_percent = Column(Float, default=0.0)
    
    # Validity
    effective_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])


class AgentSubscription(Base):
    __tablename__ = "agent_subscriptions"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    tier_id = Column(String(50), ForeignKey("pricing_tiers.id"), nullable=False)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Subscription Details
    status = Column(String(50), default="active")  # active, paused, cancelled, expired
    billing_cycle = Column(String(50))  # monthly, annual
    
    # Dates
    start_date = Column(DateTime, nullable=False)
    renewal_date = Column(DateTime, nullable=False)
    cancelled_date = Column(DateTime)
    
    # Pricing at time of subscription
    monthly_amount = Column(Float)
    annual_amount = Column(Float)
    
    # Usage Tracking
    executions_used = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    reset_date = Column(DateTime)  # When monthly limits reset
    
    # Metadata
    auto_renew = Column(Boolean, default=True)
    payment_method_id = Column(String(100))  # Stripe payment method ID
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tier = relationship("PricingTier", back_populates="subscriptions")
    agent = relationship("AIAgent", foreign_keys=[agent_id])


class TrialLicense(Base):
    __tablename__ = "trial_licenses"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Trial Details
    status = Column(String(50), default="active")  # active, converted, expired, cancelled
    start_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=False)
    
    # Trial Limits
    monthly_executions = Column(Integer)
    monthly_tokens = Column(Integer)
    
    # Usage
    executions_used = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    
    # Conversion
    converted_to_tier_id = Column(String(50), ForeignKey("pricing_tiers.id"))
    converted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])


class AgentSale(Base):
    __tablename__ = "agent_sales"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    
    # Sale Details
    sale_type = Column(String(50))  # subscription, one_time, execution
    tier_id = Column(String(50), ForeignKey("pricing_tiers.id"))
    
    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Revenue Split
    agent_revenue = Column(Float)  # Author gets 50%
    platform_revenue = Column(Float)  # Platform gets 30%
    referrer_revenue = Column(Float)  # Referrer gets 20%
    referrer_id = Column(String(50))  # Who referred this customer
    
    # Transaction Details
    transaction_date = Column(DateTime, default=datetime.utcnow)
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)
    
    # Status
    status = Column(String(50), default="completed")  # pending, completed, failed, refunded
    payment_id = Column(String(100))  # Stripe payment ID
    refund_id = Column(String(100))
    refund_amount = Column(Float)
    refund_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])
    tier = relationship("PricingTier", foreign_keys=[tier_id])


class AgentPayment(Base):
    __tablename__ = "agent_payments"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    user_id = Column(String(50), ForeignKey("template_authors.id"), nullable=False)
    
    # Payment Details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Payment Method
    payment_type = Column(String(50))  # bank_transfer, stripe, paypal
    payment_method = Column(String(100))  # Account details or payment ID
    
    # Status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed, cancelled
    stripe_transfer_id = Column(String(100))
    
    # Dates
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Metadata
    payment_period_start = Column(DateTime)
    payment_period_end = Column(DateTime)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])


class AgentPayoutBatch(Base):
    __tablename__ = "agent_payout_batches"
    
    id = Column(String(50), primary_key=True)
    
    # Batch Details
    payout_period_start = Column(DateTime, nullable=False)
    payout_period_end = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Amounts
    total_agents = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    total_payments = Column(Integer, default=0)
    
    # Processing
    stripe_batch_id = Column(String(100))
    processing_started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    successful_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    errors = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class RevenueAnalytics(Base):
    __tablename__ = "revenue_analytics"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Time Period
    period_date = Column(String(10))  # YYYY-MM-DD
    period_month = Column(String(7))  # YYYY-MM
    period_year = Column(String(4))  # YYYY
    
    # Sales Metrics
    total_sales = Column(Float, default=0.0)
    new_subscriptions = Column(Integer, default=0)
    recurring_revenue = Column(Float, default=0.0)
    one_time_revenue = Column(Float, default=0.0)
    
    # Customer Metrics
    total_customers = Column(Integer, default=0)
    active_subscribers = Column(Integer, default=0)
    trial_users = Column(Integer, default=0)
    churned_customers = Column(Integer, default=0)
    
    # Revenue Split
    author_revenue = Column(Float, default=0.0)  # 50%
    platform_revenue = Column(Float, default=0.0)  # 30%
    referrer_revenue = Column(Float, default=0.0)  # 20%
    
    # Metrics
    arpu = Column(Float, default=0.0)  # Average Revenue Per User
    mrr = Column(Float, default=0.0)  # Monthly Recurring Revenue
    churn_rate = Column(Float, default=0.0)  # Customer churn percentage
    lifetime_value = Column(Float, default=0.0)  # Estimated LTV
    
    # Discounts Applied
    discount_amount = Column(Float, default=0.0)
    refund_amount = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])


class Discount(Base):
    __tablename__ = "discounts"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"))  # null = platform-wide
    
    # Discount Details
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    # Type
    discount_type = Column(String(50))  # percentage, fixed, free_trial
    discount_value = Column(Float, nullable=False)  # 10 for 10%, 50 for $50
    
    # Restrictions
    max_uses = Column(Integer)  # null = unlimited
    usage_count = Column(Integer, default=0)
    min_purchase_amount = Column(Float)
    applicable_tiers = Column(JSON, default=list)  # empty = all tiers
    
    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])


class FeaturedPlacement(Base):
    __tablename__ = "featured_placements"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Placement Details
    placement_type = Column(String(50))  # homepage, category, trending, sponsored
    position = Column(Integer)  # Order in display
    
    # Duration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Cost
    placement_cost = Column(Float, nullable=False)
    payment_status = Column(String(50), default="pending")  # pending, paid, expired
    
    # Metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    # ROI
    ctr = Column(Float)  # Click-through rate
    conversion_rate = Column(Float)
    revenue_generated = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", foreign_keys=[agent_id])
