"""
Versioned API Router for Phase 6 Academic Audit & System Report Export.
"""
from fastapi import APIRouter, Depends
from auth.rbac import get_current_user, require_role
from models.schemas import ReportExportResponse, UserSchema
from services.export_service import export_service

router_v1 = APIRouter(prefix="/api/v1/export", tags=["Phase 6 Report Export"])


@router_v1.get("/student/me", response_model=ReportExportResponse)
def export_student_report(user: UserSchema = Depends(require_role(["student"]))):
    """Generates official academic audit report export for authenticated student."""
    return export_service.export_student_report(user)


@router_v1.get("/admin/overview", response_model=ReportExportResponse)
def export_admin_report(user: UserSchema = Depends(require_role(["admin"]))):
    """Generates institutional overview report export for admin."""
    return export_service.export_admin_report(user)
