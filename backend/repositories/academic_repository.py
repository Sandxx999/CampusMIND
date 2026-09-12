"""Academic Repository for CampusMIND 2.0.

Provides database access for AcademicTerms, CourseOfferings, and Enrollments.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import AcademicTerm, CourseOffering, Course, Enrollment, StudentProfile, FacultyProfile


class AcademicRepository:
    def get_current_term(self, db: Session) -> Optional[AcademicTerm]:
        """Retrieves the current active academic term."""
        return db.query(AcademicTerm).filter(AcademicTerm.is_current == True).first()

    def get_term_by_id(self, db: Session, term_id: str) -> Optional[AcademicTerm]:
        """Retrieves an academic term by ID."""
        return db.query(AcademicTerm).filter(AcademicTerm.id == term_id).first()

    def get_term_by_code(self, db: Session, code: str) -> Optional[AcademicTerm]:
        """Retrieves an academic term by code."""
        return db.query(AcademicTerm).filter(AcademicTerm.code == code).first()

    def list_terms(self, db: Session, limit: int = 50, offset: int = 0) -> List[AcademicTerm]:
        """Lists academic terms ordered by creation date."""
        return db.query(AcademicTerm).order_by(AcademicTerm.created_at.desc()).offset(offset).limit(limit).all()

    def create_term(self, db: Session, data: Dict[str, Any]) -> AcademicTerm:
        """Creates a new academic term. Resets other terms if is_current is True."""
        if data.get("is_current"):
            db.query(AcademicTerm).update({AcademicTerm.is_current: False})
        
        term = AcademicTerm(
            id=data.get("id", f"term_{uuid.uuid4().hex[:12]}"),
            code=data["code"],
            name=data["name"],
            academic_year=data["academic_year"],
            semester=data["semester"],
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            is_current=data.get("is_current", False),
        )
        db.add(term)
        db.commit()
        db.refresh(term)
        return term

    def get_offering_by_id(self, db: Session, offering_id: str) -> Optional[CourseOffering]:
        """Retrieves a course offering by ID with relationships preloaded."""
        return db.query(CourseOffering).filter(CourseOffering.id == offering_id).first()

    def list_offerings(
        self,
        db: Session,
        term_id: Optional[str] = None,
        department_id: Optional[str] = None,
        faculty_profile_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CourseOffering]:
        """Lists course offerings matching filters."""
        query = db.query(CourseOffering)
        if term_id:
            query = query.filter(CourseOffering.term_id == term_id)
        if faculty_profile_id:
            query = query.filter(CourseOffering.faculty_profile_id == faculty_profile_id)
        if department_id:
            query = query.join(Course).filter(Course.department_id == department_id)
        return query.order_by(CourseOffering.created_at.desc()).offset(offset).limit(limit).all()

    def count_offerings(
        self,
        db: Session,
        term_id: Optional[str] = None,
        department_id: Optional[str] = None,
        faculty_profile_id: Optional[str] = None,
    ) -> int:
        """Counts course offerings matching filters."""
        query = db.query(func.count(CourseOffering.id))
        if term_id:
            query = query.filter(CourseOffering.term_id == term_id)
        if faculty_profile_id:
            query = query.filter(CourseOffering.faculty_profile_id == faculty_profile_id)
        if department_id:
            query = query.join(Course).filter(Course.department_id == department_id)
        return query.scalar() or 0

    def create_offering(self, db: Session, data: Dict[str, Any]) -> CourseOffering:
        """Creates a new course offering."""
        offering = CourseOffering(
            id=data.get("id", f"offering_{uuid.uuid4().hex[:12]}"),
            course_id=data["course_id"],
            term_id=data["term_id"],
            faculty_profile_id=data.get("faculty_profile_id"),
            section=data.get("section", "A"),
            room=data.get("room"),
            schedule=data.get("schedule"),
            max_capacity=data.get("max_capacity", 60),
            status=data.get("status", "active"),
        )
        db.add(offering)
        db.commit()
        db.refresh(offering)
        return offering

    def get_student_enrollments(self, db: Session, student_profile_id: str) -> List[Enrollment]:
        """Retrieves enrollments for a specific student."""
        return db.query(Enrollment).filter(Enrollment.student_profile_id == student_profile_id).all()


academic_repository = AcademicRepository()
