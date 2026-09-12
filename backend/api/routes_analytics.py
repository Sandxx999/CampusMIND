"""
Versioned API Router for Phase 5 Academic Analytics.

Mounted under /api/v1/analytics
Provides student, faculty, and admin academic intelligence endpoints.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from auth.rbac import get_current_user
from models.schemas import (

    UserSchema,
    StudentAnalyticsSummaryResponse,
    StudentAttendanceAnalyticsResponse,
    StudentPerformanceAnalyticsResponse,
    AttendanceRiskSchema,
    RecommendationSchema,
    FacultyOfferingAnalyticsResponse,
    AdminOverviewAnalyticsResponse,
    AdminDepartmentAnalyticsResponse,
    AdminProgramAnalyticsResponse,
)
from services.analytics_service import analytics_service

router_v1 = APIRouter(prefix="/api/v1/analytics", tags=["Phase 5 Academic Analytics"])


# -----------------------------------------------------------------------------
# STUDENT ANALYTICS ENDPOINTS
# -----------------------------------------------------------------------------

@router_v1.get("/student/me", response_model=StudentAnalyticsSummaryResponse)
def get_student_me_analytics(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves overall academic analytics summary for the authenticated student."""
    return analytics_service.get_student_me_summary(db, current_user)


@router_v1.get("/student/me/attendance", response_model=StudentAttendanceAnalyticsResponse)
def get_student_me_attendance(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves course-wise attendance breakdown and trend for the authenticated student."""
    return analytics_service.get_student_me_attendance(db, current_user)


@router_v1.get("/student/me/performance", response_model=StudentPerformanceAnalyticsResponse)
def get_student_me_performance(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves assessment and grade performance analytics for the authenticated student."""
    return analytics_service.get_student_me_performance(db, current_user)


@router_v1.get("/student/me/risk", response_model=AttendanceRiskSchema)
def get_student_me_risk(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves attendance risk analysis and recovery formula for the authenticated student."""
    return analytics_service.get_student_me_risk(db, current_user)


@router_v1.get("/student/me/recommendations", response_model=List[RecommendationSchema])
def get_student_me_recommendations(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves explainable rule-based academic recommendations for the authenticated student."""
    return analytics_service.get_student_me_recommendations(db, current_user)


# -----------------------------------------------------------------------------
# FACULTY ANALYTICS ENDPOINTS
# -----------------------------------------------------------------------------

@router_v1.get("/faculty/offerings/{offering_id}", response_model=FacultyOfferingAnalyticsResponse)
def get_faculty_offering_analytics(
    offering_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves aggregated section performance & attendance distribution for authorized faculty."""
    return analytics_service.get_faculty_offering_analytics(db, offering_id, current_user)


@router_v1.get("/faculty/offerings/{offering_id}/attendance")
def get_faculty_offering_attendance(
    offering_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves section attendance metrics and at-risk student list for authorized faculty."""
    data = analytics_service.get_faculty_offering_analytics(db, offering_id, current_user)
    return {
        "offering_id": data["offering_id"],
        "average_attendance_pct": data["average_attendance_pct"],
        "attendance_distribution": data["attendance_distribution"],
        "students_requiring_attention": data["students_requiring_attention"],
    }


@router_v1.get("/faculty/offerings/{offering_id}/performance")
def get_faculty_offering_performance(
    offering_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves section assessment average breakdown for authorized faculty."""
    data = analytics_service.get_faculty_offering_analytics(db, offering_id, current_user)
    return {
        "offering_id": data["offering_id"],
        "average_assessment_pct": data["average_assessment_pct"],
        "assessments": data["assessments"],
    }


# -----------------------------------------------------------------------------
# ADMIN ANALYTICS ENDPOINTS
# -----------------------------------------------------------------------------

@router_v1.get("/admin/overview", response_model=AdminOverviewAnalyticsResponse)
def get_admin_overview_analytics(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves institution-wide administrative overview analytics."""
    return analytics_service.get_admin_overview(db, current_user)


@router_v1.get("/admin/departments/{department_id}", response_model=AdminDepartmentAnalyticsResponse)
def get_admin_department_analytics(
    department_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves department-level aggregated academic analytics for administrators."""
    return analytics_service.get_admin_department_analytics(db, department_id, current_user)


@router_v1.get("/admin/programs/{program_id}", response_model=AdminProgramAnalyticsResponse)
def get_admin_program_analytics(
    program_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves program-level aggregated academic analytics for administrators."""
    return analytics_service.get_admin_program_analytics(db, program_id, current_user)
