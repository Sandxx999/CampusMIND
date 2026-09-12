"""
Data Migration Tooling: SQLite to Canonical PostgreSQL / Relational DB.
Reads legacy records from campusmind.db SQLite and transforms them into canonical
User, StudentProfile, QueryLog, and QueryFeedback relational entities with transaction safety.
"""
import os
import sys
import sqlite3
import argparse
from datetime import datetime, timezone

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import settings
from db.session import get_db_session, create_tables
from db.models import (
    Role,
    User,
    StudentProfile,
    QueryLog,
    QueryFeedback,
)


def migrate_sqlite_to_canonical(sqlite_path: str, target_db_url: str = None):
    """
    Reads records from legacy SQLite DB and populates canonical ORM database.
    Does NOT destroy the source SQLite file.
    """
    target_url = target_db_url or settings.DATABASE_URL
    print(f"Starting data migration from SQLite ({sqlite_path}) -> Canonical Database ({target_url})")

    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"Source SQLite database not found at {sqlite_path}")

    # Initialize target schema
    create_tables(target_url)

    source_conn = sqlite3.connect(sqlite_path)
    source_conn.row_factory = sqlite3.Row
    s_cursor = source_conn.cursor()

    # Read students
    s_cursor.execute("SELECT * FROM students")
    students_rows = [dict(r) for r in s_cursor.fetchall()]
    print(f"Fetched {len(students_rows)} student records from legacy SQLite.")

    # Read query logs
    try:
        s_cursor.execute("SELECT * FROM query_logs")
        logs_rows = [dict(r) for r in s_cursor.fetchall()]
    except Exception:
        logs_rows = []
    print(f"Fetched {len(logs_rows)} query log records from legacy SQLite.")

    # Read feedback
    try:
        s_cursor.execute("SELECT * FROM query_feedback")
        feedback_rows = [dict(r) for r in s_cursor.fetchall()]
    except Exception:
        feedback_rows = []
    print(f"Fetched {len(feedback_rows)} query feedback records from legacy SQLite.")

    source_conn.close()

    # Perform transformation and insertion into target database
    with get_db_session(target_url) as session:
        # Ensure student role exists
        student_role = session.get(Role, "role_student")
        if not student_role:
            student_role = Role(id="role_student", name="student", description="Student role")
            session.add(student_role)
            session.flush()

        migrated_students = 0
        for s in students_rows:
            enrollment_no = s["enrollment_no"]
            username = "student1" if enrollment_no == "2024IFHE001" else f"student_{enrollment_no.lower()}"

            user = session.query(User).filter(User.username == username).first()
            if not user:
                user = User(
                    id=f"usr_{enrollment_no.lower()}",
                    username=username,
                    email=s["email"],
                    display_name=s["name"],
                    status="active",
                    role_id="role_student",
                )
                session.add(user)
                session.flush()

            sp = session.query(StudentProfile).filter(StudentProfile.enrollment_no == enrollment_no).first()
            if not sp:
                sp = StudentProfile(
                    id=f"prof_{enrollment_no.lower()}",
                    user_id=user.id,
                    enrollment_no=s["enrollment_no"],
                    branch=s["branch"],
                    year=s["year"],
                    semester=s["semester"],
                    courses_enrolled=s["courses_enrolled"],
                    sgpa=s["sgpa"],
                    cgpa=s["cgpa"],
                    attendance_pct=s["attendance_pct"],
                    backlogs=s["backlogs"],
                    fee_status=s["fee_status"],
                    mobile_no=s["mobile_no"],
                )
                session.add(sp)
                migrated_students += 1

        migrated_logs = 0
        for l in logs_rows:
            ql = session.get(QueryLog, l["id"])
            if not ql:
                # Try parsing timestamp
                try:
                    ts = datetime.fromisoformat(l["timestamp"])
                except Exception:
                    ts = datetime.now(timezone.utc)

                ql = QueryLog(
                    id=l["id"],
                    timestamp=ts,
                    username=l["username"],
                    role=l["role"],
                    question=l["question"],
                    answer=l["answer"],
                    latency_ms=l["latency_ms"],
                    chunk_count=l["chunk_count"],
                    confidence=l["confidence"],
                    is_fallback=bool(l["is_fallback"]),
                )
                session.add(ql)
                migrated_logs += 1

        migrated_feedback = 0
        for fb in feedback_rows:
            q_id = fb["query_id"]
            if session.get(QueryLog, q_id):
                try:
                    ts = datetime.fromisoformat(fb["timestamp"])
                except Exception:
                    ts = datetime.now(timezone.utc)

                qf = QueryFeedback(
                    query_id=q_id,
                    is_positive=bool(fb["is_positive"]),
                    timestamp=ts,
                )
                session.add(qf)
                migrated_feedback += 1

    print(
        f"Migration complete! Successfully migrated:\n"
        f"  - {migrated_students} student profiles\n"
        f"  - {migrated_logs} query logs\n"
        f"  - {migrated_feedback} query feedback entries"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate legacy SQLite database to Canonical Relational DB")
    parser.add_argument(
        "--source-sqlite",
        default=os.path.join(os.path.dirname(__file__), "../campusmind.db"),
        help="Path to source campusmind.db file",
    )
    parser.add_argument(
        "--target-db-url",
        default=None,
        help="Target DATABASE_URL (defaults to settings.DATABASE_URL)",
    )
    args = parser.parse_args()
    migrate_sqlite_to_canonical(args.source_sqlite, args.target_db_url)
