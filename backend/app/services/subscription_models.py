"""
Phase 12: Subscription Models
Subscription and billing models for enterprise plans
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELED = "canceled"
    EXPIRED = "expired"


class BillingCycle(str, Enum):
    """Billing cycle"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PricingPlan:
    """Pricing plan definition"""

    def __init__(self, tier: SubscriptionTier, monthly_price: float,
                 annual_price: float, features: Dict, quotas: Dict):
        self.tier = tier
        self.monthly_price = monthly_price
        self.annual_price = annual_price
        self.features = features
        self.quotas = quotas

    def get_annual_savings(self) -> float:
        """Calculate annual savings vs monthly billing"""
        monthly_total = self.monthly_price * 12
        savings = monthly_total - self.annual_price
        return max(0, savings)

    def get_annual_discount_percent(self) -> float:
        """Get annual plan discount percentage"""
        if self.monthly_price == 0:
            return 0
        monthly_total = self.monthly_price * 12
        discount = (monthly_total - self.annual_price) / monthly_total * 100
        return max(0, discount)


# Define all pricing plans
PRICING_PLANS = {
    SubscriptionTier.FREE: PricingPlan(
        tier=SubscriptionTier.FREE,
        monthly_price=0,
        annual_price=0,
        features={
            "workflows": 10,
            "executions_per_month": 100,
            "team_members": 1,
            "storage_gb": 5,
            "api_calls_per_month": 1000,
            "advanced_analytics": False,
            "api_keys": 1,
            "custom_integrations": False,
            "sso": False,
            "audit_logging": False,
            "support": "community",
        },
        quotas={
            "max_workflows": 10,
            "max_executions_monthly": 100,
            "max_team_members": 1,
            "storage_gb": 5,
            "api_calls_monthly": 1000,
            "max_api_keys": 1,
        }
    ),

    SubscriptionTier.STARTER: PricingPlan(
        tier=SubscriptionTier.STARTER,
        monthly_price=29,
        annual_price=290,  # ~17% discount
        features={
            "workflows": 100,
            "executions_per_month": 10000,
            "team_members": 5,
            "storage_gb": 100,
            "api_calls_per_month": 50000,
            "advanced_analytics": True,
            "api_keys": 5,
            "custom_integrations": True,
            "sso": False,
            "audit_logging": False,
            "support": "email",
        },
        quotas={
            "max_workflows": 100,
            "max_executions_monthly": 10000,
            "max_team_members": 5,
            "storage_gb": 100,
            "api_calls_monthly": 50000,
            "max_api_keys": 5,
        }
    ),

    SubscriptionTier.PROFESSIONAL: PricingPlan(
        tier=SubscriptionTier.PROFESSIONAL,
        monthly_price=99,
        annual_price=990,  # ~17% discount
        features={
            "workflows": 1000,
            "executions_per_month": 100000,
            "team_members": 50,
            "storage_gb": 1000,
            "api_calls_per_month": 500000,
            "advanced_analytics": True,
            "api_keys": 25,
            "custom_integrations": True,
            "sso": True,
            "audit_logging": True,
            "support": "priority_email",
        },
        quotas={
            "max_workflows": 1000,
            "max_executions_monthly": 100000,
            "max_team_members": 50,
            "storage_gb": 1000,
            "api_calls_monthly": 500000,
            "max_api_keys": 25,
        }
    ),

    SubscriptionTier.ENTERPRISE: PricingPlan(
        tier=SubscriptionTier.ENTERPRISE,
        monthly_price=0,  # Custom pricing
        annual_price=0,  # Custom pricing
        features={
            "workflows": -1,  # Unlimited
            "executions_per_month": -1,  # Unlimited
            "team_members": -1,  # Unlimited
            "storage_gb": -1,  # Unlimited
            "api_calls_per_month": -1,  # Unlimited
            "advanced_analytics": True,
            "api_keys": -1,  # Unlimited
            "custom_integrations": True,
            "sso": True,
            "audit_logging": True,
            "support": "dedicated",
        },
        quotas={
            "max_workflows": -1,  # Unlimited
            "max_executions_monthly": -1,
            "max_team_members": -1,
            "storage_gb": -1,
            "api_calls_monthly": -1,
            "max_api_keys": -1,
        }
    ),
}


