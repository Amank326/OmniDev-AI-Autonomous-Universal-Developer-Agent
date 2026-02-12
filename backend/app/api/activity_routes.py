"""
Phase 7B: Activity Tracking & Audit Logging API Routes

15+ endpoints for activity logs, engagement scoring, audit trails, anomalies,
churn predictions, recommendations, and project metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.advanced_analytics_service import AdvancedAnalyticsService
from app.models.activity_models import (
    UserActivity, EngagementMetrics, AuditLog, AnomalyDetection,
    ChurnPrediction, CustomerSegment, PredictiveAlert, ProjectMetrics,
    RecommendationEngine
)

router = APIRouter(prefix="/api/activity", tags=["activity"])

# ==================== PYDANTIC MODELS ====================

class ActivityLogResponse(BaseModel):
    id: int
    customer_id: int
    activity_type: str
    description: Optional[str]
    endpoint: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EngagementMetricsResponse(BaseModel):
    engagement_score: float
    login_frequency_score: float
    feature_usage_score: float
    api_usage_score: float
    logins_30d: int
    active_days_30d: int
    feature_count_used: int
    last_activity_at: Optional[datetime]
    engagement_trend: Optional[str]
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: str
    changes_summary: Optional[str]
    actor_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnomalyResponse(BaseModel):
    id: int
    anomaly_type: str
    severity: str
    metric_name: str
    expected_value: Optional[float]
    actual_value: Optional[float]
    deviation_percent: Optional[float]
    description: Optional[str]
    detected_at: datetime
    
    class Config:
        from_attributes = True


class ChurnPredictionResponse(BaseModel):
    customer_id: int
    churn_probability: float
    churn_risk_level: str
    engagement_score: Optional[float]
    days_since_last_activity: Optional[int]
    intervention_recommended: bool
    suggested_intervention: Optional[str]
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: int
    recommendation_type: str
    recommendation_title: str
    recommendation_score: float
    expected_value: Optional[Decimal]
    sent: bool
    clicked: bool
    converted: bool
    
    class Config:
        from_attributes = True


class CustomerSegmentResponse(BaseModel):
    customer_id: int
    segment_name: str
    value_segment: str
    engagement_segment: str
    segment_score: float
    
    class Config:
        from_attributes = True


class ProjectMetricsResponse(BaseModel):
    id: int
    project_name: str
    api_calls: int
    active_endpoints: int
    error_rate: float
    avg_response_time_ms: float
    uptime_percentage: float
    last_api_call_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PredictiveAlertResponse(BaseModel):
    id: int
    alert_type: str
    alert_title: str
    priority: str
    urgency: str
    recommended_action: Optional[str]
    acknowledged: bool
    resolved: bool
    
    class Config:
        from_attributes = True


# ==================== ENDPOINTS ====================

# ========== ACTIVITY LOGS (Endpoint 1-3) ==========

@router.get("/logs", response_model=List[ActivityLogResponse])
async def get_activity_logs(
    customer_id: int = Query(..., description="Customer ID"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    days: int = Query(30, description="Days to look back"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get activity logs for a customer (paginated)
    
    **Features:**
    - Filter by customer
    - Pagination support (limit/offset)
    - Time range filtering (days)
    - Real-time activity tracking
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(UserActivity).filter(
        UserActivity.customer_id == customer_id,
        UserActivity.created_at >= start_date
    ).order_by(UserActivity.created_at.desc()).offset(offset).limit(limit).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="No activities found")
    
    return logs


@router.post("/logs/log-event")
async def log_event(
    activity_type: str = Query(...),
    description: Optional[str] = None,
    endpoint: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Log a custom activity event
    
    **Features:**
    - Create custom activity logs
    - Track user actions
    - Store metadata
    """
    activity = AdvancedAnalyticsService.log_user_activity(
        db=db,
        customer_id=user.customer_id,
        activity_type=activity_type,
        description=description,
        endpoint=endpoint
    )
    
    if not activity:
        raise HTTPException(status_code=400, detail="Failed to log activity")
    
    return {"status": "logged", "activity_id": activity.id}


