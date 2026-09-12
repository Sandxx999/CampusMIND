import sqlite3
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from auth.rbac import can_access_student_record, get_current_user, require_role
from models.schemas import UserSchema
from config import settings

router = APIRouter(prefix="/api/students", tags=["Student Management"])

DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

class StudentSchema(BaseModel):
    enrollment_no: str
    name: str
    email: str
    mobile_no: str
    branch: str
    year: int
    semester: int
    courses_enrolled: str
    sgpa: float
    cgpa: float
    attendance_pct: float
    backlogs: int
    fee_status: str

class StudentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    students: List[StudentSchema]

class StudentStatsSummary(BaseModel):
    total_students: int
    avg_cgpa: float
    avg_attendance_pct: float
    total_backlogs: int
    branch_distribution: dict
    fee_status_breakdown: dict

def get_db_connection():
    db_file = os.path.abspath(DB_PATH)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("", response_model=StudentListResponse)
def list_students(
    query: Optional[str] = Query(None, description="Search by name, enrollment number, or mobile number"),
    branch: Optional[str] = Query(None, description="Filter by branch / department"),
    year: Optional[int] = Query(None, description="Filter by academic year (1-4)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user)
):
    """
    Search and filter student records with pagination for faculty/admin users.
    Student users receive their own record only, regardless of supplied filters.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if user.role == "student":
        if not user.enrollment_no:
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student identity is not linked to an enrollment record.",
            )
        cursor.execute(
            "SELECT * FROM students WHERE UPPER(enrollment_no) = UPPER(?)",
            (user.enrollment_no,),
        )
        row = cursor.fetchone()
        conn.close()
        students = [StudentSchema(**dict(row))] if row and offset == 0 else []
        return StudentListResponse(total=1 if row else 0, limit=limit, offset=offset, students=students)

    conditions = []
    params = []

    if query:
        q = f"%{query.strip()}%"
        conditions.append("(name LIKE ? OR enrollment_no LIKE ? OR mobile_no LIKE ? OR email LIKE ?)")
        params.extend([q, q, q, q])

    if branch:
        conditions.append("branch LIKE ?")
        params.append(f"%{branch.strip()}%")

    if year is not None:
        conditions.append("year = ?")
        params.append(year)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # Count total matching
    count_sql = f"SELECT COUNT(*) FROM students{where_clause}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]

    # Fetch paginated rows
    fetch_sql = f"SELECT * FROM students{where_clause} ORDER BY enrollment_no ASC LIMIT ? OFFSET ?"
    cursor.execute(fetch_sql, params + [limit, offset])
    rows = cursor.fetchall()
    conn.close()

    students = [StudentSchema(**dict(r)) for r in rows]
    return StudentListResponse(total=total, limit=limit, offset=offset, students=students)

@router.get("/stats/summary", response_model=StudentStatsSummary)
def get_student_stats(user: UserSchema = Depends(require_role(["faculty", "admin"]))):
    """
    Aggregates student analytics including average CGPA, attendance, branch distribution, and fee status breakdown.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), AVG(cgpa), AVG(attendance_pct), SUM(backlogs) FROM students")
    total, avg_cgpa, avg_attendance, total_backlogs = cursor.fetchone()

    if not total or total == 0:
        conn.close()
        return StudentStatsSummary(
            total_students=0,
            avg_cgpa=0.0,
            avg_attendance_pct=0.0,
            total_backlogs=0,
            branch_distribution={},
            fee_status_breakdown={}
        )

    # Branch distribution
    cursor.execute("SELECT branch, COUNT(*) FROM students GROUP BY branch")
    branch_dist = {row[0]: row[1] for row in cursor.fetchall()}

    # Fee status breakdown
    cursor.execute("SELECT fee_status, COUNT(*) FROM students GROUP BY fee_status")
    fee_dist = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return StudentStatsSummary(
        total_students=total,
        avg_cgpa=round(avg_cgpa or 0.0, 2),
        avg_attendance_pct=round(avg_attendance or 0.0, 1),
        total_backlogs=total_backlogs or 0,
        branch_distribution=branch_dist,
        fee_status_breakdown=fee_dist
    )

@router.get("/{enrollment_no}", response_model=StudentSchema)
def get_student_by_enrollment(enrollment_no: str, user: UserSchema = Depends(get_current_user)):
    """
    Retrieves detailed academic profile and contact details for a specific student by Enrollment Number.
    """
    if not can_access_student_record(user, enrollment_no):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this student record.",
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE UPPER(enrollment_no) = UPPER(?)", (enrollment_no.strip(),))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student record with enrollment number '{enrollment_no}' was not found in campus database."
        )

    return StudentSchema(**dict(row))
