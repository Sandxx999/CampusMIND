"""
Student Data Repository.
Encapsulates data access and SQL query execution for student records.
"""
from typing import List, Optional, Tuple, Dict, Any
from db.session import get_db_connection


class StudentRepository:
    """Repository handling all database persistence operations for students."""

    def __init__(self, db_conn_factory=get_db_connection):
        self.db_conn_factory = db_conn_factory

    def get_by_enrollment(self, enrollment_no: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single student record matching the enrollment number (case-insensitive)."""
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM students WHERE UPPER(enrollment_no) = UPPER(?)",
                (enrollment_no.strip(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_students(
        self,
        query: Optional[str] = None,
        branch: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Lists student records matching filter criteria with total count and pagination."""
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

            # Count total matching
            cursor.execute(f"SELECT COUNT(*) FROM students{where_clause}", params)
            total = cursor.fetchone()[0]

            # Fetch paginated rows
            fetch_sql = f"SELECT * FROM students{where_clause} ORDER BY enrollment_no ASC LIMIT ? OFFSET ?"
            cursor.execute(fetch_sql, params + [limit, offset])
            rows = cursor.fetchall()
            students = [dict(r) for r in rows]

            return total, students
        finally:
            conn.close()

    def get_stats_summary(self) -> Dict[str, Any]:
        """Aggregates overall student statistics, branch breakdown, and fee status distribution."""
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
                    "fee_status_breakdown": {}
                }

            # Branch distribution
            cursor.execute("SELECT branch, COUNT(*) FROM students GROUP BY branch")
            branch_dist = {row[0]: row[1] for row in cursor.fetchall()}

            # Fee status breakdown
            cursor.execute("SELECT fee_status, COUNT(*) FROM students GROUP BY fee_status")
            fee_dist = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_students": total,
                "avg_cgpa": round(avg_cgpa or 0.0, 2),
                "avg_attendance_pct": round(avg_attendance or 0.0, 1),
                "total_backlogs": total_backlogs or 0,
                "branch_distribution": branch_dist,
                "fee_status_breakdown": fee_dist
            }
        finally:
            conn.close()


student_repository = StudentRepository()
