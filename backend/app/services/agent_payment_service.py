"""
Phase 16: Agent Payment Service
- Payment processing and transaction recording
- Revenue splitting and distribution
- Subscription management
- Refund handling
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import uuid


class AgentPaymentService:
    """Process payments for agent subscriptions and usage"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ PRICING TIERS ============
    
    def create_pricing_tier(
        self,
        agent_id: str,
        name: str,
        monthly_price: float,
        monthly_executions: Optional[int] = None,
        monthly_tokens: Optional[int] = None,
        features: Optional[list] = None,
        annual_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a pricing tier for an agent"""
        from app.models.agent_monetization_models import PricingTier
        
        tier_id = str(uuid.uuid4())
        
        tier = PricingTier(
            id=tier_id,
            agent_id=agent_id,
            name=name,
            slug=name.lower().replace(" ", "-"),
            monthly_price=monthly_price,
            annual_price=annual_price or (monthly_price * 11),  # 1 month free
            monthly_executions=monthly_executions,
            monthly_tokens=monthly_tokens,
            features=features or [],
            created_at=datetime.utcnow()
        )
        
        self.db.add(tier)
        self.db.commit()
        
        return {
            "tier_id": tier_id,
            "name": name,
            "monthly_price": monthly_price,
            "annual_price": tier.annual_price,
            "created_at": tier.created_at.isoformat()
        }
    
    def get_agent_tiers(self, agent_id: str) -> list:
        """Get all pricing tiers for an agent"""
        from app.models.agent_monetization_models import PricingTier
        
        return self.db.query(PricingTier).filter(
            PricingTier.agent_id == agent_id,
            PricingTier.is_active == True
        ).order_by(PricingTier.display_order).all()
    
    def update_tier_pricing(
        self,
        tier_id: str,
        monthly_price: Optional[float] = None,
        annual_price: Optional[float] = None
    ) -> bool:
        """Update tier pricing"""
        from app.models.agent_monetization_models import PricingTier
        
        tier = self.db.query(PricingTier).filter(PricingTier.id == tier_id).first()
        if not tier:
            return False
        
        if monthly_price is not None:
            tier.monthly_price = monthly_price
        if annual_price is not None:
            tier.annual_price = annual_price
        
        tier.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    # ============ SUBSCRIPTIONS ============
    
    def create_subscription(
        self,
        user_id: str,
        agent_id: str,
        tier_id: str,
        billing_cycle: str,  # monthly or annual
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Create a subscription for an agent"""
        from app.models.agent_monetization_models import AgentSubscription, PricingTier
        
        tier = self.db.query(PricingTier).filter(PricingTier.id == tier_id).first()
        if not tier:
            raise ValueError(f"Tier {tier_id} not found")
        
        subscription_id = str(uuid.uuid4())
        start_date = datetime.utcnow()
        
        if billing_cycle == "annual":
            renewal_date = start_date + timedelta(days=365)
            amount = tier.annual_price or (tier.monthly_price * 12)
        else:
            renewal_date = start_date + timedelta(days=30)
            amount = tier.monthly_price
        
        subscription = AgentSubscription(
            id=subscription_id,
            user_id=user_id,
            tier_id=tier_id,
            agent_id=agent_id,
            status="active",
            billing_cycle=billing_cycle,
            start_date=start_date,
            renewal_date=renewal_date,
            monthly_amount=tier.monthly_price,
            annual_amount=tier.annual_price,
            auto_renew=True,
            payment_method_id=payment_method_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(subscription)
        
        # Record the sale
        self._record_sale(agent_id, user_id, tier_id, amount, "subscription")
        
        self.db.commit()
        
        return {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "tier_id": tier_id,
            "amount": amount,
            "billing_cycle": billing_cycle,
            "start_date": start_date.isoformat(),
            "renewal_date": renewal_date.isoformat()
        }
    
    def get_user_subscriptions(self, user_id: str) -> list:
        """Get all active subscriptions for a user"""
        from app.models.agent_monetization_models import AgentSubscription
        
        return self.db.query(AgentSubscription).filter(
            AgentSubscription.user_id == user_id,
            AgentSubscription.status == "active"
        ).all()
    
    def update_subscription_status(
        self,
        subscription_id: str,
        status: str  # active, paused, cancelled
    ) -> bool:
        """Update subscription status"""
        from app.models.agent_monetization_models import AgentSubscription
        
        subscription = self.db.query(AgentSubscription).filter(
            AgentSubscription.id == subscription_id
        ).first()
        
        if not subscription:
            return False
        
        subscription.status = status
        if status == "cancelled":
            subscription.cancelled_date = datetime.utcnow()
        
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def track_usage(
        self,
        subscription_id: str,
        executions: int = 0,
        tokens: int = 0
    ) -> None:
        """Track subscription usage"""
        from app.models.agent_monetization_models import AgentSubscription
        
        subscription = self.db.query(AgentSubscription).filter(
            AgentSubscription.id == subscription_id
        ).first()
        
        if subscription:
            subscription.executions_used += executions
            subscription.tokens_used += tokens
            subscription.updated_at = datetime.utcnow()
            self.db.commit()
    
    # ============ SALES & TRANSACTIONS ============
    
    def _record_sale(
        self,
        agent_id: str,
        user_id: str,
        tier_id: str,
        amount: float,
        sale_type: str,
        referrer_id: Optional[str] = None
    ) -> str:
        """Record a sale transaction"""
        from app.models.agent_monetization_models import AgentSale
        
        sale_id = str(uuid.uuid4())
        
        # Revenue split: 50% author, 30% platform, 20% referrer
        agent_revenue = amount * 0.50
        platform_revenue = amount * 0.30
        referrer_revenue = amount * 0.20 if referrer_id else 0
        
        sale = AgentSale(
            id=sale_id,
            agent_id=agent_id,
            user_id=user_id,
            sale_type=sale_type,
            tier_id=tier_id if sale_type == "subscription" else None,
            amount=amount,
            agent_revenue=agent_revenue,
            platform_revenue=platform_revenue,
            referrer_revenue=referrer_revenue,
            referrer_id=referrer_id,
            status="completed",
            created_at=datetime.utcnow()
        )
        
        self.db.add(sale)
        self.db.commit()
        
        return sale_id
    
    def process_payment(
        self,
        agent_id: str,
        user_id: str,
        amount: float,
        tier_id: str,
        payment_type: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """Process a payment"""
        from app.models.agent_monetization_models import AgentPayment
        
        payment = AgentPayment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            amount=amount,
            payment_type=payment_type,
            stripe_transfer_id=payment_id,
            status="completed",
            processed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(payment)
        
        # Record the sale
        self._record_sale(agent_id, user_id, tier_id, amount, "one_time")
        
        self.db.commit()
        
        return {
            "payment_id": payment.id,
            "status": "completed",
            "amount": amount,
            "processed_at": payment.processed_at.isoformat()
        }
    
    def refund_payment(
        self,
        sale_id: str,
        refund_amount: float,
        reason: str
    ) -> bool:
        """Process a refund"""
        from app.models.agent_monetization_models import AgentSale
        
        sale = self.db.query(AgentSale).filter(AgentSale.id == sale_id).first()
        if not sale:
            return False
        
        sale.status = "refunded"
        sale.refund_amount = refund_amount
        sale.refund_reason = reason
        sale.refund_id = str(uuid.uuid4())
        
        self.db.commit()
        
        return True
    
    # ============ TRIAL LICENSES ============
    
    def create_trial_license(
        self,
        user_id: str,
        agent_id: str,
        trial_days: int,
        monthly_executions: int,
        monthly_tokens: int
    ) -> Dict[str, Any]:
        """Create a trial license"""
        from app.models.agent_monetization_models import TrialLicense
        
        trial_id = str(uuid.uuid4())
        start_date = datetime.utcnow()
        expiry_date = start_date + timedelta(days=trial_days)
        
        trial = TrialLicense(
            id=trial_id,
            user_id=user_id,
            agent_id=agent_id,
            start_date=start_date,
            expiry_date=expiry_date,
            monthly_executions=monthly_executions,
            monthly_tokens=monthly_tokens,
            created_at=datetime.utcnow()
        )
        
        self.db.add(trial)
        self.db.commit()
        
        return {
            "trial_id": trial_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "start_date": start_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "days_remaining": trial_days
        }
    
    def check_trial_validity(self, trial_id: str) -> Dict[str, Any]:
        """Check if trial is still valid"""
        from app.models.agent_monetization_models import TrialLicense
        
        trial = self.db.query(TrialLicense).filter(
            TrialLicense.id == trial_id
        ).first()
        
        if not trial:
            return {"valid": False}
        
        if trial.status != "active":
            return {"valid": False, "reason": f"Trial is {trial.status}"}
        
        if datetime.utcnow() > trial.expiry_date:
            trial.status = "expired"
            self.db.commit()
            return {"valid": False, "reason": "Trial expired"}
        
        days_remaining = (trial.expiry_date - datetime.utcnow()).days
        
        return {
            "valid": True,
            "trial_id": trial_id,
            "days_remaining": days_remaining,
            "executions_remaining": max(0, trial.monthly_executions - trial.executions_used),
            "tokens_remaining": max(0, trial.monthly_tokens - trial.tokens_used)
        }
    
    def convert_trial_to_subscription(
        self,
        trial_id: str,
        tier_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Convert a trial to a paid subscription"""
        from app.models.agent_monetization_models import TrialLicense
        
        trial = self.db.query(TrialLicense).filter(
            TrialLicense.id == trial_id
        ).first()
        
        if not trial or trial.status != "active":
            raise ValueError("Trial not found or not active")
        
        # Create subscription
        subscription = self.create_subscription(
            user_id=trial.user_id,
            agent_id=trial.agent_id,
            tier_id=tier_id,
            billing_cycle="monthly",
            payment_method_id=payment_method_id
        )
        
        # Mark trial as converted
        trial.status = "converted"
        trial.converted_to_tier_id = tier_id
        trial.converted_at = datetime.utcnow()
        self.db.commit()
        
        return subscription
    
    # ============ DISCOUNTS ============
    
    def create_discount(
        self,
        code: str,
        discount_type: str,  # percentage, fixed
        discount_value: float,
        agent_id: Optional[str] = None,
        max_uses: Optional[int] = None,
        valid_until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a discount code"""
        from app.models.agent_monetization_models import Discount
        
        discount = Discount(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            valid_until=valid_until,
            created_at=datetime.utcnow()
        )
        
        self.db.add(discount)
        self.db.commit()
        
        return {
            "code": code,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "created_at": discount.created_at.isoformat()
        }
    
    def apply_discount(self, code: str, amount: float) -> Dict[str, float]:
        """Apply a discount code"""
        from app.models.agent_monetization_models import Discount
        
        discount = self.db.query(Discount).filter(
            Discount.code == code,
            Discount.is_active == True
        ).first()
        
        if not discount:
            raise ValueError("Invalid discount code")
        
        if discount.valid_until and datetime.utcnow() > discount.valid_until:
            raise ValueError("Discount code expired")
        
        if discount.max_uses and discount.usage_count >= discount.max_uses:
            raise ValueError("Discount code usage limit reached")
        
        # Calculate discount
        if discount.discount_type == "percentage":
            discount_amount = amount * (discount.discount_value / 100)
        else:
            discount_amount = discount.discount_value
        
        final_amount = max(0, amount - discount_amount)
        
        # Increment usage
        discount.usage_count += 1
        self.db.commit()
        
        return {
            "original_amount": amount,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "discount_type": discount.discount_type,
            "discount_value": discount.discount_value
        }
    
    # ============ PAYMENT METHODS ============
    
    def save_payment_method(
        self,
        user_id: str,
        payment_method_id: str,
        payment_type: str,
        last_four: str
    ) -> bool:
        """Save payment method for future use (via Stripe)"""
        # In real implementation, this integrates with Stripe
        # For now, just validate the payment method can be used
        return True
    
    def get_user_payment_methods(self, user_id: str) -> list:
        """Get saved payment methods for a user"""
        # In real implementation, retrieve from Stripe
        return []
    
    # ============ ANALYTICS ============
    
    def get_sales_metrics(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get sales metrics for an agent"""
        from app.models.agent_monetization_models import AgentSale
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        sales = self.db.query(AgentSale).filter(
            AgentSale.agent_id == agent_id,
            AgentSale.created_at >= cutoff_date,
            AgentSale.status == "completed"
        ).all()
        
        if not sales:
            return {
                "agent_id": agent_id,
                "period_days": days,
                "total_sales": 0,
                "total_revenue": 0.0
            }
        
        total_revenue = sum(s.amount for s in sales)
        subscriptions = sum(1 for s in sales if s.sale_type == "subscription")
        
        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_sales": len(sales),
            "subscription_sales": subscriptions,
            "one_time_sales": len(sales) - subscriptions,
            "total_revenue": total_revenue,
            "average_sale": total_revenue / len(sales) if sales else 0,
            "agent_revenue": sum(s.agent_revenue for s in sales),
            "platform_revenue": sum(s.platform_revenue for s in sales),
            "refund_amount": sum(s.refund_amount or 0 for s in sales if s.status == "refunded")
        }
