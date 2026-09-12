"""Versioned API Router for Phase 7 Academic Interventions.

Mounted under /api/v1/interventions
Provides intervention issuance, status tracking, and query endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request
from auth.rbac import get_current_user, require_role
from models.schemas import (
    UserSchema,
    AcademicInterventionCreateRequest,
    AcademicInterventionUpdateRequest,
    AcademicInterventionResponse,
    AcademicInterventionListResponse,
)
from services.intervention_service import intervention_service

router_v1 = APIRouter(prefix="/api/v1/interventions", tags=["Phase 7 Academic Interventions"])


@router_v1.post("", response_model=AcademicInterventionResponse)
def create_intervention(
    body: AcademicInterventionCreateRequest,
    request: Request,
    current_user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """Issues an academic intervention notice for an at-risk student."""
    return intervention_service.create_intervention(
        current_user=current_user,
        student_profile_id=body.student_profile_id,
        risk_category=body.risk_category,
        title=body.title,
        description=body.description,
        recommended_action=body.recommended_action,
        ip_address=request.client.host if request.client else None,
    )


@router_v1.get("", response_model=AcademicInterventionListResponse)
def list_interventions(
    student_profile_id: Optional[str] = None,
    risk_category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user),
):
    """Lists academic interventions filtered by student ownership and role boundaries."""
    return intervention_service.list_interventions(
        current_user=current_user,
        student_profile_id=student_profile_id,
        risk_category=risk_category,
        status_filter=status,
    )


@router_v1.patch("/{intervention_id}", response_model=AcademicInterventionResponse)
def update_intervention(
    intervention_id: str,
    body: AcademicInterventionUpdateRequest,
    request: Request,
    current_user: UserSchema = Depends(get_current_user),
):
    """Updates the status and resolution notes of an academic intervention notice."""
    return intervention_service.update_intervention(
        current_user=current_user,
        intervention_id=intervention_id,
        status_val=body.status,
        resolution_notes=body.resolution_notes,
        ip_address=request.client.host if request.client else None,
    )
