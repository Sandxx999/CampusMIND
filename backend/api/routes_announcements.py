"""Announcements API Routes for CampusMIND 2.0.

Exposes endpoints for institutional announcements and feed management under /api/v1/announcements.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from auth.rbac import get_current_user, require_role
from models.schemas import (
    AnnouncementCreateRequest,
    AnnouncementSchema,
    AnnouncementListResponse,
    UserSchema,
)
from services.announcement_service import announcement_service

router_v1 = APIRouter(prefix="/api/v1/announcements", tags=["Institutional Announcements"])


@router_v1.get("", response_model=AnnouncementListResponse)
def list_announcements(
    department_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user),
):
    """
    Lists institutional announcements targeted for the user's role and department.
    """
    return announcement_service.list_announcements(
        user=user,
        department_id=department_id,
        limit=limit,
        offset=offset,
    )


@router_v1.post("", response_model=AnnouncementSchema)
def create_announcement(
    req: AnnouncementCreateRequest,
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """
    Creates a new institutional announcement.
    Forbidden for students.
    """
    return announcement_service.create_announcement(user, req.model_dump())
