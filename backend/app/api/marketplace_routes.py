"""
Phase 14: Marketplace API Routes
- 20+ REST endpoints
- Template discovery, search, sharing
- Revenue tracking and analytics
- Community contributions
"""

from fastapi import APIRouter, Header, Query, Body, HTTPException
from typing import Optional, List
from app.services.marketplace_service import MarketplaceService, SearchFilter
from app.services.workflow_sharing_service import WorkflowSharingService
from app.services.contribution_service import ContributionService
from app.services.revenue_manager import RevenueManager
import uuid

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])

# Service instances
marketplace_svc = None
sharing_svc = None
contribution_svc = None
revenue_mgr = None


def set_marketplace_services(m, w, c, r):
    """Inject service instances"""
    global marketplace_svc, sharing_svc, contribution_svc, revenue_mgr
    marketplace_svc = m
    sharing_svc = w
    contribution_svc = c
    revenue_mgr = r


# ==================== DISCOVERY ====================

@router.get("/featured")
async def get_featured(limit: int = Query(6, ge=1, le=20)):
    """Get featured templates"""
    return {
        "templates": marketplace_svc.get_featured_templates(limit=limit)
    }


@router.get("/trending")
async def get_trending(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=20)
):
    """Get trending templates"""
    return {
        "period_days": days,
        "templates": marketplace_svc.get_trending_templates(days=days, limit=limit)
    }


@router.get("/categories")
async def get_categories():
    """Get all template categories"""
    return {
        "categories": marketplace_svc.get_categories()
    }


