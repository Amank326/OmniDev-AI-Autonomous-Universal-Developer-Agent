"""
Phase 12: RBAC Service
Role-based access control enforcement and management
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from .rbac_models import (
    Role, Permission, UserRole, ResourceAccess, PredefinedRole,
    SYSTEM_ROLES, RoleHierarchy, ALL_PERMISSIONS
)

logger = logging.getLogger(__name__)


class RBACService:
    """
    Central RBAC service for access control management and enforcement
    """

    def __init__(self):
        self.user_roles: Dict[str, List[UserRole]] = {}  # user_id -> [UserRole]
        self.custom_roles: Dict[str, Role] = {}  # role_id -> Role
        self.resource_access: Dict[str, List[ResourceAccess]] = {}  # user_id -> [ResourceAccess]
        self.permission_cache: Dict[Tuple[str, str], bool] = {}  # (user_id, perm) -> bool

    def assign_role_to_user(self, user_id: str, role: str, 
                           tenant_id: str = None, assigned_by: str = None) -> bool:
        """
        Assign a role to a user
        Returns True if successful
        """
        logger.info(f"Assigning role {role} to user {user_id} (tenant={tenant_id})")

        # Get role object
        role_obj = self._get_role_object(role)
        if not role_obj:
            logger.error(f"Role not found: {role}")
            return False

        # Create user role assignment
        user_role = UserRole(user_id, role_obj, tenant_id)
        user_role.assigned_by = assigned_by

        if user_id not in self.user_roles:
            self.user_roles[user_id] = []

        self.user_roles[user_id].append(user_role)

        # Clear cache for this user
        self._clear_user_cache(user_id)

        return True

    def revoke_role_from_user(self, user_id: str, role: str, 
                             tenant_id: str = None) -> bool:
        """
        Revoke a role from a user
        Returns True if successful
        """
        logger.info(f"Revoking role {role} from user {user_id}")

        if user_id not in self.user_roles:
            return False

        # Remove matching role
        original_count = len(self.user_roles[user_id])
        self.user_roles[user_id] = [
            ur for ur in self.user_roles[user_id]
            if not (ur.role.name == role or ur.role.id == role) or 
               (tenant_id and ur.tenant_id != tenant_id)
        ]

        if len(self.user_roles[user_id]) < original_count:
            self._clear_user_cache(user_id)
            return True

        return False

    def _get_role_object(self, role: str) -> Optional[Role]:
        """Get role object by name or ID"""
        # Check system roles
        for system_role in SYSTEM_ROLES.values():
            if system_role.id == role or system_role.name == role:
                return system_role

        # Check custom roles
        return self.custom_roles.get(role)

    def has_permission(self, user_id: str, permission: str, 
                      tenant_id: str = None) -> bool:
        """
        Check if user has a specific permission
        Returns True if user has permission
        """
        # Check cache
        cache_key = (user_id, permission, tenant_id)
        if cache_key in self.permission_cache:
            return self.permission_cache[cache_key]

        # Get user's roles
        roles = self._get_user_roles(user_id, tenant_id)

        # Check if any role has the permission
        perm_obj = self._get_permission_object(permission)
        if not perm_obj:
            logger.warning(f"Permission not found: {permission}")
            return False

        has_perm = any(role.has_permission(perm_obj) for role in roles)

        # Cache result
        self.permission_cache[cache_key] = has_perm
        return has_perm

    def has_any_permission(self, user_id: str, permissions: List[str],
                          tenant_id: str = None) -> bool:
        """
        Check if user has ANY of the specified permissions (OR)
        """
        return any(
            self.has_permission(user_id, perm, tenant_id)
            for perm in permissions
        )

    def has_all_permissions(self, user_id: str, permissions: List[str],
                           tenant_id: str = None) -> bool:
        """
        Check if user has ALL specified permissions (AND)
        """
        return all(
            self.has_permission(user_id, perm, tenant_id)
            for perm in permissions
        )

    def get_user_permissions(self, user_id: str, 
                            tenant_id: str = None) -> Set[str]:
        """
        Get all permissions for a user
        Returns set of permission IDs
        """
        roles = self._get_user_roles(user_id, tenant_id)
        permissions = set()

        for role in roles:
            for perm in role.get_all_permissions():
                permissions.add(perm.id)
                permissions.add(f"{perm.resource}:{perm.action}")

        return permissions

    def get_user_roles(self, user_id: str, 
                      tenant_id: str = None) -> List[str]:
        """
        Get role names for a user
        """
        roles = self._get_user_roles(user_id, tenant_id)
        return [role.name for role in roles]

    def _get_user_roles(self, user_id: str, tenant_id: str = None) -> List[Role]:
        """Internal: Get role objects for user"""
        if user_id not in self.user_roles:
            return []

        user_role_objs = self.user_roles[user_id]

        # Filter by tenant if specified
        if tenant_id:
            user_role_objs = [
                ur for ur in user_role_objs
                if ur.tenant_id is None or ur.tenant_id == tenant_id
            ]

        return [ur.role for ur in user_role_objs]

    def _get_permission_object(self, permission: str) -> Optional[Permission]:
        """Internal: Get permission object by name or ID"""
        # Check all defined permissions
        for perm in ALL_PERMISSIONS.values():
            if perm.id == permission or perm.name == permission:
                return perm

            # Also match resource:action format
            if f"{perm.resource}:{perm.action}" == permission:
                return perm

        return None

    def create_custom_role(self, name: str, description: str,
                          permissions: List[str]) -> Optional[Role]:
        """
        Create a custom role
        Returns role object or None if failed
        """
        logger.info(f"Creating custom role: {name}")

        # Prevent duplicate system role names
        if any(name == role.name for role in SYSTEM_ROLES.values()):
            logger.error(f"Cannot create custom role with system role name: {name}")
            return None

        role_id = f"role_{name.lower().replace(' ', '_')}"
        role = Role(role_id, name, description, is_system_role=False)

        # Add specified permissions
        for perm_id in permissions:
            perm = self._get_permission_object(perm_id)
            if perm:
                role.add_permission(perm)

        self.custom_roles[role_id] = role
        logger.info(f"Custom role created: {role_id}")

        return role

    def delete_custom_role(self, role_id: str) -> bool:
        """
        Delete a custom role
        Cannot delete system roles
        """
        if role_id in SYSTEM_ROLES:
            logger.error(f"Cannot delete system role: {role_id}")
            return False

        if role_id in self.custom_roles:
            del self.custom_roles[role_id]
            logger.info(f"Custom role deleted: {role_id}")

            # Clear cache for affected users
            for user_id in list(self.user_roles.keys()):
                self.user_roles[user_id] = [
                    ur for ur in self.user_roles[user_id]
                    if ur.role.id != role_id
                ]
                self._clear_user_cache(user_id)

            return True

        return False

    def grant_resource_access(self, user_id: str, resource_id: str,
                             resource_type: str, access_level: str = "read",
                             granted_by: str = None) -> bool:
        """
        Grant user access to a specific resource
        """
        logger.info(f"Granting {access_level} access on {resource_type}/{resource_id} to {user_id}")

        if user_id not in self.resource_access:
            self.resource_access[user_id] = []

        # Check for existing access
        for ra in self.resource_access[user_id]:
            if ra.resource_id == resource_id and ra.resource_type == resource_type:
                ra.access_level = access_level  # Update
                return True

        # Create new access
        ra = ResourceAccess(user_id, resource_id, resource_type, access_level)
        ra.granted_by = granted_by
        self.resource_access[user_id].append(ra)

        self._clear_user_cache(user_id)
        return True

    def revoke_resource_access(self, user_id: str, resource_id: str,
                              resource_type: str) -> bool:
        """
        Revoke user access to a specific resource
        """
        logger.info(f"Revoking access on {resource_type}/{resource_id} from {user_id}")

        if user_id not in self.resource_access:
            return False

        original_count = len(self.resource_access[user_id])
        self.resource_access[user_id] = [
            ra for ra in self.resource_access[user_id]
            if not (ra.resource_id == resource_id and ra.resource_type == resource_type)
        ]

        if len(self.resource_access[user_id]) < original_count:
            self._clear_user_cache(user_id)
            return True

        return False

    def can_access_resource(self, user_id: str, resource_id: str,
                           resource_type: str, required_level: str = "read") -> bool:
        """
        Check if user can access a resource at specified level
        """
        if user_id not in self.resource_access:
            return False

        access_levels = {"read": 1, "write": 2, "admin": 3}
        required_score = access_levels.get(required_level, 0)

        for ra in self.resource_access[user_id]:
            if ra.resource_id == resource_id and ra.resource_type == resource_type:
                current_score = access_levels.get(ra.access_level, 0)
                return current_score >= required_score

        return False

    def bulk_assign_role(self, user_ids: List[str], role: str,
                        tenant_id: str = None, assigned_by: str = None) -> Tuple[int, int]:
        """
        Assign role to multiple users
        Returns (successful, failed) count
        """
        successful = 0
        failed = 0

        for user_id in user_ids:
            if self.assign_role_to_user(user_id, role, tenant_id, assigned_by):
                successful += 1
            else:
                failed += 1

        logger.info(f"Bulk role assignment: {successful} successful, {failed} failed")
        return successful, failed

    def can_elevate_to_role(self, from_user_id: str, to_role: str) -> bool:
        """
        Check if user can be elevated to another role
        Considers role hierarchy
        """
        user_roles = self.get_user_roles(from_user_id)
        if not user_roles:
            return False

        # Get max hierarchy level of user's current roles
        user_level = max(
            RoleHierarchy.get_level(role)
            for role in user_roles
        )

        # Get level of target role
        target_level = RoleHierarchy.get_level(to_role)

        return user_level >= target_level

    def _clear_user_cache(self, user_id: str) -> None:
        """Clear permission cache for a user"""
        keys_to_delete = [
            key for key in self.permission_cache.keys()
            if key[0] == user_id
        ]
        for key in keys_to_delete:
            del self.permission_cache[key]

    def clear_all_cache(self) -> None:
        """Clear all permission cache"""
        self.permission_cache.clear()
        logger.info("RBAC cache cleared")

    def get_role_details(self, role_id: str) -> Optional[Dict]:
        """Get detailed information about a role"""
        role = self._get_role_object(role_id)
        if not role:
            return None

        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "permissions": [
                {
                    "id": p.id,
                    "name": p.name,
                    "resource": p.resource,
                    "action": p.action,
                }
                for p in role.get_all_permissions()
            ],
            "permission_count": len(role.get_all_permissions()),
        }

    def get_all_roles(self) -> List[Dict]:
        """Get all available roles"""
        roles = []

        # System roles
        for role in SYSTEM_ROLES.values():
            roles.append(self.get_role_details(role.id))

        # Custom roles
        for role in self.custom_roles.values():
            roles.append(self.get_role_details(role.id))

        return roles
