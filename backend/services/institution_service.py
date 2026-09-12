from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models.schemas import UserSchema
from analytics.institution_engine import institution_engine
from repositories.audit_repository import audit_repository
from fastapi import HTTPException, status

class InstitutionService:
    def _enforce_admin(self, user: UserSchema):
        if user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: System Admin authorization required.")

    def get_overview(self, db: Session, user: UserSchema, academic_year: str, semester: int) -> Dict[str, Any]:
        self._enforce_admin(user)
        res = institution_engine.compute_overview(db, academic_year, semester)
        audit_repository.log_audit_event(
            event_type="analytics_access_institution_overview",
            actor_username=user.username,
            details="Retrieved institution overview"
        )
        return res

    def get_attendance_trends(self, db: Session, user: UserSchema, department_id: str, academic_year: str) -> List[Dict[str, Any]]:
        self._enforce_admin(user)
        res = institution_engine.compute_attendance_trends(db, department_id, academic_year)
        audit_repository.log_audit_event(
            event_type="analytics_access_institution_attendance",
            actor_username=user.username,
            details="Retrieved institution attendance trends"
        )
        return res

    def get_performance_trends(self, db: Session, user: UserSchema, department_id: str, academic_year: str) -> List[Dict[str, Any]]:
        self._enforce_admin(user)
        res = institution_engine.compute_performance_trends(db, department_id, academic_year)
        audit_repository.log_audit_event(
            event_type="analytics_access_institution_performance",
            actor_username=user.username,
            details="Retrieved institution performance trends"
        )
        return res

    def get_risk_summary(self, db: Session, user: UserSchema, department_id: str) -> Dict[str, Any]:
        self._enforce_admin(user)
        res = institution_engine.compute_risk_summary(db, department_id)
        audit_repository.log_audit_event(
            event_type="analytics_access_institution_risk",
            actor_username=user.username,
            details="Retrieved institution risk summary"
        )
        return res

    def get_interventions_summary(self, db: Session, user: UserSchema, department_id: str) -> Dict[str, Any]:
        self._enforce_admin(user)
        res = institution_engine.compute_interventions_summary(db, department_id)
        audit_repository.log_audit_event(
            event_type="analytics_access_institution_interventions",
            actor_username=user.username,
            details="Retrieved institution interventions summary"
        )
        return res

    def get_department_performance(self, db: Session, user: UserSchema) -> List[Dict[str, Any]]:
        self._enforce_admin(user)
        res = institution_engine.compute_department_performance(db)
        audit_repository.log_audit_event(
            event_type="analytics_access_institution_departments",
            actor_username=user.username,
            details="Retrieved institution department performance"
        )
        return res

    def get_decision_support(self, db: Session, user: UserSchema, department_id: str = None) -> Dict[str, Any]:
        self._enforce_admin(user)
        res = institution_engine.compute_decision_support(db, department_id)
        audit_repository.log_audit_event(
            event_type="analytics_access_decision_support",
            actor_username=user.username,
            details="Retrieved decision support and early-warning intelligence"
        )
        return res

institution_service = InstitutionService()
