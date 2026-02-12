"""
Analytics Models for Phase 6: Analytics & Revenue Dashboard

Tracks metrics, revenue, subscriptions, and customer analytics.
Provides data for dashboard aggregation and report generation.
"""

from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.database import Base


class MetricType(str, Enum):
    """Types of metrics tracked in the system"""
    # Revenue metrics
    MRR = "monthly_recurring_revenue"  # Monthly recurring revenue
    ARR = "annual_recurring_revenue"   # Annual recurring revenue
    TOTAL_REVENUE = "total_revenue"    # Total revenue earned
    NEW_REVENUE = "new_revenue"        # Revenue from new subscriptions
    CHURNED_REVENUE = "churned_revenue"  # Revenue lost from cancellations
    
    # Subscription metrics
    ACTIVE_SUBSCRIPTIONS = "active_subscriptions"
    NEW_SUBSCRIPTIONS = "new_subscriptions"
    CHURNED_SUBSCRIPTIONS = "churned_subscriptions"
    TRIAL_CONVERSIONS = "trial_conversions"
    UPGRADE_COUNT = "upgrade_count"
    
    # Customer metrics
    TOTAL_CUSTOMERS = "total_customers"
    NEW_CUSTOMERS = "new_customers"
    CHURNED_CUSTOMERS = "churned_customers"
    CUSTOMER_LIFETIME_VALUE = "customer_lifetime_value"
    AVERAGE_REVENUE_PER_USER = "average_revenue_per_user"


