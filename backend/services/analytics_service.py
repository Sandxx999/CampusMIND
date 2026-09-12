"""
Analytics Service Layer for CampusMIND 2.0.

Bridging API controllers, server-side authorization enforcement,
analytics engine calculations, and audit logging.
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.models import User, StudentProfile, FacultyProfile, CourseOffering
from models.schemas import UserSchema
from analytics.engine import analytics_engine
from repositories.audit_repository import audit_repository


class AnalyticsService:
    """Service handling authorization-guarded analytics execution."""

    # -------------------------------------------------------------------------
    # STUDENT ENDPOINTS HELPERS
    # -------------------------------------------------------------------------

    def _get_authenticated_student_profile(self, db: Session, user: UserSchema) -> StudentProfile:
        """Retrieves and validates the authenticated student's profile."""
        db_user = db.query(User).filter(User.username == user.username).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User identity record not found.",
            )

        sp = db.query(StudentProfile).filter(StudentProfile.user_id == db_user.id).first()
        if not sp:
            # Fallback by enrollment_no if present
            if user.enrollment_no:
                sp = db.query(StudentProfile).filter(StudentProfile.enrollment_no == user.enrollment_no).first()

        if not sp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student academic profile not found for authenticated user.",
            )

        return sp

    def get_student_me_summary(self, db: Session, user: UserSchema) -> Dict[str, Any]:
        """Returns comprehensive analytics summary for the authenticated student."""
        sp = self._get_authenticated_student_profile(db, user)
        res = analytics_engine.compute_student_summary(db, sp.id)

        audit_repository.log_audit_event(
            event_type="analytics_access_student",
            actor_username=user.username,
            details=f"Retrieved student analytics summary for enrollment {sp.enrollment_no}",
        )
        return res

    def get_student_me_attendance(self, db: Session, user: UserSchema) -> Dict[str, Any]:
        """Returns attendance analytics for the authenticated student."""
        sp = self._get_authenticated_student_profile(db, user)
        res = analytics_engine.compute_student_attendance(db, sp.id)

        audit_repository.log_audit_event(
            event_type="analytics_access_student_attendance",
            actor_username=user.username,
            details=f"Retrieved attendance analytics for enrollment {sp.enrollment_no}",
        )
        return res

    def get_student_me_performance(self, db: Session, user: UserSchema) -> Dict[str, Any]:
        """Returns performance analytics for the authenticated student."""
        sp = self._get_authenticated_student_profile(db, user)
        res = analytics_engine.compute_student_performance(db, sp.id)

        audit_repository.log_audit_event(
            event_type="analytics_access_student_performance",
            actor_username=user.username,
            details=f"Retrieved performance analytics for enrollment {sp.enrollment_no}",
        )
        return res

    def get_student_me_risk(self, db: Session, user: UserSchema) -> Dict[str, Any]:
        """Returns attendance risk analysis for the authenticated student."""
        sp = self._get_authenticated_student_profile(db, user)
        att_data = analytics_engine.compute_student_attendance(db, sp.id)

        audit_repository.log_audit_event(
            event_type="analytics_access_student_risk",
            actor_username=user.username,
            details=f"Retrieved risk analysis for enrollment {sp.enrollment_no}",
        )
        return att_data["risk_analysis"]

    def get_student_me_recommendations(self, db: Session, user: UserSchema) -> list:
        """Returns explainable recommendations for the authenticated student."""
        summary = self.get_student_me_summary(db, user)
        return summary.get("recommendations", [])

    # -------------------------------------------------------------------------
    # FACULTY ENDPOINTS HELPERS
    # -------------------------------------------------------------------------

    def _get_authenticated_faculty_profile(self, db: Session, user: UserSchema) -> FacultyProfile:
        """Retrieves and validates the authenticated faculty's profile."""
        if user.role not in ("faculty", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Faculty or Admin role required.",
            )

        db_user = db.query(User).filter(User.username == user.username).first()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User record not found.")

        fp = db.query(FacultyProfile).filter(FacultyProfile.user_id == db_user.id).first()
        if not fp and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Faculty profile record not found.",
            )
        return fp

    def get_faculty_offering_analytics(self, db: Session, offering_id: str, user: UserSchema) -> Dict[str, Any]:
        """Returns offering section analytics for authorized faculty member."""
        if user.role == "admin":
            # Admins can inspect any offering
            offering = db.query(CourseOffering).filter(CourseOffering.id == offering_id).first()
            if not offering:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course offering not found.")
            fac_profile_id = offering.faculty_profile_id or ""
        else:
            fp = self._get_authenticated_faculty_profile(db, user)
            fac_profile_id = fp.id
            offering = (
                db.query(CourseOffering)
                .filter(CourseOffering.id == offering_id, CourseOffering.faculty_profile_id == fp.id)
                .first()
            )
            if not offering:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not assigned to teach this course offering section.",
                )

        res = analytics_engine.compute_faculty_offering_analytics(db, offering_id, fac_profile_id)

        audit_repository.log_audit_event(
            event_type="analytics_access_faculty_offering",
            actor_username=user.username,
            details=f"Retrieved offering analytics for course offering {offering_id}",
        )
        return res

    # -------------------------------------------------------------------------
    # ADMIN ENDPOINTS HELPERS
    # -------------------------------------------------------------------------

    def _enforce_admin_authorization(self, user: UserSchema) -> None:
        """Verifies that authenticated user holds system admin role."""
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: System Admin authorization required.",
            )

    def get_admin_overview(self, db: Session, user: UserSchema) -> Dict[str, Any]:
        """Returns institutional overview analytics for administrators."""
        self._enforce_admin_authorization(user)
        res = analytics_engine.compute_admin_overview(db)

        audit_repository.log_audit_event(
            event_type="analytics_access_admin_overview",
            actor_username=user.username,
            details="Retrieved institutional admin analytics overview",
        )
        return res

    def get_admin_department_analytics(self, db: Session, department_id: str, user: UserSchema) -> Dict[str, Any]:
        """Returns department-level analytics for administrators."""
        self._enforce_admin_authorization(user)
        res = analytics_engine.compute_admin_department_analytics(db, department_id)
        if res.get("not_found"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

        audit_repository.log_audit_event(
            event_type="analytics_access_admin_department",
            actor_username=user.username,
            details=f"Retrieved admin analytics for department {department_id}",
        )
        return res

    def get_admin_program_analytics(self, db: Session, program_id: str, user: UserSchema) -> Dict[str, Any]:
        """Returns program-level analytics for administrators."""
        self._enforce_admin_authorization(user)
        res = analytics_engine.compute_admin_program_analytics(db, program_id)
        if res.get("not_found"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found.")

        audit_repository.log_audit_event(
            event_type="analytics_access_admin_program",
            actor_username=user.username,
            details=f"Retrieved admin analytics for program {program_id}",
        )
        return res


analytics_service = AnalyticsService()
