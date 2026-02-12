"""
Phase 7B: Activity Tracking & Engagement Models

Comprehensive activity tracking, engagement scoring, audit logging, and analytics models
for advanced metrics, real-time dashboards, and AI-powered insights.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, 
    JSON, ForeignKey, Index, Enum as SQLEnum, DECIMAL, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# ==================== ENUMS ====================

class ActivityType(str, Enum):
    """20+ user activity types for comprehensive tracking"""
    # User Activities
    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    SETTINGS_CHANGE = "settings_change"
    
    # Subscription Activities
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    
    # Payment Activities
    PAYMENT_PROCESSED = "payment_processed"
    PAYMENT_FAILED = "payment_failed"
    INVOICE_VIEWED = "invoice_viewed"
    INVOICE_DOWNLOADED = "invoice_downloaded"
    
    # Product/Project Activities
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    PROJECT_SHARED = "project_shared"
    
    # Engagement Activities
    API_CALL = "api_call"
    DASHBOARD_VIEW = "dashboard_view"
    REPORT_GENERATED = "report_generated"
    FEATURE_USED = "feature_used"


class AuditAction(str, Enum):
    """Audit log action types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    INTEGRATE = "integrate"
    DEACTIVATE = "deactivate"


class AnomalyType(str, Enum):
    """Types of detected anomalies"""
    REVENUE_SPIKE = "revenue_spike"
    REVENUE_DROP = "revenue_drop"
    UNUSUAL_TRAFFIC = "unusual_traffic"
    PAYMENT_FAILURE_SPIKE = "payment_failure_spike"
    CHURN_SPIKE = "churn_spike"
    CUSTOMER_INACTIVE = "customer_inactive"
    ENGAGEMENT_DROP = "engagement_drop"


class HealthScore(str, Enum):
    """Customer health score classifications"""
    EXCELLENT = "excellent"  # 85-100
    GOOD = "good"  # 65-84
    FAIR = "fair"  # 45-64
    POOR = "poor"  # 25-44
    CRITICAL = "critical"  # 0-24


# ==================== MODELS ====================

class UserActivity(Base):
    """Log all user actions for activity tracking and engagement analysis"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=False, index=True)
    activity_type = Column(SQLEnum(ActivityType), nullable=False, index=True)
    
    # Activity Details
    description = Column(Text)
    meta_data = Column(JSON)  # Additional activity data (endpoint, params, response)
    duration_ms = Column(Integer)  # Execution time if applicable
    
    # Context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    endpoint = Column(String(255))  # API endpoint or page path
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="activities")
    
    __table_args__ = (
        Index("idx_customer_activity_date", "customer_id", "created_at"),
        Index("idx_activity_type_date", "activity_type", "created_at"),
    )


class EngagementMetrics(Base):
    """Calculate and store engagement scores for customers (0-100 scale)"""
    __tablename__ = "engagement_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), unique=True, nullable=False, index=True)
    
    # Overall Engagement Score (0-100)
    engagement_score = Column(Float, default=0.0, nullable=False)  # 0-100
    
    # Component Scores (contributing to overall)
    login_frequency_score = Column(Float, default=0.0)  # 0-20 (based on logins/month)
    feature_usage_score = Column(Float, default=0.0)  # 0-20 (based on feature diversity)
    api_usage_score = Column(Float, default=0.0)  # 0-20 (based on API calls)
    support_interaction_score = Column(Float, default=0.0)  # 0-20 (based on tickets/issues)
    retention_score = Column(Float, default=0.0)  # 0-20 (based on subscription tenure)
    
    # Activity Metrics
    logins_30d = Column(Integer, default=0)  # Logins in last 30 days
    active_days_30d = Column(Integer, default=0)  # Days with activity in last 30 days
    feature_count_used = Column(Integer, default=0)  # Unique features used
    api_calls_30d = Column(Integer, default=0)  # API calls in last 30 days
    avg_session_duration_min = Column(Float, default=0.0)  # Average session duration in minutes
    
    # Engagement Trends
    last_activity_at = Column(DateTime, nullable=True, index=True)
    days_since_last_activity = Column(Integer, default=0)
    engagement_trend = Column(String(10))  # "increasing", "stable", "declining"
    
    # Risk Indicators
    engagement_declining = Column(Boolean, default=False)  # True if trend is declining
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="engagement_metrics")
    
    __table_args__ = (
        Index("idx_engagement_score", "engagement_score"),
        Index("idx_engagement_trend_date", "engagement_trend", "updated_at"),
    )


class ProjectMetrics(Base):
    """Track metrics per customer project for multi-project engagement"""
    __tablename__ = "project_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    
    # Usage Metrics
    api_calls = Column(Integer, default=0)
    active_endpoints = Column(Integer, default=0)
    data_processed_gb = Column(Float, default=0.0)
    
    # Health Metrics
    error_rate = Column(Float, default=0.0)  # Percentage
    avg_response_time_ms = Column(Float, default=0.0)
    uptime_percentage = Column(Float, default=100.0)
    
    # Engagement
    last_api_call_at = Column(DateTime, nullable=True, index=True)
    days_since_last_call = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="projects")
    
    __table_args__ = (
        Index("idx_project_customer_date", "customer_id", "updated_at"),
    )


class SystemMetrics(Base):
    """Platform-wide system metrics and health indicators"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Traffic Metrics
    total_requests = Column(BigInteger, default=0)
    requests_per_minute = Column(Float, default=0.0)
    unique_active_users = Column(Integer, default=0)
    
    # Performance Metrics
    avg_response_time_ms = Column(Float, default=0.0)
    p95_response_time_ms = Column(Float, default=0.0)
    p99_response_time_ms = Column(Float, default=0.0)
    
    # Reliability Metrics
    success_rate = Column(Float, default=100.0)  # Percentage
    error_rate = Column(Float, default=0.0)  # Percentage
    failure_rate_5xx = Column(Float, default=0.0)  # 5xx errors
    
    # Resource Metrics
    cpu_usage_percent = Column(Float, default=0.0)
    memory_usage_percent = Column(Float, default=0.0)
    database_connection_count = Column(Integer, default=0)
    
    # Business Metrics
    revenue_today = Column(DECIMAL(12, 2), default=0)
    new_subscriptions_today = Column(Integer, default=0)
    canceled_subscriptions_today = Column(Integer, default=0)
    
    # Anomaly Flags
    anomaly_detected = Column(Boolean, default=False)
    anomaly_severity = Column(String(20))  # "low", "medium", "high", "critical"
    
    # Timestamp (hourly/daily aggregate)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index("idx_system_metrics_date", "recorded_at"),
    )


