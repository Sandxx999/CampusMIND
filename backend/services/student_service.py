"""
Student Service.
Encapsulates business rules for student record retrieval and stats aggregation.
"""
from typing import Optional
from fastapi import HTTPException, status
from auth.rbac import can_access_student_record
from models.schemas import StudentListResponse, StudentSchema, StudentStatsSummary, UserSchema
from repositories.student_repository import student_repository, StudentRepository


class StudentService:
    """Service handling student operations, authorization checks, and analytics."""

    def __init__(self, repo: StudentRepository = student_repository):
        self.repo = repo

    def list_students(
        self,
        user: UserSchema,
        query: Optional[str] = None,
        branch: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> StudentListResponse:
        """
        Lists student records matching filter criteria.
        Students receive only their own record, regardless of provided filters.
        """
        if user.role == "student":
            if not user.enrollment_no:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student identity is not linked to an enrollment record.",
                )
            row = self.repo.get_by_enrollment(user.enrollment_no)
            students = [StudentSchema(**row)] if row and offset == 0 else []
            return StudentListResponse(
                total=1 if row else 0, limit=limit, offset=offset, students=students
            )

        total, rows = self.repo.list_students(
            query=query, branch=branch, year=year, limit=limit, offset=offset
        )
        students = [StudentSchema(**r) for r in rows]
        return StudentListResponse(total=total, limit=limit, offset=offset, students=students)

    def get_student_by_enrollment(self, user: UserSchema, enrollment_no: str) -> StudentSchema:
        """Retrieves single student record by enrollment number after validating access rights."""
        if not can_access_student_record(user, enrollment_no):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this student record.",
            )

        row = self.repo.get_by_enrollment(enrollment_no)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student record with enrollment number '{enrollment_no}' was not found in campus database.",
            )

        return StudentSchema(**row)

    def get_student_stats(self) -> StudentStatsSummary:
        """Aggregates student analytics summary for staff/admin dashboard."""
        stats = self.repo.get_stats_summary()
        return StudentStatsSummary(**stats)


student_service = StudentService()
