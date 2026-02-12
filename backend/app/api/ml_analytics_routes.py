"""
Phase 17: Advanced ML Analytics Routes
- Pricing optimization endpoints
- Churn prediction endpoints
- Recommendation endpoints
- Cohort analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/v1/analytics", tags=["ml-analytics"])

# Service dependencies (injected from main.py)
pricing_optimizer = None
churn_predictor = None
recommendation_engine = None
cohort_analytics = None


def set_analytics_services(pricing, churn, recommendations, cohorts):
    """Inject services"""
    global pricing_optimizer, churn_predictor, recommendation_engine, cohort_analytics
    pricing_optimizer = pricing
    churn_predictor = churn
    recommendation_engine = recommendations
    cohort_analytics = cohorts


# ============ PRICING OPTIMIZATION ============

@router.post("/pricing/{agent_id}/elasticity-model")
async def train_elasticity_model(
    agent_id: str,
    body: Dict[str, Any] = None,
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Train price elasticity model"""
    try:
        days = body.get("days", 90) if body else 90
        result = pricing_optimizer.train_price_elasticity_model(agent_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pricing/{agent_id}/optimize")
async def optimize_pricing(
    agent_id: str,
    current_price: float = Query(...),
    current_revenue: float = Query(...),
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get pricing recommendations"""
    try:
        result = pricing_optimizer.optimize_pricing(agent_id, current_price, current_revenue)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pricing/revenue-prediction")
async def predict_revenue(
    body: Dict[str, float],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Predict revenue for agent"""
    try:
        result = pricing_optimizer.predict_revenue(body)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pricing/{agent_id}/a-b-test")
async def design_ab_test(
    agent_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Design A/B test for pricing"""
    try:
        result = pricing_optimizer.a_b_test_pricing(
            agent_id=agent_id,
            control_price=body["control_price"],
            test_prices=body["test_prices"],
            sample_size=body.get("sample_size", 100),
            duration_days=body.get("duration_days", 7)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pricing/{agent_id}/insights")
async def get_pricing_insights(
    agent_id: str,
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get pricing insights and recommendations"""
    try:
        result = pricing_optimizer.get_pricing_insights(agent_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ CHURN PREDICTION ============

@router.post("/churn/train-model")
async def train_churn_model(
    body: List[Dict[str, Any]],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Train churn prediction model"""
    try:
        result = churn_predictor.train_churn_model(body)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/churn/predict")
async def predict_churn(
    body: Dict[str, float],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Predict churn probability for user"""
    try:
        result = churn_predictor.predict_churn_probability(body)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/churn/identify-at-risk")
async def identify_at_risk(
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Identify at-risk users"""
    try:
        result = churn_predictor.identify_at_risk_users(
            body.get("users_data", []),
            risk_threshold=body.get("threshold", 0.5)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/churn/{user_id}/interventions")
async def get_retention_interventions(
    user_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get retention interventions for user"""
    try:
        result = churn_predictor.generate_retention_interventions(
            user_data=body.get("user_data", {}),
            churn_probability=body.get("churn_probability", 0.5)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/churn/metrics")
async def get_churn_metrics(
    days: int = Query(30, ge=1, le=365),
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get churn metrics and trends"""
    try:
        result = churn_predictor.track_churn_metrics(days)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/churn/insights")
async def get_churn_insights(
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get churn insights and recommendations"""
    try:
        result = churn_predictor.get_churn_insights()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ RECOMMENDATIONS ============

@router.post("/recommendations/build-matrix")
async def build_recommendation_matrix(
    body: Dict[str, List[Dict[str, Any]]],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Build user-agent interaction matrix"""
    try:
        result = recommendation_engine.build_user_agent_matrix(
            users_data=body.get("users", []),
            agents_data=body.get("agents", [])
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/recommendations/agents")
async def get_agent_recommendations(
    user_id: str,
    limit: int = Query(5, ge=1, le=50),
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get personalized agent recommendations"""
    try:
        # Would fetch user profile and available agents from database
        result = recommendation_engine.personalized_agent_discovery(
            user_id=user_id,
            user_profile={"user_id": user_id},
            available_agents=[],
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/recommendations/tier-upgrade")
async def recommend_tier_upgrade(
    user_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Recommend tier upgrades"""
    try:
        result = recommendation_engine.recommend_tier_upgrade(
            user_id=user_id,
            current_usage=body.get("usage", {}),
            current_tier=body.get("tier", {}),
            available_tiers=body.get("available_tiers", [])
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommendations/system-health")
async def get_recommendation_health(
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get recommendation system health"""
    try:
        result = recommendation_engine.get_recommendation_insights()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ COHORT ANALYSIS ============

@router.post("/cohorts/create")
async def create_cohort(
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Create cohort definition"""
    try:
        result = cohort_analytics.create_cohort_definition(
            cohort_name=body["name"],
            definition_type=body["type"],
            filters=body.get("filters", {})
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cohorts/by-signup-date")
async def build_signup_cohorts(
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Build cohorts by signup date"""
    try:
        result = cohort_analytics.build_signup_cohorts(
            users_data=body.get("users", []),
            bucket_days=body.get("bucket_days", 30)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cohorts/{cohort_id}/retention-curve")
async def get_retention_curve(
    cohort_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get retention curve for cohort"""
    try:
        result = cohort_analytics.calculate_retention_curve(
            cohort_id=cohort_id,
            cohort_members=body.get("members", []),
            subscription_data=body.get("subscriptions", []),
            max_weeks=body.get("max_weeks", 52)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cohorts/{cohort_id}/revenue-analysis")
async def analyze_cohort_revenue(
    cohort_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Analyze revenue for cohort"""
    try:
        result = cohort_analytics.analyze_cohort_revenue(
            cohort_id=cohort_id,
            cohort_members=body.get("members", []),
            transaction_data=body.get("transactions", [])
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cohorts/{cohort_id}/churn-analysis")
async def analyze_cohort_churn(
    cohort_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Analyze churn for cohort"""
    try:
        result = cohort_analytics.analyze_cohort_churn(
            cohort_id=cohort_id,
            cohort_members=body.get("members", []),
            subscription_data=body.get("subscriptions", [])
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cohorts/compare")
async def compare_cohorts(
    body: Dict[str, Dict[str, Any]],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Compare multiple cohorts"""
    try:
        result = cohort_analytics.compare_cohorts(body)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ HEALTH ============

@router.get("/ml-analytics/health")
async def analytics_health() -> Dict[str, Any]:
    """ML Analytics module health check"""
    return {
        "status": "healthy",
        "module": "ml_analytics",
        "timestamp": datetime.utcnow().isoformat()
    }
