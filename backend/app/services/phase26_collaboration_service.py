"""
Phase 26: Collaboration Service
Real-time presence, workspace management, activity tracking
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import uuid

# ========================================================================
# ENUMS
# ========================================================================

class WorkspaceRole(Enum):
    """Workspace user roles"""
    ADMIN = "admin"           # Full access
    ANALYST = "analyst"       # Can create/edit metrics
    VIEWER = "viewer"         # Read-only access
    GUEST = "guest"          # Limited guest access

class PresenceStatus(Enum):
    """User presence status"""
    ACTIVE = "active"
    IDLE = "idle"
    AWAY = "away"
    OFFLINE = "offline"


# ========================================================================
# DATACLASSES
# ========================================================================

@dataclass
class WorkspaceMember:
    """Workspace member with role and permissions"""
    user_id: str
    workspace_id: str
    role: WorkspaceRole
    joined_date: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
@dataclass
class Workspace:
    """Collaborative workspace"""
    workspace_id: str
    name: str
    description: str
    owner_id: str
    created_date: datetime
    updated_date: datetime
    members: Dict[str, WorkspaceMember] = field(default_factory=dict)
    is_public: bool = False
    default_metrics: List[str] = field(default_factory=list)
    
@dataclass
class PresenceInfo:
    """User presence information"""
    user_id: str
    workspace_id: str
    status: PresenceStatus
    last_activity: datetime
    current_view: Optional[str] = None  # metric_id, dashboard_id, etc
    cursor_position: Optional[Dict] = None

@dataclass
class Activity:
    """User activity log entry"""
    activity_id: str
    user_id: str
    workspace_id: str
    action: str  # created_metric, shared_insight, viewed_dashboard, etc
    resource_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)


# ========================================================================
# COLLABORATION SERVICE
# ========================================================================

class CollaborationService:
    """Manages real-time collaboration, presence, and workspace sharing"""
    
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.presence_info: Dict[str, PresenceInfo] = {}
        self.activity_logs: Dict[str, List[Activity]] = {}
        self.invitations: Dict[str, Dict] = {}
        self.workspace_members_index: Dict[str, Set[str]] = {}
    
    
    # ====================================================================
    # WORKSPACE MANAGEMENT
    # ====================================================================
    
    def create_workspace(self, name: str, description: str, owner_id: str) -> Workspace:
        """Create new workspace"""
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(
            workspace_id=workspace_id,
            name=name,
            description=description,
            owner_id=owner_id,
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow()
        )
        
        # Add owner as admin
        owner_member = WorkspaceMember(
            user_id=owner_id,
            workspace_id=workspace_id,
            role=WorkspaceRole.ADMIN
        )
        workspace.members[owner_id] = owner_member
        
        self.workspaces[workspace_id] = workspace
        self.activity_logs[workspace_id] = []
        self.workspace_members_index[workspace_id] = {owner_id}
        
        self._log_activity(
            workspace_id=workspace_id,
            user_id=owner_id,
            action="created_workspace",
            metadata={"workspace_name": name}
        )
        
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID"""
        return self.workspaces.get(workspace_id)
    
    def update_workspace(self, workspace_id: str, name: Optional[str] = None,
                        description: Optional[str] = None, 
                        is_public: Optional[bool] = None) -> Workspace:
        """Update workspace settings"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None
        
        if name:
            workspace.name = name
        if description is not None:
            workspace.description = description
        if is_public is not None:
            workspace.is_public = is_public
        
        workspace.updated_date = datetime.utcnow()
        return workspace
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete workspace"""
        if workspace_id in self.workspaces:
            del self.workspaces[workspace_id]
            if workspace_id in self.activity_logs:
                del self.activity_logs[workspace_id]
            if workspace_id in self.workspace_members_index:
                del self.workspace_members_index[workspace_id]
            return True
        return False
    
    def set_default_metrics(self, workspace_id: str, metric_ids: List[str]) -> Workspace:
        """Set default metrics for workspace"""
        workspace = self.workspaces.get(workspace_id)
        if workspace:
            workspace.default_metrics = metric_ids
        return workspace
    
    
    # ====================================================================
    # MEMBER MANAGEMENT
    # ====================================================================
    
    def add_member(self, workspace_id: str, user_id: str, 
                   role: WorkspaceRole = WorkspaceRole.ANALYST) -> WorkspaceMember:
        """Add member to workspace"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None
        
        if user_id in workspace.members:
            # Update existing member
            workspace.members[user_id].is_active = True
            workspace.members[user_id].role = role
            return workspace.members[user_id]
        
        member = WorkspaceMember(
            user_id=user_id,
            workspace_id=workspace_id,
            role=role
        )
        workspace.members[user_id] = member
        self.workspace_members_index[workspace_id].add(user_id)
        
        self._log_activity(
            workspace_id=workspace_id,
            user_id=user_id,
            action="added_to_workspace",
            metadata={"role": role.value}
        )
        
        return member
    
    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        """Remove member from workspace"""
        workspace = self.workspaces.get(workspace_id)
        if workspace and user_id in workspace.members:
            workspace.members[user_id].is_active = False
            self.workspace_members_index[workspace_id].discard(user_id)
            return True
        return False
    
    def update_member_role(self, workspace_id: str, user_id: str, 
                          role: WorkspaceRole) -> Optional[WorkspaceMember]:
        """Update member role"""
        workspace = self.workspaces.get(workspace_id)
        if workspace and user_id in workspace.members:
            workspace.members[user_id].role = role
            return workspace.members[user_id]
        return None
    
    def get_workspace_members(self, workspace_id: str) -> List[WorkspaceMember]:
        """Get all members in workspace"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return []
        return [m for m in workspace.members.values() if m.is_active]
    
    def get_members_by_role(self, workspace_id: str, role: WorkspaceRole) -> List[WorkspaceMember]:
        """Get members with specific role"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return []
        return [m for m in workspace.members.values() 
                if m.is_active and m.role == role]
    
    def get_user_workspaces(self, user_id: str) -> List[Workspace]:
        """Get all workspaces user is member of"""
        return [w for w in self.workspaces.values() 
                if user_id in w.members and w.members[user_id].is_active]
    
    
    # ====================================================================
    # PRESENCE TRACKING
    # ====================================================================
    
    def update_presence(self, user_id: str, workspace_id: str, 
                       status: PresenceStatus, 
                       current_view: Optional[str] = None,
                       cursor_position: Optional[Dict] = None) -> PresenceInfo:
        """Update user presence"""
        presence_key = f"{user_id}:{workspace_id}"
        
        presence = PresenceInfo(
            user_id=user_id,
            workspace_id=workspace_id,
            status=status,
            last_activity=datetime.utcnow(),
            current_view=current_view,
            cursor_position=cursor_position
        )
        
        self.presence_info[presence_key] = presence
        return presence
    
    def get_presence(self, user_id: str, workspace_id: str) -> Optional[PresenceInfo]:
        """Get user presence info"""
        presence_key = f"{user_id}:{workspace_id}"
        presence = self.presence_info.get(presence_key)
        
        # Check if presence is stale (>5 min)
        if presence and (datetime.utcnow() - presence.last_activity) > timedelta(minutes=5):
            presence.status = PresenceStatus.AWAY
        
        return presence
    
    def get_workspace_presence(self, workspace_id: str) -> List[PresenceInfo]:
        """Get all active users in workspace"""
        presence_list = []
        for presence in self.presence_info.values():
            if presence.workspace_id == workspace_id:
                if (datetime.utcnow() - presence.last_activity) > timedelta(hours=1):
                    continue  # Skip inactive
                presence_list.append(presence)
        return presence_list
    
    def set_idle(self, user_id: str, workspace_id: str) -> PresenceInfo:
        """Mark user as idle"""
        return self.update_presence(user_id, workspace_id, PresenceStatus.IDLE)
    
    def set_away(self, user_id: str, workspace_id: str) -> PresenceInfo:
        """Mark user as away"""
        return self.update_presence(user_id, workspace_id, PresenceStatus.AWAY)
    
    def set_active(self, user_id: str, workspace_id: str) -> PresenceInfo:
        """Mark user as active"""
        return self.update_presence(user_id, workspace_id, PresenceStatus.ACTIVE)
    
    def set_offline(self, user_id: str, workspace_id: str) -> PresenceInfo:
        """Mark user as offline"""
        return self.update_presence(user_id, workspace_id, PresenceStatus.OFFLINE)
    
    
    # ====================================================================
    # INVITATIONS
    # ====================================================================
    
    def create_invitation(self, workspace_id: str, invited_by: str, 
                         email: str, role: WorkspaceRole = WorkspaceRole.ANALYST) -> str:
        """Create workspace invitation"""
        invitation_id = str(uuid.uuid4())
        
        self.invitations[invitation_id] = {
            "invitation_id": invitation_id,
            "workspace_id": workspace_id,
            "email": email,
            "role": role.value,
            "invited_by": invited_by,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "accepted": False
        }
        
        return invitation_id
    
    def accept_invitation(self, invitation_id: str, user_id: str) -> bool:
        """Accept invitation"""
        invitation = self.invitations.get(invitation_id)
        if not invitation:
            return False
        
        if invitation["accepted"] or datetime.utcnow() > invitation["expires_at"]:
            return False
        
        workspace_id = invitation["workspace_id"]
        role = WorkspaceRole(invitation["role"])
        
        self.add_member(workspace_id, user_id, role)
        invitation["accepted"] = True
        
        return True
    
    def revoke_invitation(self, invitation_id: str) -> bool:
        """Revoke invitation"""
        if invitation_id in self.invitations:
            del self.invitations[invitation_id]
            return True
        return False
    
    def get_pending_invitations(self, workspace_id: str) -> List[Dict]:
        """Get pending invitations for workspace"""
        return [inv for inv in self.invitations.values() 
                if inv["workspace_id"] == workspace_id and not inv["accepted"]]
    
    
    # ====================================================================
    # ACTIVITY TRACKING
    # ====================================================================
    
    def _log_activity(self, workspace_id: str, user_id: str, action: str,
                     resource_id: Optional[str] = None, 
                     metadata: Optional[Dict] = None) -> Activity:
        """Log user activity"""
        activity = Activity(
            activity_id=str(uuid.uuid4()),
            user_id=user_id,
            workspace_id=workspace_id,
            action=action,
            resource_id=resource_id,
            metadata=metadata or {}
        )
        
        if workspace_id not in self.activity_logs:
            self.activity_logs[workspace_id] = []
        
        self.activity_logs[workspace_id].append(activity)
        return activity
    
    def log_metric_created(self, workspace_id: str, user_id: str, metric_id: str) -> Activity:
        """Log metric creation"""
        return self._log_activity(workspace_id, user_id, "created_metric", 
                                 resource_id=metric_id)
    
    def log_insight_shared(self, workspace_id: str, user_id: str, insight_id: str) -> Activity:
        """Log insight sharing"""
        return self._log_activity(workspace_id, user_id, "shared_insight", 
                                 resource_id=insight_id)
    
    def log_dashboard_viewed(self, workspace_id: str, user_id: str, dashboard_id: str) -> Activity:
        """Log dashboard view"""
        return self._log_activity(workspace_id, user_id, "viewed_dashboard", 
                                 resource_id=dashboard_id)
    
    def log_metric_edited(self, workspace_id: str, user_id: str, metric_id: str) -> Activity:
        """Log metric edit"""
        return self._log_activity(workspace_id, user_id, "edited_metric", 
                                 resource_id=metric_id)
    
    def log_forecast_generated(self, workspace_id: str, user_id: str, metric_id: str) -> Activity:
        """Log forecast generation"""
        return self._log_activity(workspace_id, user_id, "generated_forecast", 
                                 resource_id=metric_id)
    
    def get_activity_log(self, workspace_id: str, limit: int = 100, 
                        offset: int = 0) -> List[Activity]:
        """Get activity log for workspace"""
        if workspace_id not in self.activity_logs:
            return []
        
        activities = self.activity_logs[workspace_id]
        # Sort by timestamp descending
        activities = sorted(activities, key=lambda a: a.timestamp, reverse=True)
        return activities[offset:offset + limit]
    
    def get_user_activity(self, workspace_id: str, user_id: str, 
                         limit: int = 50) -> List[Activity]:
        """Get activity for specific user"""
        if workspace_id not in self.activity_logs:
            return []
        
        activities = [a for a in self.activity_logs[workspace_id] if a.user_id == user_id]
        activities = sorted(activities, key=lambda a: a.timestamp, reverse=True)
        return activities[:limit]
    
    def get_recent_activity(self, workspace_id: str, hours: int = 24) -> List[Activity]:
        """Get recent activity (last N hours)"""
        if workspace_id not in self.activity_logs:
            return []
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        activities = [a for a in self.activity_logs[workspace_id] 
                     if a.timestamp > cutoff]
        return sorted(activities, key=lambda a: a.timestamp, reverse=True)
    
    
    # ====================================================================
    # UTILITY METHODS
    # ====================================================================
    
    def can_user_access_workspace(self, user_id: str, workspace_id: str) -> bool:
        """Check if user can access workspace"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False
        
        member = workspace.members.get(user_id)
        return member and member.is_active
    
    def has_permission(self, user_id: str, workspace_id: str, 
                      action: str) -> bool:
        """Check if user has permission for action"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False
        
        member = workspace.members.get(user_id)
        if not member or not member.is_active:
            return False
        
        # Permission matrix
        if member.role == WorkspaceRole.ADMIN:
            return True  # Admin can do everything
        elif member.role == WorkspaceRole.ANALYST:
            return action not in ["delete_workspace", "manage_members", "change_settings"]
        else:  # VIEWER or GUEST
            return action in ["view_metrics", "view_dashboards", "view_insights"]
    
    def get_workspace_by_name(self, name: str, owner_id: str) -> Optional[Workspace]:
        """Get workspace by name for specific owner"""
        for workspace in self.workspaces.values():
            if workspace.name == name and workspace.owner_id == owner_id:
                return workspace
        return None
