from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from auth.rbac import require_role
from db.session import get_db
from models.schemas import (
    UserSchema,
    InstitutionOverviewResponse,
    TrendData,
    InstitutionRiskSummaryResponse,
    InstitutionInterventionsSummaryResponse,
    DecisionSupportResponse
)
from services.institution_service import institution_service

router_v1 = APIRouter(prefix="/api/v1/institution", tags=["Institutional Intelligence"])

@router_v1.get("/overview", response_model=InstitutionOverviewResponse)
def get_institution_overview(
    current_user: UserSchema = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
    academic_year: str = Query(None),
    semester: int = Query(None)
):
    """Retrieves institution-level overview (Phase 10)."""
    return institution_service.get_overview(db, current_user, academic_year, semester)

@router_v1.get("/attendance-trends", response_model=List[TrendData])
def get_attendance_trends(
    current_user: UserSchema = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
    department_id: str = Query(None),
    academic_year: str = Query(None)
):
    """Retrieves institution attendance trends (Phase 10)."""
    return institution_service.get_attendance_trends(db, current_user, department_id, academic_year)

@router_v1.get("/performance-trends", response_model=List[TrendData])
def get_performance_trends(
    current_user: UserSchema = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
    department_id: str = Query(None),
    academic_year: str = Query(None)
):
    """Retrieves institution performance trends (Phase 10)."""
    return institution_service.get_performance_trends(db, current_user, department_id, academic_year)

@router_v1.get("/risk-summary", response_model=InstitutionRiskSummaryResponse)
def get_risk_summary(
    current_user: UserSchema = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
    department_id: str = Query(None)
):
    """Retrieves institutional academic risk summary (Phase 10)."""
    return institution_service.get_risk_summary(db, current_user, department_id)

@router_v1.get("/interventions-summary", response_model=InstitutionInterventionsSummaryResponse)
def get_interventions_summary(
    current_user: UserSchema = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
    department_id: str = Query(None)
):
    """Retrieves institutional intervention and action plan summary (Phase 10)."""
    return institution_service.get_interventions_summary(db, current_user, department_id)

@router_v1.get("/department-performance", response_model=List[TrendData])
def get_department_performance(
    current_user: UserSchema = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Retrieves institutional department performance comparison (Phase 10)."""
    return institution_service.get_department_performance(db, current_user)

@router_v1.get("/decision-support", response_model=DecisionSupportResponse)
def get_decision_support(
    current_user: UserSchema = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
    department_id: str = Query(None)
):
    """Retrieves institutional decision support and early-warning intelligence (Phase 11)."""
    return institution_service.get_decision_support(db, current_user, department_id)
