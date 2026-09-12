"""Unified Search API Routes for CampusMIND 2.0.

Exposes authorization-filtered unified institutional search under /api/v1/search.
"""
from fastapi import APIRouter, Depends, Query
from auth.rbac import get_current_user
from models.schemas import UnifiedSearchResponse, UserSchema
from services.search_service import search_service

router_v1 = APIRouter(prefix="/api/v1/search", tags=["Institutional Search"])


@router_v1.get("", response_model=UnifiedSearchResponse)
def search_institutional_records(
    q: str = Query(..., min_length=2, description="Search query string"),
    limit: int = Query(5, ge=1, le=20, description="Results per entity category"),
    user: UserSchema = Depends(get_current_user),
):
    """
    Executes unified search across courses, announcements, campus events, and documents.
    Results are automatically filtered for server-side role and audience authorization.
    """
    return search_service.search_institutional_records(
        user=user,
        query=q,
        limit_per_category=limit,
    )
