"""Versioned API Router for Phase 7 Student Action Plans.

Mounted under /api/v1/plans
Provides creation and query endpoints for academic recovery action plans.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request
from auth.rbac import get_current_user
from models.schemas import (
    UserSchema,
    StudentActionPlanCreateRequest,
    StudentActionPlanResponse,
    StudentActionPlanListResponse,
)
from services.intervention_service import intervention_service

router_v1 = APIRouter(prefix="/api/v1/plans", tags=["Phase 7 Student Action Plans"])


@router_v1.post("", response_model=StudentActionPlanResponse)
def create_action_plan(
    body: StudentActionPlanCreateRequest,
    request: Request,
    student_profile_id: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user),
):
    """Creates a new student academic recovery action plan."""
    return intervention_service.create_action_plan(
        current_user=current_user,
        title=body.title,
        target_attendance_pct=body.target_attendance_pct,
        target_sgpa=body.target_sgpa,
        milestones=body.milestones,
        student_profile_id=student_profile_id,
        ip_address=request.client.host if request.client else None,
    )


@router_v1.get("", response_model=StudentActionPlanListResponse)
def list_action_plans(
    student_profile_id: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user),
):
    """Lists student recovery action plans scoped by student identity and ownership."""
    return intervention_service.list_action_plans(
        current_user=current_user,
        student_profile_id=student_profile_id,
    )
