"""
Advanced Query Parameters for API Filtering and Pagination

Provides reusable query parameter models for consistent filtering across endpoints.

Models:
    - PaginationParams: Offset and limit-based pagination
    - SearchParams: Text search with multiple fields
    - FilterParams: Field-based filtering
    - SortParams: Sorting by multiple fields

Features:
    - Type-safe query parameters
    - Sensible defaults and limits
    - Field validation
    - SQL injection prevention (SQLAlchemy handles escaping)
"""

from typing import Optional, List
from fastapi import Query
from pydantic import BaseModel, Field
from enum import Enum


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.
    
    Attributes:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 20, max: 100)
    
    Example:
        GET /api/projects?skip=0&limit=20
    """
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(20, ge=1, le=100, description="Maximum records to return")
    
    @property
    def offset(self) -> int:
        """Alias for skip."""
        return self.skip


class ProjectFilter(BaseModel):
    """
    Filter parameters for projects endpoint.
    
    Attributes:
        status: Filter by project status (active, completed, archived)
        owner_id: Filter by project owner
        search: Text search in title and description
        sort_by: Field to sort by (created_at, updated_at, title)
        sort_order: Sort order (asc, desc)
    
    Example:
        GET /api/projects?status=active&owner_id=123&sort_by=created_at&sort_order=desc
    """
    status: Optional[str] = Field(None, description="Filter by status")
    owner_id: Optional[int] = Field(None, description="Filter by owner")
    search: Optional[str] = Field(None, description="Text search")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


class TaskFilter(BaseModel):
    """
    Filter parameters for tasks endpoint.
    
    Attributes:
        status: Filter by task status (pending, in_progress, completed)
        priority: Filter by priority (low, medium, high)
        assigned_to: Filter by assigned user
        project_id: Filter by project
        search: Text search in title and description
    """
    status: Optional[str] = Field(None, description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    assigned_to: Optional[int] = Field(None, description="Filter by assigned user")
    project_id: Optional[int] = Field(None, description="Filter by project")
    search: Optional[str] = Field(None, description="Text search")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


class UserFilter(BaseModel):
    """
    Filter parameters for users endpoint.
    
    Attributes:
        is_active: Filter by active status
        is_admin: Filter by admin status
        search: Text search in username and email
    """
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_admin: Optional[bool] = Field(None, description="Filter by admin status")
    search: Optional[str] = Field(None, description="Text search")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


def apply_pagination(query, skip: int = 0, limit: int = 20):
    """
    Apply pagination to SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        skip: Number of records to skip
        limit: Maximum records to return
    
    Returns:
        Paginated query
    """
    return query.offset(skip).limit(limit)


def apply_sorting(query, model, sort_by: str = "created_at", sort_order: str = "desc"):
    """
    Apply sorting to SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        model: SQLAlchemy model class
        sort_by: Field name to sort by
        sort_order: Sort order (asc or desc)
    
    Returns:
        Sorted query
    """
    if not hasattr(model, sort_by):
        # Fall back to default if invalid field
        sort_by = "created_at"
    
    column = getattr(model, sort_by)
    
    if sort_order.lower() == "desc":
        return query.order_by(column.desc())
    else:
        return query.order_by(column.asc())


def apply_search(query, model, search_fields: List[str], search_term: str):
    """
    Apply text search to SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        model: SQLAlchemy model class
        search_fields: List of field names to search in
        search_term: Search term
    
    Returns:
        Filtered query
    """
    if not search_term:
        return query
    
    search_pattern = f"%{search_term}%"
    filters = []
    
    for field in search_fields:
        if hasattr(model, field):
            column = getattr(model, field)
            filters.append(column.ilike(search_pattern))
    
    if filters:
        from sqlalchemy import or_
        return query.filter(or_(*filters))
    
    return query
