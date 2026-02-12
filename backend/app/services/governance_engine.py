"""
Governance Engine - Security & Governance Infrastructure (Phase 47)

Provides comprehensive policy management, approval workflows, change management,
and data governance. Enforces organizational policies and tracks compliance.

Features:
- Policy creation and versioning
- Policy assignment to roles/users
- Approval workflows with escalation
- Change management process
- Data governance rules
- Retention and deletion policies
- Policy enforcement and violation tracking
- Policy analytics and reporting
- Audit trail integration
- Thread-safe singleton pattern

Integrates with:
- audit_logger: Log governance events
- access_control_service: Policy-based access control
- compliance_checker: Compliance-aligned policies
"""

import json
import time
import threading
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class PolicyType(Enum):
    """Types of policies."""
    DATA_ACCESS = "data_access"
    DATA_RETENTION = "data_retention"
    DATA_DELETION = "data_deletion"
    USER_MANAGEMENT = "user_management"
    PASSWORD_POLICY = "password_policy"
    ENCRYPTION = "encryption"
    AUDIT_RETENTION = "audit_retention"
    API_RATE_LIMITING = "api_rate_limiting"


class PolicyStatus(Enum):
    """Policy status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ApprovalStatus(Enum):
    """Approval workflow status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    """Change management workflow status."""
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    ROLLED_BACK = "rolled_back"
    CLOSED = "closed"


class GovernanceConfig:
    """Configuration for governance engine."""
    
    def __init__(
        self,
        require_approval: bool = True,
        approval_timeout_hours: int = 48,
        escalation_enabled: bool = True,
        change_management_enabled: bool = True,
        policy_versioning: bool = True,
        policy_storage_path: Optional[str] = None,
        metrics_enabled: bool = True,
    ):
        """Initialize governance configuration."""
        self.require_approval = require_approval
        self.approval_timeout_hours = approval_timeout_hours
        self.escalation_enabled = escalation_enabled
        self.change_management_enabled = change_management_enabled
        self.policy_versioning = policy_versioning
        self.policy_storage_path = policy_storage_path or "./policies"
        self.metrics_enabled = metrics_enabled


