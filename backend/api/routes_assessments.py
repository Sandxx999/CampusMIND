"""Assessment API Routes for CampusMIND 2.0.

Exposes endpoints for academic assessments, grade submissions, and result views under /api/v1/assessments.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from auth.rbac import get_current_user, require_role
from models.schemas import (
    AssessmentCreateRequest,
    AssessmentSchema,
    GradeBulkCreateRequest,
    StudentAssessmentResultsResponse,
    UserSchema,
)
from services.assessment_service import assessment_service

router_v1 = APIRouter(prefix="/api/v1/assessments", tags=["Assessment & Performance"])


@router_v1.post("", response_model=AssessmentSchema)
def create_assessment(
    req: AssessmentCreateRequest,
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """Creates a new academic assessment. Restricted to Faculty and Admin."""
    return assessment_service.create_assessment(user, req.model_dump())


@router_v1.post("/{assessment_id}/grades")
def record_grades(
    assessment_id: str,
    req: GradeBulkCreateRequest,
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """
    Submits or updates student grades for an assessment.
    Validates obtained_marks boundary: 0 <= obtained_marks <= max_marks.
    """
    return assessment_service.record_grades(
        user=user,
        assessment_id=assessment_id,
        grades_data=[g.model_dump() for g in req.grades],
    )


@router_v1.get("/student/{enrollment_no}", response_model=StudentAssessmentResultsResponse)
def get_student_results(
    enrollment_no: str,
    offering_id: Optional[str] = Query(None),
    user: UserSchema = Depends(get_current_user),
):
    """
    Retrieves student academic assessment results.
    Students can ONLY access their own academic results.
    """
    return assessment_service.get_student_results(
        user=user,
        enrollment_no=enrollment_no,
        offering_id=offering_id,
    )