class Subscription:
    """User subscription to a plan"""

    def __init__(self, subscription_id: str, tenant_id: str,
                 tier: SubscriptionTier, billing_cycle: BillingCycle = BillingCycle.MONTHLY):
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.tier = tier
        self.billing_cycle = billing_cycle
        self.status = SubscriptionStatus.TRIAL
        self.start_date = datetime.utcnow()
        self.end_date = self.start_date + timedelta(days=14)  # 14-day trial
        self.trial_end_date = self.end_date
        self.next_billing_date = self.end_date
        self.auto_renew = True
        self.canceled_date: Optional[datetime] = None
        self.cancel_reason: Optional[str] = None

    @property
    def plan(self) -> PricingPlan:
        """Get pricing plan for current tier"""
        return PRICING_PLANS[self.tier]

    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == SubscriptionStatus.TRIAL

    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == SubscriptionStatus.ACTIVE

    @property
    def is_expired(self) -> bool:
        """Check if subscription has expired"""
        return datetime.utcnow() > self.end_date

    @property
    def days_remaining(self) -> int:
        """Get days remaining in subscription"""
        if self.is_expired:
            return 0
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)

    @property
    def current_price(self) -> float:
        """Get current monthly price"""
        if self.billing_cycle == BillingCycle.MONTHLY:
            return self.plan.monthly_price
        else:  # Annual
            return self.plan.annual_price / 12

    def upgrade_to_tier(self, new_tier: SubscriptionTier) -> bool:
        """Upgrade subscription to higher tier"""
        current_level = self._get_tier_level(self.tier)
        new_level = self._get_tier_level(new_tier)

        if new_level <= current_level:
            logger.warning(f"Cannot downgrade from {self.tier} to {new_tier}")
            return False

        logger.info(f"Upgrading subscription {self.subscription_id} from {self.tier} to {new_tier}")
        self.tier = new_tier
        self.status = SubscriptionStatus.ACTIVE
        return True

    def downgrade_to_tier(self, new_tier: SubscriptionTier,
                         effective_date: datetime = None) -> bool:
        """Downgrade subscription to lower tier"""
        current_level = self._get_tier_level(self.tier)
        new_level = self._get_tier_level(new_tier)

        if new_level >= current_level:
            logger.warning(f"Cannot upgrade from {self.tier} to {new_tier}")
            return False

        logger.info(f"Downgrading subscription {self.subscription_id} from {self.tier} to {new_tier}")
        self.tier = new_tier

        # Downgrade effective next billing cycle
        if effective_date is None:
            effective_date = self.next_billing_date

        return True

    def activate_subscription(self) -> bool:
        """Activate subscription from trial"""
        if self.status != SubscriptionStatus.TRIAL:
            logger.warning(f"Cannot activate non-trial subscription {self.subscription_id}")
            return False

        logger.info(f"Activating subscription {self.subscription_id}")
        self.status = SubscriptionStatus.ACTIVE
        self.trial_end_date = datetime.utcnow()

        # Set next billing date based on cycle
        if self.billing_cycle == BillingCycle.MONTHLY:
            self.next_billing_date = datetime.utcnow() + timedelta(days=30)
            self.end_date = self.next_billing_date
        else:  # Annual
            self.next_billing_date = datetime.utcnow() + timedelta(days=365)
            self.end_date = self.next_billing_date

        return True

    def cancel_subscription(self, reason: str = "") -> bool:
        """Cancel subscription"""
        if self.status == SubscriptionStatus.CANCELED:
            return False

        logger.info(f"Canceling subscription {self.subscription_id}: {reason}")
        self.status = SubscriptionStatus.CANCELED
        self.canceled_date = datetime.utcnow()
        self.cancel_reason = reason
        self.auto_renew = False
        return True

    def suspend_subscription(self, reason: str = "") -> bool:
        """Suspend subscription (e.g., payment failed)"""
        logger.info(f"Suspending subscription {self.subscription_id}: {reason}")
        self.status = SubscriptionStatus.SUSPENDED
        return True

    def resume_subscription(self) -> bool:
        """Resume suspended subscription"""
        if self.status != SubscriptionStatus.SUSPENDED:
            return False

        logger.info(f"Resuming subscription {self.subscription_id}")
        self.status = SubscriptionStatus.ACTIVE
        return True

    def _get_tier_level(self, tier: SubscriptionTier) -> int:
        """Get numeric level for tier (for comparison)"""
        levels = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.STARTER: 1,
            SubscriptionTier.PROFESSIONAL: 2,
            SubscriptionTier.ENTERPRISE: 3,
        }
        return levels.get(tier, -1)

    def get_feature_limit(self, feature: str) -> int:
        """Get limit for a feature"""
        return self.plan.features.get(feature, 0)

    def has_feature(self, feature: str) -> bool:
        """Check if plan includes feature"""
        feature_value = self.plan.features.get(feature)
        if feature_value is None:
            return False
        if isinstance(feature_value, bool):
            return feature_value
        if isinstance(feature_value, int):
            return feature_value > 0
        return bool(feature_value)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "subscription_id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "tier": self.tier.value,
            "status": self.status.value,
            "billing_cycle": self.billing_cycle.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "trial_end_date": self.trial_end_date.isoformat(),
            "next_billing_date": self.next_billing_date.isoformat(),
            "auto_renew": self.auto_renew,
            "canceled_date": self.canceled_date.isoformat() if self.canceled_date else None,
            "cancel_reason": self.cancel_reason,
            "is_trial": self.is_trial,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "days_remaining": self.days_remaining,
            "current_price": self.current_price,
        }


