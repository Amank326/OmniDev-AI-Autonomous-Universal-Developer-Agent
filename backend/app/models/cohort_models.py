"""Phase 8: Advanced Cohort & Retention Analysis Models - SQLite Compatible

Simplified ORM models for Phase 8 advanced analytics without FK constraints for SQLite compatibility.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, func, Index, UniqueConstraint
from datetime import datetime
import enum

from app.database.config import Base


class CohortType(str, enum.Enum):
    """Types of cohorts for analysis"""
    SIGNUP_MONTH = "signup_month"
    SIGNUP_QUARTER = "signup_quarter"
    SIGNUP_YEAR = "signup_year"
    FIRST_PURCHASE_MONTH = "first_purchase_month"
    FIRST_FEATURE_MONTH = "first_feature_month"
    PRODUCT_TIER = "product_tier"
    GEOGRAPHIC = "geographic"
    COHORT_CUSTOM = "custom"


class MetricType(str, enum.Enum):
    """Types of custom metrics"""
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    CUSTOM_FORMULA = "custom_formula"


class JourneyStage(str, enum.Enum):
    """Customer journey stages"""
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    ACTIVATION = "activation"
    RETENTION = "retention"
    REVENUE = "revenue"
    ADVOCACY = "advocacy"
    CHURN = "churn"


class InterventionStatus(str, enum.Enum):
    """Status of churn interventions"""
    SUGGESTED = "suggested"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============= PHASE 8 TABLES =============

class CohortAnalysis(Base):
    """Core cohort analysis table"""
    __tablename__ = 'cohort_analysis'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    cohort_type = Column(String(50), nullable=False)
    cohort_name = Column(String(100), nullable=False)
    cohort_date = Column(DateTime, nullable=False)
    size = Column(Integer, nullable=False)
    active_count = Column(Integer, nullable=False)
    retention_rate = Column(Float, nullable=False)
    avg_engagement_score = Column(Float)
    avg_api_calls = Column(Float)
    avg_revenue_per_user = Column(Float)
    churn_rate = Column(Float)
    days_to_churn_avg = Column(Integer)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_cohort_customer', 'customer_id'),
        Index('idx_cohort_type_date', 'cohort_type', 'cohort_date'),
        Index('idx_cohort_name', 'cohort_name'),
        Index('idx_cohort_retention', 'retention_rate'),
    )


class RetentionCurve(Base):
    """Retention curve data - Tracks cohort retention over time"""
    __tablename__ = 'retention_curve'
    
    id = Column(Integer, primary_key=True)
    cohort_id = Column(Integer, nullable=False)
    customer_id = Column(Integer, nullable=False)
    days_since_cohort = Column(Integer, nullable=False)
    period_label = Column(String(50), nullable=False)
    retained_count = Column(Integer, nullable=False)
    retention_percentage = Column(Float, nullable=False)
    active_in_period = Column(Boolean, nullable=False)
    api_calls_in_period = Column(Integer, nullable=False)
    revenue_in_period = Column(Float, nullable=False)
    features_used = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_retention_cohort_period', 'cohort_id', 'days_since_cohort'),
        Index('idx_retention_customer_period', 'customer_id', 'days_since_cohort'),
        Index('idx_retention_percentage', 'retention_percentage'),
    )


class LifetimeValue(Base):
    """Customer Lifetime Value (LTV) calculations"""
    __tablename__ = 'lifetime_value'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    historical_ltv = Column(Float, nullable=False)
    months_active = Column(Integer, nullable=False)
    arpu = Column(Float, nullable=False)
    projected_ltv = Column(Float, nullable=False)
    projection_confidence = Column(Float)
    ltv_tier = Column(String(50))
    ltv_percentile = Column(Float)
    ltv_if_retained_12mo = Column(Float)
    ltv_if_churn_today = Column(Float)
    ltv_if_upsell = Column(Float)
    retention_probability_12mo = Column(Float)
    churn_risk_score = Column(Float)
    calculated_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_ltv_customer', 'customer_id'),
        Index('idx_ltv_historical', 'historical_ltv'),
        Index('idx_ltv_projected', 'projected_ltv'),
        Index('idx_ltv_tier', 'ltv_tier'),
        Index('idx_ltv_percentile', 'ltv_percentile'),
    )


class CustomerJourney(Base):
    """Maps customer journey through AARRR funnel"""
    __tablename__ = 'customer_journey'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    ltv_id = Column(Integer, nullable=False)
    current_stage = Column(String(50), nullable=False)
    stage_entry_date = Column(DateTime, nullable=False)
    days_in_stage = Column(Integer, nullable=False)
    awareness_date = Column(DateTime)
    consideration_date = Column(DateTime)
    activation_date = Column(DateTime)
    retention_date = Column(DateTime)
    revenue_date = Column(DateTime)
    advocacy_date = Column(DateTime)
    churn_date = Column(DateTime)
    time_to_activation_days = Column(Integer)
    time_to_first_revenue_days = Column(Integer)
    time_in_retention_months = Column(Integer)
    features_adopted = Column(Integer, nullable=False)
    integration_count = Column(Integer, nullable=False)
    team_size = Column(Integer)
    engagement_trajectory = Column(String(50))
    momentum_score = Column(Float)
    at_risk = Column(Boolean, default=False)
    risk_factors = Column(JSON)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_journey_customer', 'customer_id'),
        Index('idx_journey_stage', 'current_stage'),
        Index('idx_journey_momentum', 'momentum_score'),
        Index('idx_journey_at_risk', 'at_risk'),
    )


class ChurnFlow(Base):
    """Maps customer journey towards churn"""
    __tablename__ = 'churn_flow'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    churn_probability = Column(Float, nullable=False)
    risk_level = Column(String(20))
    days_to_churn_predicted = Column(Integer)
    activity_decline = Column(Boolean, default=False)
    feature_usage_drop = Column(Boolean, default=False)
    api_call_decrease = Column(Boolean, default=False)
    engagement_score_drop = Column(Boolean, default=False)
    support_tickets_increase = Column(Boolean, default=False)
    intervention_offered = Column(Boolean, default=False)
    intervention_type = Column(String(100))
    intervention_date = Column(DateTime)
    intervention_accepted = Column(Boolean)
    churned = Column(Boolean, default=False)
    churn_date = Column(DateTime)
    save_successful = Column(Boolean)
    signals_detected = Column(Integer)
    signal_names = Column(JSON)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_churn_flow_customer', 'customer_id'),
        Index('idx_churn_flow_probability', 'churn_probability'),
        Index('idx_churn_flow_risk_level', 'risk_level'),
        Index('idx_churn_flow_churned', 'churned'),
        Index('idx_churn_flow_intervention', 'intervention_offered'),
    )


class FeatureAdoption(Base):
    """Tracks feature adoption patterns"""
    __tablename__ = 'feature_adoption'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    feature_name = Column(String(100), nullable=False)
    feature_category = Column(String(50))
    first_used_at = Column(DateTime, nullable=False)
    days_to_adopt = Column(Integer)
    usage_count = Column(Integer, nullable=False)
    usage_frequency = Column(String(20))
    last_used_at = Column(DateTime)
    impact_on_retention = Column(Float)
    correlated_with_upgrade = Column(Boolean)
    cohort_adoption_rate = Column(Float)
    early_adopter = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_feature_adoption_customer_feature', 'customer_id', 'feature_name'),
        Index('idx_feature_adoption_days_to_adopt', 'days_to_adopt'),
        Index('idx_feature_adoption_usage_frequency', 'usage_frequency'),
        Index('idx_feature_adoption_impact', 'impact_on_retention'),
    )


class RetentionIntervention(Base):
    """Tracks interventions designed to prevent churn"""
    __tablename__ = 'retention_intervention'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    churn_flow_id = Column(Integer, nullable=False)
    intervention_type = Column(String(50), nullable=False)
    intervention_name = Column(String(255), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    offered_at = Column(DateTime, nullable=False)
    offered_by = Column(String(100))
    status = Column(String(50), nullable=False)
    accepted_at = Column(DateTime)
    accepted = Column(Boolean)
    revenue_impact = Column(Float)
    churn_prevented = Column(Boolean)
    retention_extension = Column(Integer)
    success = Column(Boolean)
    roi = Column(Float)
    notes = Column(String(500))
    
    __table_args__ = (
        Index('idx_intervention_customer', 'customer_id'),
        Index('idx_intervention_type', 'intervention_type'),
        Index('idx_intervention_status', 'status'),
        Index('idx_intervention_accepted', 'accepted'),
        Index('idx_intervention_success', 'success'),
    )


class CustomMetric(Base):
    """User-defined custom metrics"""
    __tablename__ = 'custom_metric'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    metric_type = Column(String(50), nullable=False)
    formula = Column(String(1000))
    source_table = Column(String(100))
    source_fields = Column(JSON)
    time_period = Column(String(50))
    aggregation = Column(String(50))
    last_calculated = Column(DateTime)
    current_value = Column(Float)
    previous_value = Column(Float)
    change_percentage = Column(Float)
    trend_direction = Column(String(20))
    threshold_warning = Column(Float)
    threshold_critical = Column(Float)
    is_public = Column(Boolean, default=False)
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_custom_metric_customer', 'customer_id'),
        Index('idx_custom_metric_name', 'name'),
        Index('idx_custom_metric_type', 'metric_type'),
        UniqueConstraint('customer_id', 'name', name='uq_custom_metric_customer_name'),
    )


class MetricHistory(Base):
    """Time series history of custom metric values"""
    __tablename__ = 'metric_history'
    
    id = Column(Integer, primary_key=True)
    metric_id = Column(Integer, nullable=False)
    customer_id = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False)
    change_from_previous = Column(Float)
    percent_change = Column(Float)
    
    __table_args__ = (
        Index('idx_metric_history_metric_recorded', 'metric_id', 'recorded_at'),
        Index('idx_metric_history_customer_recorded', 'customer_id', 'recorded_at'),
    )
