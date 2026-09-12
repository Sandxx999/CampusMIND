"""Academic Intervention, Recovery Action Plan, and Notification Dispatch Service for CampusMIND 2.0.

Provides authorization-enforced workflows for managing academic interventions,
student recovery action plans, and user notifications.
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from db.models import (
    User,
    StudentProfile,
    AcademicIntervention,
    StudentActionPlan,
    NotificationAlert,
    utc_now,
)
from models.schemas import UserSchema
from repositories.audit_repository import audit_repository


class InterventionService:
    """Service handling academic interventions, action plans, and notifications."""

    def create_intervention(
        self,
        current_user: UserSchema,
        student_profile_id: str,
        risk_category: str,
        title: str,
        description: str,
        recommended_action: str,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates an academic intervention notice for an at-risk student.
        Restricted to Faculty and Admin roles.
        """
        if current_user.role not in {"faculty", "admin"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Only faculty and admin roles can issue academic interventions.",
            )

        with get_db_session() as session:
            student = session.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student profile '{student_profile_id}' not found.",
                )

            issuer = session.query(User).filter(User.username == current_user.username).first()
            if not issuer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Issuer user '{current_user.username}' not found.",
                )

            intervention_id = str(uuid.uuid4())
            intervention = AcademicIntervention(
                id=intervention_id,
                student_profile_id=student_profile_id,
                issued_by_id=issuer.id,
                risk_category=risk_category.strip().lower(),
                title=title.strip(),
                description=description.strip(),
                recommended_action=recommended_action.strip(),
                status="pending",
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            session.add(intervention)

            # Auto-generate notification alert for student
            notification_id = str(uuid.uuid4())
            notification = NotificationAlert(
                id=notification_id,
                user_id=student.user_id,
                category="academic",
                severity="critical" if risk_category in {"attendance", "performance"} else "warning",
                title=f"Academic Intervention: {title}",
                message=f"An academic intervention notice has been issued by {issuer.display_name}. Action required.",
                is_read=False,
                link="/analytics",
                created_at=utc_now(),
            )
            session.add(notification)
            session.commit()

            audit_repository.log_audit_event(
                event_type="INTERVENTION_CREATED",
                actor_username=current_user.username,
                user_id=issuer.id,
                ip_address=ip_address,
                details=json.dumps({
                    "intervention_id": intervention_id,
                    "student_profile_id": student_profile_id,
                    "risk_category": risk_category,
                }),
            )

            return {
                "id": intervention.id,
                "student_profile_id": intervention.student_profile_id,
                "enrollment_no": student.enrollment_no,
                "student_name": student.user.display_name if student.user else student.enrollment_no,
                "issued_by_id": intervention.issued_by_id,
                "issued_by_name": issuer.display_name,
                "risk_category": intervention.risk_category,
                "title": intervention.title,
                "description": intervention.description,
                "recommended_action": intervention.recommended_action,
                "status": intervention.status,
                "resolution_notes": intervention.resolution_notes,
                "created_at": intervention.created_at.isoformat(),
                "updated_at": intervention.updated_at.isoformat(),
            }

    def update_intervention(
        self,
        current_user: UserSchema,
        intervention_id: str,
        status_val: str,
        resolution_notes: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates the status and resolution notes of an academic intervention notice.
        Students can update status to 'acknowledged' for their own intervention.
        Faculty and Admin can update to any status including 'resolved'.
        """
        with get_db_session() as session:
            db_user = session.query(User).filter(User.username == current_user.username).first()
            intervention = session.query(AcademicIntervention).filter(AcademicIntervention.id == intervention_id).first()
            if not intervention:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Academic intervention '{intervention_id}' not found.",
                )

            student_profile = session.query(StudentProfile).filter(StudentProfile.id == intervention.student_profile_id).first()
            if not student_profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

            # Authorization Check
            if current_user.role == "student":
                is_owner = (
                    (db_user and student_profile.user_id == db_user.id)
                    or (current_user.enrollment_no and student_profile.enrollment_no.casefold() == current_user.enrollment_no.casefold())
                )
                if not is_owner:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. Students can only update their own intervention notices.",
                    )
                if status_val.lower() not in {"acknowledged"}:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Students can only transition intervention status to 'acknowledged'.",
                    )

            intervention.status = status_val.lower()
            if resolution_notes:
                intervention.resolution_notes = resolution_notes.strip()
            intervention.updated_at = utc_now()
            session.commit()

            audit_repository.log_audit_event(
                event_type="INTERVENTION_UPDATED",
                actor_username=current_user.username,
                user_id=db_user.id if db_user else None,
                ip_address=ip_address,
                details=json.dumps({
                    "intervention_id": intervention_id,
                    "new_status": intervention.status,
                }),
            )

            return {
                "id": intervention.id,
                "student_profile_id": intervention.student_profile_id,
                "enrollment_no": student_profile.enrollment_no,
                "student_name": student_profile.user.display_name if student_profile.user else student_profile.enrollment_no,
                "issued_by_id": intervention.issued_by_id,
                "issued_by_name": intervention.issued_by.display_name if intervention.issued_by else "Advisor",
                "risk_category": intervention.risk_category,
                "title": intervention.title,
                "description": intervention.description,
                "recommended_action": intervention.recommended_action,
                "status": intervention.status,
                "resolution_notes": intervention.resolution_notes,
                "created_at": intervention.created_at.isoformat(),
                "updated_at": intervention.updated_at.isoformat(),
            }

    def list_interventions(
        self,
        current_user: UserSchema,
        student_profile_id: Optional[str] = None,
        risk_category: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Lists academic interventions based on role boundaries.
        Students only see interventions issued to them.
        Faculty/Admin see filtered interventions across students.
        """
        with get_db_session() as session:
            query = session.query(AcademicIntervention)
            db_user = session.query(User).filter(User.username == current_user.username).first()

            if current_user.role == "student":
                filters = []
                if db_user:
                    filters.append(StudentProfile.user_id == db_user.id)
                if current_user.enrollment_no:
                    filters.append(StudentProfile.enrollment_no == current_user.enrollment_no)

                if not filters:
                    return {"total": 0, "interventions": []}

                student_profile = session.query(StudentProfile).filter(filters[0] if len(filters) == 1 else (filters[0] | filters[1])).first()
                if not student_profile:
                    return {"total": 0, "interventions": []}
                query = query.filter(AcademicIntervention.student_profile_id == student_profile.id)
            elif student_profile_id:
                query = query.filter(AcademicIntervention.student_profile_id == student_profile_id)

            if risk_category:
                query = query.filter(AcademicIntervention.risk_category == risk_category.strip().lower())
            if status_filter:
                query = query.filter(AcademicIntervention.status == status_filter.strip().lower())

            interventions = query.order_by(AcademicIntervention.created_at.desc()).all()

            results = []
            for item in interventions:
                sp = item.student_profile
                results.append({
                    "id": item.id,
                    "student_profile_id": item.student_profile_id,
                    "enrollment_no": sp.enrollment_no if sp else "N/A",
                    "student_name": sp.user.display_name if sp and sp.user else "Student",
                    "issued_by_id": item.issued_by_id,
                    "issued_by_name": item.issued_by.display_name if item.issued_by else "Advisor",
                    "risk_category": item.risk_category,
                    "title": item.title,
                    "description": item.description,
                    "recommended_action": item.recommended_action,
                    "status": item.status,
                    "resolution_notes": item.resolution_notes,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                })

            return {"total": len(results), "interventions": results}

    def create_action_plan(
        self,
        current_user: UserSchema,
        title: str,
        target_attendance_pct: Optional[float],
        target_sgpa: Optional[float],
        milestones: List[str],
        student_profile_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a student recovery action plan."""
        with get_db_session() as session:
            db_user = session.query(User).filter(User.username == current_user.username).first()

            if current_user.role == "student":
                filters = []
                if db_user:
                    filters.append(StudentProfile.user_id == db_user.id)
                if current_user.enrollment_no:
                    filters.append(StudentProfile.enrollment_no == current_user.enrollment_no)
                student = session.query(StudentProfile).filter(filters[0] if len(filters) == 1 else (filters[0] | filters[1])).first()
            else:
                if not student_profile_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="student_profile_id required for non-student creation.",
                    )
                student = session.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()

            if not student:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

            plan_id = str(uuid.uuid4())
            plan = StudentActionPlan(
                id=plan_id,
                student_profile_id=student.id,
                title=title.strip(),
                target_attendance_pct=target_attendance_pct,
                target_sgpa=target_sgpa,
                milestones=json.dumps(milestones),
                status="active",
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            session.add(plan)
            session.commit()

            audit_repository.log_audit_event(
                event_type="ACTION_PLAN_CREATED",
                actor_username=current_user.username,
                user_id=db_user.id if db_user else None,
                ip_address=ip_address,
                details=json.dumps({"plan_id": plan_id, "student_profile_id": student.id}),
            )

            return {
                "id": plan.id,
                "student_profile_id": plan.student_profile_id,
                "enrollment_no": student.enrollment_no,
                "title": plan.title,
                "target_attendance_pct": plan.target_attendance_pct,
                "target_sgpa": plan.target_sgpa,
                "milestones": json.loads(plan.milestones),
                "status": plan.status,
                "created_at": plan.created_at.isoformat(),
                "updated_at": plan.updated_at.isoformat(),
            }

    def list_action_plans(
        self,
        current_user: UserSchema,
        student_profile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Lists student recovery action plans scoped by student identity and ownership."""
        with get_db_session() as session:
            query = session.query(StudentActionPlan)
            db_user = session.query(User).filter(User.username == current_user.username).first()

            if current_user.role == "student":
                filters = []
                if db_user:
                    filters.append(StudentProfile.user_id == db_user.id)
                if current_user.enrollment_no:
                    filters.append(StudentProfile.enrollment_no == current_user.enrollment_no)
                if not filters:
                    return {"total": 0, "plans": []}
                student = session.query(StudentProfile).filter(filters[0] if len(filters) == 1 else (filters[0] | filters[1])).first()
                if not student:
                    return {"total": 0, "plans": []}
                query = query.filter(StudentActionPlan.student_profile_id == student.id)
            elif student_profile_id:
                query = query.filter(StudentActionPlan.student_profile_id == student_profile_id)

            plans = query.order_by(StudentActionPlan.created_at.desc()).all()
            results = []
            for item in plans:
                sp = item.student_profile
                results.append({
                    "id": item.id,
                    "student_profile_id": item.student_profile_id,
                    "enrollment_no": sp.enrollment_no if sp else "N/A",
                    "title": item.title,
                    "target_attendance_pct": item.target_attendance_pct,
                    "target_sgpa": item.target_sgpa,
                    "milestones": json.loads(item.milestones) if item.milestones else [],
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                })

            return {"total": len(results), "plans": results}

    def list_notifications(
        self,
        current_user: UserSchema,
        unread_only: bool = False,
    ) -> Dict[str, Any]:
        """Lists user notification alerts."""
        with get_db_session() as session:
            user = session.query(User).filter(User.username == current_user.username).first()
            if not user:
                return {"unread_count": 0, "total": 0, "notifications": []}

            query = session.query(NotificationAlert).filter(NotificationAlert.user_id == user.id)
            if unread_only:
                query = query.filter(NotificationAlert.is_read == False)

            alerts = query.order_by(NotificationAlert.created_at.desc()).all()
            unread_count = session.query(NotificationAlert).filter(
                NotificationAlert.user_id == user.id,
                NotificationAlert.is_read == False,
            ).count()

            results = [
                {
                    "id": a.id,
                    "user_id": a.user_id,
                    "category": a.category,
                    "severity": a.severity,
                    "title": a.title,
                    "message": a.message,
                    "is_read": a.is_read,
                    "link": a.link,
                    "created_at": a.created_at.isoformat(),
                }
                for a in alerts
            ]

            return {
                "unread_count": unread_count,
                "total": len(results),
                "notifications": results,
            }

    def mark_notifications_read(
        self,
        current_user: UserSchema,
        notification_ids: List[str],
    ) -> Dict[str, Any]:
        """Marks user notification alerts as read."""
        with get_db_session() as session:
            user = session.query(User).filter(User.username == current_user.username).first()
            if not user:
                return {"updated": 0}

            query = session.query(NotificationAlert).filter(
                NotificationAlert.user_id == user.id,
                NotificationAlert.id.in_(notification_ids),
            )
            alerts = query.all()
            for a in alerts:
                a.is_read = True
            session.commit()
            return {"updated": len(alerts)}


intervention_service = InterventionService()
