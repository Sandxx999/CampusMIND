"""
Canonical Relational Database Models for CampusMIND 2.0.
Defines normalized schemas for Identity, RBAC, Academic Domains, Profiles, and Audit Logs.
Supports both SQLite and PostgreSQL.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from db.base import Base


def utc_now() -> datetime:
    """Returns timezone-aware UTC current timestamp."""
    return datetime.now(timezone.utc)


class Role(Base):
    """System role entity (student, faculty, admin)."""

    __tablename__ = "roles"

    id = Column(String(36), primary_key=True)
    name = Column(String(36), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    """Core user identity model for authentication and platform-wide profile binding."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False, index=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    role = relationship("Role", back_populates="users")
    student_profile = relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    faculty_profile = relationship(
        "FacultyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    admin_profile = relationship(
        "AdminProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    query_logs = relationship("QueryLog", back_populates="user")
    audit_events = relationship("AuditEvent", back_populates="user")


class Department(Base):
    """Academic department entity (e.g. CSE, AI&DS, ECE, EEE, ME, CE, MBA, LAW)."""

    __tablename__ = "departments"

    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    programs = relationship("Program", back_populates="department")
    courses = relationship("Course", back_populates="department")
    student_profiles = relationship("StudentProfile", back_populates="department")
    faculty_profiles = relationship("FacultyProfile", back_populates="department")


class Program(Base):
    """Academic program entity (e.g. B.Tech Computer Science, MBA)."""

    __tablename__ = "programs"

    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    duration_years = Column(Integer, default=4, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    department = relationship("Department", back_populates="programs")
    student_profiles = relationship("StudentProfile", back_populates="program")


class Course(Base):
    """Academic course subject entity."""

    __tablename__ = "courses"

    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(150), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    credits = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    department = relationship("Department", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")


class StudentProfile(Base):
    """Domain profile for student-specific academic information, decoupled from User identity."""

    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    enrollment_no = Column(String(50), unique=True, nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    program_id = Column(String(36), ForeignKey("programs.id"), nullable=True, index=True)
    branch = Column(String(100), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    courses_enrolled = Column(Text, nullable=False)
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    attendance_pct = Column(Float, nullable=False)
    backlogs = Column(Integer, default=0, nullable=False)
    fee_status = Column(String(100), nullable=False)
    mobile_no = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="student_profiles")
    program = relationship("Program", back_populates="student_profiles")
    enrollments = relationship("Enrollment", back_populates="student_profile")


class FacultyProfile(Base):
    """Domain profile for faculty members."""

    __tablename__ = "faculty_profiles"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    designation = Column(String(100), default="Assistant Professor", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department", back_populates="faculty_profiles")


class AdminProfile(Base):
    """Domain profile for administrator accounts."""

    __tablename__ = "admin_profiles"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    designation = Column(String(100), default="System Administrator", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user = relationship("User", back_populates="admin_profile")


class Enrollment(Base):
    """Junction entity mapping students to enrolled academic courses."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "course_id",
            "academic_year",
            "semester",
            name="uq_student_course_term",
        ),
    )

    id = Column(String(36), primary_key=True)
    student_profile_id = Column(
        String(36), ForeignKey("student_profiles.id"), nullable=False, index=True
    )
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
    grade = Column(String(5), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    student_profile = relationship("StudentProfile", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class QueryLog(Base):
    """Audit entity storing chat/RAG queries, LLM latency, and confidence metrics."""

    __tablename__ = "query_logs"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    is_fallback = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="query_logs")
    feedback = relationship("QueryFeedback", back_populates="query_log", cascade="all, delete-orphan")


class QueryFeedback(Base):
    """Audit entity recording user feedback for RAG responses."""

    __tablename__ = "query_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(64), ForeignKey("query_logs.id"), nullable=False, index=True)
    is_positive = Column(Boolean, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    query_log = relationship("QueryLog", back_populates="feedback")


class AuditEvent(Base):
    """Security audit trail for tracking critical administrative and identity events."""

    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    actor_username = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="audit_events")