class UsageMetrics:
    """Track subscription usage"""

    def __init__(self, subscription_id: str, tenant_id: str):
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.current_month_start = datetime.utcnow().replace(day=1)
        self.workflows_created = 0
        self.executions_completed = 0
        self.api_calls_made = 0
        self.storage_used_gb = 0
        self.team_members = 0

    def record_workflow_creation(self) -> None:
        """Record workflow creation"""
        self.workflows_created += 1

    def record_execution(self) -> None:
        """Record workflow execution"""
        self.executions_completed += 1

    def record_api_call(self) -> None:
        """Record API call"""
        self.api_calls_made += 1

    def record_storage(self, size_gb: float) -> None:
        """Record storage usage"""
        self.storage_used_gb = max(self.storage_used_gb, size_gb)

    def record_team_member(self, count: int) -> None:
        """Record team member count"""
        self.team_members = max(self.team_members, count)

    def check_quota_exceeded(self, subscription: Subscription) -> Dict[str, bool]:
        """Check which quotas are exceeded"""
        plan = subscription.plan
        exceeded = {}

        if plan.quotas.get("max_workflows", -1) > 0:
            exceeded["workflows"] = self.workflows_created > plan.quotas["max_workflows"]

        if plan.quotas.get("max_executions_monthly", -1) > 0:
            exceeded["executions"] = self.executions_completed > plan.quotas["max_executions_monthly"]

        if plan.quotas.get("api_calls_monthly", -1) > 0:
            exceeded["api_calls"] = self.api_calls_made > plan.quotas["api_calls_monthly"]

        if plan.quotas.get("storage_gb", -1) > 0:
            exceeded["storage"] = self.storage_used_gb > plan.quotas["storage_gb"]

        if plan.quotas.get("max_team_members", -1) > 0:
            exceeded["team_members"] = self.team_members > plan.quotas["max_team_members"]

        return exceeded

    def get_usage_percent(self, subscription: Subscription) -> Dict[str, float]:
        """Get usage as percentage of quota"""
        plan = subscription.plan
        usage = {}

        if plan.quotas.get("max_workflows", -1) > 0:
            usage["workflows"] = (self.workflows_created / plan.quotas["max_workflows"]) * 100
        else:
            usage["workflows"] = 0

        if plan.quotas.get("max_executions_monthly", -1) > 0:
            usage["executions"] = (self.executions_completed / plan.quotas["max_executions_monthly"]) * 100
        else:
            usage["executions"] = 0

        if plan.quotas.get("api_calls_monthly", -1) > 0:
            usage["api_calls"] = (self.api_calls_made / plan.quotas["api_calls_monthly"]) * 100
        else:
            usage["api_calls"] = 0

        if plan.quotas.get("storage_gb", -1) > 0:
            usage["storage"] = (self.storage_used_gb / plan.quotas["storage_gb"]) * 100
        else:
            usage["storage"] = 0

        return usage

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "subscription_id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "workflows_created": self.workflows_created,
            "executions_completed": self.executions_completed,
            "api_calls_made": self.api_calls_made,
            "storage_used_gb": self.storage_used_gb,
            "team_members": self.team_members,
            "period_start": self.current_month_start.isoformat(),
        }