@router.get("/categories/{category_id}")
async def get_category_templates(
    category_id: str,
    sort: SearchFilter = Query(SearchFilter.POPULAR),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """Get templates by category"""
    templates, total = marketplace_svc.get_category_templates(
        category_id=category_id,
        sort=sort,
        limit=limit,
        offset=offset
    )
    
    return {
        "category_id": category_id,
        "total": total,
        "templates": templates,
        "pagination": {
            "limit": limit,
            "offset": offset
        }
    }


@router.get("/authors/{author_id}")
async def get_author_profile(author_id: str):
    """Get author profile"""
    profile = marketplace_svc.get_author_profile(author_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return profile


# ==================== SEARCH ====================

@router.get("/search")
async def search_templates(
    q: str = Query(..., min_length=1),
    tags: Optional[List[str]] = Query(None),
    category_id: Optional[str] = None,
    min_rating: float = Query(0, ge=0, le=5),
    max_price: Optional[float] = None,
    author_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """Full-text search with filters"""
    templates, total = marketplace_svc.search_templates(
        query=q,
        tags=tags,
        category_id=category_id,
        min_rating=min_rating,
        max_price=max_price,
        author_id=author_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "query": q,
        "total": total,
        "templates": templates,
        "pagination": {
            "limit": limit,
            "offset": offset
        }
    }


# ==================== TEMPLATES ====================

@router.get("/templates/{template_id}")
async def get_template_details(template_id: str):
    """Get template details"""
    # In production: query database
    marketplace_svc.increment_template_views(template_id)
    
    return {
        "message": "Template details endpoint",
        "template_id": template_id
    }


@router.get("/templates/{template_id}/versions")
async def get_template_versions(template_id: str):
    """Get template version history"""
    versions = marketplace_svc.get_template_versions(template_id)
    
    return {
        "template_id": template_id,
        "versions": versions
    }


@router.post("/templates")
async def create_template(
    x_user_id: str = Header(...),
    template_data: dict = Body(...)
):
    """Create new template"""
    result = contribution_svc.submit_template(
        user_id=x_user_id,
        name=template_data.get("name"),
        description=template_data.get("description"),
        workflow_config=template_data.get("workflow_config"),
        category_id=template_data.get("category_id"),
        tags=template_data.get("tags", []),
        icon_url=template_data.get("icon_url"),
        requirements=template_data.get("requirements"),
        is_paid=template_data.get("is_paid", False),
        price=template_data.get("price", 0.0)
    )
    
    return result


@router.post("/templates/{template_id}/publish")
async def publish_template(
    template_id: str,
    x_user_id: str = Header(...)
):
    """Publish template to marketplace"""
    result = contribution_svc.publish_template(template_id, x_user_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/templates/{template_id}/fork")
async def fork_template(
    template_id: str,
    x_user_id: str = Header(...),
    fork_data: dict = Body(...)
):
    """Fork a template"""
    result = marketplace_svc.fork_template(
        template_id=template_id,
        user_id=x_user_id,
        new_name=fork_data.get("name"),
        new_description=fork_data.get("description")
    )
    
    return result


# ==================== RATINGS ====================

@router.post("/templates/{template_id}/ratings")
async def create_rating(
    template_id: str,
    x_user_id: str = Header(...),
    rating_data: dict = Body(...)
):
    """Create or update rating"""
    result = marketplace_svc.create_rating(
        template_id=template_id,
        user_id=x_user_id,
        rating=rating_data.get("rating"),
        review_title=rating_data.get("title"),
        review_text=rating_data.get("text"),
        ease_of_use=rating_data.get("ease_of_use"),
        customization_level=rating_data.get("customization"),
        documentation_quality=rating_data.get("documentation")
    )
    
    return result


@router.get("/templates/{template_id}/ratings")
async def get_ratings(
    template_id: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("helpful")
):
    """Get template ratings"""
    ratings, total = marketplace_svc.get_template_ratings(
        template_id=template_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by
    )
    
    return {
        "template_id": template_id,
        "total": total,
        "ratings": ratings
    }


# ==================== SHARING ====================

@router.post("/templates/{template_id}/share")
async def create_share(
    template_id: str,
    x_user_id: str = Header(...),
    share_data: dict = Body(...)
):
    """Create a share link"""
    result = sharing_svc.create_share(
        template_id=template_id,
        shared_by_user_id=x_user_id,
        shared_with_user_id=share_data.get("user_id"),
        team_id=share_data.get("team_id"),
        is_public_link=share_data.get("is_public", False),
        can_fork=share_data.get("can_fork", True),
        can_suggest=share_data.get("can_suggest", True),
        can_rate=share_data.get("can_rate", True),
        expiration_days=share_data.get("expiration_days")
    )
    
    return result


@router.get("/share/{share_token}")
async def access_shared_template(share_token: str):
    """Access template via share token"""
    template = sharing_svc.access_shared_template(share_token)
    
    if not template:
        raise HTTPException(status_code=404, detail="Share not found or expired")
    
    return template


@router.post("/templates/{template_id}/suggestions")
async def create_suggestion(
    template_id: str,
    x_user_id: str = Header(...),
    suggestion_data: dict = Body(...)
):
    """Submit improvement suggestion"""
    result = sharing_svc.create_suggestion(
        template_id=template_id,
        user_id=x_user_id,
        suggestion_type=suggestion_data.get("type"),
        title=suggestion_data.get("title"),
        description=suggestion_data.get("description"),
        modified_workflow=suggestion_data.get("modified_workflow"),
        code_changes=suggestion_data.get("code_changes")
    )
    
    return result


@router.get("/templates/{template_id}/suggestions")
async def get_suggestions(
    template_id: str,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """Get suggestions for template"""
    suggestions, total = sharing_svc.get_template_suggestions(
        template_id=template_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return {
        "template_id": template_id,
        "total": total,
        "suggestions": suggestions
    }


# ==================== CONTRIBUTIONS ====================

@router.get("/contributions/candidates")
async def get_featured_candidates():
    """Get templates eligible for featuring"""
    return {
        "candidates": contribution_svc.get_featured_candidates()
    }


@router.get("/contributions/quality/{template_id}")
async def get_quality_score(template_id: str):
    """Get template quality score"""
    score = contribution_svc.get_quality_score(template_id)
    
    if not score:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return score


@router.get("/contributions/trending/{template_id}")
async def get_trending_score(template_id: str):
    """Get trending score for template"""
    score = contribution_svc.get_trending_score(template_id)
    
    return score


# ==================== REVENUE ====================

@router.post("/templates/{template_id}/purchase")
async def record_purchase(
    template_id: str,
    x_user_id: str = Header(...),
    purchase_data: dict = Body(...)
):
    """Record template purchase"""
    result = revenue_mgr.record_purchase(
        template_id=template_id,
        user_id=x_user_id,
        amount=purchase_data.get("amount"),
        source=purchase_data.get("source", "marketplace"),
        referrer_id=purchase_data.get("referrer_id")
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/authors/{author_id}/earnings")
async def get_author_earnings(
    author_id: str,
    months: int = Query(12, ge=1, le=24)
):
    """Get author earnings"""
    earnings = revenue_mgr.get_author_earnings(author_id, months=months)
    
    if not earnings:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return earnings


@router.get("/templates/{template_id}/revenue")
async def get_template_revenue(template_id: str):
    """Get template revenue metrics"""
    revenue = revenue_mgr.get_template_revenue(template_id)
    
    if not revenue:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return revenue


@router.get("/analytics/platform")
async def get_platform_analytics(months: int = Query(12, ge=1, le=24)):
    """Get platform-wide financial analytics"""
    return revenue_mgr.get_platform_analytics(months=months)


@router.get("/analytics/top-templates")
async def get_top_templates(limit: int = Query(10, ge=1, le=20)):
    """Get highest-earning templates"""
    return {
        "templates": revenue_mgr.get_top_earning_templates(limit=limit)
    }


@router.get("/analytics/top-authors")
async def get_top_authors(limit: int = Query(10, ge=1, le=20)):
    """Get highest-earning authors"""
    return {
        "authors": revenue_mgr.get_top_earning_authors(limit=limit)
    }


# ==================== HEALTH ====================

@router.get("/health")
async def marketplace_health():
    """Health check"""
    return {
        "status": "healthy",
        "services": {
            "marketplace": True,
            "sharing": True,
            "contributions": True,
            "revenue": True
        }
    }
