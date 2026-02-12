"""
Phase 16: Agent Pricing Service
- Dynamic pricing and pricing models
- Volume discounts and tiers
- Trial and freemium management
"""

from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid


class AgentPricingService:
    """Manage agent pricing strategies"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ PRICING MODELS ============
    
    def create_pricing_model(
        self,
        agent_id: str,
        pricing_model: str,  # fixed, per_execution, per_token, freemium
        base_price: float,
        price_per_execution: Optional[float] = None,
        price_per_1k_input_tokens: Optional[float] = None,
        price_per_1k_output_tokens: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create pricing model for an agent"""
        from app.models.agent_monetization_models import AgentPrice
        
        model = AgentPrice(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            pricing_model=pricing_model,
            base_price=base_price,
            price_per_execution=price_per_execution,
            price_per_1k_input_tokens=price_per_1k_input_tokens,
            price_per_1k_output_tokens=price_per_1k_output_tokens,
            created_at=datetime.utcnow()
        )
        
        self.db.add(model)
        self.db.commit()
        
        return {
            "pricing_model": pricing_model,
            "agent_id": agent_id,
            "base_price": base_price,
            "created_at": model.created_at.isoformat()
        }
    
    def get_agent_pricing(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current pricing model"""
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).order_by(desc(AgentPrice.effective_date)).first()
        
        if not pricing:
            return None
        
        return {
            "pricing_model": pricing.pricing_model,
            "base_price": pricing.base_price,
            "price_per_execution": pricing.price_per_execution,
            "price_per_1k_input_tokens": pricing.price_per_1k_input_tokens,
            "price_per_1k_output_tokens": pricing.price_per_1k_output_tokens,
            "has_free_tier": pricing.has_free_tier,
            "trial_available": pricing.trial_available,
            "trial_days": pricing.trial_days
        }
    
    # ============ COST CALCULATION ============
    
    def calculate_execution_cost(
        self,
        agent_id: str,
        execution_type: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        apply_discount: Optional[float] = None
    ) -> Dict[str, float]:
        """Calculate cost for an execution"""
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id,
            AgentPrice.effective_date <= datetime.utcnow()
        ).order_by(desc(AgentPrice.effective_date)).first()
        
        if not pricing:
            return {"cost": 0.0}
        
        cost = 0.0
        
        if pricing.pricing_model == "fixed":
            cost = pricing.base_price
        
        elif pricing.pricing_model == "per_execution":
            cost = pricing.price_per_execution or pricing.base_price
        
        elif pricing.pricing_model == "per_token":
            input_cost = (input_tokens / 1000) * (pricing.price_per_1k_input_tokens or 0)
            output_cost = (output_tokens / 1000) * (pricing.price_per_1k_output_tokens or 0)
            cost = input_cost + output_cost
        
        elif pricing.pricing_model == "freemium":
            # Freemium charges after threshold
            free_tokens = pricing.free_monthly_tokens or 0
            if (input_tokens + output_tokens) > free_tokens:
                excess_tokens = (input_tokens + output_tokens) - free_tokens
                cost = (excess_tokens / 1000) * (pricing.price_per_1k_output_tokens or 0.001)
        
        # Apply volume discount
        if apply_discount:
            cost = cost * (1 - apply_discount)
        
        return {
            "cost": max(0, cost),
            "pricing_model": pricing.pricing_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
    
    def apply_volume_discount(
        self,
        agent_id: str,
        execution_count: int
    ) -> float:
        """Get volume discount rate"""
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).first()
        
        if not pricing or not pricing.volume_discounts:
            return 0.0
        
        # volume_discounts format: {1000: 0.05, 10000: 0.10}
        discount_rate = 0.0
        for threshold, rate in sorted(pricing.volume_discounts.items()):
            if execution_count >= threshold:
                discount_rate = rate
        
        return discount_rate
    
    # ============ VOLUME DISCOUNTS ============
    
    def set_volume_discounts(
        self,
        agent_id: str,
        discount_tiers: Dict[int, float]
    ) -> bool:
        """Set volume discount tiers"""
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).first()
        
        if not pricing:
            return False
        
        pricing.volume_discounts = discount_tiers
        pricing.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def set_annual_discount(self, agent_id: str, discount_percent: float) -> bool:
        """Set annual billing discount"""
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).first()
        
        if not pricing:
            return False
        
        pricing.annual_discount_percent = discount_percent
        pricing.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    # ============ FREE TIER & TRIAL ============
    
    def enable_free_tier(
        self,
        agent_id: str,
        monthly_executions: int,
        monthly_tokens: int
    ) -> bool:
        """Enable free tier for an agent"""
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).first()
        
        if not pricing:
            return False
        
        pricing.has_free_tier = True
        pricing.free_monthly_executions = monthly_executions
        pricing.free_monthly_tokens = monthly_tokens
        pricing.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def enable_trial(
        self,
        agent_id: str,
        trial_days: int,
        monthly_executions: int,
        monthly_tokens: int
    ) -> bool:
        """Enable trial for an agent"""
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).first()
        
        if not pricing:
            return False
        
        pricing.trial_available = True
        pricing.trial_days = trial_days
        pricing.trial_monthly_executions = monthly_executions
        pricing.trial_monthly_tokens = monthly_tokens
        pricing.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def check_free_tier_usage(
        self,
        agent_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Check free tier usage for a user"""
        from app.models.agent_models import AgentExecution
        from app.models.agent_monetization_models import AgentPrice
        
        pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).first()
        
        if not pricing or not pricing.has_free_tier:
            return {"has_free_tier": False}
        
        # Check current month usage
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.user_id == user_id,
            AgentExecution.created_at >= month_start
        ).all()
        
        executions_used = len(executions)
        tokens_used = sum(e.total_tokens or 0 for e in executions)
        
        return {
            "has_free_tier": True,
            "monthly_executions_limit": pricing.free_monthly_executions,
            "monthly_tokens_limit": pricing.free_monthly_tokens,
            "executions_used": executions_used,
            "tokens_used": tokens_used,
            "executions_remaining": max(0, pricing.free_monthly_executions - executions_used),
            "tokens_remaining": max(0, pricing.free_monthly_tokens - tokens_used),
            "within_limits": (executions_used <= pricing.free_monthly_executions and
                            tokens_used <= pricing.free_monthly_tokens)
        }
    
    # ============ PRICE HISTORY ============
    
    def update_pricing(
        self,
        agent_id: str,
        base_price: Optional[float] = None,
        effective_date: Optional[datetime] = None
    ) -> bool:
        """Create new pricing version"""
        from app.models.agent_monetization_models import AgentPrice
        
        current_pricing = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).order_by(desc(AgentPrice.effective_date)).first()
        
        if not current_pricing:
            return False
        
        # Create new pricing record with same properties
        new_pricing = AgentPrice(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            pricing_model=current_pricing.pricing_model,
            base_price=base_price or current_pricing.base_price,
            price_per_execution=current_pricing.price_per_execution,
            price_per_1k_input_tokens=current_pricing.price_per_1k_input_tokens,
            price_per_1k_output_tokens=current_pricing.price_per_1k_output_tokens,
            has_free_tier=current_pricing.has_free_tier,
            trial_available=current_pricing.trial_available,
            effective_date=effective_date or datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_pricing)
        self.db.commit()
        
        return True
    
    def get_price_history(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pricing change history"""
        from app.models.agent_monetization_models import AgentPrice
        
        history = self.db.query(AgentPrice).filter(
            AgentPrice.agent_id == agent_id
        ).order_by(desc(AgentPrice.effective_date)).limit(limit).all()
        
        return [
            {
                "base_price": p.base_price,
                "pricing_model": p.pricing_model,
                "effective_date": p.effective_date.isoformat(),
                "created_at": p.created_at.isoformat()
            }
            for p in history
        ]
    
    # ============ PRICING ANALYTICS ============
    
    def get_pricing_recommendations(self, agent_id: str) -> Dict[str, Any]:
        """Get pricing optimization recommendations"""
        from app.models.agent_monetization_models import AgentSale, RevenueAnalytics
        from app.models.agent_models import AIAgent
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            return {}
        
        # Get recent sales
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_sales = self.db.query(AgentSale).filter(
            AgentSale.agent_id == agent_id,
            AgentSale.created_at >= week_ago
        ).all()
        
        if not recent_sales:
            return {"recommendation": "Insufficient data"}
        
        # Analyze pricing elasticity
        avg_price = sum(s.amount for s in recent_sales) / len(recent_sales) if recent_sales else 0
        conversion_rate = (len(recent_sales) / agent.deployments * 100) if agent.deployments > 0 else 0
        
        recommendations = []
        
        if conversion_rate < 5:
            recommendations.append({
                "issue": "Low conversion rate",
                "suggestion": "Consider lowering price or adding free trial",
                "potential_impact": "+10-20% conversions"
            })
        
        if agent.downloads > 10000 and avg_price < 10:
            recommendations.append({
                "issue": "Underpriced popular agent",
                "suggestion": "Increase price to capture more value",
                "potential_impact": "+15-30% revenue"
            })
        
        if agent.average_rating < 3.5:
            recommendations.append({
                "issue": "Low ratings",
                "suggestion": "Focus on quality before raising price",
                "potential_impact": "Better long-term sustainability"
            })
        
        return {
            "agent_id": agent_id,
            "current_price": avg_price,
            "conversion_rate": conversion_rate,
            "recommendations": recommendations
        }
    
    def compare_pricing_models(self, agent_id: str) -> Dict[str, Any]:
        """Compare potential pricing models"""
        from app.models.agent_models import AIAgent, AgentExecution
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            return {}
        
        # Get execution statistics
        month_ago = datetime.utcnow() - timedelta(days=30)
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.created_at >= month_ago
        ).all()
        
        total_tokens = sum(e.total_tokens or 0 for e in executions)
        
        # Estimate revenue under different models
        scenarios = {
            "fixed_monthly": {
                "model": "Fixed $99/month subscription",
                "estimated_monthly_revenue": 99 * max(1, len(executions) / 100)
            },
            "per_token": {
                "model": "$0.001 per 1K tokens",
                "estimated_monthly_revenue": (total_tokens / 1000) * 0.001
            },
            "per_execution": {
                "model": "$1 per execution",
                "estimated_monthly_revenue": len(executions) * 1
            },
            "hybrid": {
                "model": "$29/month + $0.10 per execution",
                "estimated_monthly_revenue": 29 + (len(executions) * 0.10)
            }
        }
        
        return {
            "agent_id": agent_id,
            "execution_count": len(executions),
            "total_tokens": total_tokens,
            "pricing_scenarios": scenarios,
            "recommendation": max(scenarios.items(), key=lambda x: x[1].get("estimated_monthly_revenue", 0))[0]
        }
