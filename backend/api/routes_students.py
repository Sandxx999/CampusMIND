from typing import Optional
from fastapi import APIRouter, Depends, Query
from auth.rbac import get_current_user, require_role
from models.schemas import StudentListResponse, StudentSchema, StudentStatsSummary, UserSchema
from services.student_service import student_service

router = APIRouter(prefix="/api/students", tags=["Student Management"])
router_v1 = APIRouter(prefix="/api/v1/students", tags=["Student Management"])


@router.get("", response_model=StudentListResponse)
@router_v1.get("", response_model=StudentListResponse)
def list_students(
    query: Optional[str] = Query(None, description="Search by name, enrollment number, or mobile number"),
    branch: Optional[str] = Query(None, description="Filter by branch / department"),
    year: Optional[int] = Query(None, description="Filter by academic year (1-4)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user),
):
    """
    Search and filter student records with pagination for faculty/admin users.
    Student users receive their own record only.
    """
    return student_service.list_students(
        user=user, query=query, branch=branch, year=year, limit=limit, offset=offset
    )


@router.get("/stats/summary", response_model=StudentStatsSummary)
@router_v1.get("/stats/summary", response_model=StudentStatsSummary)
def get_student_stats(user: UserSchema = Depends(require_role(["faculty", "admin"]))):
    """
    Aggregates student analytics including average CGPA, attendance, branch distribution, and fee status breakdown.
    """
    return student_service.get_student_stats()


@router.get("/{enrollment_no}", response_model=StudentSchema)
@router_v1.get("/{enrollment_no}", response_model=StudentSchema)
def get_student_by_enrollment(enrollment_no: str, user: UserSchema = Depends(get_current_user)):
    """
    Retrieves detailed academic profile and contact details for a specific student by Enrollment Number.
    """
    return student_service.get_student_by_enrollment(user=user, enrollment_no=enrollment_no)
