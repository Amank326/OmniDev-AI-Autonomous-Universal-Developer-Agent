"""
Phase 14: Workflow Sharing Service
- Public/private template sharing
- Sharing links and permissions
- Community feedback (comments, suggestions)
- Collaboration and team sharing
- Notification system for shares
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.models.marketplace_models import (
    WorkflowShare, TemplateSuggestion, TemplateDownload, WorkflowTemplate
)
from app.database.config import SessionLocal
from sqlalchemy import and_, or_, desc
import uuid
import secrets


class WorkflowSharingService:
    """Workflow Sharing and Collaboration"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    # ==================== SHARING ====================
    
    def create_share(
        self,
        template_id: str,
        shared_by_user_id: str,
        shared_with_user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        is_public_link: bool = False,
        can_fork: bool = True,
        can_suggest: bool = True,
        can_rate: bool = True,
        expiration_days: Optional[int] = None
    ) -> Dict:
        """Create a share for template"""
        share = WorkflowShare(
            id=str(uuid.uuid4()),
            template_id=template_id,
            shared_by_user_id=shared_by_user_id,
            shared_with_user_id=shared_with_user_id,
            team_id=team_id,
            is_public_link=is_public_link,
            can_view=True,
            can_fork=can_fork,
            can_suggest_improvements=can_suggest,
            can_rate=can_rate,
            share_token=secrets.token_urlsafe(32),
            expiration_date=datetime.utcnow() + timedelta(days=expiration_days)
                if expiration_days else None
        )
        
        self.db.add(share)
        self.db.commit()
        
        return {
            "id": share.id,
            "share_token": share.share_token,
            "is_public_link": is_public_link,
            "expiration_date": share.expiration_date,
            "created_at": share.created_at
        }
    
    def access_shared_template(self, share_token: str) -> Optional[Dict]:
        """Access template via share token"""
        share = self.db.query(WorkflowShare).filter(
            WorkflowShare.share_token == share_token
        ).first()
        
        if not share:
            return None
        
        # Check expiration
        if share.expiration_date and share.expiration_date < datetime.utcnow():
            return None
        
        share.accessed_at = datetime.utcnow()
        self.db.commit()
        
        template = share.template
        
        return {
            "template_id": template.id,
            "name": template.name,
            "description": template.description,
            "workflow_config": template.workflow_config,
            "permissions": {
                "can_view": share.can_view,
                "can_fork": share.can_fork,
                "can_suggest": share.can_suggest_improvements,
                "can_rate": share.can_rate
            },
            "shared_by": share.shared_by_user_id,
            "shared_at": share.created_at
        }
    
    def get_shared_templates(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Get templates shared with user"""
        shares = self.db.query(WorkflowShare).filter(
            WorkflowShare.shared_with_user_id == user_id
        ).order_by(desc(WorkflowShare.created_at))
        
        total = shares.count()
        shares = shares.limit(limit).offset(offset).all()
        
        return [
            {
                "template_id": s.template.id,
                "name": s.template.name,
                "shared_by": s.shared_by_user_id,
                "shared_at": s.created_at,
                "permissions": {
                    "can_fork": s.can_fork,
                    "can_suggest": s.can_suggest_improvements,
                    "can_rate": s.can_rate
                }
            } for s in shares
        ], total
    
    def revoke_share(self, share_id: str) -> bool:
        """Revoke a share link"""
        share = self.db.query(WorkflowShare).get(share_id)
        if share:
            self.db.delete(share)
            self.db.commit()
            return True
        return False
    
    # ==================== SUGGESTIONS & FEEDBACK ====================
    
    def create_suggestion(
        self,
        template_id: str,
        user_id: str,
        suggestion_type: str,
        title: str,
        description: str,
        modified_workflow: Optional[Dict] = None,
        code_changes: Optional[str] = None
    ) -> Dict:
        """Submit improvement suggestion"""
        suggestion = TemplateSuggestion(
            id=str(uuid.uuid4()),
            template_id=template_id,
            suggested_by_user_id=user_id,
            suggestion_type=suggestion_type,
            title=title,
            description=description,
            modified_workflow_config=modified_workflow,
            code_changes=code_changes,
            status="pending"
        )
        
        self.db.add(suggestion)
        self.db.commit()
        
        return {
            "id": suggestion.id,
            "status": "pending",
            "created_at": suggestion.created_at
        }
    
    def get_template_suggestions(
        self,
        template_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Get suggestions for a template"""
        query = self.db.query(TemplateSuggestion).filter(
            TemplateSuggestion.template_id == template_id
        )
        
        if status:
            query = query.filter(TemplateSuggestion.status == status)
        
        total = query.count()
        suggestions = query.order_by(
            desc(TemplateSuggestion.upvote_count)
        ).limit(limit).offset(offset).all()
        
        return [
            {
                "id": s.id,
                "type": s.suggestion_type,
                "title": s.title,
                "description": s.description,
                "suggested_by": s.suggested_by_user_id,
                "status": s.status,
                "votes": s.upvote_count - s.downvote_count,
                "created_at": s.created_at
            } for s in suggestions
        ], total
    
    def vote_on_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
        vote_type: str  # "upvote" or "downvote"
    ) -> Dict:
        """Vote on a suggestion"""
        suggestion = self.db.query(TemplateSuggestion).get(suggestion_id)
        
        if not suggestion:
            return None
        
        if vote_type == "upvote":
            suggestion.upvote_count += 1
        elif vote_type == "downvote":
            suggestion.downvote_count += 1
        
        self.db.commit()
        
        return {
            "upvotes": suggestion.upvote_count,
            "downvotes": suggestion.downvote_count,
            "net_votes": suggestion.upvote_count - suggestion.downvote_count
        }
    
    def approve_suggestion(
        self,
        suggestion_id: str,
        approved_by_user_id: str
    ) -> Dict:
        """Approve suggestion (template author only)"""
        suggestion = self.db.query(TemplateSuggestion).get(suggestion_id)
        
        if not suggestion:
            return None
        
        suggestion.status = "approved"
        suggestion.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "id": suggestion.id,
            "status": "approved",
            "reviewed_at": suggestion.reviewed_at
        }
    
    def implement_suggestion(
        self,
        suggestion_id: str,
        implemented_by_user_id: str,
        implementation_notes: Optional[str] = None
    ) -> Dict:
        """Mark suggestion as implemented"""
        suggestion = self.db.query(TemplateSuggestion).get(suggestion_id)
        
        if not suggestion:
            return None
        
        suggestion.status = "implemented"
        suggestion.status_reason = implementation_notes
        suggestion.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "id": suggestion.id,
            "status": "implemented",
            "implemented_at": suggestion.reviewed_at
        }
    
    # ==================== COLLABORATION ====================
    
    def add_comment_to_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
        text: str
    ) -> Dict:
        """Add comment to suggestion"""
        suggestion = self.db.query(TemplateSuggestion).get(suggestion_id)
        
        if not suggestion:
            return None
        
        comment = {
            "user_id": user_id,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if suggestion.comments is None:
            suggestion.comments = []
        
        suggestion.comments.append(comment)
        self.db.commit()
        
        return comment
    
    def get_suggestion_comments(self, suggestion_id: str) -> List[Dict]:
        """Get all comments on a suggestion"""
        suggestion = self.db.query(TemplateSuggestion).get(suggestion_id)
        
        if not suggestion:
            return []
        
        return suggestion.comments or []
    
    # ==================== DOWNLOAD TRACKING ====================
    
    def track_template_download(
        self,
        template_id: str,
        user_id: str,
        version: str,
        source: str = "marketplace",
        referrer_user_id: Optional[str] = None
    ) -> Dict:
        """Track template download for analytics"""
        download = TemplateDownload(
            id=str(uuid.uuid4()),
            template_id=template_id,
            user_id=user_id,
            version=version,
            source=source,
            referrer_user_id=referrer_user_id
        )
        
        self.db.add(download)
        
        # Update template download counter
        template = self.db.query(WorkflowTemplate).get(template_id)
        if template:
            template.downloads += 1
        
        # Update author stats
        if template and template.author:
            template.author.total_downloads += 1
        
        self.db.commit()
        
        return {
            "id": download.id,
            "tracked_at": download.installed_at
        }
    
    def get_download_analytics(
        self,
        template_id: str,
        days: int = 30
    ) -> Dict:
        """Get download analytics for a template"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        downloads = self.db.query(TemplateDownload).filter(
            TemplateDownload.template_id == template_id,
            TemplateDownload.installed_at >= cutoff_date
        ).all()
        
        # Group by source
        sources = {}
        for d in downloads:
            sources[d.source] = sources.get(d.source, 0) + 1
        
        return {
            "total_downloads": len(downloads),
            "by_source": sources,
            "active_users": len(set(d.user_id for d in downloads)),
            "period_days": days
        }
    
    def track_template_usage(
        self,
        template_id: str,
        user_id: str,
        execution_count: int = 1
    ) -> Dict:
        """Track when user runs a downloaded template"""
        download = self.db.query(TemplateDownload).filter(
            TemplateDownload.template_id == template_id,
            TemplateDownload.user_id == user_id
        ).first()
        
        if download:
            download.last_used_at = datetime.utcnow()
            download.total_runs += execution_count
            download.is_active = True
            self.db.commit()
        
        return {
            "template_id": template_id,
            "user_id": user_id,
            "total_runs": download.total_runs if download else 1
        }
    
    def get_sharing_statistics(self, template_id: str) -> Dict:
        """Get sharing metrics for template"""
        shares = self.db.query(WorkflowShare).filter(
            WorkflowShare.template_id == template_id
        ).all()
        
        downloads = self.db.query(TemplateDownload).filter(
            TemplateDownload.template_id == template_id
        ).all()
        
        active_downloads = [d for d in downloads if d.is_active]
        
        return {
            "total_shares": len(shares),
            "public_links": len([s for s in shares if s.is_public_link]),
            "private_shares": len([s for s in shares if not s.is_public_link]),
            "total_downloads": len(downloads),
            "active_users": len(set(d.user_id for d in active_downloads)),
            "average_usage": sum(d.total_runs for d in downloads) / len(downloads) if downloads else 0
        }
