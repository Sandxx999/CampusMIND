"""Academic API Routes for CampusMIND 2.0.

Exposes endpoints for academic terms, course offerings, and enrollments under /api/v1/academics.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from auth.rbac import get_current_user, require_role
from models.schemas import (
    AcademicTermSchema,
    AcademicTermCreateRequest,
    CourseOfferingListResponse,
    UserSchema,
)
from services.academic_service import academic_service

router_v1 = APIRouter(prefix="/api/v1/academics", tags=["Academic Management"])


@router_v1.get("/terms/current")
def get_current_term(user: UserSchema = Depends(get_current_user)):
    """Retrieves current active academic term."""
    return academic_service.get_current_term()


@router_v1.get("/terms")
def list_terms(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user),
):
    """Lists academic terms."""
    return academic_service.list_terms(limit=limit, offset=offset)


@router_v1.post("/terms")
def create_term(
    req: AcademicTermCreateRequest,
    user: UserSchema = Depends(require_role(["admin"])),
):
    """Creates a new academic term. Admin only."""
    return academic_service.create_term(user, req.model_dump())


@router_v1.get("/offerings", response_model=CourseOfferingListResponse)
def list_course_offerings(
    term_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user),
):
    """Lists course offerings for active terms or departments."""
    return academic_service.list_course_offerings(
        user=user,
        term_id=term_id,
        department_id=department_id,
        limit=limit,
        offset=offset,
    )
