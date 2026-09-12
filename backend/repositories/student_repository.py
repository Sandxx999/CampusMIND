"""
Student Data Repository for CampusMIND 2.0.
Encapsulates data access and persistence operations for student records.
Supports canonical relational ORM models (StudentProfile & User) with fallback to legacy SQLite tables.
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_
from db.session import get_db_session, get_db_connection
from db.models import StudentProfile, User
from core.logging import logger


class StudentRepository:
    """Repository handling database persistence operations for students."""

    def __init__(self, db_conn_factory=get_db_connection):
        self.db_conn_factory = db_conn_factory

    def get_by_enrollment(self, enrollment_no: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single student record matching the enrollment number (case-insensitive)."""
        clean_enrollment = enrollment_no.strip().upper()

        # 1. Try canonical ORM model query
        try:
            with get_db_session() as session:
                stmt = (
                    select(StudentProfile, User)
                    .join(User, StudentProfile.user_id == User.id)
                    .where(func.upper(StudentProfile.enrollment_no) == clean_enrollment)
                )
                row = session.execute(stmt).first()
                if row:
                    sp, u = row
                    return {
                        "enrollment_no": sp.enrollment_no,
                        "name": u.display_name,
                        "email": u.email,
                        "mobile_no": sp.mobile_no or "+91 9876543210",
                        "branch": sp.branch,
                        "year": sp.year,
                        "semester": sp.semester,
                        "courses_enrolled": sp.courses_enrolled,
                        "sgpa": sp.sgpa,
                        "cgpa": sp.cgpa,
                        "attendance_pct": sp.attendance_pct,
                        "backlogs": sp.backlogs,
                        "fee_status": sp.fee_status,
                    }
        except Exception as e:
            logger.debug(f"Canonical student model query failed, attempting legacy fallback: {e}")

        # 2. Fallback to legacy SQLite query
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM students WHERE UPPER(enrollment_no) = UPPER(?)",
                (clean_enrollment,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error executing legacy student lookup: {e}")
            return None
        finally:
            conn.close()

    def list_students(
        self,
        query: Optional[str] = None,
        branch: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Lists student records matching filter criteria with total count and pagination."""
        # 1. Try canonical ORM model query
        try:
            with get_db_session() as session:
                stmt = select(StudentProfile, User).join(User, StudentProfile.user_id == User.id)
                conditions = []

                if query:
                    q = f"%{query.strip()}%"
                    conditions.append(
                        or_(
                            User.display_name.ilike(q),
                            StudentProfile.enrollment_no.ilike(q),
                            StudentProfile.mobile_no.ilike(q),
                            User.email.ilike(q),
                        )
                    )

                if branch:
                    conditions.append(StudentProfile.branch.ilike(f"%{branch.strip()}%"))

                if year is not None:
                    conditions.append(StudentProfile.year == year)

                if conditions:
                    stmt = stmt.where(*conditions)

                # Total count
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total = session.scalar(count_stmt) or 0

                if total > 0:
                    fetch_stmt = stmt.order_by(StudentProfile.enrollment_no.asc()).limit(limit).offset(offset)
                    rows = session.execute(fetch_stmt).all()
                    students = [
                        {
                            "enrollment_no": sp.enrollment_no,
                            "name": u.display_name,
                            "email": u.email,
                            "mobile_no": sp.mobile_no or "+91 9876543210",
                            "branch": sp.branch,
                            "year": sp.year,
                            "semester": sp.semester,
                            "courses_enrolled": sp.courses_enrolled,
                            "sgpa": sp.sgpa,
                            "cgpa": sp.cgpa,
                            "attendance_pct": sp.attendance_pct,
                            "backlogs": sp.backlogs,
                            "fee_status": sp.fee_status,
                        }
                        for sp, u in rows
                    ]
                    return total, students
        except Exception as e:
            logger.debug(f"Canonical student list query failed, attempting legacy fallback: {e}")

        # 2. Fallback to legacy SQLite query
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
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

            cursor.execute(f"SELECT COUNT(*) FROM students{where_clause}", params)
            total = cursor.fetchone()[0]

            fetch_sql = f"SELECT * FROM students{where_clause} ORDER BY enrollment_no ASC LIMIT ? OFFSET ?"
            cursor.execute(fetch_sql, params + [limit, offset])
            rows = cursor.fetchall()
            students = [dict(r) for r in rows]

            return total, students
        except Exception as e:
            logger.error(f"Error executing legacy student list query: {e}")
            return 0, []
        finally:
            conn.close()

    def get_stats_summary(self) -> Dict[str, Any]:
        """Aggregates overall student statistics, branch breakdown, and fee status distribution."""
        # 1. Try canonical ORM model aggregation
        try:
            with get_db_session() as session:
                total = session.scalar(select(func.count(StudentProfile.id))) or 0
                if total > 0:
                    avg_cgpa = session.scalar(select(func.avg(StudentProfile.cgpa))) or 0.0
                    avg_att = session.scalar(select(func.avg(StudentProfile.attendance_pct))) or 0.0
                    total_backlogs = session.scalar(select(func.sum(StudentProfile.backlogs))) or 0

                    branch_rows = session.execute(
                        select(StudentProfile.branch, func.count(StudentProfile.id)).group_by(StudentProfile.branch)
                    ).all()
                    branch_dist = {r[0]: r[1] for r in branch_rows}

                    fee_rows = session.execute(
                        select(StudentProfile.fee_status, func.count(StudentProfile.id)).group_by(StudentProfile.fee_status)
                    ).all()
                    fee_dist = {r[0]: r[1] for r in fee_rows}

                    return {
                        "total_students": total,
                        "avg_cgpa": round(float(avg_cgpa), 2),
                        "avg_attendance_pct": round(float(avg_att), 1),
                        "total_backlogs": int(total_backlogs),
                        "branch_distribution": branch_dist,
                        "fee_status_breakdown": fee_dist,
                    }
        except Exception as e:
            logger.debug(f"Canonical student stats query failed, attempting legacy fallback: {e}")

        # 2. Fallback to legacy SQLite aggregation
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), AVG(cgpa), AVG(attendance_pct), SUM(backlogs) FROM students")
            total, avg_cgpa, avg_attendance, total_backlogs = cursor.fetchone()

            if not total or total == 0:
                return {
                    "total_students": 0,
                    "avg_cgpa": 0.0,
                    "avg_attendance_pct": 0.0,
                    "total_backlogs": 0,
                    "branch_distribution": {},
                    "fee_status_breakdown": {},
                }

            cursor.execute("SELECT branch, COUNT(*) FROM students GROUP BY branch")
            branch_dist = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT fee_status, COUNT(*) FROM students GROUP BY fee_status")
            fee_dist = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_students": total,
                "avg_cgpa": round(avg_cgpa or 0.0, 2),
                "avg_attendance_pct": round(avg_attendance or 0.0, 1),
                "total_backlogs": total_backlogs or 0,
                "branch_distribution": branch_dist,
                "fee_status_breakdown": fee_dist,
            }
        except Exception as e:
            logger.error(f"Error executing legacy student stats aggregation: {e}")
            return {
                "total_students": 0,
                "avg_cgpa": 0.0,
                "avg_attendance_pct": 0.0,
                "total_backlogs": 0,
                "branch_distribution": {},
                "fee_status_breakdown": {},
            }
        finally:
            conn.close()


student_repository = StudentRepository()
