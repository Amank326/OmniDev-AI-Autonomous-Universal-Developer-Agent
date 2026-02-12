"""
Phase 16: Monetization Routes
- Pricing and tier management
- Payment processing
- Payout management
- Revenue analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/v1/agents", tags=["monetization"])

# Service dependencies (injected from main.py)
payment_service = None
payout_service = None
pricing_service = None


def set_monetization_services(payment, payout, pricing):
    """Inject services"""
    global payment_service, payout_service, pricing_service
    payment_service = payment
    payout_service = payout
    pricing_service = pricing


# ============ PRICING TIERS ============

@router.post("/{agent_id}/tiers")
async def create_tier(
    agent_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Create pricing tier"""
    try:
        tier = payment_service.create_pricing_tier(
            agent_id=agent_id,
            name=body["name"],
            monthly_price=body["monthly_price"],
            monthly_executions=body.get("monthly_executions"),
            monthly_tokens=body.get("monthly_tokens"),
            features=body.get("features"),
            annual_price=body.get("annual_price")
        )
        return tier
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/tiers")
async def get_tiers(agent_id: str) -> Dict[str, Any]:
    """Get pricing tiers"""
    try:
        tiers = payment_service.get_agent_tiers(agent_id)
        return {
            "agent_id": agent_id,
            "tiers": [
                {
                    "id": t.id,
                    "name": t.name,
                    "monthly_price": t.monthly_price,
                    "annual_price": t.annual_price,
                    "monthly_executions": t.monthly_executions,
                    "features": t.features
                }
                for t in tiers
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{agent_id}/tiers/{tier_id}")
async def update_tier(
    agent_id: str,
    tier_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Update tier pricing"""
    try:
        success = payment_service.update_tier_pricing(
            tier_id=tier_id,
            monthly_price=body.get("monthly_price"),
            annual_price=body.get("annual_price")
        )
        if not success:
            raise HTTPException(status_code=404, detail="Tier not found")
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ SUBSCRIPTIONS ============

@router.post("/{agent_id}/subscribe")
async def subscribe(
    agent_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Subscribe to agent tier"""
    try:
        subscription = payment_service.create_subscription(
            user_id=x_user_id,
            agent_id=agent_id,
            tier_id=body["tier_id"],
            billing_cycle=body.get("billing_cycle", "monthly"),
            payment_method_id=body["payment_method_id"]
        )
        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions")
async def get_subscriptions(
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get user subscriptions"""
    try:
        subscriptions = payment_service.get_user_subscriptions(x_user_id)
        return {
            "subscriptions": [
                {
                    "id": s.id,
                    "agent_id": s.agent_id,
                    "tier_id": s.tier_id,
                    "status": s.status,
                    "billing_cycle": s.billing_cycle,
                    "renewal_date": s.renewal_date.isoformat(),
                    "monthly_amount": s.monthly_amount
                }
                for s in subscriptions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Update subscription status"""
    try:
        success = payment_service.update_subscription_status(
            subscription_id=subscription_id,
            status=body["status"]
        )
        if not success:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return {"status": "updated", "subscription_id": subscription_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ TRIAL LICENSES ============

@router.post("/{agent_id}/trial")
async def start_trial(
    agent_id: str,
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Start trial for agent"""
    try:
        trial = payment_service.create_trial_license(
            user_id=x_user_id,
            agent_id=agent_id,
            trial_days=14,
            monthly_executions=1000,
            monthly_tokens=100000
        )
        return trial
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trial/{trial_id}/check")
async def check_trial(trial_id: str) -> Dict[str, Any]:
    """Check trial status"""
    try:
        result = payment_service.check_trial_validity(trial_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trial/{trial_id}/convert")
async def convert_trial(
    trial_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Convert trial to subscription"""
    try:
        subscription = payment_service.convert_trial_to_subscription(
            trial_id=trial_id,
            tier_id=body["tier_id"],
            payment_method_id=body["payment_method_id"]
        )
        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ PRICING & COST CALCULATION ============

@router.post("/{agent_id}/pricing")
async def create_pricing_model(
    agent_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Create pricing model"""
    try:
        model = pricing_service.create_pricing_model(
            agent_id=agent_id,
            pricing_model=body["pricing_model"],
            base_price=body["base_price"],
            price_per_execution=body.get("price_per_execution"),
            price_per_1k_input_tokens=body.get("price_per_1k_input_tokens"),
            price_per_1k_output_tokens=body.get("price_per_1k_output_tokens")
        )
        return model
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/pricing")
async def get_pricing(agent_id: str) -> Dict[str, Any]:
    """Get agent pricing"""
    try:
        pricing = pricing_service.get_agent_pricing(agent_id)
        if not pricing:
            raise HTTPException(status_code=404, detail="Pricing not found")
        return pricing
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/calculate-cost")
async def calculate_cost(
    agent_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate execution cost"""
    try:
        cost = pricing_service.calculate_execution_cost(
            agent_id=agent_id,
            execution_type=body.get("execution_type", "default"),
            input_tokens=body.get("input_tokens", 0),
            output_tokens=body.get("output_tokens", 0)
        )
        return cost
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/pricing-recommendations")
async def get_pricing_recommendations(agent_id: str) -> Dict[str, Any]:
    """Get pricing optimization recommendations"""
    try:
        recommendations = pricing_service.get_pricing_recommendations(agent_id)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/pricing-comparison")
async def compare_pricing_models(agent_id: str) -> Dict[str, Any]:
    """Compare pricing models"""
    try:
        comparison = pricing_service.compare_pricing_models(agent_id)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ DISCOUNTS ============

@router.post("/discounts")
async def create_discount(
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Create discount code"""
    try:
        discount = payment_service.create_discount(
            code=body["code"],
            discount_type=body["discount_type"],
            discount_value=body["discount_value"],
            agent_id=body.get("agent_id"),
            max_uses=body.get("max_uses"),
            valid_until=body.get("valid_until")
        )
        return discount
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discounts/{code}/apply")
async def apply_discount(
    code: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply discount to amount"""
    try:
        result = payment_service.apply_discount(
            code=code,
            amount=body["amount"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ PAYOUTS ============

@router.post("/{agent_id}/request-payout")
async def request_payout(
    agent_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Request payout"""
    try:
        payout = payout_service.create_payout(
            agent_id=agent_id,
            user_id=x_user_id,
            amount=body["amount"],
            payout_method=body["payout_method"],
            notes=body.get("notes")
        )
        return payout
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/payout-balance")
async def get_payout_balance(
    agent_id: str,
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get pending payout balance"""
    try:
        balance = payout_service.get_pending_payout_amount(agent_id)
        return {
            "agent_id": agent_id,
            "pending_amount": balance,
            "currency": "USD"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payout-status/{payment_id}")
async def get_payout_status(payment_id: str) -> Dict[str, Any]:
    """Get payout status"""
    try:
        status = payout_service.get_payout_status(payment_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/payout-history")
async def get_payout_history(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """Get payout history"""
    try:
        history = payout_service.get_payout_history(agent_id, limit=limit)
        return {"payouts": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ REVENUE ANALYTICS ============

@router.get("/{agent_id}/sales-metrics")
async def get_sales_metrics(
    agent_id: str,
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get sales metrics"""
    try:
        metrics = payment_service.get_sales_metrics(agent_id, days=days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/monthly-report/{month}")
async def get_monthly_report(agent_id: str, month: str) -> Dict[str, Any]:
    """Get monthly financial report"""
    try:
        report = payout_service.generate_monthly_report(agent_id, month)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/yearly-summary/{year}")
async def get_yearly_summary(agent_id: str, year: int) -> Dict[str, Any]:
    """Get yearly financial summary"""
    try:
        summary = payout_service.get_yearly_summary(agent_id, year)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/revenue-trends")
async def get_revenue_trends(
    agent_id: str,
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get revenue trends"""
    try:
        trends = payout_service.get_revenue_trends(agent_id, days=days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-agents")
async def get_top_agents(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get top earning agents"""
    try:
        top_agents = payout_service.get_top_agents(limit=limit, days=days)
        return {"top_agents": top_agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ HEALTH ============

@router.get("/monetization/health")
async def monetization_health() -> Dict[str, Any]:
    """Monetization module health check"""
    return {
        "status": "healthy",
        "module": "monetization",
        "timestamp": datetime.utcnow().isoformat()
    }
