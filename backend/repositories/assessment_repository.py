"""Assessment & Performance Repository for CampusMIND 2.0.

Provides database access for Academic Assessments and AssessmentGrades.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import Assessment, AssessmentGrade, StudentProfile, CourseOffering


class AssessmentRepository:
    def create_assessment(self, db: Session, data: Dict[str, Any]) -> Assessment:
        """Creates a new academic assessment."""
        assessment = Assessment(
            id=data.get("id", f"asm_{uuid.uuid4().hex[:12]}"),
            title=data["title"],
            assessment_type=data["assessment_type"],
            max_marks=float(data["max_marks"]),
            weightage=float(data.get("weightage", 100.0)),
            assessment_date=data.get("assessment_date"),
            course_offering_id=data.get("course_offering_id"),
            course_id=data.get("course_id"),
            created_by_id=data["created_by_id"],
            status=data.get("status", "published"),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    def get_assessment_by_id(self, db: Session, assessment_id: str) -> Optional[Assessment]:
        """Retrieves an assessment by ID."""
        return db.query(Assessment).filter(Assessment.id == assessment_id).first()

    def list_assessments(
        self,
        db: Session,
        course_offering_id: Optional[str] = None,
        course_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Assessment]:
        """Lists academic assessments matching filters."""
        query = db.query(Assessment)
        if course_offering_id:
            query = query.filter(Assessment.course_offering_id == course_offering_id)
        if course_id:
            query = query.filter(Assessment.course_id == course_id)
        if status:
            query = query.filter(Assessment.status == status)
        return query.order_by(Assessment.created_at.desc()).offset(offset).limit(limit).all()

    def record_grade(self, db: Session, data: Dict[str, Any]) -> AssessmentGrade:
        """Creates or updates a student's assessment grade."""
        existing = db.query(AssessmentGrade).filter(
            AssessmentGrade.assessment_id == data["assessment_id"],
            AssessmentGrade.student_profile_id == data["student_profile_id"]
        ).first()

        if existing:
            existing.obtained_marks = float(data["obtained_marks"])
            existing.grade = data.get("grade", existing.grade)
            existing.feedback = data.get("feedback", existing.feedback)
            existing.evaluator_id = data.get("evaluator_id", existing.evaluator_id)
            db.commit()
            db.refresh(existing)
            return existing

        grade_rec = AssessmentGrade(
            id=data.get("id", f"grd_{uuid.uuid4().hex[:12]}"),
            assessment_id=data["assessment_id"],
            student_profile_id=data["student_profile_id"],
            obtained_marks=float(data["obtained_marks"]),
            grade=data.get("grade"),
            feedback=data.get("feedback"),
            evaluator_id=data.get("evaluator_id"),
        )
        db.add(grade_rec)
        db.commit()
        db.refresh(grade_rec)
        return grade_rec

    def get_student_grades(
        self,
        db: Session,
        student_profile_id: str,
        course_offering_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AssessmentGrade]:
        """Retrieves grades for a student."""
        query = db.query(AssessmentGrade).join(Assessment).filter(
            AssessmentGrade.student_profile_id == student_profile_id,
            Assessment.status == "published"
        )
        if course_offering_id:
            query = query.filter(Assessment.course_offering_id == course_offering_id)
        return query.order_by(Assessment.created_at.desc()).offset(offset).limit(limit).all()

    def get_assessment_grades(self, db: Session, assessment_id: str) -> List[AssessmentGrade]:
        """Retrieves all student grades for a specific assessment."""
        return db.query(AssessmentGrade).filter(AssessmentGrade.assessment_id == assessment_id).all()


assessment_repository = AssessmentRepository()
