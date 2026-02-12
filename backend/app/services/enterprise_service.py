"""
Phase 12: Enterprise Service
Unified orchestration for enterprise features
Multi-tenant, RBAC, audit logging, subscriptions
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .tenant_manager import TenantManager, Tenant
from .rbac_service import RBACService
from .audit_logger import AuditLogger, AuditEventType
from .subscription_models import Subscription, SubscriptionTier, UsageMetrics

logger = logging.getLogger(__name__)


class EnterpriseService:
    """
    Unified enterprise features orchestration service
    Coordinates multi-tenancy, RBAC, audit logging, and subscriptions
    """

    def __init__(self):
        self.tenant_manager = TenantManager()
        self.rbac_service = RBACService()
        self.audit_logger = AuditLogger()
        self.subscriptions: Dict[str, Subscription] = {}  # tenant_id -> Subscription
        self.usage_metrics: Dict[str, UsageMetrics] = {}  # tenant_id -> UsageMetrics

    # ============================================================================
    # Tenant Management
    # ============================================================================

    def create_tenant_with_subscription(self, tenant_name: str, owner_id: str,
                                       plan: SubscriptionTier = SubscriptionTier.FREE,
                                       data_residency: str = "US") -> Tuple[Tenant, Subscription]:
        """
        Create tenant with subscription and initial owner
        """
        logger.info(f"Creating tenant: {tenant_name} (owner={owner_id})")

        # Create tenant
        tenant = self.tenant_manager.create_tenant(
            tenant_name=tenant_name,
            owner_id=owner_id,
            data_residency=data_residency
        )

        if not tenant:
            logger.error(f"Failed to create tenant: {tenant_name}")
            return None, None

        # Create subscription
        subscription_id = f"sub_{tenant.id}"
        subscription = Subscription(subscription_id, tenant.id, plan)

        if plan != SubscriptionTier.FREE:
            subscription.activate_subscription()

        self.subscriptions[tenant.id] = subscription
        self.usage_metrics[tenant.id] = UsageMetrics(subscription_id, tenant.id)

        # Create owner role assignment
        self.rbac_service.assign_role_to_user(
            user_id=owner_id,
            role="SUPER_ADMIN",
            tenant_id=tenant.id,
            assigned_by="system"
        )

        # Audit log
        self.audit_logger.log_user_action(
            event_type=AuditEventType.TENANT_CREATE,
            user_id=owner_id,
            tenant_id=tenant.id,
            description=f"Tenant created: {tenant_name}",
            details={
                "tenant_id": tenant.id,
                "tenant_name": tenant_name,
                "plan": plan.value,
                "owner_id": owner_id,
            }
        )

        return tenant, subscription

    def delete_tenant(self, tenant_id: str, deleted_by: str, reason: str = "") -> bool:
        """Delete tenant and all associated data"""
        logger.info(f"Deleting tenant: {tenant_id}")

        if not self.tenant_manager.delete_tenant(tenant_id):
            return False

        # Cancel subscription
        if tenant_id in self.subscriptions:
            self.subscriptions[tenant_id].cancel_subscription(reason)
            del self.subscriptions[tenant_id]

        # Clear usage metrics
        if tenant_id in self.usage_metrics:
            del self.usage_metrics[tenant_id]

        # Audit log
        self.audit_logger.log_user_action(
            event_type=AuditEventType.TENANT_DELETE,
            user_id=deleted_by,
            tenant_id=tenant_id,
            description=f"Tenant deleted",
            details={"reason": reason}
        )

        return True

    def add_tenant_member(self, tenant_id: str, user_id: str, role: str,
                         added_by: str) -> bool:
        """Add member to tenant with role"""
        logger.info(f"Adding member {user_id} to tenant {tenant_id} with role {role}")

        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {tenant_id}")
            return False

        # Add to tenant
        if not self.tenant_manager.add_tenant_member(tenant_id, user_id):
            return False

        # Assign role
        self.rbac_service.assign_role_to_user(user_id, role, tenant_id, added_by)

        # Audit log
        self.audit_logger.log_user_action(
            event_type=AuditEventType.TENANT_MEMBER_ADD,
            user_id=added_by,
            tenant_id=tenant_id,
            description=f"Member {user_id} added with role {role}",
            details={"user_id": user_id, "role": role}
        )

        return True

    def remove_tenant_member(self, tenant_id: str, user_id: str,
                            removed_by: str) -> bool:
        """Remove member from tenant"""
        logger.info(f"Removing member {user_id} from tenant {tenant_id}")

        if not self.tenant_manager.remove_tenant_member(tenant_id, user_id):
            return False

        # Revoke all roles
        roles = self.rbac_service.get_user_roles(user_id, tenant_id)
        for role in roles:
            self.rbac_service.revoke_role_from_user(user_id, role, tenant_id)

        # Audit log
        self.audit_logger.log_user_action(
            event_type=AuditEventType.TENANT_MEMBER_REMOVE,
            user_id=removed_by,
            tenant_id=tenant_id,
            description=f"Member {user_id} removed",
            details={"user_id": user_id}
        )

        return True

    # ============================================================================
    # RBAC Management
    # ============================================================================

    def assign_user_role(self, user_id: str, role: str, tenant_id: str,
                        assigned_by: str) -> bool:
        """Assign role to user"""
        logger.info(f"Assigning {role} to {user_id} in tenant {tenant_id}")

        if not self.rbac_service.assign_role_to_user(user_id, role, tenant_id, assigned_by):
            return False

        # Audit log
        self.audit_logger.log_permission_change(
            action="assign",
            user_id=user_id,
            target_user_id=user_id,
            tenant_id=tenant_id,
            role_or_permission=role,
            changed_by=assigned_by
        )

        return True

    def revoke_user_role(self, user_id: str, role: str, tenant_id: str,
                        revoked_by: str) -> bool:
        """Revoke role from user"""
        logger.info(f"Revoking {role} from {user_id} in tenant {tenant_id}")

        if not self.rbac_service.revoke_role_from_user(user_id, role, tenant_id):
            return False

        # Audit log
        self.audit_logger.log_permission_change(
            action="revoke",
            user_id=user_id,
            target_user_id=user_id,
            tenant_id=tenant_id,
            role_or_permission=role,
            changed_by=revoked_by
        )

        return True

    def check_permission(self, user_id: str, permission: str,
                        tenant_id: str) -> bool:
        """Check if user has permission"""
        return self.rbac_service.has_permission(user_id, permission, tenant_id)

    def get_user_permissions(self, user_id: str, tenant_id: str) -> set:
        """Get all permissions for user"""
        return self.rbac_service.get_user_permissions(user_id, tenant_id)

    # ============================================================================
    # Subscription Management
    # ============================================================================

    def get_subscription(self, tenant_id: str) -> Optional[Subscription]:
        """Get tenant subscription"""
        return self.subscriptions.get(tenant_id)

    def upgrade_subscription(self, tenant_id: str, new_tier: SubscriptionTier,
                            upgraded_by: str) -> bool:
        """Upgrade tenant subscription"""
        subscription = self.subscriptions.get(tenant_id)
        if not subscription:
            logger.error(f"Subscription not found: {tenant_id}")
            return False

        old_tier = subscription.tier
        if not subscription.upgrade_to_tier(new_tier):
            return False

        logger.info(f"Subscription {tenant_id} upgraded: {old_tier} -> {new_tier}")

        # Audit log
        self.audit_logger.log_user_action(
            event_type="subscription.upgrade",
            user_id=upgraded_by,
            tenant_id=tenant_id,
            description=f"Subscription upgraded to {new_tier.value}",
            details={"from": old_tier.value, "to": new_tier.value}
        )

        return True

    def get_usage_metrics(self, tenant_id: str) -> Optional[UsageMetrics]:
        """Get tenant usage metrics"""
        return self.usage_metrics.get(tenant_id)

    def check_quota(self, tenant_id: str) -> Dict:
        """Check tenant quota usage"""
        subscription = self.subscriptions.get(tenant_id)
        metrics = self.usage_metrics.get(tenant_id)

        if not subscription or not metrics:
            return {}

        exceeded = metrics.check_quota_exceeded(subscription)
        usage_percent = metrics.get_usage_percent(subscription)

        return {
            "exceeded": exceeded,
            "usage_percent": usage_percent,
            "metrics": metrics.to_dict(),
        }

    # ============================================================================
    # Audit Logging
    # ============================================================================

    def log_user_action(self, event_type: str, user_id: str, tenant_id: str,
                       description: str = "", details: Dict = None) -> str:
        """Log user action"""
        return self.audit_logger.log_user_action(
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            description=description,
            details=details
        )

    def log_resource_change(self, action: str, resource_type: str,
                           resource_id: str, user_id: str, tenant_id: str,
                           old_value: Dict = None, new_value: Dict = None) -> str:
        """Log resource change"""
        return self.audit_logger.log_resource_change(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            tenant_id=tenant_id,
            old_value=old_value,
            new_value=new_value
        )

    def get_audit_log(self, tenant_id: str, filters: Dict = None,
                     limit: int = 100) -> List[Dict]:
        """Get audit log for tenant"""
        return self.audit_logger.get_audit_log(tenant_id, filters=filters, limit=limit)

    def export_audit_log(self, tenant_id: str, format: str = "json",
                        filters: Dict = None) -> str:
        """Export audit log"""
        return self.audit_logger.export_audit_log(tenant_id, format=format, filters=filters)

    def get_audit_stats(self, tenant_id: str) -> Dict:
        """Get audit log statistics"""
        return self.audit_logger.get_audit_stats(tenant_id)

    # ============================================================================
    # Comprehensive Health Check
    # ============================================================================

    def get_enterprise_status(self, tenant_id: str) -> Dict:
        """Get comprehensive enterprise status"""
        tenant = self.tenant_manager.get_tenant(tenant_id)
        subscription = self.subscriptions.get(tenant_id)
        metrics = self.usage_metrics.get(tenant_id)
        audit_stats = self.audit_logger.get_audit_stats(tenant_id)

        if not tenant:
            return {"error": f"Tenant not found: {tenant_id}"}

        return {
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "status": tenant.status.value,
                "created_at": tenant.created_at.isoformat(),
                "member_count": len(tenant.members),
                "data_residency": tenant.data_residency,
            },
            "subscription": subscription.to_dict() if subscription else None,
            "usage": metrics.to_dict() if metrics else None,
            "quota_check": self.check_quota(tenant_id),
            "audit_stats": audit_stats,
        }

    def get_system_health(self) -> Dict:
        """Get system health across all tenants"""
        return {
            "total_tenants": len(self.tenant_manager.tenants),
            "total_subscriptions": len(self.subscriptions),
            "subscription_distribution": self._get_subscription_distribution(),
            "audit_logs_count": len(self.audit_logger.logs),
        }

    def _get_subscription_distribution(self) -> Dict[str, int]:
        """Get distribution of subscriptions by tier"""
        distribution = {}
        for sub in self.subscriptions.values():
            tier = sub.tier.value
            distribution[tier] = distribution.get(tier, 0) + 1
        return distribution
