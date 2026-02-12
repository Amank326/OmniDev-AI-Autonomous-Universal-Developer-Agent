"""
Usage Quota Service - Usage tracking and quota enforcement
Manages usage tracking, quota limits, and overage detection per tier
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import json


class QuotaType(str, Enum):
    """Types of quotas"""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ROLLING_30 = "rolling_30"
    UNLIMITED = "unlimited"


class UsageMetric(str, Enum):
    """Types of usage metrics"""
    EXECUTIONS = "executions"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    USERS = "users"
    AGENTS = "agents"


class UsageQuotaService:
    """
    Service for tracking usage against tier quotas,
    managing feature flags, and detecting overages.
    """
    
    def __init__(self):
        """Initialize usage quota service"""
        self.usage_tracking = {}
        self.quota_limits = {}
        self.feature_flags = {}
        self.overage_records = {}
        self.quota_resets = {}
    
    def initialize_customer_quotas(
        self,
        customer_id: str,
        tier_limits: Dict,
        reset_cycle: str = "monthly",
    ) -> Dict:
        """
        Initialize quotas for new customer.
        
        Args:
            customer_id: Customer ID
            tier_limits: Tier-specific limits
            reset_cycle: How often quota resets
        
        Returns:
            Quota configuration
        """
        quotas = {
            customer_id: {
                "max_executions": tier_limits.get("max_monthly_executions"),
                "max_api_calls": tier_limits.get("max_api_calls"),
                "max_storage_gb": tier_limits.get("storage_gb"),
                "max_users": tier_limits.get("user_limit"),
                "max_agents": tier_limits.get("max_agents"),
                "reset_cycle": reset_cycle,
                "created_at": datetime.utcnow().isoformat(),
            }
        }
        
        self.quota_limits.update(quotas)
        
        # Initialize tracking
        self.usage_tracking[customer_id] = {
            "executions": 0,
            "api_calls": 0,
            "storage_gb": 0,
            "users": 0,
            "agents": 0,
            "last_reset": datetime.utcnow().isoformat(),
        }
        
        # Calculate next reset
        next_reset = self._calculate_next_reset(reset_cycle)
        self.quota_resets[customer_id] = next_reset
        
        return quotas[customer_id]
    
    def track_usage(
        self,
        customer_id: str,
        metric: str,
        amount: float,
    ) -> Dict:
        """
        Track usage of a metric.
        
        Args:
            customer_id: Customer ID
            metric: Metric type (executions, api_calls, storage, etc)
            amount: Amount used
        
        Returns:
            Updated usage and overage status
        """
        if customer_id not in self.usage_tracking:
            return {"status": "error", "message": "Customer not found"}
        
        usage = self.usage_tracking[customer_id]
        quota = self.quota_limits.get(customer_id, {})
        
        # Update usage
        current = usage.get(metric, 0)
        usage[metric] = current + amount
        
        # Check if over quota
        limit_key = f"max_{metric}"
        limit = quota.get(limit_key)
        
        is_exceeded = False
        overage_amount = 0
        
        if limit is not None and usage[metric] > limit:
            is_exceeded = True
            overage_amount = usage[metric] - limit
            
            # Record overage
            self._record_overage(customer_id, metric, overage_amount)
        
        return {
            "customer_id": customer_id,
            "metric": metric,
            "amount_used": amount,
            "total_usage": usage[metric],
            "limit": limit,
            "is_exceeded": is_exceeded,
            "overage_amount": round(overage_amount, 2) if is_exceeded else 0,
            "percentage_used": (usage[metric] / limit * 100) if limit else 0,
            "tracked_at": datetime.utcnow().isoformat(),
        }
    
    def _record_overage(
        self,
        customer_id: str,
        metric: str,
        overage_amount: float,
    ):
        """Record overage for billing/alerts"""
        if customer_id not in self.overage_records:
            self.overage_records[customer_id] = []
        
        overage = {
            "metric": metric,
            "amount": overage_amount,
            "recorded_at": datetime.utcnow().isoformat(),
            "status": "pending",  # pending, billed, waived
        }
        
        self.overage_records[customer_id].append(overage)
    
    def get_usage_status(self, customer_id: str) -> Dict:
        """
        Get comprehensive usage status for customer.
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Current usage and quota status
        """
        usage = self.usage_tracking.get(customer_id, {})
        quota = self.quota_limits.get(customer_id, {})
        
        if not usage:
            return {"status": "error", "message": "Customer not found"}
        
        metrics_status = {}
        
        for metric in [UsageMetric.EXECUTIONS, UsageMetric.API_CALLS, UsageMetric.STORAGE, 
                      UsageMetric.USERS, UsageMetric.AGENTS]:
            metric_key = metric.value
            limit_key = f"max_{metric_key}"
            
            current = usage.get(metric_key, 0)
            limit = quota.get(limit_key)
            
            metrics_status[metric_key] = {
                "current": current,
                "limit": limit,
                "unlimited": limit is None,
                "percentage_used": (current / limit * 100) if limit else 0,
                "remaining": (limit - current) if limit else None,
                "status": self._get_usage_status(current, limit),
            }
        
        # Calculate next reset
        next_reset = self.quota_resets.get(customer_id)
        days_until_reset = (datetime.fromisoformat(next_reset) - datetime.utcnow()).days if next_reset else None
        
        return {
            "customer_id": customer_id,
            "metrics": metrics_status,
            "next_reset": next_reset,
            "days_until_reset": days_until_reset,
            "overages": self.overage_records.get(customer_id, []),
        }
    
    def _get_usage_status(self, current: float, limit: Optional[float]) -> str:
        """Determine usage status"""
        if limit is None:
            return "unlimited"
        
        percentage = (current / limit) * 100
        
        if percentage >= 100:
            return "exceeded"
        elif percentage >= 80:
            return "warning"
        elif percentage >= 50:
            return "caution"
        else:
            return "good"
    
    def _calculate_next_reset(self, reset_cycle: str) -> str:
        """Calculate next quota reset date"""
        now = datetime.utcnow()
        
        if reset_cycle == "monthly":
            if now.month == 12:
                next_reset = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_reset = now.replace(month=now.month + 1, day=1)
        
        elif reset_cycle == "annual":
            next_reset = now.replace(year=now.year + 1, month=1, day=1)
        
        elif reset_cycle == "rolling_30":
            next_reset = now + timedelta(days=30)
        
        else:
            next_reset = now + timedelta(days=30)
        
        return next_reset.isoformat()
    
    def reset_quota(self, customer_id: str) -> Dict:
        """
        Reset quota for customer (on schedule or manual).
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Reset confirmation
        """
        if customer_id not in self.usage_tracking:
            return {"status": "error", "message": "Customer not found"}
        
        # Reset usage
        for metric in [UsageMetric.EXECUTIONS, UsageMetric.API_CALLS, UsageMetric.STORAGE, 
                      UsageMetric.USERS, UsageMetric.AGENTS]:
            self.usage_tracking[customer_id][metric.value] = 0
        
        # Update last reset
        self.usage_tracking[customer_id]["last_reset"] = datetime.utcnow().isoformat()
        
        # Recalculate next reset
        quota = self.quota_limits.get(customer_id, {})
        reset_cycle = quota.get("reset_cycle", "monthly")
        self.quota_resets[customer_id] = self._calculate_next_reset(reset_cycle)
        
        return {
            "customer_id": customer_id,
            "status": "reset",
            "reset_at": datetime.utcnow().isoformat(),
            "next_reset": self.quota_resets[customer_id],
        }
    
    def set_feature_flag(
        self,
        customer_id: str,
        feature_name: str,
        enabled: bool,
        reason: Optional[str] = None,
        expiration_date: Optional[str] = None,
    ) -> Dict:
        """
        Set feature flag for customer.
        
        Args:
            customer_id: Customer ID
            feature_name: Feature name
            enabled: Is feature enabled
            reason: Reason for flag
            expiration_date: When flag expires
        
        Returns:
            Flag configuration
        """
        if customer_id not in self.feature_flags:
            self.feature_flags[customer_id] = {}
        
        flag = {
            "feature": feature_name,
            "enabled": enabled,
            "set_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "expires_at": expiration_date,
        }
        
        self.feature_flags[customer_id][feature_name] = flag
        
        return flag
    
    def is_feature_enabled(
        self,
        customer_id: str,
        feature_name: str,
    ) -> bool:
        """
        Check if feature is enabled for customer.
        
        Args:
            customer_id: Customer ID
            feature_name: Feature name
        
        Returns:
            True if enabled
        """
        flags = self.feature_flags.get(customer_id, {})
        flag = flags.get(feature_name)
        
        if not flag:
            return True  # Default enabled if no flag set
        
        # Check expiration
        if flag.get("expires_at"):
            expiration = datetime.fromisoformat(flag["expires_at"])
            if datetime.utcnow() > expiration:
                return not flag["enabled"]  # Flag expired
        
        return flag["enabled"]
    
    def get_feature_flags(self, customer_id: str) -> Dict:
        """Get all feature flags for customer"""
        return self.feature_flags.get(customer_id, {})
    
    def check_quota_limit(
        self,
        customer_id: str,
        metric: str,
        requested_amount: float = 1.0,
    ) -> Dict:
        """
        Check if quota allows requested operation.
        
        Args:
            customer_id: Customer ID
            metric: Metric to check
            requested_amount: Amount to check
        
        Returns:
            Quota check result
        """
        usage = self.usage_tracking.get(customer_id)
        quota = self.quota_limits.get(customer_id, {})
        
        if not usage:
            return {"allowed": False, "reason": "Customer not found"}
        
        limit_key = f"max_{metric}"
        limit = quota.get(limit_key)
        
        current = usage.get(metric, 0)
        
        # Unlimited
        if limit is None:
            return {
                "allowed": True,
                "reason": "Unlimited quota",
                "current": current,
                "limit": None,
            }
        
        # Check if would exceed
        if current + requested_amount > limit:
            remaining = limit - current
            return {
                "allowed": False,
                "reason": "Quota exceeded",
                "current": current,
                "limit": limit,
                "requested": requested_amount,
                "remaining": max(0, remaining),
            }
        
        return {
            "allowed": True,
            "reason": "Within quota",
            "current": current,
            "limit": limit,
            "remaining": limit - current,
        }
    
    def get_overage_report(self, customer_id: str) -> Dict:
        """
        Get overage report for billing.
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Overage details
        """
        overages = self.overage_records.get(customer_id, [])
        
        total_overages = {}
        total_cost = 0.0
        
        for overage in overages:
            metric = overage["metric"]
            amount = overage["amount"]
            
            if metric not in total_overages:
                total_overages[metric] = 0
            
            total_overages[metric] += amount
            
            # Calculate overage cost (example rates)
            if metric == "executions":
                total_cost += amount * 0.001  # $0.001 per execution
            elif metric == "storage":
                total_cost += amount * 0.10  # $0.10 per GB
            elif metric == "users":
                total_cost += amount * 10.0  # $10 per user
        
        return {
            "customer_id": customer_id,
            "period": "current_month",
            "total_overages": total_overages,
            "total_overage_cost": round(total_cost, 2),
            "overage_records": overages,
            "pending_billed": sum(1 for o in overages if o["status"] == "pending"),
        }
    
    def bulk_track_usage(
        self,
        customer_id: str,
        metrics: Dict[str, float],
    ) -> Dict:
        """
        Track multiple metrics at once.
        
        Args:
            customer_id: Customer ID
            metrics: Dict of metric_name -> amount
        
        Returns:
            Results for all metrics
        """
        results = {}
        
        for metric, amount in metrics.items():
            result = self.track_usage(customer_id, metric, amount)
            results[metric] = result
        
        return {
            "customer_id": customer_id,
            "metrics_tracked": results,
            "any_exceeded": any(r.get("is_exceeded") for r in results.values()),
        }
    
    def get_quota_analytics(self) -> Dict:
        """
        Get analytics on quota usage across customers.
        
        Returns:
            Quota analytics
        """
        total_customers = len(self.usage_tracking)
        exceeded_quota = 0
        approaching_quota = 0
        
        for customer_id, usage in self.usage_tracking.items():
            quota = self.quota_limits.get(customer_id, {})
            
            for metric in [UsageMetric.EXECUTIONS, UsageMetric.API_CALLS, UsageMetric.STORAGE, 
                          UsageMetric.USERS, UsageMetric.AGENTS]:
                metric_key = metric.value
                limit_key = f"max_{metric_key}"
                
                current = usage.get(metric_key, 0)
                limit = quota.get(limit_key)
                
                if limit and current > limit:
                    exceeded_quota += 1
                elif limit and current > limit * 0.8:
                    approaching_quota += 1
        
        return {
            "total_customers": total_customers,
            "customers_exceeded_quota": exceeded_quota,
            "customers_approaching_quota": approaching_quota,
            "alert_percentage": ((exceeded_quota + approaching_quota) / total_customers * 100) if total_customers > 0 else 0,
        }
