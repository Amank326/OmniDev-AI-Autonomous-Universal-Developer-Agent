"""
Phase 56: Role-Based Access Control (RBAC)
Comprehensive RBAC system with roles, permissions, access policies,
and resource-based access control.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime
from enum import Enum


class AccessDecision(Enum):
    """Access control decision."""
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"


class PolicyEffect(Enum):
    """Policy effect."""
    ALLOW = "allow"
    DENY = "deny"


class ResourceType(Enum):
    """Types of resources in the system."""
    DOCUMENT = "document"
    ENDPOINT = "endpoint"
    DATASET = "dataset"
    SERVICE = "service"
    REPORT = "report"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    API_KEY = "api_key"


@dataclass
class Permission:
    """Permission definition."""
    permission_id: str
    name: str
    description: str = ""
    resource_type: Optional[ResourceType] = None
    action: Optional[str] = None  # create, read, update, delete, etc.
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, resource_type: str, action: str) -> bool:
        """Check if permission matches resource and action."""
        if self.resource_type and str(self.resource_type.value) != resource_type:
            return False
        if self.action and self.action != action:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'permission_id': self.permission_id,
            'name': self.name,
            'description': self.description,
            'resource_type': self.resource_type.value if self.resource_type else None,
            'action': self.action
        }


@dataclass
class Role:
    """Role definition."""
    role_id: str
    name: str
    description: str = ""
    permissions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    parent_roles: Set[str] = field(default_factory=set)  # Role inheritance
    is_system_role: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission_id: str) -> bool:
        """Check if role has permission."""
        return permission_id in self.permissions

    def add_permission(self, permission_id: str) -> 'Role':
        """Add permission to role."""
        self.permissions.add(permission_id)
        return self

    def remove_permission(self, permission_id: str) -> 'Role':
        """Remove permission from role."""
        self.permissions.discard(permission_id)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'role_id': self.role_id,
            'name': self.name,
            'description': self.description,
            'permissions': list(self.permissions),
            'created_at': self.created_at.isoformat(),
            'is_system_role': self.is_system_role
        }


@dataclass
class Subject:
    """Subject (user/service) with roles."""
    subject_id: str
    subject_type: str  # user, service, client, etc.
    roles: Set[str] = field(default_factory=set)
    direct_permissions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_role(self, role_id: str) -> bool:
        """Check if subject has role."""
        return role_id in self.roles

    def add_role(self, role_id: str) -> 'Subject':
        """Add role to subject."""
        self.roles.add(role_id)
        return self

    def remove_role(self, role_id: str) -> 'Subject':
        """Remove role from subject."""
        self.roles.discard(role_id)
        return self

    def add_direct_permission(self, permission_id: str) -> 'Subject':
        """Add direct permission to subject (not through role)."""
        self.direct_permissions.add(permission_id)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'subject_id': self.subject_id,
            'subject_type': self.subject_type,
            'roles': list(self.roles),
            'direct_permissions': list(self.direct_permissions),
            'created_at': self.created_at.isoformat()
        }


@dataclass
class PolicyRule:
    """Policy rule for access control."""
    rule_id: str
    effect: PolicyEffect
    subjects: Set[str] = field(default_factory=set)  # subject IDs or roles
    actions: Set[str] = field(default_factory=set)  # create, read, update, delete
    resources: Set[str] = field(default_factory=set)  # resource patterns
    conditions: Dict[str, Any] = field(default_factory=dict)  # contextual conditions
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 0  # Higher priority rules evaluated first

    def matches(
        self,
        subject_id: str,
        role_ids: List[str],
        action: str,
        resource: str
    ) -> bool:
        """Check if rule matches the access request."""
        # Check subjects
        subject_match = False
        if subject_id in self.subjects:
            subject_match = True
        elif any(role in self.subjects for role in role_ids):
            subject_match = True

        if not subject_match:
            return False

        # Check action
        if self.actions and action not in self.actions:
            return False

        # Check resource (simple wildcard support)
        if self.resources:
            resource_match = False
            for resource_pattern in self.resources:
                if self._pattern_matches(resource, resource_pattern):
                    resource_match = True
                    break
            if not resource_match:
                return False

        return True

    @staticmethod
    def _pattern_matches(resource: str, pattern: str) -> bool:
        """Simple pattern matching for resources."""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return resource.startswith(pattern[:-1])
        return resource == pattern

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_id': self.rule_id,
            'effect': self.effect.value,
            'subjects': list(self.subjects),
            'actions': list(self.actions),
            'resources': list(self.resources),
            'priority': self.priority
        }


@dataclass
class AccessRequest:
    """Request to evaluate access."""
    subject_id: str
    action: str
    resource: str
    resource_type: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'subject_id': self.subject_id,
            'action': self.action,
            'resource': self.resource,
            'resource_type': self.resource_type,
            'context': self.context
        }


@dataclass
class AccessDecisionRecord:
    """Record of access control decision."""
    decision_id: str
    request: AccessRequest
    decision: AccessDecision
    allowed: bool
    reason: str
    matched_rules: List[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'decision_id': self.decision_id,
            'request': self.request.to_dict(),
            'decision': self.decision.value,
            'allowed': self.allowed,
            'reason': self.reason,
            'matched_rules': self.matched_rules,
            'evaluated_at': self.evaluated_at.isoformat()
        }


class RBACEngine:
    """Role-Based Access Control engine."""

    def __init__(self):
        """Initialize RBAC engine."""
        self.permissions: Dict[str, Permission] = {}
        self.roles: Dict[str, Role] = {}
        self.subjects: Dict[str, Subject] = {}
        self.policies: List[PolicyRule] = []
        self.decisions: List[AccessDecisionRecord] = []
        self._init_default_roles()

    def _init_default_roles(self) -> None:
        """Initialize default system roles."""
        # Admin role
        admin = Role(
            role_id="admin",
            name="Administrator",
            description="Full system access",
            is_system_role=True
        )
        self.roles["admin"] = admin

        # User role
        user = Role(
            role_id="user",
            name="User",
            description="Basic user access",
            is_system_role=True
        )
        self.roles["user"] = user

        # Guest role
        guest = Role(
            role_id="guest",
            name="Guest",
            description="Limited guest access",
            is_system_role=True
        )
        self.roles["guest"] = guest

    # ===================== PERMISSION MANAGEMENT =====================

    def register_permission(
        self,
        permission_id: str,
        name: str,
        description: str = "",
        resource_type: Optional[ResourceType] = None,
        action: Optional[str] = None
    ) -> Permission:
        """Register a new permission."""
        permission = Permission(
            permission_id=permission_id,
            name=name,
            description=description,
            resource_type=resource_type,
            action=action
        )
        self.permissions[permission_id] = permission
        return permission

    def get_permission(self, permission_id: str) -> Optional[Permission]:
        """Get permission."""
        return self.permissions.get(permission_id)

    def get_permissions_for_resource(
        self,
        resource_type: str,
        action: Optional[str] = None
    ) -> List[Permission]:
        """Get permissions for resource type."""
        perms = []
        for perm in self.permissions.values():
            if perm.resource_type and perm.resource_type.value == resource_type:
                if action is None or perm.action == action:
                    perms.append(perm)
        return perms

    # ===================== ROLE MANAGEMENT =====================

    def create_role(
        self,
        role_id: str,
        name: str,
        description: str = "",
        permissions: List[str] = None
    ) -> Role:
        """Create new role."""
        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            permissions=set(permissions or [])
        )
        self.roles[role_id] = role
        return role

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role."""
        return self.roles.get(role_id)

    def grant_permission_to_role(
        self,
        role_id: str,
        permission_id: str
    ) -> bool:
        """Grant permission to role."""
        role = self.get_role(role_id)
        if not role:
            return False
        role.add_permission(permission_id)
        return True

    def revoke_permission_from_role(
        self,
        role_id: str,
        permission_id: str
    ) -> bool:
        """Revoke permission from role."""
        role = self.get_role(role_id)
        if not role:
            return False
        role.remove_permission(permission_id)
        return True

    # ===================== SUBJECT MANAGEMENT =====================

    def register_subject(
        self,
        subject_id: str,
        subject_type: str,
        roles: List[str] = None
    ) -> Subject:
        """Register subject (user/service)."""
        subject = Subject(
            subject_id=subject_id,
            subject_type=subject_type,
            roles=set(roles or [])
        )
        self.subjects[subject_id] = subject
        return subject

    def get_subject(self, subject_id: str) -> Optional[Subject]:
        """Get subject."""
        return self.subjects.get(subject_id)

    def assign_role_to_subject(
        self,
        subject_id: str,
        role_id: str
    ) -> bool:
        """Assign role to subject."""
        subject = self.get_subject(subject_id)
        if not subject:
            return False
        subject.add_role(role_id)
        return True

    def revoke_role_from_subject(
        self,
        subject_id: str,
        role_id: str
    ) -> bool:
        """Revoke role from subject."""
        subject = self.get_subject(subject_id)
        if not subject:
            return False
        subject.remove_role(role_id)
        return True

    def grant_permission_to_subject(
        self,
        subject_id: str,
        permission_id: str
    ) -> bool:
        """Grant direct permission to subject."""
        subject = self.get_subject(subject_id)
        if not subject:
            return False
        subject.add_direct_permission(permission_id)
        return True

    # ===================== POLICY MANAGEMENT =====================

    def add_policy(self, rule: PolicyRule) -> 'RBACEngine':
        """Add access policy rule."""
        self.policies.append(rule)
        # Sort by priority (higher first)
        self.policies.sort(key=lambda r: r.priority, reverse=True)
        return self

    def remove_policy(self, rule_id: str) -> bool:
        """Remove policy rule."""
        self.policies = [r for r in self.policies if r.rule_id != rule_id]
        return True

    # ===================== ACCESS EVALUATION =====================

    def evaluate_access(
        self,
        subject_id: str,
        action: str,
        resource: str,
        resource_type: str,
        context: Dict[str, Any] = None
    ) -> Tuple[bool, str]:
        """Evaluate if subject can perform action on resource."""
        request = AccessRequest(
            subject_id=subject_id,
            action=action,
            resource=resource,
            resource_type=resource_type,
            context=context or {}
        )

        subject = self.get_subject(subject_id)
        if not subject:
            decision = AccessDecision.DENY
            reason = "Subject not found"
            allowed = False
        else:
            allowed, decision, reason = self._evaluate_request(subject, request)

        # Record decision
        self._record_decision(request, decision, allowed, reason)

        return allowed, reason

    def _evaluate_request(
        self,
        subject: Subject,
        request: AccessRequest
    ) -> Tuple[bool, AccessDecision, str]:
        """Internal access evaluation logic."""
        # Check admin role (always allow)
        if "admin" in subject.roles:
            return True, AccessDecision.ALLOW, "Subject has admin role"

        # Collect all permissions from roles and direct permissions
        all_permissions = set(subject.direct_permissions)
        
        for role_id in subject.roles:
            role = self.get_role(role_id)
            if role:
                all_permissions.update(role.permissions)

        # Check direct permissions
        for permission_id in all_permissions:
            perm = self.get_permission(permission_id)
            if perm and perm.matches(request.resource_type, request.action):
                return True, AccessDecision.ALLOW, f"Permission granted: {permission_id}"

        # Evaluate policies
        matching_rules = []
        for rule in self.policies:
            if rule.matches(subject.subject_id, list(subject.roles), 
                           request.action, request.resource):
                matching_rules.append(rule.rule_id)
                
                if rule.effect == PolicyEffect.ALLOW:
                    return True, AccessDecision.ALLOW, f"Policy allows: {rule.rule_id}"
                elif rule.effect == PolicyEffect.DENY:
                    return False, AccessDecision.DENY, f"Policy denies: {rule.rule_id}"

        # Default deny
        return False, AccessDecision.DENY, "No matching permissions or policies"

    def _record_decision(
        self,
        request: AccessRequest,
        decision: AccessDecision,
        allowed: bool,
        reason: str
    ) -> None:
        """Record access decision."""
        from secrets import token_urlsafe
        decision_id = f"decision_{token_urlsafe(12)}"
        
        record = AccessDecisionRecord(
            decision_id=decision_id,
            request=request,
            decision=decision,
            allowed=allowed,
            reason=reason
        )
        self.decisions.append(record)

    # ===================== AUDIT & REPORTING =====================

    def get_decisions(
        self,
        subject_id: Optional[str] = None,
        allowed: Optional[bool] = None,
        hours: int = 24
    ) -> List[AccessDecisionRecord]:
        """Get access decisions."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        
        decisions = [d for d in self.decisions if d.evaluated_at >= cutoff]
        
        if subject_id:
            decisions = [d for d in decisions if d.request.subject_id == subject_id]
        
        if allowed is not None:
            decisions = [d for d in decisions if d.allowed == allowed]

        return decisions

    def get_subject_permissions(self, subject_id: str) -> List[str]:
        """Get all permissions for a subject (through roles and direct)."""
        subject = self.get_subject(subject_id)
        if not subject:
            return []

        permissions = set(subject.direct_permissions)
        
        for role_id in subject.roles:
            role = self.get_role(role_id)
            if role:
                permissions.update(role.permissions)

        return list(permissions)

    def get_statistics(self) -> Dict[str, Any]:
        """Get RBAC statistics."""
        allowed_decisions = sum(1 for d in self.decisions if d.allowed)
        denied_decisions = sum(1 for d in self.decisions if not d.allowed)
        
        return {
            'total_permissions': len(self.permissions),
            'total_roles': len(self.roles),
            'total_subjects': len(self.subjects),
            'total_policies': len(self.policies),
            'total_decisions': len(self.decisions),
            'allowed_decisions': allowed_decisions,
            'denied_decisions': denied_decisions,
            'denial_rate': round(denied_decisions / (allowed_decisions + denied_decisions) * 100, 2) 
                          if (allowed_decisions + denied_decisions) > 0 else 0
        }


# Singleton instance
_rbac_engine: Optional[RBACEngine] = None


def get_rbac_engine() -> RBACEngine:
    """Get RBAC engine singleton."""
    global _rbac_engine
    if _rbac_engine is None:
        _rbac_engine = RBACEngine()
    return _rbac_engine


def reset_rbac_engine() -> None:
    """Reset RBAC engine (for testing)."""
    global _rbac_engine
    _rbac_engine = None
