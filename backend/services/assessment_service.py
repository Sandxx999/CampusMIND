"""Assessment & Performance Service for CampusMIND 2.0.

Implements business logic and validation for academic assessments, grade entry, and student performance retrieval.
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from db.models import User, StudentProfile, CourseOffering, Assessment, AssessmentGrade
from models.schemas import UserSchema
from repositories.assessment_repository import assessment_repository
from repositories.audit_repository import audit_repository


class AssessmentService:
    def create_assessment(self, user: UserSchema, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new academic assessment. Restricted to Faculty and Admin."""
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to create assessments."
            )

        max_marks = float(data.get("max_marks", 0))
        if max_marks <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment max_marks must be greater than 0."
            )

        with get_db_session() as session:
            actor = session.query(User).filter(User.username == user.username).first()
            assessment_data = {
                "title": data["title"],
                "assessment_type": data.get("assessment_type", "assignment"),
                "max_marks": max_marks,
                "weightage": float(data.get("weightage", 100.0)),
                "assessment_date": data.get("assessment_date"),
                "course_offering_id": data.get("course_offering_id"),
                "course_id": data.get("course_id"),
                "created_by_id": actor.id if actor else "usr_admin1",
                "status": data.get("status", "published"),
            }
            asm = assessment_repository.create_assessment(session, assessment_data)
            
            audit_repository.log_audit_event(
                event_type="ASSESSMENT_CREATED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Created assessment '{asm.title}' (ID: {asm.id}, Max: {asm.max_marks})"
            )

            return {
                "id": asm.id,
                "title": asm.title,
                "assessment_type": asm.assessment_type,
                "max_marks": asm.max_marks,
                "weightage": asm.weightage,
                "status": asm.status,
            }

    def record_grades(
        self,
        user: UserSchema,
        assessment_id: str,
        grades_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Records or updates grades for an assessment.
        Validates obtained_marks boundaries: 0 <= obtained_marks <= max_marks.
        Restricted to Faculty and Admin.
        """
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to modify grade records."
            )

        with get_db_session() as session:
            asm = assessment_repository.get_assessment_by_id(session, assessment_id)
            if not asm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assessment '{assessment_id}' not found."
                )

            actor = session.query(User).filter(User.username == user.username).first()
            recorded_list = []

            for item in grades_data:
                obtained = float(item.get("obtained_marks", 0))
                if obtained < 0 or obtained > asm.max_marks:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid obtained marks {obtained}. Must be between 0 and maximum marks ({asm.max_marks})."
                    )

                student_profile_id = item.get("student_profile_id")
                if not student_profile_id and item.get("enrollment_no"):
                    sp = session.query(StudentProfile).filter(
                        StudentProfile.enrollment_no == item["enrollment_no"].strip()
                    ).first()
                    if sp:
                        student_profile_id = sp.id

                if not student_profile_id:
                    continue

                g_data = {
                    "assessment_id": asm.id,
                    "student_profile_id": student_profile_id,
                    "obtained_marks": obtained,
                    "grade": item.get("grade"),
                    "feedback": item.get("feedback"),
                    "evaluator_id": actor.id if actor else None,
                }
                rec = assessment_repository.record_grade(session, g_data)
                recorded_list.append(rec)

            audit_repository.log_audit_event(
                event_type="GRADE_RECORDED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Recorded {len(recorded_list)} grades for assessment '{asm.title}'"
            )

            return {
                "assessment_id": asm.id,
                "assessment_title": asm.title,
                "recorded_count": len(recorded_list),
            }

    def get_student_results(
        self,
        user: UserSchema,
        enrollment_no: str,
        offering_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves academic assessment results for a student.
        Students can ONLY access their own records.
        """
        if user.role == "student":
            if not user.enrollment_no or user.enrollment_no.casefold() != enrollment_no.strip().casefold():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Students can only access their own academic results."
                )

        with get_db_session() as session:
            student = session.query(StudentProfile).filter(
                StudentProfile.enrollment_no == enrollment_no.strip()
            ).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student record with enrollment_no '{enrollment_no}' not found."
                )

            grades = assessment_repository.get_student_grades(
                session,
                student_profile_id=student.id,
                course_offering_id=offering_id,
            )

            results = []
            for g in grades:
                results.append({
                    "id": g.id,
                    "assessment_id": g.assessment_id,
                    "assessment_title": g.assessment.title if g.assessment else None,
                    "assessment_type": g.assessment.assessment_type if g.assessment else None,
                    "max_marks": g.assessment.max_marks if g.assessment else None,
                    "obtained_marks": g.obtained_marks,
                    "percentage": round((g.obtained_marks / g.assessment.max_marks * 100.0), 2) if g.assessment and g.assessment.max_marks > 0 else 0.0,
                    "grade": g.grade,
                    "feedback": g.feedback,
                })

            return {
                "enrollment_no": student.enrollment_no,
                "student_name": student.user.display_name if student.user else None,
                "total_assessments": len(results),
                "results": results,
            }


assessment_service = AssessmentService()
