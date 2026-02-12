"""
Phase 14: Community Contribution Service
- Template submission and review workflow
- Template approval and publishing
- Community standards and guidelines
- Featured template selection
- Trending algorithm
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.models.marketplace_models import WorkflowTemplate, TemplateAuthor
from app.database.config import SessionLocal
from sqlalchemy import and_, desc
import uuid


class ContributionService:
    """Community Contributions Management"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    # Quality thresholds
    APPROVAL_RATING_THRESHOLD = 3.5
    APPROVAL_REVIEW_COUNT = 5
    FEATURED_RATING_THRESHOLD = 4.5
    FEATURED_DOWNLOADS = 100
    
    # ==================== TEMPLATE SUBMISSION ====================
    
    def submit_template(
        self,
        user_id: str,
        name: str,
        description: str,
        workflow_config: Dict,
        category_id: str,
        tags: List[str],
        icon_url: Optional[str] = None,
        requirements: Optional[Dict] = None,
        is_paid: bool = False,
        price: float = 0.0
    ) -> Dict:
        """Submit a new template for community"""
        # Ensure author exists
        author = self.db.query(TemplateAuthor).filter(
            TemplateAuthor.user_id == user_id
        ).first()
        
        if not author:
            author = TemplateAuthor(
                id=str(uuid.uuid4()),
                user_id=user_id,
                username=f"user_{user_id[:8]}"
            )
            self.db.add(author)
            self.db.commit()
        
        # Create template (private until approved)
        template = WorkflowTemplate(
            id=str(uuid.uuid4()),
            author_id=author.id,
            category_id=category_id,
            name=name,
            slug=self._generate_slug(name),
            description=description,
            workflow_config=workflow_config,
            tags=tags,
            icon_url=icon_url,
            requirements=requirements or {},
            is_public=False,  # Private until approved
            is_paid=is_paid,
            price=price,
            version="1.0.0",
            latest_version="1.0.0"
        )
        
        self.db.add(template)
        
        # Increment author count
        author.total_templates += 1
        
        self.db.commit()
        
        return {
            "id": template.id,
            "status": "draft",
            "name": name,
            "created_at": template.created_at,
            "message": "Template submitted. Publish when ready."
        }
    
    def publish_template(self, template_id: str, user_id: str) -> Dict:
        """Publish a template to marketplace"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if not template:
            return {"error": "Template not found"}
        
        # Verify ownership
        if template.author.user_id != user_id:
            return {"error": "Not authorized"}
        
        # Basic validation
        if not self._validate_template(template):
            return {"error": "Template does not meet requirements"}
        
        template.is_public = True
        template.published_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "id": template.id,
            "status": "published",
            "published_at": template.published_at
        }
    
    def unpublish_template(self, template_id: str, user_id: str) -> Dict:
        """Unpublish a template"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if not template:
            return {"error": "Template not found"}
        
        if template.author.user_id != user_id:
            return {"error": "Not authorized"}
        
        template.is_public = False
        template.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "id": template.id,
            "status": "unpublished"
        }
    
    # ==================== QUALITY CHECKS ====================
    
    def _validate_template(self, template: WorkflowTemplate) -> bool:
        """Validate template meets quality standards"""
        checks = {
            "has_name": bool(template.name),
            "has_description": bool(template.description) and len(template.description) >= 50,
            "has_workflow": bool(template.workflow_config),
            "has_category": bool(template.category_id),
            "has_icon": bool(template.icon_url),
            "valid_tags": len(template.tags) >= 1 and len(template.tags) <= 5
        }
        
        return all(checks.values())
    
    def get_quality_score(self, template_id: str) -> Dict:
        """Calculate template quality score"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if not template:
            return None
        
        scores = {
            "rating": min(template.average_rating / 5.0, 1.0) * 25,  # 0-25
            "reviews": min(template.rating_count / 10, 1.0) * 15,  # 0-15
            "downloads": min(template.downloads / 100, 1.0) * 20,  # 0-20
            "documentation": 10 if self._has_good_docs(template) else 0,  # 0-10
            "recency": 10 if self._is_recently_updated(template) else 0,  # 0-10
            "tags_quality": min(len(template.tags) / 5, 1.0) * 10  # 0-10
            # Total: 100
        }
        
        total_score = sum(scores.values())
        
        return {
            "overall": round(total_score, 1),
            "breakdown": {k: round(v, 1) for k, v in scores.items()},
            "ready_for_feature": total_score >= 70,
            "quality_tier": self._get_quality_tier(total_score)
        }
    
    def _has_good_docs(self, template: WorkflowTemplate) -> bool:
        """Check if template has good documentation"""
        description_length = len(template.description or "") >= 200
        has_examples = "example" in template.full_description.lower() if template.full_description else False
        return description_length and has_examples
    
    def _is_recently_updated(self, template: WorkflowTemplate) -> bool:
        """Check if template was updated in last 30 days"""
        if not template.updated_at:
            return False
        return (datetime.utcnow() - template.updated_at).days <= 30
    
    def _get_quality_tier(self, score: float) -> str:
        """Get quality tier based on score"""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "acceptable"
        else:
            return "needs_improvement"
    
    # ==================== FEATURED & TRENDING ====================
    
    def get_featured_candidates(self) -> List[Dict]:
        """Get templates eligible for featuring"""
        candidates = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.is_public == True,
            WorkflowTemplate.is_archived == False,
            WorkflowTemplate.average_rating >= self.FEATURED_RATING_THRESHOLD,
            WorkflowTemplate.rating_count >= self.APPROVAL_REVIEW_COUNT,
            WorkflowTemplate.downloads >= self.FEATURED_DOWNLOADS
        ).order_by(
            desc(WorkflowTemplate.average_rating)
        ).limit(20).all()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "rating": round(c.average_rating, 2),
                "downloads": c.downloads,
                "reviews": c.rating_count,
                "quality_score": self.get_quality_score(c.id)["overall"]
            } for c in candidates
        ]
    
    def feature_template(
        self,
        template_id: str,
        featured_by: str,
        reason: Optional[str] = None
    ) -> Dict:
        """Feature a template on marketplace"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if not template:
            return {"error": "Template not found"}
        
        # Check eligibility
        quality = self.get_quality_score(template_id)
        if not quality["ready_for_feature"]:
            return {
                "error": "Template does not meet feature requirements",
                "quality_score": quality["overall"]
            }
        
        template.is_featured = True
        template.featured_at = datetime.utcnow()
        template.is_verified = True
        
        self.db.commit()
        
        return {
            "id": template.id,
            "status": "featured",
            "featured_at": template.featured_at
        }
    
    def unfeature_template(self, template_id: str) -> Dict:
        """Remove featured status"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if template:
            template.is_featured = False
            self.db.commit()
        
        return {"id": template_id, "is_featured": False}
    
    def calculate_trending_score(self, template_id: str, days: int = 7) -> float:
        """Calculate trending score based on recent activity"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if not template:
            return 0.0
        
        # Trending algorithm:
        # Downloads (50%) + Views (30%) + Ratings (20%)
        # Within last N days
        
        # For simplicity, using current totals as proxy
        # In production, track historical data
        
        downloads_score = min(template.downloads / 50, 1.0) * 50  # 0-50
        views_score = min(template.views / 200, 1.0) * 30  # 0-30
        rating_score = (template.average_rating / 5.0) * 20  # 0-20
        
        return downloads_score + views_score + rating_score
    
    def get_trending_score(self, template_id: str) -> Dict:
        """Get detailed trending metrics"""
        trending = self.calculate_trending_score(template_id)
        
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        return {
            "template_id": template_id,
            "trending_score": round(trending, 2),
            "rank": self._get_trending_rank(trending),
            "momentum": "rising" if trending > 50 else "stable" if trending > 30 else "declining",
            "metrics": {
                "downloads": template.downloads,
                "views": template.views,
                "rating": round(template.average_rating, 2),
                "reviews": template.rating_count
            }
        }
    
    def _get_trending_rank(self, score: float) -> str:
        """Get trending rank"""
        if score >= 80:
            return "🔥 Viral"
        elif score >= 60:
            return "📈 Rising"
        elif score >= 40:
            return "⭐ Popular"
        else:
            return "New"
    
    # ==================== AUTHOR VERIFICATION ====================
    
    def verify_author(self, author_id: str, verified_by: str) -> Dict:
        """Verify an author (admin only)"""
        author = self.db.query(TemplateAuthor).get(author_id)
        
        if not author:
            return {"error": "Author not found"}
        
        author.is_verified = True
        author.verified_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "author_id": author_id,
            "is_verified": True,
            "verified_at": author.verified_at
        }
    
    def feature_author(self, author_id: str) -> Dict:
        """Feature an author"""
        author = self.db.query(TemplateAuthor).get(author_id)
        
        if not author:
            return {"error": "Author not found"}
        
        author.is_featured = True
        
        self.db.commit()
        
        return {
            "author_id": author_id,
            "is_featured": True
        }
    
    # ==================== HELPER METHODS ====================
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug"""
        slug = name.lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        
        # Ensure uniqueness
        existing = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.slug == slug
        ).first()
        
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
        return slug
