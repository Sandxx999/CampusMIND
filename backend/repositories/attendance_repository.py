"""Attendance Repository for CampusMIND 2.0.

Provides database access for student session-level attendance records.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import AttendanceRecord, StudentProfile, CourseOffering


class AttendanceRepository:
    def create_or_update_record(self, db: Session, data: Dict[str, Any]) -> AttendanceRecord:
        """Creates a new attendance record or updates existing if date & student match."""
        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_profile_id == data["student_profile_id"],
            AttendanceRecord.course_offering_id == data.get("course_offering_id"),
            AttendanceRecord.date == data["date"]
        ).first()

        if existing:
            existing.status = data["status"]
            existing.remarks = data.get("remarks", existing.remarks)
            existing.recorded_by_id = data.get("recorded_by_id", existing.recorded_by_id)
            db.commit()
            db.refresh(existing)
            return existing

        record = AttendanceRecord(
            id=data.get("id", f"att_{uuid.uuid4().hex[:12]}"),
            student_profile_id=data["student_profile_id"],
            course_offering_id=data.get("course_offering_id"),
            course_id=data.get("course_id"),
            date=data["date"],
            status=data["status"],
            recorded_by_id=data.get("recorded_by_id"),
            remarks=data.get("remarks"),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def bulk_record_attendance(self, db: Session, records_data: List[Dict[str, Any]]) -> List[AttendanceRecord]:
        """Bulk creates or updates attendance records."""
        results = []
        for r_data in records_data:
            rec = self.create_or_update_record(db, r_data)
            results.append(rec)
        return results

    def get_student_attendance(
        self,
        db: Session,
        student_profile_id: str,
        course_offering_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AttendanceRecord]:
        """Retrieves attendance records for a student."""
        query = db.query(AttendanceRecord).filter(AttendanceRecord.student_profile_id == student_profile_id)
        if course_offering_id:
            query = query.filter(AttendanceRecord.course_offering_id == course_offering_id)
        return query.order_by(AttendanceRecord.date.desc()).offset(offset).limit(limit).all()

    def get_offering_attendance(
        self,
        db: Session,
        course_offering_id: str,
        date_val: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AttendanceRecord]:
        """Retrieves attendance records for a course offering."""
        query = db.query(AttendanceRecord).filter(AttendanceRecord.course_offering_id == course_offering_id)
        if date_val:
            query = query.filter(AttendanceRecord.date == date_val)
        return query.order_by(AttendanceRecord.date.desc()).offset(offset).limit(limit).all()

    def get_student_summary(self, db: Session, student_profile_id: str) -> Dict[str, Any]:
        """Calculates total classes, attended classes, and attendance percentage for a student."""
        total = db.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.student_profile_id == student_profile_id
        ).scalar() or 0

        present = db.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.student_profile_id == student_profile_id,
            AttendanceRecord.status.in_(["present", "excused"])
        ).scalar() or 0

        pct = (present / total * 100.0) if total > 0 else 100.0
        return {
            "student_profile_id": student_profile_id,
            "total_classes": total,
            "attended_classes": present,
            "attendance_pct": round(pct, 2),
        }


attendance_repository = AttendanceRepository()
