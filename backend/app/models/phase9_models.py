"""Phase 9: Advanced Analytics Models

Database models for:
- Customer segmentation (K-means clustering)
- Churn prediction
- LTV forecasting
- Recommendations
- Real-time alerts
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.config import Base
import json


class CustomerSegment(Base):
    """Customer segment definition and metadata"""
    __tablename__ = "phase9_customer_segments"
    
    segment_id = Column(Integer, primary_key=True, index=True)
    segment_name = Column(String(100), unique=True, index=True)
    segment_type = Column(String(50), index=True)  # behavioral, rfm, engagement, risk
    customer_count = Column(Integer, default=0)
    
    # Profile summary
    avg_revenue = Column(Float, default=0.0)
    avg_ltv = Column(Float, default=0.0)
    avg_churn_risk = Column(Float, default=0.0)  # 0-1 probability
    engagement_score = Column(Float, default=0.0)  # 0-100
    
    # Clustering metadata
    cluster_center = Column(JSON)  # Stored cluster centroid
    silhouette_score = Column(Float)  # Quality metric (0-1)
    feature_weights = Column(JSON)  # Feature importance in this segment
    
    # Operational
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    profiles = relationship("SegmentProfile", back_populates="segment")
    assignments = relationship("SegmentAssignment", back_populates="segment")
    
    __table_args__ = (
        Index("idx_segment_name_active", "segment_name", "is_active"),
        Index("idx_segment_type_created", "segment_type", "created_at"),
        Index("idx_churn_risk", "avg_churn_risk"),
        Index("idx_engagement_score", "engagement_score"),
    )


class SegmentProfile(Base):
    """Detailed behavioral profile for each segment"""
    __tablename__ = "phase9_segment_profiles"
    
    profile_id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, ForeignKey("phase9_customer_segments.segment_id"), index=True)
    
    # Behavioral metrics
    avg_purchase_frequency = Column(Float)  # purchases per month
    avg_order_value = Column(Float)
    product_diversity = Column(Float)  # number of product categories
    feature_adoption_rate = Column(Float)  # % of available features used
    
    # Engagement metrics
    email_open_rate = Column(Float)
    click_through_rate = Column(Float)
    feature_usage_frequency = Column(Float)  # times per week
    last_active_days_ago = Column(Integer)
    
    # Risk indicators
    churn_risk_score = Column(Float)  # 0-100
    support_tickets_count = Column(Integer)
    complaint_rate = Column(Float)
    
    # Preferences (JSON)
    communication_preferences = Column(JSON)  # channel preferences, frequency
    product_preferences = Column(JSON)  # preferred categories, price points
    
    # Recommendations
    recommended_actions = Column(JSON)  # list of recommended interventions
    success_rate = Column(Float)  # % of recommendations that converted
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    segment = relationship("CustomerSegment", back_populates="profiles")
    
    __table_args__ = (
        Index("idx_segment_id_churn", "segment_id", "churn_risk_score"),
        Index("idx_churn_risk", "churn_risk_score"),
    )


class SegmentAssignment(Base):
    """Track which customers belong to which segments"""
    __tablename__ = "phase9_segment_assignments"
    
    assignment_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)  # Foreign key to customers table
    segment_id = Column(Integer, ForeignKey("phase9_customer_segments.segment_id"), index=True)
    
    # Assignment metadata
    confidence_score = Column(Float)  # 0-1 confidence in this assignment
    distance_to_center = Column(Float)  # ML model distance metric
    feature_vector = Column(JSON)  # Features used for assignment
    
    # Lifecycle
    assigned_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    next_recompute = Column(DateTime)  # When to recalculate assignment
    
    # Relationships
    segment = relationship("CustomerSegment", back_populates="assignments")
    
    __table_args__ = (
        Index("idx_customer_segment", "customer_id", "segment_id"),
        Index("idx_customer_confidence", "customer_id", "confidence_score"),
        Index("idx_assigned_at", "assigned_at"),
    )


class ChurnPrediction(Base):
    """Churn risk predictions for customers"""
    __tablename__ = "phase9_churn_predictions"
    
    prediction_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    
    # Prediction
    churn_probability = Column(Float)  # 0-1, higher = more likely to churn
    risk_level = Column(String(20), index=True)  # low, medium, high, critical
    confidence_score = Column(Float)  # Model confidence (0-1)
    
    # Risk factors
    primary_risk_factor = Column(String(100))  # e.g., "no_activity_60days"
    risk_factors = Column(JSON)  # List of contributing factors with scores
    
    # Intervention
    recommended_action = Column(String(200))  # e.g., "send_special_offer"
    action_effectiveness = Column(Float)  # Expected impact on churn probability
    
    # ML Model info
    model_version = Column(String(50))  # Track which model made this prediction
    feature_importance = Column(JSON)  # Top features affecting prediction
    
    # Lifecycle
    predicted_at = Column(DateTime, default=datetime.utcnow, index=True)
    valid_until = Column(DateTime)  # When prediction becomes stale
    actual_churned = Column(Boolean)  # Known outcome if available
    
    __table_args__ = (
        Index("idx_customer_churn_prob", "customer_id", "churn_probability"),
        Index("idx_customer_predicted_at", "customer_id", "predicted_at"),
        Index("idx_churn_probability", "churn_probability"),
        Index("idx_risk_level", "risk_level"),
    )


class LTVForecast(Base):
    """Lifetime Value forecasts for customers"""
    __tablename__ = "phase9_ltv_forecasts"
    
    forecast_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    
    # Current metrics
    historical_ltv = Column(Float)  # Known LTV to date
    ltv_percentile = Column(Float)  # Where customer ranks (0-100)
    
    # Forecast (next 12 months)
    forecasted_ltv_total = Column(Float)  # Projected total LTV
    forecasted_ltv_monthly = Column(JSON)  # Month-by-month breakdown
    forecasted_revenue_next_12m = Column(Float)
    
    # Confidence & uncertainty
    confidence_level = Column(Float)  # 0-1, higher = more confident
    confidence_interval_low = Column(Float)  # 80% CI lower bound
    confidence_interval_high = Column(Float)  # 80% CI upper bound
    
    # Factors affecting forecast
    trend = Column(String(20))  # increasing, stable, decreasing
    seasonality_adjusted = Column(Boolean, default=True)
    key_drivers = Column(JSON)  # Factors driving this customer's LTV
    
    # Model info
    model_version = Column(String(50))
    forecast_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Validation
    forecast_accuracy_mape = Column(Float)  # Mean Absolute Percentage Error
    last_actual_update = Column(DateTime)
    
    __table_args__ = (
        Index("idx_customer_ltv_total", "customer_id", "forecasted_ltv_total"),
        Index("idx_customer_forecast_date", "customer_id", "forecast_date"),
        Index("idx_forecasted_ltv", "forecasted_ltv_total"),
        Index("idx_ltv_percentile", "ltv_percentile"),
    )


class Recommendation(Base):
    """AI-generated personalized recommendations"""
    __tablename__ = "phase9_recommendations"
    
    recommendation_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    
    # Recommendation details
    recommendation_type = Column(String(50), index=True)  # retention, upsell, cross_sell, reactivation, vip, intervention
    action = Column(String(200))  # Specific action to take
    action_parameters = Column(JSON)  # Parameters for the action (e.g., offer details)
    
    # Reasoning & confidence
    reason = Column(Text)  # Human-readable explanation
    confidence_score = Column(Float)  # 0-1 confidence in recommendation
    expected_impact = Column(Float)  # Expected revenue/retention impact
    
    # Personalization
    personalization_level = Column(String(20))  # generic, segment, individual, dynamic
    segment_id = Column(Integer)  # Which segment informed this recommendation
    
    # A/B Testing
    variant = Column(String(50))  # A/B test variant assignment
    control_group = Column(Boolean, default=False)  # True if control group
    
    # Performance tracking
    delivered = Column(Boolean, default=False, index=True)
    delivered_at = Column(DateTime)
    converted = Column(Boolean)  # True if customer acted on recommendation
    conversion_date = Column(DateTime)
    conversion_value = Column(Float)  # Monetary value if converted
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)  # When recommendation becomes irrelevant
    feedback = Column(String(50))  # user_accepted, user_declined, no_action
    
    __table_args__ = (
        Index("idx_customer_rec_type", "customer_id", "recommendation_type"),
        Index("idx_customer_confidence", "customer_id", "confidence_score"),
        Index("idx_rec_type_converted", "recommendation_type", "converted"),
        Index("idx_created_converted", "created_at", "converted"),
        Index("idx_confidence_score", "confidence_score"),
    )


class DashboardAlert(Base):
    """Real-time alerts for dashboard notifications"""
    __tablename__ = "phase9_dashboard_alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True)
    
    # Alert classification
    alert_type = Column(String(50), index=True)  # churn_risk, revenue_anomaly, segment_shift, prediction_change
    severity = Column(String(20), index=True)  # low, medium, high, critical
    category = Column(String(50))  # business_health, customer_segment, prediction_model
    
    # Content
    title = Column(String(200))
    message = Column(Text)
    details = Column(JSON)  # Additional structured data
    
    # Context
    customer_id = Column(Integer, index=True)  # If alert is customer-specific
    segment_id = Column(Integer)  # If alert is segment-specific
    metric_name = Column(String(100))  # Which metric triggered alert
    metric_value = Column(Float)  # Current value
    threshold_value = Column(Float)  # Alert threshold
    
    # Alerting
    alert_triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)
    resolution_action = Column(String(200))
    
    # Broadcasting
    sent_to_dashboard = Column(Boolean, default=True)
    sent_to_email = Column(Boolean, default=False)
    sent_to_slack = Column(Boolean, default=False)
    
    __table_args__ = (
        Index("idx_alert_type_severity", "alert_type", "severity"),
        Index("idx_alert_triggered", "alert_triggered_at"),
        Index("idx_resolved_triggered", "resolved", "alert_triggered_at"),
        Index("idx_customer_severity", "customer_id", "severity"),
        Index("idx_segment_type", "segment_id", "alert_type"),
    )


class MLModelMetrics(Base):
    """Track performance of deployed ML models"""
    __tablename__ = "phase9_ml_model_metrics"
    
    metric_id = Column(Integer, primary_key=True, index=True)
    
    # Model identification
    model_name = Column(String(100), index=True)  # churn_prediction, ltv_forecast, etc.
    model_version = Column(String(50), index=True)
    
    # Performance metrics
    accuracy = Column(Float)  # Classification accuracy or regression R²
    precision = Column(Float)  # True positives / (true + false positives)
    recall = Column(Float)  # True positives / (true + false negatives)
    f1_score = Column(Float)  # Harmonic mean of precision & recall
    auc_roc = Column(Float)  # Area under ROC curve (0-1)
    
    # Regression metrics (for forecasting)
    mape = Column(Float)  # Mean Absolute Percentage Error
    rmse = Column(Float)  # Root Mean Squared Error
    mae = Column(Float)  # Mean Absolute Error
    
    # Training info
    training_samples = Column(Integer)
    training_completed_at = Column(DateTime)
    
    # Deployment
    deployed = Column(Boolean, default=True, index=True)
    deployed_at = Column(DateTime)
    production_inference_count = Column(Integer, default=0)
    
    # Drift detection
    data_drift_detected = Column(Boolean, default=False)
    model_drift_detected = Column(Boolean, default=False)
    last_drift_check = Column(DateTime)
    
    __table_args__ = (
        Index("idx_model_name_version", "model_name", "model_version"),
        Index("idx_model_deployed", "model_name", "deployed"),
        Index("idx_deployed_at", "deployed_at"),
    )
