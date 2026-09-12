"""
Phase 2 Production Data & Identity Architecture Test Suite.
Verifies SQLAlchemy 2.x session management, canonical ORM models, database constraints,
identity mapping, repository persistence, and transaction integrity.
"""
import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from db.session import get_engine, get_db_session, create_tables
from db.models import (
    Base,
    Role,
    User,
    Department,
    Program,
    Course,
    StudentProfile,
    FacultyProfile,
    AdminProfile,
    QueryLog,
    QueryFeedback,
    AuditEvent,
)
from repositories.user_repository import UserRepository
from repositories.student_repository import StudentRepository
from repositories.audit_repository import AuditRepository


def test_database_engine_and_session_lifecycle():
    """Verify engine instantiation, session lifecycle, and transaction rollback on error."""
    engine = get_engine()
    assert engine is not None

    test_role_id = f"role_test_{uuid.uuid4().hex[:8]}"
    with pytest.raises(Exception):
        with get_db_session() as session:
            r = Role(id=test_role_id, name=f"test_role_{uuid.uuid4().hex[:4]}")
            session.add(r)
            raise RuntimeError("Force transaction rollback")

    with get_db_session() as session:
        found = session.get(Role, test_role_id)
        assert found is None


def test_canonical_orm_models_and_unique_constraints():
    """Verify canonical ORM entities, relationships, and unique constraint enforcement."""
    with get_db_session() as session:
        role_id = f"role_{uuid.uuid4().hex[:6]}"
        r = Role(id=role_id, name=f"role_name_{uuid.uuid4().hex[:6]}", description="Test Role")
        session.add(r)
        session.flush()

        username = f"user_{uuid.uuid4().hex[:6]}"
        u1 = User(
            id=f"usr_{uuid.uuid4().hex[:6]}",
            username=username,
            email=f"{username}@example.com",
            display_name="Test User",
            status="active",
            role_id=r.id,
        )
        session.add(u1)
        session.flush()

        # Duplicate username must fail integrity constraint
        u2 = User(
            id=f"usr_{uuid.uuid4().hex[:6]}",
            username=username,
            email=f"other_{username}@example.com",
            display_name="Duplicate User",
            status="active",
            role_id=r.id,
        )
        session.add(u2)
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()


def test_user_repository_identity_resolution():
    """Verify UserRepository identity lookup and role mapping."""
    user_repo = UserRepository()
    username = f"identity_user_{uuid.uuid4().hex[:6]}"
    enrollment_no = f"2026TEST{uuid.uuid4().hex[:4].upper()}"

    with get_db_session() as session:
        role = session.query(Role).filter(Role.name == "student").first()
        if not role:
            role = Role(id="role_student", name="student")
            session.add(role)
            session.flush()

        u = User(
            id=f"usr_{uuid.uuid4().hex[:6]}",
            username=username,
            email=f"{username}@ifheindia.edu",
            display_name="Identity Test User",
            status="active",
            role_id=role.id,
        )
        session.add(u)
        session.flush()

        sp = StudentProfile(
            id=f"prof_{uuid.uuid4().hex[:6]}",
            user_id=u.id,
            enrollment_no=enrollment_no,
            branch="Computer Science & Engineering (CSE)",
            year=3,
            semester=5,
            courses_enrolled="CS301, CS302",
            sgpa=8.5,
            cgpa=8.7,
            attendance_pct=92.0,
            backlogs=0,
            fee_status="Paid",
            mobile_no="+91 9876543210",
        )
        session.add(sp)

    res = user_repo.get_by_username(username)
    assert res is not None
    assert res["username"] == username
    assert res["role"] == "student"
    assert res["enrollment_no"] == enrollment_no

    with get_db_session() as session:
        session.query(StudentProfile).filter(StudentProfile.enrollment_no == enrollment_no).delete()
        session.query(User).filter(User.username == username).delete()


def test_student_repository_canonical_and_fallback_queries():
    """Verify StudentRepository functions against canonical ORM models."""
    student_repo = StudentRepository()
    enrollment_no = f"2026CANON{uuid.uuid4().hex[:4].upper()}"
    username = f"std_canon_{uuid.uuid4().hex[:6]}"

    with get_db_session() as session:
        role = session.query(Role).filter(Role.name == "student").first()
        if not role:
            role = Role(id="role_student", name="student")
            session.add(role)
            session.flush()

        u = User(
            id=f"usr_{uuid.uuid4().hex[:6]}",
            username=username,
            email=f"{username}@ifheindia.edu",
            display_name="Canonical Student User",
            status="active",
            role_id=role.id,
        )
        session.add(u)
        session.flush()

        sp = StudentProfile(
            id=f"prof_{uuid.uuid4().hex[:6]}",
            user_id=u.id,
            enrollment_no=enrollment_no,
            branch="Artificial Intelligence & Data Science (AI&DS)",
            year=2,
            semester=3,
            courses_enrolled="AI301, DS301",
            sgpa=9.1,
            cgpa=9.0,
            attendance_pct=95.5,
            backlogs=0,
            fee_status="Paid",
            mobile_no="+91 9998887776",
        )
        session.add(sp)

    fetched = student_repo.get_by_enrollment(enrollment_no)
    assert fetched is not None
    assert fetched["enrollment_no"] == enrollment_no
    assert fetched["name"] == "Canonical Student User"
    assert fetched["cgpa"] == 9.0

    total, students = student_repo.list_students(query=enrollment_no)
    assert total >= 1
    assert any(s["enrollment_no"] == enrollment_no for s in students)

    with get_db_session() as session:
        session.query(StudentProfile).filter(StudentProfile.enrollment_no == enrollment_no).delete()
        session.query(User).filter(User.username == username).delete()


def test_audit_repository_persistence_and_stats():
    """Verify AuditRepository query logging, feedback tracking, and admin stats computation."""
    audit_repo = AuditRepository()
    query_id = f"qry_test_{uuid.uuid4().hex[:8]}"

    audit_repo.log_query(
        query_id=query_id,
        username="student1",
        role="student",
        question="What is the exam schedule?",
        answer="Exams start on May 15.",
        latency_ms=120.5,
        chunk_count=2,
        confidence=0.95,
        is_fallback=False,
    )

    owner = audit_repo.get_query_owner(query_id)
    assert owner == "student1"

    audit_repo.log_feedback(query_id=query_id, is_positive=True)

    stats = audit_repo.get_admin_stats()
    assert stats["total_queries"] > 0
    assert stats["avg_latency_ms"] > 0


def test_inactive_user_cannot_authenticate():
    """Verify inactive or suspended user accounts are rejected during authentication."""
    from services.auth_service import AuthService
    from models.schemas import LoginRequest
    from fastapi import HTTPException

    user_repo = UserRepository()
    auth_svc = AuthService(user_repo=user_repo)
    inactive_username = f"inactive_{uuid.uuid4().hex[:6]}"

    with get_db_session() as session:
        role = session.query(Role).filter(Role.name == "student").first()
        u = User(
            id=f"usr_{uuid.uuid4().hex[:6]}",
            username=inactive_username,
            email=f"{inactive_username}@ifheindia.edu",
            display_name="Inactive User",
            status="suspended",
            role_id=role.id if role else "role_student",
        )
        session.add(u)

    try:
        with pytest.raises(HTTPException) as exc_info:
            auth_svc.authenticate_user(LoginRequest(username=inactive_username, password="password123"))
        assert exc_info.value.status_code == 403
    finally:
        with get_db_session() as session:
            session.query(User).filter(User.username == inactive_username).delete()