@router.get("/logs/summary")
async def get_activity_summary(
    customer_id: int = Query(...),
    days: int = Query(30),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get activity summary with statistics
    
    **Returns:**
    - Total activities, types breakdown, trends, peak times
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(UserActivity).filter(
        UserActivity.customer_id == customer_id,
        UserActivity.created_at >= start_date
    ).all()
    
    return {
        "total_activities": len(logs),
        "activity_types": len(set(a.activity_type for a in logs)),
        "last_activity": max([a.created_at for a in logs]) if logs else None,
        "days_period": days
    }


# ========== ENGAGEMENT METRICS (Endpoint 4-6) ==========

@router.get("/engagement/{customer_id}", response_model=EngagementMetricsResponse)
async def get_engagement_score(
    customer_id: int,
    period_days: int = Query(30),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get engagement score (0-100) for a customer
    
    **Components (weighted):**
    - Login frequency (20 points)
    - Feature usage (20 points)
    - API usage (20 points)
    - Activity recency (20 points)
    - Subscription tenure (20 points)
    """
    AdvancedAnalyticsService.calculate_engagement_score(
        db=db,
        customer_id=customer_id,
        period_days=period_days
    )
    
    metrics = db.query(EngagementMetrics).filter(
        EngagementMetrics.customer_id == customer_id
    ).first()
    
    if not metrics:
        raise HTTPException(status_code=404, detail="Engagement metrics not found")
    
    return metrics


@router.post("/engagement/recalculate")
async def recalculate_engagement(
    customer_id: int = Query(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Manually trigger engagement score recalculation
    """
    score = AdvancedAnalyticsService.calculate_engagement_score(
        db=db,
        customer_id=customer_id
    )
    return {"engagement_score": score, "updated_at": datetime.utcnow()}


@router.get("/engagement/trends/{customer_id}")
async def get_engagement_trends(
    customer_id: int,
    period_days: int = Query(90),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Analyze engagement trends over time
    
    **Returns:**
    - Trend direction (growth/decline)
    - Weekly activity breakdown
    - Slope/velocity of change
    """
    return AdvancedAnalyticsService.analyze_engagement_trends(
        db=db,
        customer_id=customer_id,
        period_days=period_days
    )


# ========== AUDIT LOGS (Endpoint 7-8) ==========

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    customer_id: int = Query(...),
    resource_type: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get audit log trail for compliance and security
    
    **Features:**
    - Full change tracking
    - Actor attribution
    - Resource type filtering
    - Timestamp audit trail
    """
    query = db.query(AuditLog).filter(AuditLog.customer_id == customer_id)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="No audit logs found")
    
    return logs


@router.post("/audit-logs/create")
async def create_audit_log(
    action: str = Query(...),
    resource_type: str = Query(...),
    resource_id: str = Query(...),
    changes_summary: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Create an audit log entry
    """
    log = AdvancedAnalyticsService.create_audit_log(
        db=db,
        customer_id=user.customer_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes_summary=changes_summary,
        actor_type="user"
    )
    
    if not log:
        raise HTTPException(status_code=400, detail="Failed to create audit log")
    
    return {"status": "created", "log_id": log.id}


# ========== ANOMALY DETECTION (Endpoint 9-10) ==========

@router.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    customer_id: Optional[int] = None,
    severity: Optional[str] = None,
    limit: int = Query(50),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get detected anomalies
    
    **Returns:**
    - System-wide anomalies (customer_id=null)
    - Customer-specific anomalies
    - Anomaly severity and impact
    """
    query = db.query(AnomalyDetection).filter(AnomalyDetection.resolved == False)
    
    if customer_id:
        query = query.filter(AnomalyDetection.customer_id == customer_id)
    
    if severity:
        query = query.filter(AnomalyDetection.severity == severity)
    
    anomalies = query.order_by(AnomalyDetection.detected_at.desc()).limit(limit).all()
    
    return anomalies


@router.post("/anomalies/detect")
async def detect_anomalies_now(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Manually trigger anomaly detection
    """
    anomalies = AdvancedAnalyticsService.detect_anomalies(db=db)
    return {"anomalies_detected": len(anomalies), "results": anomalies}


# ========== CHURN PREDICTION (Endpoint 11-12) ==========

@router.get("/churn/{customer_id}", response_model=ChurnPredictionResponse)
async def get_churn_prediction(
    customer_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get churn probability prediction
    
    **Returns:**
    - Churn probability (0-1.0)
    - Risk level (low/medium/high/critical)
    - Contributing factors
    - Recommended intervention
    """
    prediction = db.query(ChurnPrediction).filter(
        ChurnPrediction.customer_id == customer_id
    ).first()
    
    if not prediction:
        # Calculate if not exists
        AdvancedAnalyticsService.predict_churn(db=db, customer_id=customer_id)
        prediction = db.query(ChurnPrediction).filter(
            ChurnPrediction.customer_id == customer_id
        ).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Churn prediction not available")
    
    return prediction


@router.post("/churn/predict-all")
async def predict_all_churn(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Predict churn for all customers
    """
    results = AdvancedAnalyticsService.predict_churn(db=db)
    high_risk = [r for r in results if r["risk_level"] in ["high", "critical"]]
    
    return {
        "total_predictions": len(results),
        "high_risk_count": len(high_risk),
        "results": results[:20]  # Return top 20
    }


# ========== CUSTOMER SEGMENTATION (Endpoint 13) ==========

@router.get("/segments/{customer_id}", response_model=CustomerSegmentResponse)
async def get_customer_segment(
    customer_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get customer segment classification
    
    **Segments:**
    - Value: Enterprise, Mid-market, SMB, Starter
    - Engagement: Highly-engaged, Moderate, At-risk, Dormant
    - Growth: High-growth, Stable, Declining
    """
    segment = db.query(CustomerSegment).filter(
        CustomerSegment.customer_id == customer_id
    ).first()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return segment


# ========== RECOMMENDATIONS (Endpoint 14) ==========

@router.get("/recommendations/{customer_id}", response_model=List[RecommendationResponse])
async def get_recommendations(
    customer_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get AI-generated recommendations
    
    **Types:**
    - Upsell opportunities
    - Feature adoption
    - Retention offers
    - Plan upgrades
    """
    recs = db.query(RecommendationEngine).filter(
        RecommendationEngine.customer_id == customer_id,
        RecommendationEngine.sent == False
    ).order_by(RecommendationEngine.recommendation_score.desc()).all()
    
    return recs


# ========== PROJECT METRICS (Endpoint 15) ==========

@router.get("/projects/{customer_id}", response_model=List[ProjectMetricsResponse])
async def get_project_metrics(
    customer_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get per-project metrics and health
    
    **Metrics:**
    - API call volume
    - Error rates
    - Response times
    - Uptime percentage
    - Activity recency
    """
    projects = db.query(ProjectMetrics).filter(
        ProjectMetrics.customer_id == customer_id
    ).all()
    
    return projects


# ========== PREDICTIVE ALERTS (Endpoint 16) ==========

@router.get("/alerts", response_model=List[PredictiveAlertResponse])
async def get_predictive_alerts(
    priority: Optional[str] = None,
    resolved: bool = False,
    limit: int = Query(50),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get predictive alerts
    
    **Alert Types:**
    - Churn risk alerts
    - Engagement drops
    - Anomalies detected
    - Payment issues
    - Upgrade opportunities
    """
    query = db.query(PredictiveAlert).filter(PredictiveAlert.resolved == resolved)
    
    if priority:
        query = query.filter(PredictiveAlert.priority == priority)
    
    alerts = query.order_by(PredictiveAlert.created_at.desc()).limit(limit).all()
    
    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Mark alert as acknowledged
    """
    alert = db.query(PredictiveAlert).filter(PredictiveAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = True
    db.commit()
    
    return {"status": "acknowledged"}


# ========== BULK OPERATIONS ==========

@router.post("/segment-all")
async def segment_all_customers(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Segment all customers using ML clustering
    """
    results = AdvancedAnalyticsService.segment_customers(db=db)
    return {"customers_segmented": len(results), "results": results}


@router.post("/generate-recommendations")
async def generate_recommendations_for_customer(
    customer_id: int = Query(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Generate recommendations for a customer
    """
    recs = AdvancedAnalyticsService.generate_recommendations(db=db, customer_id=customer_id)
    return {"recommendations_generated": len(recs), "results": recs}


@router.post("/generate-alerts")
async def generate_alerts(
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Generate predictive alerts for customer(s)
    """
    alerts = AdvancedAnalyticsService.generate_predictive_alerts(
        db=db,
        customer_id=customer_id
    )
    return {"alerts_generated": len(alerts), "results": alerts}
