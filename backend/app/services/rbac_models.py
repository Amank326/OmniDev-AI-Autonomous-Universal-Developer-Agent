"""
Phase 12: RBAC Models
Role-based access control data models and definitions
"""

from enum import Enum
from typing import Set, List, Dict, Any
from datetime import datetime
import uuid


class PredefinedRole(str, Enum):
    """Predefined system roles"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"
    DEVELOPER = "developer"


class Permission:
    """Represents a single permission in the system"""

    def __init__(self, permission_id: str, name: str, description: str,
                 resource: str, action: str):
        self.id = permission_id
        self.name = name
        self.description = description
        self.resource = resource  # workflow, user, team, settings, billing, audit, api
        self.action = action  # create, read, update, delete, execute, manage, etc
        self.created_at = datetime.utcnow()

    def __repr__(self):
        return f"Permission({self.resource}:{self.action})"

    def __eq__(self, other):
        if isinstance(other, Permission):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)


class Role:
    """Represents a role with associated permissions"""

    def __init__(self, role_id: str, name: str, description: str,
                 is_system_role: bool = False):
        self.id = role_id
        self.name = name
        self.description = description
        self.is_system_role = is_system_role
        self.permissions: Set[Permission] = set()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}

    def add_permission(self, permission: Permission) -> None:
        """Add permission to role"""
        self.permissions.add(permission)
        self.updated_at = datetime.utcnow()

    def remove_permission(self, permission: Permission) -> None:
        """Remove permission from role"""
        self.permissions.discard(permission)
        self.updated_at = datetime.utcnow()

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has permission"""
        return permission in self.permissions

    def get_all_permissions(self) -> Set[Permission]:
        """Get all permissions for role"""
        return self.permissions.copy()

    def __repr__(self):
        return f"Role({self.name}, {len(self.permissions)} permissions)"


class UserRole:
    """Represents assignment of role to user"""

    def __init__(self, user_id: str, role: Role, tenant_id: str = None):
        self.id = f"ur_{uuid.uuid4().hex[:12]}"
        self.user_id = user_id
        self.role = role
        self.tenant_id = tenant_id  # For tenant-scoped roles
        self.assigned_at = datetime.utcnow()
        self.assigned_by: str = None
        self.metadata: Dict[str, Any] = {}

    def __repr__(self):
        scope = f"@{self.tenant_id}" if self.tenant_id else "@system"
        return f"UserRole({self.user_id}:{self.role.name}{scope})"


class ResourceAccess:
    """Represents access to a specific resource"""

    def __init__(self, user_id: str, resource_id: str, resource_type: str,
                 access_level: str = "read"):
        self.id = f"ra_{uuid.uuid4().hex[:12]}"
        self.user_id = user_id
        self.resource_id = resource_id
        self.resource_type = resource_type  # workflow, team, project, etc
        self.access_level = access_level  # read, write, admin
        self.created_at = datetime.utcnow()
        self.granted_by: str = None

    def __repr__(self):
        return f"ResourceAccess({self.user_id}:{self.resource_type}/{self.resource_id}={self.access_level})"


# Define all system permissions
WORKFLOW_PERMISSIONS = {
    "workflow:create": Permission("perm_wf_create", "Create Workflow", "Create new workflows", "workflow", "create"),
    "workflow:read": Permission("perm_wf_read", "View Workflow", "View workflow details", "workflow", "read"),
    "workflow:update": Permission("perm_wf_update", "Edit Workflow", "Modify workflow configuration", "workflow", "update"),
    "workflow:delete": Permission("perm_wf_delete", "Delete Workflow", "Delete workflows", "workflow", "delete"),
    "workflow:execute": Permission("perm_wf_execute", "Execute Workflow", "Run workflows", "workflow", "execute"),
    "workflow:share": Permission("perm_wf_share", "Share Workflow", "Share workflows with others", "workflow", "share"),
}

USER_PERMISSIONS = {
    "user:manage": Permission("perm_user_manage", "Manage Users", "Add/remove/modify users", "user", "manage"),
    "user:invite": Permission("perm_user_invite", "Invite Users", "Invite new users to tenant", "user", "invite"),
    "user:deactivate": Permission("perm_user_deactivate", "Deactivate Users", "Deactivate user accounts", "user", "deactivate"),
    "user:reset_password": Permission("perm_user_pwd", "Reset Password", "Reset user passwords", "user", "reset_password"),
}

TEAM_PERMISSIONS = {
    "team:create": Permission("perm_team_create", "Create Team", "Create new teams", "team", "create"),
    "team:manage": Permission("perm_team_manage", "Manage Teams", "Manage team members and settings", "team", "manage"),
    "team:delete": Permission("perm_team_delete", "Delete Team", "Delete teams", "team", "delete"),
}

SETTINGS_PERMISSIONS = {
    "settings:configure": Permission("perm_settings_cfg", "Configure Settings", "Modify system settings", "settings", "configure"),
    "settings:view": Permission("perm_settings_view", "View Settings", "View configuration settings", "settings", "view"),
}

BILLING_PERMISSIONS = {
    "billing:manage": Permission("perm_bill_manage", "Manage Billing", "Manage billing and subscriptions", "billing", "manage"),
    "billing:view": Permission("perm_bill_view", "View Billing", "View billing information", "billing", "view"),
    "billing:payment": Permission("perm_bill_payment", "Manage Payments", "Process payments", "billing", "payment"),
}

AUDIT_PERMISSIONS = {
    "audit:view": Permission("perm_audit_view", "View Audit Logs", "Access audit logs", "audit", "view"),
    "audit:export": Permission("perm_audit_export", "Export Audit Logs", "Export audit data", "audit", "export"),
    "audit:configure": Permission("perm_audit_config", "Configure Audit", "Modify audit settings", "audit", "configure"),
}

