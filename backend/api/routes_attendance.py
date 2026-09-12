"""Attendance API Routes for CampusMIND 2.0.

Exposes endpoints for student session attendance retrieval and faculty marking under /api/v1/attendance.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from auth.rbac import get_current_user, require_role
from models.schemas import (
    AttendanceResponse,
    AttendanceBulkCreateRequest,
    UserSchema,
)
from services.attendance_service import attendance_service

router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["Attendance Management"])


@router_v1.get("/student/{enrollment_no}", response_model=AttendanceResponse)
def get_student_attendance(
    enrollment_no: str,
    offering_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user),
):
    """
    Retrieves student attendance summary and session logs.
    Students can only view their own attendance records.
    """
    return attendance_service.get_student_attendance(
        user=user,
        enrollment_no=enrollment_no,
        offering_id=offering_id,
        limit=limit,
        offset=offset,
    )


@router_v1.post("/offering/{offering_id}")
def record_offering_attendance(
    offering_id: str,
    req: AttendanceBulkCreateRequest,
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """
    Records or updates attendance entries for a course offering.
    Restricted to Faculty and Admin users.
    """
    return attendance_service.record_attendance(
        user=user,
        offering_id=offering_id,
        records_data=[r.model_dump() for r in req.records],
    )