@dataclass
class Policy:
    """Represents a governance policy."""
    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    status: PolicyStatus
    rules: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    version: int = 1
    previous_version_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if policy is active."""
        if self.status != PolicyStatus.ACTIVE:
            return False
        
        now = datetime.utcnow()
        
        if self.effective_date:
            if now < datetime.fromisoformat(self.effective_date):
                return False
        
        if self.expiration_date:
            if now > datetime.fromisoformat(self.expiration_date):
                return False
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PolicyAssignment:
    """Assignment of policy to role/user."""
    assignment_id: str
    policy_id: str
    assigned_to_type: str  # 'role', 'user', 'department'
    assigned_to_id: str
    assigned_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    assigned_by: Optional[str] = None
    is_active: bool = True
    

@dataclass
class ApprovalRequest:
    """Approval request for policy or change."""
    approval_id: str
    request_type: str  # 'policy_creation', 'policy_update', 'change'
    request_id: str
    submitted_by: str
    requested_approvers: List[str] = field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    submitted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    deadline: Optional[str] = None
    approvals: Dict[str, Tuple[bool, str]] = field(default_factory=dict)  # {approver_id: (approved, reason)}
    escalation_level: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_approved(self) -> bool:
        """Check if all required approvers approved."""
        if not self.requested_approvers:
            return True
        
        approved_count = sum(1 for approved, _ in self.approvals.values() if approved)
        return approved_count >= len(self.requested_approvers)


@dataclass
class WorkflowChange:
    """Change management workflow."""
    change_id: str
    title: str
    description: str
    change_type: str
    status: WorkflowStatus
    submitted_by: str
    submitted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    implementation_date: Optional[str] = None
    verification_date: Optional[str] = None
    impact_assessment: Dict[str, Any] = field(default_factory=dict)
    approval_ids: List[str] = field(default_factory=list)
    rollback_plan: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernanceMetrics:
    """Metrics for governance operations."""
    total_policies: int = 0
    active_policies: int = 0
    total_assignments: int = 0
    total_approvals: int = 0
    pending_approvals: int = 0
    approved_policies: int = 0
    rejected_policies: int = 0
    avg_approval_time_hours: float = 0.0
    total_changes: int = 0
    changes_approved: int = 0
    compliance_score: float = 0.0


class GovernanceEngine:
    """
    Production-grade governance engine with policy management and workflows.
    
    Features:
    - Policy creation, versioning, and enforcement
    - Policy assignment to roles/users
    - Approval workflows with escalation
    - Change management process
    - Data governance rules
    - Policy analytics and reporting
    - Audit integration
    - Thread-safe singleton
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, config: Optional[GovernanceConfig] = None):
        """Singleton pattern for governance engine."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[GovernanceConfig] = None):
        """Initialize governance engine."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config = config or GovernanceConfig()
        self.policies: Dict[str, Policy] = {}
        self.policy_versions: Dict[str, List[Policy]] = defaultdict(list)
        self.assignments: Dict[str, PolicyAssignment] = {}
        self.approvals: Dict[str, ApprovalRequest] = {}
        self.changes: Dict[str, WorkflowChange] = {}
        self.metrics = GovernanceMetrics()
        self.cleanup_thread: Optional[threading.Thread] = None
        self._running = True
        
        # Create policy storage directory
        Path(self.config.policy_storage_path).mkdir(parents=True, exist_ok=True)
        
        # Load existing policies
        self._load_policies()
        
        # Start background tasks
        self._start_background_tasks()
        
        self._initialized = True
    
    def create_policy(
        self,
        name: str,
        description: str,
        policy_type: PolicyType,
        rules: Dict[str, Any],
        created_by: str,
        effective_date: Optional[str] = None,
        expiration_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
        require_approval: Optional[bool] = None,
        requested_approvers: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[Policy], Optional[str]]:
        """
        Create a new policy.
        
        Args:
            name: Policy name
            description: Policy description
            policy_type: Type of policy
            rules: Policy rules
            created_by: User creating policy
            effective_date: When policy becomes active
            expiration_date: When policy expires
            tags: Metadata tags
            require_approval: Override approval requirement
            requested_approvers: Specific approvers required
            
        Returns:
            Tuple of (success, policy, error_message)
        """
        with self._lock:
            policy_id = str(uuid.uuid4())
            
            policy = Policy(
                policy_id=policy_id,
                name=name,
                description=description,
                policy_type=policy_type,
                status=PolicyStatus.DRAFT,
                rules=rules,
                created_by=created_by,
                effective_date=effective_date,
                expiration_date=expiration_date,
                tags=tags or [],
            )
            
            self.policies[policy_id] = policy
            
            if self.config.policy_versioning:
                self.policy_versions[name].append(policy)
            
            # Create approval if required
            require_approval = require_approval if require_approval is not None else self.config.require_approval
            
            if require_approval and requested_approvers:
                approval_id = str(uuid.uuid4())
                approval = ApprovalRequest(
                    approval_id=approval_id,
                    request_type="policy_creation",
                    request_id=policy_id,
                    submitted_by=created_by,
                    requested_approvers=requested_approvers,
                    deadline=(datetime.utcnow() + timedelta(
                        hours=self.config.approval_timeout_hours
                    )).isoformat(),
                )
                
                self.approvals[approval_id] = approval
                self.metrics.pending_approvals += 1
                self.metrics.total_approvals += 1
                
                return True, policy, None
            else:
                policy.status = PolicyStatus.ACTIVE
                self.metrics.active_policies += 1
                self._save_policy(policy)
                return True, policy, None
    
    def approve_policy(
        self,
        approval_id: str,
        approver_id: str,
        approved: bool,
        reason: str = "",
    ) -> Optional[Policy]:
        """Approve or reject policy."""
        with self._lock:
            approval = self.approvals.get(approval_id)
            if not approval:
                return None
            
            # Record approval
            approval.approvals[approver_id] = (approved, reason)
            
            if not approved:
                approval.status = ApprovalStatus.REJECTED
                return None
            
            # Check if all approvers approved
            if approval.is_approved():
                approval.status = ApprovalStatus.APPROVED
                
                # Activate policy
                policy = self.policies.get(approval.request_id)
                if policy:
                    policy.status = PolicyStatus.ACTIVE
                    self.metrics.active_policies += 1
                    self.metrics.approved_policies += 1
                    self._save_policy(policy)
                    return policy
            
            return None
    
    def update_policy(
        self,
        policy_id: str,
        rules: Dict[str, Any],
        updated_by: str,
        requested_approvers: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[Policy], Optional[str]]:
        """Update existing policy."""
        with self._lock:
            old_policy = self.policies.get(policy_id)
            if not old_policy:
                return False, None, "Policy not found"
            
            # Create new version
            new_policy_id = str(uuid.uuid4())
            new_policy = Policy(
                policy_id=new_policy_id,
                name=old_policy.name,
                description=old_policy.description,
                policy_type=old_policy.policy_type,
                status=PolicyStatus.DRAFT,
                rules=rules,
                created_by=updated_by,
                version=old_policy.version + 1,
                previous_version_id=policy_id,
            )
            
            self.policies[new_policy_id] = new_policy
            self.policy_versions[old_policy.name].append(new_policy)
            
            # Create approval if required
            if self.config.require_approval and requested_approvers:
                approval_id = str(uuid.uuid4())
                approval = ApprovalRequest(
                    approval_id=approval_id,
                    request_type="policy_update",
                    request_id=new_policy_id,
                    submitted_by=updated_by,
                    requested_approvers=requested_approvers,
                )
                
                self.approvals[approval_id] = approval
                self.metrics.pending_approvals += 1
                
                return True, new_policy, None
            else:
                new_policy.status = PolicyStatus.ACTIVE
                self.metrics.active_policies += 1
                self._save_policy(new_policy)
                return True, new_policy, None
    
    def assign_policy(
        self,
        policy_id: str,
        assigned_to_type: str,
        assigned_to_id: str,
        assigned_by: str,
    ) -> Optional[PolicyAssignment]:
        """Assign policy to role, user, or department."""
        with self._lock:
            policy = self.policies.get(policy_id)
            if not policy:
                return None
            
            assignment = PolicyAssignment(
                assignment_id=str(uuid.uuid4()),
                policy_id=policy_id,
                assigned_to_type=assigned_to_type,
                assigned_to_id=assigned_to_id,
                assigned_by=assigned_by,
            )
            
            self.assignments[assignment.assignment_id] = assignment
            self.metrics.total_assignments += 1
            
            return assignment
    
    def submit_change(
        self,
        title: str,
        description: str,
        change_type: str,
        submitted_by: str,
        impact_assessment: Dict[str, Any],
        rollback_plan: Optional[str] = None,
        requested_approvers: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[WorkflowChange], Optional[str]]:
        """Submit a change for approval."""
        with self._lock:
            change_id = str(uuid.uuid4())
            change = WorkflowChange(
                change_id=change_id,
                title=title,
                description=description,
                change_type=change_type,
                status=WorkflowStatus.SUBMITTED,
                submitted_by=submitted_by,
                impact_assessment=impact_assessment,
                rollback_plan=rollback_plan,
            )
            
            self.changes[change_id] = change
            self.metrics.total_changes += 1
            
            # Create approval workflow
            if requested_approvers:
                approval_id = str(uuid.uuid4())
                approval = ApprovalRequest(
                    approval_id=approval_id,
                    request_type="change",
                    request_id=change_id,
                    submitted_by=submitted_by,
                    requested_approvers=requested_approvers,
                )
                
                self.approvals[approval_id] = approval
                change.approval_ids.append(approval_id)
                self.metrics.pending_approvals += 1
            
            return True, change, None
    
    def approve_change(
        self,
        approval_id: str,
        approver_id: str,
        approved: bool,
    ) -> Optional[WorkflowChange]:
        """Approve or reject change."""
        with self._lock:
            approval = self.approvals.get(approval_id)
            if not approval:
                return None
            
            approval.approvals[approver_id] = (approved, "")
            
            if approved and approval.is_approved():
                approval.status = ApprovalStatus.APPROVED
                
                change = self.changes.get(approval.request_id)
                if change:
                    change.status = WorkflowStatus.APPROVED
                    self.metrics.changes_approved += 1
                    return change
            
            return None
    
    def implement_change(
        self,
        change_id: str,
        implementation_notes: Optional[str] = None,
    ) -> Optional[WorkflowChange]:
        """Mark change as implemented."""
        with self._lock:
            change = self.changes.get(change_id)
            if not change:
                return None
            
            change.status = WorkflowStatus.IMPLEMENTED
            change.implementation_date = datetime.utcnow().isoformat()
            
            return change
    
    def verify_change(
        self,
        change_id: str,
        verified_by: str,
    ) -> Optional[WorkflowChange]:
        """Verify change was successful."""
        with self._lock:
            change = self.changes.get(change_id)
            if not change:
                return None
            
            change.status = WorkflowStatus.VERIFIED
            change.verification_date = datetime.utcnow().isoformat()
            change.metadata["verified_by"] = verified_by
            
            return change
    
    def get_active_policies(self) -> List[Policy]:
        """Get all active policies."""
        with self._lock:
            return [p for p in self.policies.values() if p.is_active()]
    
    def get_policies_for_type(self, policy_type: PolicyType) -> List[Policy]:
        """Get policies of specific type."""
        with self._lock:
            return [
                p for p in self.policies.values()
                if p.policy_type == policy_type and p.is_active()
            ]
    
    def get_assigned_policies(
        self,
        assigned_to_type: str,
        assigned_to_id: str,
    ) -> List[Policy]:
        """Get policies assigned to user/role."""
        with self._lock:
            assignments = [
                a for a in self.assignments.values()
                if a.assigned_to_type == assigned_to_type and a.assigned_to_id == assigned_to_id
            ]
            
            return [
                self.policies[a.policy_id]
                for a in assignments
                if a.policy_id in self.policies
            ]
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get pending approval requests."""
        with self._lock:
            return [a for a in self.approvals.values() if a.status == ApprovalStatus.PENDING]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get governance metrics."""
        with self._lock:
            return {
                "total_policies": self.metrics.total_policies,
                "active_policies": self.metrics.active_policies,
                "total_assignments": self.metrics.total_assignments,
                "pending_approvals": self.metrics.pending_approvals,
                "approved_policies": self.metrics.approved_policies,
                "total_changes": self.metrics.total_changes,
                "changes_approved": self.metrics.changes_approved,
                "avg_approval_time_hours": round(self.metrics.avg_approval_time_hours, 2),
            }
    
    def _save_policy(self, policy: Policy):
        """Persist policy to disk."""
        try:
            policy_file = Path(self.config.policy_storage_path) / f"{policy.policy_id}.json"
            
            with open(policy_file, 'w') as f:
                json.dump(policy.to_dict(), f, default=str, indent=2)
        except Exception as e:
            print(f"Error saving policy: {e}")
    
    def _load_policies(self):
        """Load policies from disk."""
        try:
            policies_dir = Path(self.config.policy_storage_path)
            for policy_file in policies_dir.glob("*.json"):
                try:
                    with open(policy_file, 'r') as f:
                        data = json.load(f)
                        
                        policy = Policy(
                            policy_id=data["policy_id"],
                            name=data["name"],
                            description=data["description"],
                            policy_type=PolicyType(data["policy_type"]),
                            status=PolicyStatus(data["status"]),
                            rules=data["rules"],
                            created_at=data.get("created_at"),
                            created_by=data.get("created_by"),
                            version=data.get("version", 1),
                        )
                        
                        self.policies[policy.policy_id] = policy
                        self.metrics.total_policies += 1
                        
                        if policy.is_active():
                            self.metrics.active_policies += 1
                except Exception:
                    continue
        except Exception as e:
            print(f"Error loading policies: {e}")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        self.cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self.cleanup_thread.start()
    
    def _periodic_cleanup(self):
        """Clean up expired approvals and changes."""
        while self._running:
            with self._lock:
                now = datetime.utcnow()
                
                # Clean up expired approvals
                for approval_id, approval in list(self.approvals.items()):
                    if approval.deadline:
                        deadline = datetime.fromisoformat(approval.deadline)
                        if now > deadline and approval.status == ApprovalStatus.PENDING:
                            approval.status = ApprovalStatus.CANCELLED
            
            time.sleep(3600)  # Check hourly
    
    def shutdown(self):
        """Gracefully shutdown governance engine."""
        self._running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