API_PERMISSIONS = {
    "api:generate_token": Permission("perm_api_token", "Generate API Tokens", "Create API tokens", "api", "generate_token"),
    "api:manage_keys": Permission("perm_api_keys", "Manage API Keys", "Manage API keys", "api", "manage_keys"),
    "api:manage_scopes": Permission("perm_api_scopes", "Manage API Scopes", "Configure API scopes", "api", "manage_scopes"),
}

# Combine all permissions
ALL_PERMISSIONS = {
    **WORKFLOW_PERMISSIONS,
    **USER_PERMISSIONS,
    **TEAM_PERMISSIONS,
    **SETTINGS_PERMISSIONS,
    **BILLING_PERMISSIONS,
    **AUDIT_PERMISSIONS,
    **API_PERMISSIONS,
}


# Define system roles with their permissions
def create_super_admin_role() -> Role:
    """Super admin has all permissions"""
    role = Role(PredefinedRole.SUPER_ADMIN, "Super Admin", "Full system access", is_system_role=True)
    for perm in ALL_PERMISSIONS.values():
        role.add_permission(perm)
    return role


def create_tenant_admin_role() -> Role:
    """Tenant admin manages within tenant"""
    role = Role(PredefinedRole.TENANT_ADMIN, "Tenant Admin", "Full tenant access", is_system_role=True)
    perms_to_add = [
        *WORKFLOW_PERMISSIONS.values(),
        *USER_PERMISSIONS.values(),
        *TEAM_PERMISSIONS.values(),
        *SETTINGS_PERMISSIONS.values(),
        *BILLING_PERMISSIONS.values(),
        *AUDIT_PERMISSIONS.values(),
    ]
    for perm in perms_to_add:
        role.add_permission(perm)
    return role


def create_manager_role() -> Role:
    """Manager supervises workflows and team"""
    role = Role(PredefinedRole.MANAGER, "Manager", "Manage workflows and team", is_system_role=True)
    perms_to_add = [
        WORKFLOW_PERMISSIONS["workflow:create"],
        WORKFLOW_PERMISSIONS["workflow:read"],
        WORKFLOW_PERMISSIONS["workflow:update"],
        WORKFLOW_PERMISSIONS["workflow:execute"],
        WORKFLOW_PERMISSIONS["workflow:share"],
        USER_PERMISSIONS["user:invite"],
        TEAM_PERMISSIONS["team:create"],
        TEAM_PERMISSIONS["team:manage"],
        SETTINGS_PERMISSIONS["settings:view"],
        AUDIT_PERMISSIONS["audit:view"],
    ]
    for perm in perms_to_add:
        role.add_permission(perm)
    return role


def create_user_role() -> Role:
    """User can create and execute workflows"""
    role = Role(PredefinedRole.USER, "User", "Create and execute workflows", is_system_role=True)
    perms_to_add = [
        WORKFLOW_PERMISSIONS["workflow:create"],
        WORKFLOW_PERMISSIONS["workflow:read"],
        WORKFLOW_PERMISSIONS["workflow:update"],
        WORKFLOW_PERMISSIONS["workflow:execute"],
        SETTINGS_PERMISSIONS["settings:view"],
        API_PERMISSIONS["api:generate_token"],
    ]
    for perm in perms_to_add:
        role.add_permission(perm)
    return role


def create_viewer_role() -> Role:
    """Viewer has read-only access"""
    role = Role(PredefinedRole.VIEWER, "Viewer", "Read-only access", is_system_role=True)
    perms_to_add = [
        WORKFLOW_PERMISSIONS["workflow:read"],
        SETTINGS_PERMISSIONS["settings:view"],
        AUDIT_PERMISSIONS["audit:view"],
    ]
    for perm in perms_to_add:
        role.add_permission(perm)
    return role


def create_developer_role() -> Role:
    """Developer has full technical access"""
    role = Role(PredefinedRole.DEVELOPER, "Developer", "Full technical access", is_system_role=True)
    perms_to_add = [
        *WORKFLOW_PERMISSIONS.values(),
        SETTINGS_PERMISSIONS["settings:view"],
        API_PERMISSIONS["api:generate_token"],
        API_PERMISSIONS["api:manage_keys"],
        API_PERMISSIONS["api:manage_scopes"],
        AUDIT_PERMISSIONS["audit:view"],
    ]
    for perm in perms_to_add:
        role.add_permission(perm)
    return role


# Create all system roles
SYSTEM_ROLES = {
    PredefinedRole.SUPER_ADMIN: create_super_admin_role(),
    PredefinedRole.TENANT_ADMIN: create_tenant_admin_role(),
    PredefinedRole.MANAGER: create_manager_role(),
    PredefinedRole.USER: create_user_role(),
    PredefinedRole.VIEWER: create_viewer_role(),
    PredefinedRole.DEVELOPER: create_developer_role(),
}


class RoleHierarchy:
    """Define role hierarchy for elevation checks"""

    HIERARCHY = {
        PredefinedRole.SUPER_ADMIN: 6,
        PredefinedRole.TENANT_ADMIN: 5,
        PredefinedRole.MANAGER: 4,
        PredefinedRole.DEVELOPER: 3,
        PredefinedRole.USER: 2,
        PredefinedRole.VIEWER: 1,
    }

    @classmethod
    def can_elevate_to(cls, from_role: str, to_role: str) -> bool:
        """Check if from_role can be elevated to to_role"""
        from_level = cls.HIERARCHY.get(from_role, 0)
        to_level = cls.HIERARCHY.get(to_role, 0)
        return from_level >= to_level

    @classmethod
    def get_level(cls, role: str) -> int:
        """Get hierarchy level of role"""
        return cls.HIERARCHY.get(role, 0)
