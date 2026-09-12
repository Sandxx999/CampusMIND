"""
Canonical Relational Database Models for CampusMIND 2.0.
Defines normalized schemas for Identity, RBAC, Academic Domains, Attendance, Assessments,
Announcements, Campus Events, Knowledge Foundation, Profiles, and Audit Logs.
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
    announcements = relationship("Announcement", back_populates="author")
    organized_events = relationship("CampusEvent", back_populates="organizer")
    event_registrations = relationship("EventRegistration", back_populates="user", cascade="all, delete-orphan")
    uploaded_documents = relationship("KnowledgeDocument", back_populates="uploader")


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
    announcements = relationship("Announcement", back_populates="department")
    events = relationship("CampusEvent", back_populates="department")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="department")


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
    announcements = relationship("Announcement", back_populates="program")


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
    offerings = relationship("CourseOffering", back_populates="course")


class AcademicTerm(Base):
    """Academic term / semester period (e.g. 2024-FALL, 2025-SPRING)."""

    __tablename__ = "academic_terms"

    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    course_offerings = relationship("CourseOffering", back_populates="term", cascade="all, delete-orphan")


class CourseOffering(Base):
    """Specific course section offering taught by a faculty member in an academic term."""

    __tablename__ = "course_offerings"
    __table_args__ = (
        UniqueConstraint("course_id", "term_id", "section", name="uq_course_term_section"),
    )

    id = Column(String(36), primary_key=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False, index=True)
    term_id = Column(String(36), ForeignKey("academic_terms.id"), nullable=False, index=True)
    faculty_profile_id = Column(String(36), ForeignKey("faculty_profiles.id"), nullable=True, index=True)
    section = Column(String(20), default="A", nullable=False)
    room = Column(String(50), nullable=True)
    schedule = Column(String(100), nullable=True)
    max_capacity = Column(Integer, default=60, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    course = relationship("Course", back_populates="offerings")
    term = relationship("AcademicTerm", back_populates="course_offerings")
    faculty_profile = relationship("FacultyProfile", back_populates="course_offerings")
    enrollments = relationship("Enrollment", back_populates="course_offering")
    attendance_records = relationship("AttendanceRecord", back_populates="course_offering", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course_offering", cascade="all, delete-orphan")


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
    attendance_records = relationship("AttendanceRecord", back_populates="student_profile", cascade="all, delete-orphan")
    assessment_grades = relationship("AssessmentGrade", back_populates="student_profile", cascade="all, delete-orphan")


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
    course_offerings = relationship("CourseOffering", back_populates="faculty_profile")


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
    """Junction entity mapping students to enrolled academic courses and offerings."""

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
    course_offering_id = Column(
        String(36), ForeignKey("course_offerings.id"), nullable=True, index=True
    )
    academic_year = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
    grade = Column(String(5), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    student_profile = relationship("StudentProfile", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    course_offering = relationship("CourseOffering", back_populates="enrollments")


class AttendanceRecord(Base):
    """Session-level attendance entry for a student in a course offering."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "course_offering_id", "date", name="uq_student_offering_date"),
    )

    id = Column(String(36), primary_key=True)
    student_profile_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False, index=True)
    course_offering_id = Column(String(36), ForeignKey("course_offerings.id"), nullable=True, index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # 'present', 'absent', 'late', 'excused'
    recorded_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    student_profile = relationship("StudentProfile", back_populates="attendance_records")
    course_offering = relationship("CourseOffering", back_populates="attendance_records")
    recorded_by = relationship("User")


class Assessment(Base):
    """Academic evaluation activity (Quiz, Assignment, Midterm, Final, Lab)."""

    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True)
    title = Column(String(150), nullable=False)
    assessment_type = Column(String(30), nullable=False)  # 'quiz', 'assignment', 'midterm', 'final', 'lab'
    max_marks = Column(Float, nullable=False)
    weightage = Column(Float, default=100.0, nullable=False)
    assessment_date = Column(DateTime(timezone=True), nullable=True)
    course_offering_id = Column(String(36), ForeignKey("course_offerings.id"), nullable=True, index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=True, index=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="published", nullable=False, index=True)  # 'draft', 'published'
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    course_offering = relationship("CourseOffering", back_populates="assessments")
    created_by = relationship("User")
    grades = relationship("AssessmentGrade", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentGrade(Base):
    """Marks and grade awarded to a student for a specific assessment."""

    __tablename__ = "assessment_grades"
    __table_args__ = (
        UniqueConstraint("assessment_id", "student_profile_id", name="uq_assessment_student"),
    )

    id = Column(String(36), primary_key=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    student_profile_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False, index=True)
    obtained_marks = Column(Float, nullable=False)
    grade = Column(String(5), nullable=True)
    feedback = Column(Text, nullable=True)
    evaluator_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    assessment = relationship("Assessment", back_populates="grades")
    student_profile = relationship("StudentProfile", back_populates="assessment_grades")
    evaluator = relationship("User")


class Announcement(Base):
    """Institutional announcement entity with RBAC audience targeting."""

    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    audience = Column(String(30), default="all", nullable=False, index=True)  # 'all', 'students', 'faculty', 'admin'
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    program_id = Column(String(36), ForeignKey("programs.id"), nullable=True, index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=True, index=True)
    status = Column(String(20), default="published", nullable=False, index=True)  # 'draft', 'published', 'archived'
    priority = Column(String(20), default="normal", nullable=False)  # 'low', 'normal', 'high', 'urgent'
    publish_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    author = relationship("User", back_populates="announcements")
    department = relationship("Department", back_populates="announcements")
    program = relationship("Program", back_populates="announcements")
    course = relationship("Course")


class CampusEvent(Base):
    """Campus event entity for academic, sports, cultural, and workshop intelligence."""

    __tablename__ = "campus_events"

    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(150), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    organizer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    audience = Column(String(30), default="all", nullable=False, index=True)  # 'all', 'students', 'faculty', 'admin'
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    category = Column(String(50), default="general", nullable=False)
    capacity = Column(Integer, nullable=True)
    requires_registration = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="scheduled", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organizer = relationship("User", back_populates="organized_events")
    department = relationship("Department", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")


class EventRegistration(Base):
    """User registration for campus events."""

    __tablename__ = "event_registrations"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_user_registration"),
    )

    id = Column(String(36), primary_key=True)
    event_id = Column(String(36), ForeignKey("campus_events.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), default="registered", nullable=False)
    registered_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    event = relationship("CampusEvent", back_populates="registrations")
    user = relationship("User", back_populates="event_registrations")


class KnowledgeDocument(Base):
    """Metadata tracking for campus knowledge documents, prepared for production RAG."""

    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    category = Column(String(50), default="general", nullable=False, index=True)  # 'policy', 'syllabus', 'handbook', 'faq'
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    audience = Column(String(30), default="all", nullable=False, index=True)  # 'all', 'students', 'faculty', 'admin'
    version = Column(String(20), default="1.0", nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    checksum = Column(String(64), nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    uploader_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    department = relationship("Department", back_populates="knowledge_documents")
    uploader = relationship("User", back_populates="uploaded_documents")


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


class SSOProviderConfig(Base):
    """Institutional Single Sign-On (OIDC/SAML) provider configuration."""

    __tablename__ = "sso_provider_configs"

    id = Column(String(36), primary_key=True)
    provider_name = Column(String(100), nullable=False)
    issuer_url = Column(String(255), nullable=False)
    client_id = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    allow_jit_provisioning = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class SystemTask(Base):
    """Background system task and worker job status tracking."""

    __tablename__ = "system_tasks"

    id = Column(String(36), primary_key=True)
    task_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    progress_pct = Column(Float, default=0.0, nullable=False)
    details = Column(Text, nullable=True)
    initiated_by = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
