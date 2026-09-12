"""Academic Service for CampusMIND 2.0.

Implements business logic for managing academic terms, course offerings, and student enrollments.
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from models.schemas import UserSchema
from repositories.academic_repository import academic_repository


class AcademicService:
    def get_current_term(self) -> Dict[str, Any]:
        """Returns details of the active academic term."""
        with get_db_session() as session:
            term = academic_repository.get_current_term(session)
            if not term:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No current active academic term found."
                )
            return {
                "id": term.id,
                "code": term.code,
                "name": term.name,
                "academic_year": term.academic_year,
                "semester": term.semester,
                "is_current": term.is_current,
            }

    def list_terms(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Lists all academic terms."""
        with get_db_session() as session:
            terms = academic_repository.list_terms(session, limit=limit, offset=offset)
            return {
                "total": len(terms),
                "terms": [
                    {
                        "id": t.id,
                        "code": t.code,
                        "name": t.name,
                        "academic_year": t.academic_year,
                        "semester": t.semester,
                        "is_current": t.is_current,
                    }
                    for t in terms
                ]
            }

    def create_term(self, user: UserSchema, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new academic term. Requires admin role."""
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create academic terms."
            )
        with get_db_session() as session:
            term = academic_repository.create_term(session, data)
            return {
                "id": term.id,
                "code": term.code,
                "name": term.name,
                "academic_year": term.academic_year,
                "semester": term.semester,
                "is_current": term.is_current,
            }

    def list_course_offerings(
        self,
        user: UserSchema,
        term_id: Optional[str] = None,
        department_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Lists course offerings."""
        with get_db_session() as session:
            faculty_profile_id = None
            if user.role == "faculty":
                from db.models import User as UserModel
                usr = session.query(UserModel).filter(UserModel.username == user.username).first()
                if usr and usr.faculty_profile:
                    faculty_profile_id = usr.faculty_profile.id

            offerings = academic_repository.list_offerings(
                session,
                term_id=term_id,
                department_id=department_id,
                faculty_profile_id=faculty_profile_id if user.role == "faculty" else None,
                limit=limit,
                offset=offset,
            )
            total = academic_repository.count_offerings(
                session,
                term_id=term_id,
                department_id=department_id,
                faculty_profile_id=faculty_profile_id if user.role == "faculty" else None,
            )

            results = []
            for o in offerings:
                results.append({
                    "id": o.id,
                    "course_id": o.course_id,
                    "course_code": o.course.code if o.course else None,
                    "course_title": o.course.title if o.course else None,
                    "term_id": o.term_id,
                    "term_code": o.term.code if o.term else None,
                    "section": o.section,
                    "room": o.room,
                    "schedule": o.schedule,
                    "max_capacity": o.max_capacity,
                    "faculty_name": o.faculty_profile.user.display_name if o.faculty_profile and o.faculty_profile.user else None,
                    "status": o.status,
                })

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "offerings": results,
            }


academic_service = AcademicService()
