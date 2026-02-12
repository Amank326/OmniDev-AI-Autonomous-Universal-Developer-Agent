"""Phase 8: Cohort Analysis API Routes

Provides REST endpoints for:
- Cohort analysis (creation, retrieval, comparison)
- Retention curve visualization
- Lifetime value projections
- Customer journey mapping
- Churn flow analysis
- Feature adoption tracking
- Intervention management
- Custom metrics definition and calculation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.database.config import get_db
from app.services.cohort_analytics_service import CohortAnalyticsService
from app.models.cohort_models import (
    CohortType, JourneyStage, InterventionStatus, MetricType
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CohortResponse(BaseModel):
    """Cohort analysis response"""
    id: int
    cohort_name: str
    cohort_type: str
    size: int
    active_count: int
    retention_rate: float
    avg_engagement_score: Optional[float]
    churn_rate: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RetentionPointResponse(BaseModel):
    """Single retention curve point"""
    period_label: str
    days_since_cohort: int
    retained_count: int
    retention_percentage: float
    api_calls_in_period: int
    revenue_in_period: float


class RetentionCurveResponse(BaseModel):
    """Complete retention curve"""
    cohort_id: int
    cohort_name: str
    points: List[RetentionPointResponse]
    
    class Config:
        from_attributes = True


class LifetimeValueResponse(BaseModel):
    """Customer LTV projection"""
    customer_id: int
    historical_ltv: float
    projected_ltv: float
    ltv_tier: str
    retention_probability_12mo: float
    ltv_if_retained_12mo: float
    ltv_if_upsell: float
    churn_risk_score: float
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerJourneyResponse(BaseModel):
    """Customer journey mapping"""
    customer_id: int
    current_stage: str
    days_in_stage: int
    engagement_trajectory: Optional[str]
    momentum_score: float
    at_risk: bool
    features_adopted: int
    time_to_activation_days: Optional[int]
    
    class Config:
        from_attributes = True


class ChurnFlowResponse(BaseModel):
    """Churn flow analysis"""
    customer_id: int
    churn_probability: float
    risk_level: str
    signals_detected: int
    activity_decline: bool
    feature_usage_drop: bool
    engagement_score_drop: bool
    intervention_offered: bool
    churned: bool
    
    class Config:
        from_attributes = True


class RetentionInterventionResponse(BaseModel):
    """Intervention details"""
    id: int
    customer_id: int
    intervention_type: str
    intervention_name: str
    status: str
    accepted: bool
    success: bool
    revenue_impact: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomMetricResponse(BaseModel):
    """Custom metric definition"""
    id: int
    name: str
    metric_type: str
    formula: Optional[str]
    current_value: float
    previous_value: Optional[float]
    trend_direction: str
    threshold_warning: Optional[float]
    
    class Config:
        from_attributes = True


class FeatureAdoptionResponse(BaseModel):
    """Feature adoption tracking"""
    customer_id: int
    feature_name: str
    days_to_adopt: int
    usage_count: int
    usage_frequency: str
    early_adopter: bool
    impact_on_retention: Optional[float]
    
    class Config:
        from_attributes = True


# Create router
router = APIRouter(
    prefix="/api/cohorts",
    tags=["cohort-analysis"]
)


# ============================================================================
# COHORT ANALYSIS ENDPOINTS
# ============================================================================

@router.post("/create", response_model=CohortResponse)
async def create_cohort(
    cohort_name: str = Query(..., description="Name of cohort (e.g., 'January 2025')"),
    cohort_type: str = Query(..., description="Type: signup_month, product_tier, etc."),
    customer_ids: List[int] = Query(..., description="List of customer IDs in cohort"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new cohort analysis
    
    **Cohort Types:**
    - signup_month: Group by signup month
    - product_tier: Group by subscription tier
    - geographic: Group by region
    - first_purchase_month: Group by first purchase date
    
    **Example:**
    ```
    POST /api/cohorts/create?cohort_name=January%202025&cohort_type=signup_month&customer_ids=1&customer_ids=2&customer_ids=3
    ```
    """
    try:
        cohort = CohortAnalyticsService.create_cohort_analysis(
            db=db,
            customer_ids=customer_ids,
            cohort_type=CohortType(cohort_type),
            cohort_name=cohort_name,
            cohort_date=datetime.utcnow()
        )
        return cohort
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/retention/{cohort_id}", response_model=RetentionCurveResponse)
async def get_retention_curve(
    cohort_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get retention curve for a cohort
    
    Shows retention percentage at key time intervals:
    - Day 0: Day of signup (100%)
    - Week 1: After 1 week
    - Month 1: After 1 month  
    - Month 3: After 3 months
    - Month 6: After 6 months
    - Month 12: After 1 year
    
    **Example:**
    ```
    GET /api/cohorts/retention/1
    ```
    """
    try:
        curves = CohortAnalyticsService.calculate_retention_curve(db, cohort_id)
        
        from app.models.cohort_models import CohortAnalysis
        cohort = db.query(CohortAnalysis).filter_by(id=cohort_id).first()
        
        return RetentionCurveResponse(
            cohort_id=cohort_id,
            cohort_name=cohort.cohort_name if cohort else "Unknown",
            points=[
                RetentionPointResponse(
                    period_label=curve.period_label,
                    days_since_cohort=curve.days_since_cohort,
                    retained_count=curve.retained_count,
                    retention_percentage=curve.retention_percentage,
                    api_calls_in_period=curve.api_calls_in_period,
                    revenue_in_period=curve.revenue_in_period
                )
                for curve in curves
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/compare", response_model=List[RetentionCurveResponse])
async def compare_cohorts(
    cohort_ids: List[int] = Query(..., description="List of cohort IDs to compare"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare retention curves across multiple cohorts
    
    Shows how different cohorts compare in retention over time
    
    **Example:**
    ```
    GET /api/cohorts/compare?cohort_ids=1&cohort_ids=2&cohort_ids=3
    ```
    """
    try:
        results = []
        for cohort_id in cohort_ids:
            curves = CohortAnalyticsService.calculate_retention_curve(db, cohort_id)
            
            from app.models.cohort_models import CohortAnalysis
            cohort = db.query(CohortAnalysis).filter_by(id=cohort_id).first()
            
            results.append(RetentionCurveResponse(
                cohort_id=cohort_id,
                cohort_name=cohort.cohort_name if cohort else "Unknown",
                points=[
                    RetentionPointResponse(
                        period_label=curve.period_label,
                        days_since_cohort=curve.days_since_cohort,
                        retained_count=curve.retained_count,
                        retention_percentage=curve.retention_percentage,
                        api_calls_in_period=curve.api_calls_in_period,
                        revenue_in_period=curve.revenue_in_period
                    )
                    for curve in curves
                ]
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# LIFETIME VALUE ENDPOINTS
# ============================================================================

@router.get("/ltv/{customer_id}", response_model=LifetimeValueResponse)
async def get_lifetime_value(
    customer_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get LTV projection for customer
    
    Shows:
    - Historical LTV (actual spending)
    - Projected LTV (ML forecast)
    - LTV tier (High/Medium/Low)
    - Scenario analysis (if retained, upsold, etc.)
    - 12-month retention probability
    
    **Example:**
    ```
    GET /api/cohorts/ltv/123
    ```
    """
    try:
        ltv = CohortAnalyticsService.project_lifetime_value(db, customer_id)
        return ltv
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ltv/recalculate")
async def recalculate_ltv_for_all(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recalculate LTV for all customers (batch operation)
    
    Runs ML model to project LTV based on latest data
    """
    try:
        from app.database.models import StripeCustomer
        customers = db.query(StripeCustomer).all()
        
        count = 0
        for customer in customers:
            try:
                CohortAnalyticsService.project_lifetime_value(db, customer.id)
                count += 1
            except:
                continue
        
        return {"updated": count, "total": len(customers)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CUSTOMER JOURNEY ENDPOINTS
# ============================================================================

@router.get("/journey/{customer_id}", response_model=CustomerJourneyResponse)
async def get_customer_journey(
    customer_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get customer journey through AARRR funnel
    
    Shows:
    - Current stage (Awareness → Activation → Revenue → Retention → Advocacy)
    - Days in current stage
    - Engagement trajectory (growing/stable/declining)
    - Risk indicators
    - Feature adoption count
    
    **Example:**
    ```
    GET /api/cohorts/journey/123
    ```
    """
    try:
        journey = CohortAnalyticsService.map_customer_journey(db, customer_id)
        return journey
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/journey-by-stage/{stage}")
async def get_customers_by_stage(
    stage: str,
    limit: int = Query(50, description="Limit results"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all customers at a specific journey stage
    
    **Stages:**
    - awareness
    - consideration
    - activation
    - retention
    - revenue
    - advocacy
    - churn
    
    **Example:**
    ```
    GET /api/cohorts/journey-by-stage/at_risk?limit=100
    ```
    """
    try:
        from app.models.cohort_models import CustomerJourney
        
        journeys = db.query(CustomerJourney)\
            .filter_by(current_stage=JourneyStage(stage))\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return {
            "stage": stage,
            "count": len(journeys),
            "customers": [j.customer_id for j in journeys]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CHURN FLOW ENDPOINTS
# ============================================================================

@router.get("/churn-flow/{customer_id}", response_model=ChurnFlowResponse)
async def get_churn_flow(
    customer_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze customer's churn flow and early warning signals
    
    Detects:
    - Activity decline (>30% drop)
    - Feature usage drop
    - API call decrease
    - Engagement score drop
    - Support ticket increase
    
    **Example:**
    ```
    GET /api/cohorts/churn-flow/123
    ```
    """
    try:
        flow = CohortAnalyticsService.analyze_churn_flow(db, customer_id)
        return flow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/at-risk-customers")
async def get_at_risk_customers(
    limit: int = Query(50),
    offset: int = Query(0),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get customers at high churn risk
    
    Returns customers with churn_probability > 0.7 and/or multiple warning signals
    """
    try:
        from app.models.cohort_models import ChurnFlow
        
        at_risk = db.query(ChurnFlow)\
            .filter(ChurnFlow.churn_probability > 0.7)\
            .order_by(ChurnFlow.churn_probability.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return {
            "count": len(at_risk),
            "customers": [
                {
                    "customer_id": flow.customer_id,
                    "churn_probability": flow.churn_probability,
                    "signals_detected": flow.signals_detected,
                    "risk_level": flow.risk_level
                }
                for flow in at_risk
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# FEATURE ADOPTION ENDPOINTS
# ============================================================================

@router.post("/feature-adoption/{customer_id}/{feature_name}")
async def track_feature_adoption(
    customer_id: int,
    feature_name: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track feature adoption for customer
    
    **Features:**
    - api_webhooks
    - custom_dashboards
    - integrations
    - advanced_analytics
    - team_collaboration
    - sso
    
    **Example:**
    ```
    POST /api/cohorts/feature-adoption/123/api_webhooks
    ```
    """
    try:
        adoption = CohortAnalyticsService.track_feature_adoption(
            db, customer_id, feature_name, first_use=True
        )
        return {
            "customer_id": customer_id,
            "feature": feature_name,
            "usage_count": adoption.usage_count,
            "usage_frequency": adoption.usage_frequency,
            "early_adopter": adoption.early_adopter
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feature-adoption/{customer_id}", response_model=List[FeatureAdoptionResponse])
async def get_feature_adoption(
    customer_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all features adopted by customer
    
    Shows adoption timeline and impact on retention
    """
    try:
        from app.models.cohort_models import FeatureAdoption
        
        adoptions = db.query(FeatureAdoption)\
            .filter_by(customer_id=customer_id)\
            .all()
        
        return adoptions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# INTERVENTION ENDPOINTS
# ============================================================================

@router.post("/interventions", response_model=RetentionInterventionResponse)
async def create_intervention(
    customer_id: int,
    intervention_type: str,
    intervention_name: str,
    description: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create retention intervention for at-risk customer
    
    **Types:**
    - discount: Pricing adjustment
    - upgrade: Feature unlock/upgrade offer
    - training: Personalized training/onboarding
    - support: Dedicated support
    - business_review: Executive check-in
    
    **Example:**
    ```
    POST /api/cohorts/interventions?customer_id=123&intervention_type=discount&intervention_name=20%_discount
    ```
    """
    try:
        from app.models.cohort_models import RetentionIntervention
        
        intervention = RetentionIntervention(
            customer_id=customer_id,
            intervention_type=intervention_type,
            intervention_name=intervention_name,
            description=description,
            status=InterventionStatus.SUGGESTED,
            offered_at=datetime.utcnow()
        )
        
        db.add(intervention)
        db.commit()
        db.refresh(intervention)
        
        return intervention
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/interventions/{intervention_id}/accept")
async def accept_intervention(
    intervention_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark intervention as accepted by customer
    """
    try:
        from app.models.cohort_models import RetentionIntervention
        
        intervention = db.query(RetentionIntervention)\
            .filter_by(id=intervention_id)\
            .first()
        
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")
        
        intervention.accepted = True
        intervention.accepted_at = datetime.utcnow()
        intervention.status = InterventionStatus.IN_PROGRESS
        
        db.commit()
        
        return {"success": True, "message": "Intervention accepted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/interventions/{intervention_id}/effectiveness")
async def evaluate_intervention(
    intervention_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluate intervention effectiveness
    
    Shows:
    - Churn prevented (yes/no)
    - Revenue impact ($)
    - ROI (Return on Investment)
    - Success (yes/no)
    """
    try:
        effectiveness = CohortAnalyticsService.evaluate_intervention_effectiveness(
            db, intervention_id
        )
        return effectiveness
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CUSTOM METRICS ENDPOINTS
# ============================================================================

@router.post("/metrics", response_model=CustomMetricResponse)
async def create_custom_metric(
    name: str,
    metric_type: str,
    formula: Optional[str] = None,
    source_table: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create custom metric for tracking
    
    **Types:**
    - count: Count of rows
    - sum: Sum of values
    - average: Average value
    - percentage: % calculation
    - ratio: Ratio of two metrics
    - custom_formula: Custom SQL formula
    
    **Example:**
    ```
    POST /api/cohorts/metrics?name=API%20Success%20Rate&metric_type=percentage&formula=successful_calls/total_calls
    ```
    """
    try:
        from app.models.cohort_models import CustomMetric
        
        metric = CustomMetric(
            customer_id=current_user.id,
            name=name,
            metric_type=MetricType(metric_type),
            formula=formula,
            source_table=source_table,
            created_by=current_user.email
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        return metric
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics/{metric_id}", response_model=CustomMetricResponse)
async def get_custom_metric(
    metric_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get custom metric definition and current value
    """
    try:
        from app.models.cohort_models import CustomMetric
        
        metric = db.query(CustomMetric)\
            .filter_by(id=metric_id)\
            .first()
        
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        
        return metric
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics/{metric_id}/history")
async def get_metric_history(
    metric_id: int,
    days: int = Query(30, description="Days of history"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get metric value history for trending
    
    Shows metric values over time for chart visualization
    """
    try:
        from app.models.cohort_models import MetricHistory
        
        history = db.query(MetricHistory)\
            .filter_by(metric_id=metric_id)\
            .filter(MetricHistory.recorded_at >= datetime.utcnow() - timedelta(days=days))\
            .order_by(MetricHistory.recorded_at)\
            .all()
        
        return {
            "metric_id": metric_id,
            "days": days,
            "points": [
                {
                    "date": h.recorded_at,
                    "value": h.value,
                    "change": h.percent_change
                }
                for h in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
