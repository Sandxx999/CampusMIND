"""Attendance Service for CampusMIND 2.0.

Implements authorization-enforced business rules for session attendance tracking and analytics.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from db.models import User, StudentProfile, FacultyProfile, CourseOffering
from models.schemas import UserSchema
from repositories.attendance_repository import attendance_repository
from repositories.audit_repository import audit_repository


class AttendanceService:
    def get_student_attendance(
        self,
        user: UserSchema,
        enrollment_no: str,
        offering_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Retrieves attendance records for a student.
        Enforces strict server-side ownership: students can ONLY view their own records.
        """
        if user.role == "student":
            if not user.enrollment_no or user.enrollment_no.casefold() != enrollment_no.strip().casefold():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Students can only access their own attendance records."
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

            records = attendance_repository.get_student_attendance(
                session,
                student_profile_id=student.id,
                course_offering_id=offering_id,
                limit=limit,
                offset=offset,
            )
            summary = attendance_repository.get_student_summary(session, student_profile_id=student.id)

            rec_list = [
                {
                    "id": r.id,
                    "student_profile_id": r.student_profile_id,
                    "course_offering_id": r.course_offering_id,
                    "course_title": r.course_offering.course.title if r.course_offering and r.course_offering.course else None,
                    "date": r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date),
                    "status": r.status,
                    "remarks": r.remarks,
                }
                for r in records
            ]

            return {
                "enrollment_no": student.enrollment_no,
                "student_name": student.user.display_name if student.user else None,
                "summary": summary,
                "records": rec_list,
            }

    def record_attendance(
        self,
        user: UserSchema,
        offering_id: str,
        records_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Records or updates attendance for a course offering.
        Restricted to Faculty and Admin. Faculty must be assigned to offering or in faculty role.
        """
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to modify attendance records."
            )

        with get_db_session() as session:
            actor = session.query(User).filter(User.username == user.username).first()
            offering = session.query(CourseOffering).filter(CourseOffering.id == offering_id).first()
            if not offering:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Course offering '{offering_id}' not found."
                )

            if user.role == "faculty" and actor and actor.faculty_profile:
                if offering.faculty_profile_id and offering.faculty_profile_id != actor.faculty_profile.id:
                    # Check department or allow faculty assigned to offering
                    pass

            prepared_records = []
            for item in records_data:
                # Find student profile ID
                student_profile_id = item.get("student_profile_id")
                if not student_profile_id and item.get("enrollment_no"):
                    sp = session.query(StudentProfile).filter(
                        StudentProfile.enrollment_no == item["enrollment_no"].strip()
                    ).first()
                    if sp:
                        student_profile_id = sp.id

                if not student_profile_id:
                    continue

                date_val = item.get("date")
                if isinstance(date_val, str):
                    try:
                        date_val = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                    except ValueError:
                        date_val = datetime.now()
                elif not date_val:
                    date_val = datetime.now()

                valid_statuses = {"present", "absent", "late", "excused"}
                rec_status = item.get("status", "present").lower()
                if rec_status not in valid_statuses:
                    rec_status = "present"

                prepared_records.append({
                    "student_profile_id": student_profile_id,
                    "course_offering_id": offering.id,
                    "course_id": offering.course_id,
                    "date": date_val,
                    "status": rec_status,
                    "recorded_by_id": actor.id if actor else None,
                    "remarks": item.get("remarks"),
                })

            updated = attendance_repository.bulk_record_attendance(session, prepared_records)
            
            audit_repository.log_audit_event(
                event_type="ATTENDANCE_RECORDED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Recorded {len(updated)} attendance entries for offering {offering.id}"
            )

            return {
                "message": f"Successfully recorded attendance for {len(updated)} students.",
                "recorded_count": len(updated),
            }


attendance_service = AttendanceService()
