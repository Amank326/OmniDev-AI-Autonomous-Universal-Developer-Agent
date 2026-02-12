"""
Phase 14: Marketplace Service
- Template discovery and search
- Featured templates and trending section
- Template ratings and reviews
- Versioning and fork/clone operations
- Template metadata and analytics
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.models.marketplace_models import (
    WorkflowTemplate, TemplateCategory, TemplateAuthor, TemplateRating,
    TemplateRevision, WorkflowShare, TemplateSuggestion, TemplateDownload
)
from app.database.config import SessionLocal
from sqlalchemy import and_, or_, func, desc
import uuid
import json
from enum import Enum


class SearchFilter(Enum):
    POPULAR = "popular"
    NEWEST = "newest"
    HIGHEST_RATED = "highest_rated"
    MOST_FORKED = "most_forked"
    TRENDING = "trending"
    FEATURED = "featured"


class MarketplaceService:
    """API Marketplace Business Logic"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    # ==================== DISCOVERY ====================
    
    def get_featured_templates(self, limit: int = 6) -> List[Dict]:
        """Get featured templates for homepage"""
        templates = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.is_featured == True,
            WorkflowTemplate.is_public == True,
            WorkflowTemplate.is_archived == False
        ).order_by(
            desc(WorkflowTemplate.featured_at)
        ).limit(limit).all()
        
        return self._serialize_templates(templates)
    
    def get_trending_templates(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get trending templates based on recent downloads and views"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        templates = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.is_public == True,
            WorkflowTemplate.is_archived == False,
            WorkflowTemplate.created_at > cutoff_date
        ).order_by(
            desc(WorkflowTemplate.downloads + WorkflowTemplate.views)
        ).limit(limit).all()
        
        return self._serialize_templates(templates)
    
    def get_category_templates(
        self, 
        category_id: str, 
        sort: SearchFilter = SearchFilter.POPULAR,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Get templates by category with pagination"""
        query = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.category_id == category_id,
            WorkflowTemplate.is_public == True,
            WorkflowTemplate.is_archived == False
        )
        
        # Apply sorting
        if sort == SearchFilter.POPULAR:
            query = query.order_by(desc(WorkflowTemplate.downloads))
        elif sort == SearchFilter.NEWEST:
            query = query.order_by(desc(WorkflowTemplate.created_at))
        elif sort == SearchFilter.HIGHEST_RATED:
            query = query.order_by(desc(WorkflowTemplate.average_rating))
        elif sort == SearchFilter.MOST_FORKED:
            query = query.order_by(desc(WorkflowTemplate.forks))
        elif sort == SearchFilter.TRENDING:
            # Trending: combo of recent downloads and views
            query = query.order_by(
                desc(WorkflowTemplate.downloads * 2 + WorkflowTemplate.views)
            )
        
        total = query.count()
        templates = query.limit(limit).offset(offset).all()
        
        return self._serialize_templates(templates), total
    
    # ==================== SEARCH ====================
    
    def search_templates(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        category_id: Optional[str] = None,
        min_rating: float = 0,
        max_price: Optional[float] = None,
        author_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Full-text search with filters"""
        db_query = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.is_public == True,
            WorkflowTemplate.is_archived == False
        )
        
        # Text search in name and description
        if query:
            search_term = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    WorkflowTemplate.name.ilike(search_term),
                    WorkflowTemplate.description.ilike(search_term)
                )
            )
        
        # Category filter
        if category_id:
            db_query = db_query.filter(WorkflowTemplate.category_id == category_id)
        
        # Tags filter
        if tags:
            for tag in tags:
                tag_filter = f"%{tag}%"
                db_query = db_query.filter(
                    WorkflowTemplate.tags.astext.ilike(tag_filter)
                )
        
        # Rating filter
        if min_rating > 0:
            db_query = db_query.filter(WorkflowTemplate.average_rating >= min_rating)
        
        # Price filter
        if max_price is not None:
            db_query = db_query.filter(
                or_(
                    WorkflowTemplate.is_paid == False,
                    WorkflowTemplate.price <= max_price
                )
            )
        
        # Author filter
        if author_id:
            db_query = db_query.filter(WorkflowTemplate.author_id == author_id)
        
        # Sort by relevance
        total = db_query.count()
        templates = db_query.order_by(
            desc(WorkflowTemplate.downloads)
        ).limit(limit).offset(offset).all()
        
        return self._serialize_templates(templates), total
    
    # ==================== RATINGS & REVIEWS ====================
    
    def create_rating(
        self,
        template_id: str,
        user_id: str,
        rating: int,
        review_title: Optional[str] = None,
        review_text: Optional[str] = None,
        ease_of_use: Optional[int] = None,
        customization_level: Optional[int] = None,
        documentation_quality: Optional[int] = None
    ) -> Dict:
        """Create or update template rating"""
        # Check if already rated
        existing = self.db.query(TemplateRating).filter(
            TemplateRating.template_id == template_id,
            TemplateRating.user_id == user_id
        ).first()
        
        if existing:
            existing.rating = rating
            existing.review_title = review_title
            existing.review_text = review_text
            if ease_of_use:
                existing.ease_of_use = ease_of_use
            if customization_level:
                existing.customization_level = customization_level
            if documentation_quality:
                existing.documentation_quality = documentation_quality
            existing.updated_at = datetime.utcnow()
            rating_obj = existing
        else:
            rating_obj = TemplateRating(
                id=str(uuid.uuid4()),
                template_id=template_id,
                user_id=user_id,
                rating=rating,
                review_title=review_title,
                review_text=review_text,
                ease_of_use=ease_of_use,
                customization_level=customization_level,
                documentation_quality=documentation_quality
            )
            self.db.add(rating_obj)
        
        self.db.commit()
        self._update_template_rating_stats(template_id)
        
        return {
            "id": rating_obj.id,
            "template_id": template_id,
            "rating": rating_obj.rating,
            "created_at": rating_obj.created_at
        }
    
    def get_template_ratings(
        self,
        template_id: str,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "helpful"
    ) -> Tuple[List[Dict], int]:
        """Get ratings for a template"""
        query = self.db.query(TemplateRating).filter(
            TemplateRating.template_id == template_id
        )
        
        if sort_by == "helpful":
            query = query.order_by(desc(TemplateRating.helpful_count))
        elif sort_by == "newest":
            query = query.order_by(desc(TemplateRating.created_at))
        elif sort_by == "highest":
            query = query.order_by(desc(TemplateRating.rating))
        
        total = query.count()
        ratings = query.limit(limit).offset(offset).all()
        
        return [self._serialize_rating(r) for r in ratings], total
    
    # ==================== VERSIONING ====================
    
    def create_template_revision(
        self,
        template_id: str,
        version: str,
        workflow_config: Dict,
        changelog: str,
        is_major: bool = False,
        is_release: bool = True
    ) -> Dict:
        """Create a new version of template"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        revision = TemplateRevision(
            id=str(uuid.uuid4()),
            template_id=template_id,
            author_id=template.author_id,
            version=version,
            workflow_config=workflow_config,
            changelog=changelog,
            is_major=is_major,
            is_release=is_release,
            published_at=datetime.utcnow() if is_release else None
        )
        
        self.db.add(revision)
        
        # Update template version
        template.version = version
        template.latest_version = version
        template.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "id": revision.id,
            "version": version,
            "published_at": revision.published_at
        }
    
    def get_template_versions(self, template_id: str) -> List[Dict]:
        """Get all versions of a template"""
        revisions = self.db.query(TemplateRevision).filter(
            TemplateRevision.template_id == template_id,
            TemplateRevision.is_release == True
        ).order_by(desc(TemplateRevision.created_at)).all()
        
        return [
            {
                "id": r.id,
                "version": r.version,
                "changelog": r.changelog,
                "published_at": r.published_at,
                "download_count": r.download_count
            } for r in revisions
        ]
    
    # ==================== FORK & CLONE ====================
    
    def fork_template(
        self,
        template_id: str,
        user_id: str,
        new_name: str,
        new_description: Optional[str] = None
    ) -> Dict:
        """Fork a template to user's account"""
        original = self.db.query(WorkflowTemplate).get(template_id)
        
        # Create new template as fork
        forked = WorkflowTemplate(
            id=str(uuid.uuid4()),
            author_id=user_id,
            category_id=original.category_id,
            name=new_name,
            slug=self._generate_slug(new_name),
            description=new_description or original.description,
            workflow_config=original.workflow_config.copy(),
            tags=original.tags.copy(),
            is_public=False,  # Forks are private by default
            version="1.0.0",
            latest_version="1.0.0"
        )
        
        self.db.add(forked)
        
        # Increment fork counter on original
        original.forks += 1
        
        self.db.commit()
        
        return {
            "id": forked.id,
            "name": forked.name,
            "original_template_id": template_id,
            "is_public": forked.is_public
        }
    
    def clone_template_version(
        self,
        template_id: str,
        version: str,
        user_id: str,
        as_new_template: bool = False
    ) -> Dict:
        """Clone specific version of template"""
        revision = self.db.query(TemplateRevision).filter(
            TemplateRevision.template_id == template_id,
            TemplateRevision.version == version
        ).first()
        
        if not revision:
            raise ValueError(f"Version {version} not found")
        
        revision.download_count += 1
        
        if as_new_template:
            # Fork as new template
            original = revision.template
            cloned = WorkflowTemplate(
                id=str(uuid.uuid4()),
                author_id=user_id,
                name=f"{original.name} (v{version})",
                slug=self._generate_slug(f"{original.name} {version}"),
                description=original.description,
                workflow_config=revision.workflow_config.copy(),
                is_public=False,
                version="1.0.0",
                latest_version="1.0.0"
            )
            self.db.add(cloned)
            self.db.commit()
            return {"id": cloned.id, "version": "1.0.0"}
        
        self.db.commit()
        return {
            "workflow_config": revision.workflow_config,
            "version": version
        }
    
    # ==================== HELPER METHODS ====================
    
    def _serialize_templates(self, templates: List[WorkflowTemplate]) -> List[Dict]:
        """Convert templates to serializable dicts"""
        return [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "description": t.description,
                "icon_url": t.icon_url,
                "author": {
                    "id": t.author.id,
                    "username": t.author.username,
                    "is_verified": t.author.is_verified
                },
                "category": {
                    "id": t.category.id,
                    "name": t.category.name
                } if t.category else None,
                "tags": t.tags,
                "stats": {
                    "downloads": t.downloads,
                    "forks": t.forks,
                    "rating": round(t.average_rating, 2),
                    "rating_count": t.rating_count,
                    "views": t.views
                },
                "is_public": t.is_public,
                "is_featured": t.is_featured,
                "is_paid": t.is_paid,
                "price": t.price if t.is_paid else 0,
                "version": t.latest_version,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            } for t in templates
        ]
    
    def _serialize_rating(self, rating: TemplateRating) -> Dict:
        """Convert rating to dict"""
        return {
            "id": rating.id,
            "user_id": rating.user_id,
            "rating": rating.rating,
            "title": rating.review_title,
            "text": rating.review_text,
            "helpful_count": rating.helpful_count,
            "ease_of_use": rating.ease_of_use,
            "customization": rating.customization_level,
            "documentation": rating.documentation_quality,
            "created_at": rating.created_at
        }
    
    def _update_template_rating_stats(self, template_id: str):
        """Recalculate rating stats"""
        ratings = self.db.query(TemplateRating).filter(
            TemplateRating.template_id == template_id
        ).all()
        
        if not ratings:
            return
        
        template = self.db.query(WorkflowTemplate).get(template_id)
        template.rating_count = len(ratings)
        template.average_rating = sum(r.rating for r in ratings) / len(ratings)
        self.db.commit()
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug"""
        slug = name.lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        return slug
    
    def get_categories(self) -> List[Dict]:
        """Get all template categories"""
        categories = self.db.query(TemplateCategory).order_by(
            TemplateCategory.order
        ).all()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "icon": c.icon,
                "slug": c.slug
            } for c in categories
        ]
    
    def get_author_profile(self, author_id: str) -> Dict:
        """Get author profile and stats"""
        author = self.db.query(TemplateAuthor).get(author_id)
        
        if not author:
            return None
        
        return {
            "id": author.id,
            "username": author.username,
            "display_name": author.display_name,
            "bio": author.bio,
            "avatar_url": author.avatar_url,
            "website_url": author.website_url,
            "github_url": author.github_url,
            "stats": {
                "templates": author.total_templates,
                "downloads": author.total_downloads,
                "forks": author.total_forks,
                "average_rating": round(author.average_rating, 2),
                "earnings": author.total_earnings
            },
            "is_verified": author.is_verified,
            "is_featured": author.is_featured,
            "created_at": author.created_at
        }
    
    def increment_template_views(self, template_id: str):
        """Track template views"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        if template:
            template.views += 1
            self.db.commit()
