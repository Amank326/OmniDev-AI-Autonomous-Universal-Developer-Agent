"""
Phase 14: API Marketplace & Workflow Sharing Models
- WorkflowTemplate: Public template definitions
- TemplateCategory: Organization and discovery
- TemplateRating: Community feedback system
- TemplateRevision: Version control for templates
- TemplateAuthor: Creator profiles and stats
- RevenueSplit: Author earnings tracking
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.config import Base
from datetime import datetime, timedelta
import enum


class TemplateCategory(Base):
    __tablename__ = "template_categories"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(200))
    slug = Column(String(100), unique=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    templates = relationship("WorkflowTemplate", back_populates="category")


class TemplateTag(Base):
    __tablename__ = "template_tags"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), unique=True)
    description = Column(Text)
    color = Column(String(20))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class TemplateAuthor(Base):
    __tablename__ = "template_authors"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, unique=True)
    username = Column(String(100))
    display_name = Column(String(200))
    bio = Column(Text)
    avatar_url = Column(String(500))
    website_url = Column(String(500))
    github_url = Column(String(500))
    
    # Stats
    total_templates = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    total_forks = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_earnings = Column(Float, default=0.0)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    
    # Preferences
    receive_earnings_notifications = Column(Boolean, default=True)
    auto_approve_suggested_improvements = Column(Boolean, default=False)
    public_earnings_stats = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"
    
    id = Column(String(50), primary_key=True)
    author_id = Column(String(50), ForeignKey("template_authors.id"), nullable=False)
    category_id = Column(String(50), ForeignKey("template_categories.id"))
    
    # Basic info
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True)
    description = Column(Text, nullable=False)
    full_description = Column(Text)
    icon_url = Column(String(500))
    banner_image_url = Column(String(500))
    
    # Metadata
    version = Column(String(50), default="1.0.0")
    latest_version = Column(String(50), default="1.0.0")
    tags = Column(JSON, default=list)  # ["automation", "productivity"]
    
    # Stats
    downloads = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    rating_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    views = Column(Integer, default=0)
    
    # Visibility & Status
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Content
    workflow_config = Column(JSON, nullable=False)  # Full workflow definition
    preview_image_urls = Column(JSON, default=list)
    requirements = Column(JSON, default=dict)  # {"integrations": [], "permissions": []}
    
    # Monetization
    is_paid = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    revenue_share_percent = Column(Float, default=50.0)  # Author gets 50%
    
    # Licensing
    license_type = Column(String(50), default="MIT")  # MIT, GPL, Apache, Commercial
    license_url = Column(String(500))
    
    # Community
    total_comments = Column(Integer, default=0)
    total_suggestions = Column(Integer, default=0)
    featured_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    author = relationship("TemplateAuthor", foreign_keys=[author_id])
    category = relationship("TemplateCategory", back_populates="templates")
    ratings = relationship("TemplateRating", back_populates="template", cascade="all, delete-orphan")
    revisions = relationship("TemplateRevision", back_populates="template", cascade="all, delete-orphan")
    shared_with = relationship("WorkflowShare", back_populates="template", cascade="all, delete-orphan")


class TemplateRevision(Base):
    __tablename__ = "template_revisions"
    
    id = Column(String(50), primary_key=True)
    template_id = Column(String(50), ForeignKey("workflow_templates.id"), nullable=False)
    author_id = Column(String(50), ForeignKey("template_authors.id"))
    
    version = Column(String(50), nullable=False)
    changelog = Column(Text)
    
    workflow_config = Column(JSON, nullable=False)
    requirements = Column(JSON, default=dict)
    
    # Version metadata
    is_major = Column(Boolean, default=False)  # Major version bump
    is_release = Column(Boolean, default=False)  # Public release
    
    download_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    template = relationship("WorkflowTemplate", back_populates="revisions")


class TemplateRating(Base):
    __tablename__ = "template_ratings"
    
    id = Column(String(50), primary_key=True)
    template_id = Column(String(50), ForeignKey("workflow_templates.id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_title = Column(String(200))
    review_text = Column(Text)
    
    # Quality signals
    is_helpful = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)  # "X found helpful"
    
    # Usage experience
    ease_of_use = Column(Integer)  # 1-5
    customization_level = Column(Integer)  # 1-5 (how customizable)
    documentation_quality = Column(Integer)  # 1-5
    
    # Tags
    tags = Column(JSON, default=list)  # ["easy-setup", "well-documented"]
    
    verified_user = Column(Boolean, default=False)  # User actually uses it
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    template = relationship("WorkflowTemplate", back_populates="ratings")


class WorkflowShare(Base):
    __tablename__ = "workflow_shares"
    
    id = Column(String(50), primary_key=True)
    template_id = Column(String(50), ForeignKey("workflow_templates.id"), nullable=False)
    shared_by_user_id = Column(String(50), nullable=False)
    
    # Share target
    shared_with_user_id = Column(String(50))  # Individual user
    team_id = Column(String(50))  # Or team
    is_public_link = Column(Boolean, default=False)  # Public share link
    
    # Permissions
    can_view = Column(Boolean, default=True)
    can_fork = Column(Boolean, default=True)
    can_suggest_improvements = Column(Boolean, default=True)
    can_rate = Column(Boolean, default=True)
    
    # Collaboration
    share_token = Column(String(100), unique=True)
    expiration_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_at = Column(DateTime)
    
    template = relationship("WorkflowTemplate", back_populates="shared_with")


class RevenueSplit(Base):
    __tablename__ = "revenue_splits"
    
    id = Column(String(50), primary_key=True)
    template_id = Column(String(50), ForeignKey("workflow_templates.id"), nullable=False)
    author_id = Column(String(50), ForeignKey("template_authors.id"), nullable=False)
    
    # Split configuration
    author_percent = Column(Float, nullable=False)  # 50%
    platform_percent = Column(Float, nullable=False)  # 30%
    referrer_percent = Column(Float, default=20.0)  # 20% (if referred)
    
    # Monthly tracking
    month = Column(String(7))  # YYYY-MM
    
    # Revenue data
    total_downloads = Column(Integer, default=0)
    paid_downloads = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    author_earnings = Column(Float, default=0.0)
    platform_earnings = Column(Float, default=0.0)
    referrer_earnings = Column(Float, default=0.0)
    
    # Payout
    payout_status = Column(String(50), default="pending")  # pending, processed, failed
    payout_date = Column(DateTime)
    payout_reference = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateSuggestion(Base):
    __tablename__ = "template_suggestions"
    
    id = Column(String(50), primary_key=True)
    template_id = Column(String(50), ForeignKey("workflow_templates.id"), nullable=False)
    suggested_by_user_id = Column(String(50), nullable=False)
    
    # Suggestion type
    suggestion_type = Column(String(50))  # "improvement", "bug_fix", "feature"
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Changes proposed
    modified_workflow_config = Column(JSON)
    code_changes = Column(Text)
    
    # Status
    status = Column(String(50), default="pending")  # pending, approved, rejected, implemented
    status_reason = Column(Text)
    
    # Voting
    upvote_count = Column(Integer, default=0)
    downvote_count = Column(Integer, default=0)
    
    # Community feedback
    comments = Column(JSON, default=list)  # [{user_id, text, timestamp}]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    
    template = relationship("WorkflowTemplate", foreign_keys=[template_id])


class TemplateDownload(Base):
    __tablename__ = "template_downloads"
    
    id = Column(String(50), primary_key=True)
    template_id = Column(String(50), ForeignKey("workflow_templates.id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    
    version = Column(String(50))
    
    # Source tracking
    source = Column(String(50))  # "marketplace", "shared_link", "team"
    referrer_user_id = Column(String(50))  # Who referred this user
    
    # Installation tracking
    installed_at = Column(DateTime, default=datetime.utcnow)
    
    # Usage
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    total_runs = Column(Integer, default=0)
    total_modifications = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