class ChartType(str, Enum):
    """Types of charts for dashboard visualization"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    METRIC = "metric"  # Single metric display


class AnalyticsEvent(Base):
    """
    Tracks individual analytics events (payments, subscriptions, etc)
    Used as the source of truth for metric calculations
    """
    __tablename__ = "analytics_events"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("stripe_customers.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)  # payment, subscription_created, subscription_canceled, etc
    event_source = Column(String(50), nullable=False)  # stripe_webhook, manual, system
    amount = Column(Integer, nullable=True)  # In cents
    currency = Column(String(3), default="usd")
    meta_data = Column(JSON, nullable=True)  # Event-specific data
    occurred_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_analytics_events_customer_id", "customer_id"),
        Index("ix_analytics_events_event_type", "event_type"),
        Index("ix_analytics_events_occurred_at", "occurred_at"),
    )


class RevenueMetric(Base):
    """
    Aggregated revenue metrics calculated daily
    Stores historical revenue data for trend analysis
    """
    __tablename__ = "revenue_metrics"

    id = Column(String(36), primary_key=True)
    metric_type = Column(String(50), nullable=False)  # MRR, ARR, TOTAL_REVENUE, etc
    value = Column(Float, nullable=False)  # Metric value
    currency = Column(String(3), default="usd")
    period_date = Column(DateTime, nullable=False)  # Date of metric calculation
    calculation_method = Column(String(100), nullable=True)  # How metric was calculated
    meta_data = Column(JSON, nullable=True)  # Additional context
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for time-series queries
    __table_args__ = (
        Index("ix_revenue_metrics_type_date", "metric_type", "period_date"),
        Index("ix_revenue_metrics_period_date", "period_date"),
    )


class SubscriptionMetric(Base):
    """
    Subscription-level metrics (count, churn rate, etc)
    Calculated daily for trend tracking
    """
    __tablename__ = "subscription_metrics"

    id = Column(String(36), primary_key=True)
    metric_type = Column(String(50), nullable=False)  # active_subscriptions, new, churned, etc
    value = Column(Integer, nullable=False)
    tier = Column(String(50), nullable=True)  # Filter by pricing tier (optional)
    period_date = Column(DateTime, nullable=False)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_subscription_metrics_type_date", "metric_type", "period_date"),
        Index("ix_subscription_metrics_tier_date", "tier", "period_date"),
    )


class CustomerMetric(Base):
    """
    Per-customer analytics (LTV, ARPU, health score, etc)
    Updated when subscription or payment changes
    """
    __tablename__ = "customer_metrics"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("stripe_customers.id", ondelete="CASCADE"), nullable=False)
    total_revenue = Column(Float, default=0)  # Lifetime revenue in dollars
    payment_count = Column(Integer, default=0)
    average_order_value = Column(Float, default=0)
    lifetime_value = Column(Float, default=0)  # Calculated LTV
    health_score = Column(Integer, default=100)  # 0-100, factors in payment history
    churn_risk = Column(Float, default=0)  # 0-1.0, probability of churning
    days_since_last_payment = Column(Integer, default=0)
    last_payment_date = Column(DateTime, nullable=True)
    mrr_contribution = Column(Float, default=0)  # Monthly revenue from this customer
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_customer_metrics_customer_id", "customer_id"),
        Index("ix_customer_metrics_churn_risk", "churn_risk"),
        Index("ix_customer_metrics_health_score", "health_score"),
    )


class ForecastedMetric(Base):
    """
    Forecasted metrics (predicted revenue, churn, etc)
    Generated by analysis service using historical data
    """
    __tablename__ = "forecasted_metrics"

    id = Column(String(36), primary_key=True)
    metric_type = Column(String(50), nullable=False)  # MRR, ARR, churn_rate, etc
    forecast_date = Column(DateTime, nullable=False)  # Date being forecasted
    predicted_value = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)  # 0-1.0, prediction confidence
    lower_bound = Column(Float, nullable=True)  # Pessimistic estimate
    upper_bound = Column(Float, nullable=True)  # Optimistic estimate
    forecast_method = Column(String(50), nullable=False)  # linear, trend, ml, etc
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta_data = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_forecasted_metrics_type_date", "metric_type", "forecast_date"),
    )


class DashboardWidget(Base):
    """
    Configurable dashboard widgets for user customization
    Users can add/remove/reorder widgets on their analytics dashboard
    """
    __tablename__ = "dashboard_widgets"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("stripe_customers.id", ondelete="CASCADE"), nullable=False)
    widget_name = Column(String(100), nullable=False)  # MRR Chart, Churn Rate, etc
    widget_type = Column(String(50), nullable=False)  # metric, chart, table, etc
    chart_type = Column(String(50), nullable=True)  # line, bar, pie, etc (if widget_type=chart)
    metric_types = Column(JSON, nullable=False)  # Array of MetricTypes to display
    position = Column(Integer, default=0)  # Order on dashboard
    size = Column(String(20), default="medium")  # small, medium, large
    is_active = Column(Boolean, default=True)
    refresh_interval_minutes = Column(Integer, default=15)
    config = Column(JSON, nullable=True)  # Widget-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_dashboard_widgets_customer_id", "customer_id"),
    )


class AnalyticsReport(Base):
    """
    Generated analytics reports (monthly, custom, etc)
    Stores report metadata and download links
    """
    __tablename__ = "analytics_reports"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("stripe_customers.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(50), nullable=False)  # monthly, custom, quarterly, etc
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    file_path = Column(String(500), nullable=True)  # Path to generated report file
    file_format = Column(String(10), default="pdf")  # pdf, csv, json, xlsx
    metrics_included = Column(JSON, nullable=False)  # Array of metrics in report
    generated_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # When download link expires
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_analytics_reports_customer_id", "customer_id"),
        Index("ix_analytics_reports_period", "period_start", "period_end"),
    )


class AnalyticsAlert(Base):
    """
    Alerts for significant business events or anomalies
    Notifies users of important metrics changes
    """
    __tablename__ = "analytics_alerts"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("stripe_customers.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # revenue_drop, churn_spike, trial_low, etc
    metric_type = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=False)  # Threshold that triggered alert
    severity = Column(String(20), default="warning")  # info, warning, critical
    message = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_analytics_alerts_customer_id", "customer_id"),
        Index("ix_analytics_alerts_type", "alert_type"),
    )
