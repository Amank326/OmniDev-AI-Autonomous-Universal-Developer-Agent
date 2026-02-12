"""
Phase 12: Tenant Manager
Multi-tenant isolation and management
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    TRIAL = "trial"


class DataResidency(str, Enum):
    US = "us"
    EU = "eu"
    APAC = "apac"
    CA = "ca"


class Tenant:
    """Represents a tenant in the system"""

    def __init__(self, tenant_id: str, name: str, owner_id: str):
        self.id = tenant_id
        self.name = name
        self.owner_id = owner_id
        self.status = TenantStatus.ACTIVE
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.custom_domain: Optional[str] = None
        self.logo_url: Optional[str] = None
        self.theme_config: Dict[str, Any] = {}
        self.data_residency = DataResidency.US
        self.features: Dict[str, bool] = {}
        self.quotas: Dict[str, int] = {}
        self.metadata: Dict[str, Any] = {}
        self.settings: Dict[str, Any] = {}


class TenantManager:
    """
    Manages tenant lifecycle, isolation, and configuration
    """

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_users: Dict[str, List[str]] = {}  # tenant_id -> [user_ids]
        self.user_tenant_map: Dict[str, List[str]] = {}  # user_id -> [tenant_ids]

    def create_tenant(self, name: str, owner_id: str, 
                     plan: str = "STARTER",
                     data_residency: DataResidency = DataResidency.US) -> Tenant:
        """
        Create a new tenant
        Returns tenant object with initialized features and quotas
        """
        tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
        logger.info(f"Creating tenant: {tenant_id} ({name})")

        tenant = Tenant(tenant_id, name, owner_id)
        tenant.data_residency = data_residency

        # Set plan-based features and quotas
        self._initialize_plan(tenant, plan)

        # Add owner as team member
        self.add_tenant_member(tenant_id, owner_id)

        self.tenants[tenant_id] = tenant

        logger.info(f"Tenant created: {tenant_id}")
        return tenant

    def _initialize_plan(self, tenant: Tenant, plan: str) -> None:
        """Initialize features and quotas based on plan"""
        plans = {
            "FREE": {
                "features": {
                    "workflows": True,
                    "automation": True,
                    "analytics": True,
                    "api": False,
                    "sso": False,
                    "audit_logs": False,
                    "team_management": False,
                    "custom_domain": False,
                },
                "quotas": {
                    "workflows": 10,
                    "executions_per_month": 100,
                    "team_members": 1,
                    "storage_gb": 1,
                    "api_calls_per_month": 0,
                },
            },
            "STARTER": {
                "features": {
                    "workflows": True,
                    "automation": True,
                    "analytics": True,
                    "api": True,
                    "sso": False,
                    "audit_logs": True,
                    "team_management": True,
                    "custom_domain": False,
                },
                "quotas": {
                    "workflows": 100,
                    "executions_per_month": 1000,
                    "team_members": 5,
                    "storage_gb": 10,
                    "api_calls_per_month": 5000,
                },
            },
            "PROFESSIONAL": {
                "features": {
                    "workflows": True,
                    "automation": True,
                    "analytics": True,
                    "api": True,
                    "sso": True,
                    "audit_logs": True,
                    "team_management": True,
                    "custom_domain": True,
                },
                "quotas": {
                    "workflows": 1000,
                    "executions_per_month": 10000,
                    "team_members": 50,
                    "storage_gb": 100,
                    "api_calls_per_month": 50000,
                },
            },
            "ENTERPRISE": {
                "features": {
                    "workflows": True,
                    "automation": True,
                    "analytics": True,
                    "api": True,
                    "sso": True,
                    "audit_logs": True,
                    "team_management": True,
                    "custom_domain": True,
                },
                "quotas": {
                    "workflows": 10000,
                    "executions_per_month": 1000000,
                    "team_members": 1000,
                    "storage_gb": 1000,
                    "api_calls_per_month": 1000000,
                },
            },
        }

        config = plans.get(plan, plans["STARTER"])
        tenant.features = config["features"]
        tenant.quotas = config["quotas"]
        tenant.metadata["plan"] = plan

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)

    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by custom domain"""
        for tenant in self.tenants.values():
            if tenant.custom_domain == domain:
                return tenant
        return None

    def list_tenants(self) -> List[Tenant]:
        """List all tenants"""
        return list(self.tenants.values())

    def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> Optional[Tenant]:
        """Update tenant information"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        logger.info(f"Updating tenant: {tenant_id}")

        # Update allowed fields
        allowed_fields = {"name", "custom_domain", "logo_url", "theme_config", "settings"}
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(tenant, field, value)

        tenant.updated_at = datetime.utcnow()
        return tenant

    def delete_tenant(self, tenant_id: str, hard_delete: bool = False) -> bool:
        """
        Soft delete tenant (mark as deleted) or hard delete
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        logger.warning(f"Deleting tenant: {tenant_id} (hard={hard_delete})")

        if hard_delete:
            # Completely remove all data
            del self.tenants[tenant_id]
            if tenant_id in self.tenant_users:
                del self.tenant_users[tenant_id]
        else:
            # Soft delete
            tenant.status = TenantStatus.DELETED
            tenant.updated_at = datetime.utcnow()

        return True

    def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """Suspend tenant (prevents access)"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        logger.warning(f"Suspending tenant: {tenant_id} - Reason: {reason}")
        tenant.status = TenantStatus.SUSPENDED
        tenant.metadata["suspension_reason"] = reason
        tenant.metadata["suspended_at"] = datetime.utcnow().isoformat()
        return True

    def unsuspend_tenant(self, tenant_id: str) -> bool:
        """Unsuspend tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        logger.info(f"Unsuspending tenant: {tenant_id}")
        tenant.status = TenantStatus.ACTIVE
        tenant.metadata.pop("suspension_reason", None)
        tenant.metadata.pop("suspended_at", None)
        return True

    def add_tenant_member(self, tenant_id: str, user_id: str) -> bool:
        """Add user to tenant"""
        if tenant_id not in self.tenant_users:
            self.tenant_users[tenant_id] = []

        if user_id not in self.tenant_users[tenant_id]:
            self.tenant_users[tenant_id].append(user_id)

        if user_id not in self.user_tenant_map:
            self.user_tenant_map[user_id] = []

        if tenant_id not in self.user_tenant_map[user_id]:
            self.user_tenant_map[user_id].append(tenant_id)

        logger.info(f"Added user {user_id} to tenant {tenant_id}")
        return True

    def remove_tenant_member(self, tenant_id: str, user_id: str) -> bool:
        """Remove user from tenant"""
        if tenant_id in self.tenant_users and user_id in self.tenant_users[tenant_id]:
            self.tenant_users[tenant_id].remove(user_id)

        if user_id in self.user_tenant_map and tenant_id in self.user_tenant_map[user_id]:
            self.user_tenant_map[user_id].remove(tenant_id)

        logger.info(f"Removed user {user_id} from tenant {tenant_id}")
        return True

    def get_tenant_members(self, tenant_id: str) -> List[str]:
        """Get all members in a tenant"""
        return self.tenant_users.get(tenant_id, [])

    def get_user_tenants(self, user_id: str) -> List[Tenant]:
        """Get all tenants for a user"""
        tenant_ids = self.user_tenant_map.get(user_id, [])
        return [self.tenants[tid] for tid in tenant_ids if tid in self.tenants]

    def get_tenant_features(self, tenant_id: str) -> Dict[str, bool]:
        """Get enabled features for a tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {}
        return tenant.features

    def is_feature_enabled(self, tenant_id: str, feature: str) -> bool:
        """Check if a feature is enabled for tenant"""
        features = self.get_tenant_features(tenant_id)
        return features.get(feature, False)

    def get_tenant_quota(self, tenant_id: str, quota_key: str) -> Optional[int]:
        """Get quota value for tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        return tenant.quotas.get(quota_key)

    def check_quota(self, tenant_id: str, quota_key: str, usage: int) -> bool:
        """Check if usage is within quota"""
        quota = self.get_tenant_quota(tenant_id, quota_key)
        if quota is None:
            return False
        return usage <= quota

    def enforce_quota(self, tenant_id: str, quota_key: str, usage: int) -> bool:
        """Enforce quota - returns False if over limit"""
        if not self.check_quota(tenant_id, quota_key, usage):
            logger.warning(f"Quota exceeded for {tenant_id}: {quota_key}")
            return False
        return True

    def upgrade_plan(self, tenant_id: str, new_plan: str) -> bool:
        """Upgrade tenant to different plan"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        logger.info(f"Upgrading tenant {tenant_id} to plan {new_plan}")
        self._initialize_plan(tenant, new_plan)
        tenant.updated_at = datetime.utcnow()
        return True

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get usage statistics for tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {}

        members = self.get_tenant_members(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "plan": tenant.metadata.get("plan", "UNKNOWN"),
            "status": tenant.status,
            "created_at": tenant.created_at.isoformat(),
            "member_count": len(members),
            "features": tenant.features,
            "quotas": tenant.quotas,
            "data_residency": tenant.data_residency,
        }

    def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate that user can access tenant"""
        tenants = self.get_user_tenants(user_id)
        return any(t.id == tenant_id for t in tenants)

    def isolate_query(self, query: str, tenant_id: str) -> str:
        """
        Add tenant isolation to query
        Ensures queries only access tenant data
        """
        # This is a stub - actual implementation would depend on ORM
        # In practice, this would add WHERE tenant_id = ? to queries
        return query

    def get_data_residency_region(self, tenant_id: str) -> str:
        """Get data residency region for tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return "us"

        region_map = {
            DataResidency.US: "us-east-1",
            DataResidency.EU: "eu-west-1",
            DataResidency.APAC: "ap-southeast-1",
            DataResidency.CA: "ca-central-1",
        }

        return region_map.get(tenant.data_residency, "us-east-1")
