"""
Subscription Tier Service - Tier management, feature access, and tier transitions
Manages subscription tiers, feature access control, and customer tier progression
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import json


class TierLevel(str, Enum):
    """Subscription tier levels"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class TransitionType(str, Enum):
    """Type of tier transition"""
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    REACTIVATION = "reactivation"
    CHURN = "churn"


class SubscriptionTierService:
    """
    Service for managing subscription tiers, feature access control,
    and tier transitions (upgrades/downgrades).
    """
    
    def __init__(self):
        """Initialize subscription tier service"""
        self.tiers = self._initialize_tiers()
        self.tier_features = self._initialize_tier_features()
        self.customer_tiers = {}
        self.transition_history = {}
        self.feature_usage = {}
        self.grandfathering_rules = {}
    
    def _initialize_tiers(self) -> Dict:
        """Initialize default tier definitions"""
        return {
            TierLevel.STARTER: {
                "name": "Starter",
                "monthly_price": 29.00,
                "annual_price": 290.00,  # 10% discount
                "max_agents": 2,
                "max_monthly_executions": 5000,
                "max_api_calls": 10000,
                "support_tier": "email",
                "features": [
                    "basic_analytics",
                    "email_support",
                    "api_access",
                ],
                "description": "Perfect for getting started",
                "user_limit": 1,
                "storage_gb": 10,
                "uptime_sla": "99.0%",
                "onboarding_included": True,
            },
            
            TierLevel.PROFESSIONAL: {
                "name": "Professional",
                "monthly_price": 99.00,
                "annual_price": 990.00,  # 10% discount
                "max_agents": 10,
                "max_monthly_executions": 50000,
                "max_api_calls": 100000,
                "support_tier": "priority",
                "features": [
                    "basic_analytics",
                    "advanced_analytics",
                    "email_support",
                    "priority_support",
                    "api_access",
                    "webhook_support",
                    "custom_integrations",
                    "team_collaboration",
                ],
                "description": "For growing teams",
                "user_limit": 5,
                "storage_gb": 100,
                "uptime_sla": "99.9%",
                "onboarding_included": True,
                "dedicated_account_manager": False,
            },
            
            TierLevel.ENTERPRISE: {
                "name": "Enterprise",
                "monthly_price": 499.00,
                "annual_price": 4990.00,  # 10% discount
                "max_agents": None,  # Unlimited
                "max_monthly_executions": None,  # Unlimited
                "max_api_calls": None,  # Unlimited
                "support_tier": "24/7",
                "features": [
                    "basic_analytics",
                    "advanced_analytics",
                    "predictive_analytics",
                    "email_support",
                    "priority_support",
                    "phone_support",
                    "api_access",
                    "webhook_support",
                    "custom_integrations",
                    "team_collaboration",
                    "sso",
                    "audit_logs",
                    "custom_branding",
                    "white_label",
                ],
                "description": "For large enterprises",
                "user_limit": None,  # Unlimited
                "storage_gb": 1000,
                "uptime_sla": "99.99%",
                "onboarding_included": True,
                "dedicated_account_manager": True,
                "custom_development": True,
            },
            
            TierLevel.CUSTOM: {
                "name": "Custom",
                "monthly_price": None,  # Custom pricing
                "annual_price": None,
                "max_agents": None,
                "max_monthly_executions": None,
                "max_api_calls": None,
                "support_tier": "dedicated",
                "features": [],  # Custom features per contract
                "description": "Custom solutions for your needs",
                "user_limit": None,
                "storage_gb": None,
                "uptime_sla": "custom",
                "onboarding_included": True,
                "dedicated_account_manager": True,
                "custom_development": True,
                "custom_sla": True,
            },
        }
    
    def _initialize_tier_features(self) -> Dict:
        """Initialize feature mappings for tiers"""
        return {
            "basic_analytics": {
                "description": "Basic usage and performance analytics",
                "available_in": [TierLevel.STARTER, TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "advanced_analytics": {
                "description": "Advanced analytics with custom dashboards",
                "available_in": [TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "predictive_analytics": {
                "description": "ML-powered predictive analytics",
                "available_in": [TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "api_access": {
                "description": "REST API access",
                "available_in": [TierLevel.STARTER, TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "webhook_support": {
                "description": "Webhook integrations",
                "available_in": [TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "custom_integrations": {
                "description": "Custom third-party integrations",
                "available_in": [TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "sso": {
                "description": "Single Sign-On (SAML, OAuth)",
                "available_in": [TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "audit_logs": {
                "description": "Comprehensive audit logging",
                "available_in": [TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "custom_branding": {
                "description": "Custom branding and themes",
                "available_in": [TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "white_label": {
                "description": "White-label solution",
                "available_in": [TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "team_collaboration": {
                "description": "Team workspaces and collaboration",
                "available_in": [TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "email_support": {
                "description": "Email support",
                "available_in": [TierLevel.STARTER, TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "priority_support": {
                "description": "Priority support queue",
                "available_in": [TierLevel.PROFESSIONAL, TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
            "phone_support": {
                "description": "Phone support",
                "available_in": [TierLevel.ENTERPRISE, TierLevel.CUSTOM],
            },
        }
    
    def get_tier_definition(self, tier_level: TierLevel) -> Dict:
        """Get tier definition"""
        return self.tiers.get(tier_level.value, {})
    
    def list_all_tiers(self) -> List[Dict]:
        """List all available tiers"""
        return [
            {
                "tier": tier_level.value,
                **self.tiers[tier_level.value]
            }
            for tier_level in TierLevel
        ]
    
    def subscribe_to_tier(
        self,
        customer_id: str,
        tier_level: str,
        billing_cycle: str = "monthly",
        start_date: Optional[str] = None,
    ) -> Dict:
        """
        Subscribe customer to a tier.
        
        Args:
            customer_id: Customer ID
            tier_level: Tier level (starter, professional, enterprise, custom)
            billing_cycle: "monthly" or "annual"
            start_date: Start date (default: today)
        
        Returns:
            Subscription details
        """
        tier_def = self.tiers.get(tier_level)
        if not tier_def:
            return {"status": "error", "message": f"Tier {tier_level} not found"}
        
        # Determine price
        if billing_cycle == "annual":
            price = tier_def["annual_price"]
            next_billing = datetime.fromisoformat(start_date or datetime.utcnow().isoformat())
            next_billing += timedelta(days=365)
        else:
            price = tier_def["monthly_price"]
            next_billing = datetime.fromisoformat(start_date or datetime.utcnow().isoformat())
            next_billing += timedelta(days=30)
        
        subscription = {
            "customer_id": customer_id,
            "tier_level": tier_level,
            "tier_name": tier_def["name"],
            "billing_cycle": billing_cycle,
            "price": price,
            "status": "active",
            "start_date": start_date or datetime.utcnow().isoformat(),
            "next_billing_date": next_billing.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "features": tier_def["features"],
        }
        
        self.customer_tiers[customer_id] = subscription
        
        return subscription
    
    def upgrade_tier(
        self,
        customer_id: str,
        new_tier_level: str,
        proration: bool = True,
    ) -> Dict:
        """
        Upgrade customer to higher tier.
        
        Args:
            customer_id: Customer ID
            new_tier_level: New tier level
            proration: Calculate pro-rata credit
        
        Returns:
            Upgrade details with credits
        """
        current = self.customer_tiers.get(customer_id)
        if not current:
            return {"status": "error", "message": "No current subscription"}
        
        current_tier = self.tiers[current["tier_level"]]
        new_tier = self.tiers[new_tier_level]
        
        # Calculate proration
        proration_credit = 0.0
        if proration:
            # Days remaining in billing period
            next_bill = datetime.fromisoformat(current["next_billing_date"])
            today = datetime.utcnow()
            days_remaining = (next_bill - today).days
            
            # Current daily rate
            current_daily = current["price"] / 30
            # New daily rate
            new_daily = (new_tier[f"{current['billing_cycle']}_price"] or 0) / 30
            
            # Credit for unused portion
            proration_credit = current_daily * days_remaining
        
        # New price
        new_price = (new_tier["annual_price"] if current["billing_cycle"] == "annual" 
                    else new_tier["monthly_price"])
        
        # Calculate new amount due
        amount_due = max(0, new_price - proration_credit)
        
        # Update subscription
        current.update({
            "tier_level": new_tier_level,
            "tier_name": new_tier["name"],
            "price": new_price,
            "features": new_tier["features"],
            "upgraded_at": datetime.utcnow().isoformat(),
        })
        
        # Record transition
        self._record_transition(
            customer_id=customer_id,
            from_tier=current["tier_level"],
            to_tier=new_tier_level,
            transition_type=TransitionType.UPGRADE.value,
            proration_credit=proration_credit,
            amount_due=amount_due,
        )
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "from_tier": current["tier_level"],
            "to_tier": new_tier_level,
            "proration_credit": round(proration_credit, 2),
            "new_price": new_price,
            "amount_due": round(amount_due, 2),
            "effective_immediately": True,
        }
    
    def downgrade_tier(
        self,
        customer_id: str,
        new_tier_level: str,
        effective_date: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict:
        """
        Downgrade customer to lower tier.
        
        Args:
            customer_id: Customer ID
            new_tier_level: New tier level
            effective_date: When downgrade takes effect
            reason: Downgrade reason
        
        Returns:
            Downgrade details
        """
        current = self.customer_tiers.get(customer_id)
        if not current:
            return {"status": "error", "message": "No current subscription"}
        
        new_tier = self.tiers[new_tier_level]
        new_price = (new_tier["annual_price"] if current["billing_cycle"] == "annual" 
                    else new_tier["monthly_price"])
        
        # Downgrades typically effective next billing cycle
        if not effective_date:
            effective_date = current["next_billing_date"]
        
        # Update subscription
        current.update({
            "tier_level": new_tier_level,
            "tier_name": new_tier["name"],
            "price": new_price,
            "features": new_tier["features"],
            "downgraded_at": datetime.utcnow().isoformat(),
            "effective_date": effective_date,
        })
        
        # Record transition
        self._record_transition(
            customer_id=customer_id,
            from_tier=current["tier_level"],
            to_tier=new_tier_level,
            transition_type=TransitionType.DOWNGRADE.value,
            effective_date=effective_date,
            reason=reason,
        )
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "from_tier": current["tier_level"],
            "to_tier": new_tier_level,
            "effective_date": effective_date,
            "new_price": new_price,
        }
    
    def _record_transition(
        self,
        customer_id: str,
        from_tier: str,
        to_tier: str,
        transition_type: str,
        **kwargs
    ):
        """Record tier transition for analytics"""
        if customer_id not in self.transition_history:
            self.transition_history[customer_id] = []
        
        transition = {
            "from_tier": from_tier,
            "to_tier": to_tier,
            "transition_type": transition_type,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        self.transition_history[customer_id].append(transition)
    
    def get_customer_tier(self, customer_id: str) -> Dict:
        """Get current tier for customer"""
        return self.customer_tiers.get(customer_id, {})
    
    def has_feature(self, customer_id: str, feature: str) -> bool:
        """Check if customer has access to feature"""
        subscription = self.customer_tiers.get(customer_id)
        if not subscription:
            return False
        
        return feature in subscription.get("features", [])
    
    def get_feature_limits(self, customer_id: str) -> Dict:
        """Get feature limits for customer's tier"""
        subscription = self.customer_tiers.get(customer_id)
        if not subscription:
            return {}
        
        tier_def = self.tiers[subscription["tier_level"]]
        
        return {
            "max_agents": tier_def["max_agents"],
            "max_monthly_executions": tier_def["max_monthly_executions"],
            "max_api_calls": tier_def["max_api_calls"],
            "user_limit": tier_def["user_limit"],
            "storage_gb": tier_def["storage_gb"],
            "uptime_sla": tier_def["uptime_sla"],
        }
    
    def apply_grandfathering(
        self,
        customer_id: str,
        original_tier: str,
        new_tier: str,
        features_to_retain: List[str],
        expiration_date: Optional[str] = None,
    ) -> Dict:
        """
        Apply grandfathering rule to retain features from old tier.
        Used when deprecated features should be retained for existing customers.
        
        Args:
            customer_id: Customer ID
            original_tier: Original tier level
            new_tier: New tier level
            features_to_retain: Features to keep from original
            expiration_date: When grandfathering expires
        
        Returns:
            Grandfathering configuration
        """
        grandfathering = {
            "customer_id": customer_id,
            "original_tier": original_tier,
            "new_tier": new_tier,
            "features_to_retain": features_to_retain,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expiration_date,
            "status": "active",
        }
        
        self.grandfathering_rules[customer_id] = grandfathering
        
        return grandfathering
    
    def get_transition_history(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get tier transition history for customer"""
        history = self.transition_history.get(customer_id, [])
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_tier_analytics(self, agent_id: Optional[str] = None) -> Dict:
        """
        Get analytics on tier distribution and transitions.
        
        Args:
            agent_id: Optional agent ID to filter by
        
        Returns:
            Tier analytics
        """
        tier_counts = {tier: 0 for tier in TierLevel}
        tier_revenue = {tier: 0 for tier in TierLevel}
        
        for subscription in self.customer_tiers.values():
            tier = subscription["tier_level"]
            tier_counts[tier] += 1
            tier_revenue[tier] += subscription.get("price", 0)
        
        return {
            "tier_distribution": tier_counts,
            "tier_revenue": tier_revenue,
            "total_customers": len(self.customer_tiers),
            "total_mrr": sum(tier_revenue.values()),
            "average_tier": self._calculate_average_tier(),
            "upgrade_rate": self._calculate_upgrade_rate(),
            "downgrade_rate": self._calculate_downgrade_rate(),
        }
    
    def _calculate_average_tier(self) -> float:
        """Calculate average tier value"""
        tier_values = {
            TierLevel.STARTER: 1,
            TierLevel.PROFESSIONAL: 2,
            TierLevel.ENTERPRISE: 3,
            TierLevel.CUSTOM: 4,
        }
        
        if not self.customer_tiers:
            return 0
        
        total = sum(
            tier_values.get(sub["tier_level"], 0)
            for sub in self.customer_tiers.values()
        )
        
        return total / len(self.customer_tiers)
    
    def _calculate_upgrade_rate(self) -> float:
        """Calculate percentage of customers who have upgraded"""
        if not self.transition_history:
            return 0
        
        upgrades = sum(
            1 for transitions in self.transition_history.values()
            for t in transitions
            if t.get("transition_type") == TransitionType.UPGRADE.value
        )
        
        return (upgrades / len(self.transition_history)) * 100 if self.transition_history else 0
    
    def _calculate_downgrade_rate(self) -> float:
        """Calculate percentage of customers who have downgraded"""
        if not self.transition_history:
            return 0
        
        downgrades = sum(
            1 for transitions in self.transition_history.values()
            for t in transitions
            if t.get("transition_type") == TransitionType.DOWNGRADE.value
        )
        
        return (downgrades / len(self.transition_history)) * 100 if self.transition_history else 0
    
    def compare_tiers(self, tier1: str, tier2: str) -> Dict:
        """
        Compare two tiers to highlight differences.
        
        Args:
            tier1: First tier to compare
            tier2: Second tier to compare
        
        Returns:
            Comparison highlighting differences
        """
        def1 = self.tiers.get(tier1, {})
        def2 = self.tiers.get(tier2, {})
        
        differences = {}
        
        for key in set(list(def1.keys()) + list(def2.keys())):
            val1 = def1.get(key)
            val2 = def2.get(key)
            
            if val1 != val2:
                differences[key] = {
                    tier1: val1,
                    tier2: val2,
                    "better_in": tier2 if val2 > val1 else tier1,
                }
        
        return {
            "tier1": tier1,
            "tier2": tier2,
            "differences": differences,
            "recommendation": f"Upgrade to {tier2}" if tier2 in [TierLevel.ENTERPRISE, TierLevel.CUSTOM] else "Compare features",
        }