class AuditLog(Base):
    """Comprehensive audit trail for compliance and security"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=False, index=True)
    
    # Audit Details
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # "subscription", "payment", "customer", etc.
    resource_id = Column(String(100), nullable=False)
    
    # Change Details
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    changes_summary = Column(Text)  # Human-readable description
    
    # Context
    actor_id = Column(String(100))  # Who made the change (user or system)
    actor_type = Column(String(50))  # "user", "system", "admin"
    ip_address = Column(String(45))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_customer_action_date", "customer_id", "action", "created_at"),
        Index("idx_resource_type_date", "resource_type", "created_at"),
    )


class AnomalyDetection(Base):
    """Track detected anomalies in customer behavior or system performance"""
    __tablename__ = "anomaly_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=True, index=True)  # None for system-wide
    
    # Anomaly Details
    anomaly_type = Column(SQLEnum(AnomalyType), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    
    # Data
    metric_name = Column(String(100), nullable=False)
    expected_value = Column(Float)
    actual_value = Column(Float)
    deviation_percent = Column(Float)  # Percentage deviation from baseline
    
    # Analysis
    description = Column(Text)
    recommended_action = Column(Text)
    
    # Resolution
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100))
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="anomalies")
    
    __table_args__ = (
        Index("idx_anomaly_severity_date", "severity", "detected_at"),
        Index("idx_anomaly_unresolved", "resolved", "detected_at"),
    )


class ChurnPrediction(Base):
    """ML-powered churn probability predictions for early intervention"""
    __tablename__ = "churn_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), unique=True, nullable=False, index=True)
    
    # Prediction Results
    churn_probability = Column(Float, nullable=False)  # 0.0 to 1.0 (0% to 100%)
    churn_risk_level = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    
    # Contributing Factors
    engagement_score = Column(Float)
    days_since_last_activity = Column(Integer)
    subscription_tenure_days = Column(Integer)
    payment_issues_count = Column(Integer, default=0)
    support_tickets_30d = Column(Integer, default=0)
    
    # Historical Data Points
    avg_monthly_api_calls = Column(Float, default=0.0)
    ltv_percentile = Column(Float)  # Customer's LTV compared to others (0-100)
    
    # Intervention
    intervention_recommended = Column(Boolean, default=False)
    suggested_intervention = Column(String(500))  # e.g., "offer discount", "schedule call", etc.
    
    # Model Info
    model_version = Column(String(50))  # e.g., "v1.0", "v2.1"
    confidence_score = Column(Float)  # Model confidence (0.0-1.0)
    
    # Timestamps
    predicted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="churn_prediction")
    
    __table_args__ = (
        Index("idx_churn_probability", "churn_probability"),
        Index("idx_churn_risk_level", "churn_risk_level"),
    )


class CustomerSegment(Base):
    """ML-powered customer segmentation for targeted strategies"""
    __tablename__ = "customer_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), unique=True, nullable=False, index=True)
    
    # Segment Classification
    segment_name = Column(String(100), nullable=False, index=True)  # e.g., "high-value-disengaged", "growth-potential"
    segment_description = Column(Text)
    
    # Segmentation Metrics
    segment_score = Column(Float, nullable=False)  # 0-1.0, confidence score
    
    # Multi-dimensional Segments
    value_segment = Column(String(50))  # "enterprise", "mid-market", "smb", "starter"
    engagement_segment = Column(String(50))  # "highly-engaged", "moderate", "at-risk", "dormant"
    growth_segment = Column(String(50))  # "high-growth", "stable", "declining"
    
    # Segment Characteristics
    characteristics = Column(JSON)  # Key attributes defining this segment
    recommended_actions = Column(JSON)  # List of recommended strategies
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="segment")
    
    __table_args__ = (
        Index("idx_segment_name", "segment_name"),
        Index("idx_value_engagement", "value_segment", "engagement_segment"),
    )


class PredictiveAlert(Base):
    """AI-generated alerts for proactive business decisions"""
    __tablename__ = "predictive_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=True, index=True)
    
    # Alert Details
    alert_type = Column(String(100), nullable=False, index=True)  # e.g., "churn_risk", "upgrade_opportunity", "payment_issue"
    alert_title = Column(String(255), nullable=False)
    alert_description = Column(Text)
    
    # Priority & Urgency
    priority = Column(String(20), nullable=False)  # "critical", "high", "medium", "low"
    urgency = Column(String(20), nullable=False)  # "immediate", "within_24h", "within_7d", "routine"
    
    # Prediction Confidence
    confidence_score = Column(Float)  # 0.0-1.0
    predicted_impact = Column(String(500))  # What will happen if not addressed
    
    # Recommended Action
    recommended_action = Column(String(500))
    action_owner = Column(String(100))  # Who should handle this
    
    # Status Tracking
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)
    
    action_taken = Column(String(500))
    outcome = Column(String(50))  # "success", "partial", "failed", "pending"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    due_date = Column(DateTime)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="predictive_alerts")
    
    __table_args__ = (
        Index("idx_alert_priority_date", "priority", "created_at"),
        Index("idx_alert_status", "resolved", "dismissed", "created_at"),
    )


class RecommendationEngine(Base):
    """AI-powered recommendations for upsells, features, and engagement"""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=False, index=True)
    
    # Recommendation Details
    recommendation_type = Column(String(100), nullable=False, index=True)  # "upsell", "feature", "plan_change", "engagement"
    recommendation_title = Column(String(255), nullable=False)
    recommendation_description = Column(Text)
    
    # Prediction Data
    recommendation_score = Column(Float, nullable=False)  # 0-100, confidence/priority
    expected_value = Column(DECIMAL(10, 2))  # Expected revenue impact
    expected_acceptance_prob = Column(Float)  # Probability customer accepts (0-1.0)
    
    # Details
    recommended_plan = Column(String(100))  # If applicable
    recommended_feature = Column(String(255))  # If applicable
    additional_cost = Column(DECIMAL(10, 2))  # Monthly cost increase
    projected_roi = Column(String(100))  # e.g., "150% ROI", "2x value"
    
    # Engagement
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    converted = Column(Boolean, default=False)
    converted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime)  # When recommendation is no longer valid
    
    # Relationships
    customer = relationship("StripeCustomer", back_populates="recommendations")
    
    __table_args__ = (
        Index("idx_recommendation_score", "recommendation_score"),
        Index("idx_recommendation_type", "recommendation_type", "created_at"),
    )
