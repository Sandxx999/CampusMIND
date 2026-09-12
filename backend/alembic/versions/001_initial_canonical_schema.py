"""Initial canonical relational schema for CampusMIND 2.0.

Revision ID: 001_initial_canonical_schema
Revises: 
Create Date: 2026-09-12 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_canonical_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=36), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # 2. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('role_id', sa.String(length=36), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role_id'), 'users', ['role_id'], unique=False)

    # 3. Departments
    op.create_table(
        'departments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_code'), 'departments', ['code'], unique=True)

    # 4. Programs
    op.create_table(
        'programs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('department_id', sa.String(length=36), nullable=False),
        sa.Column('duration_years', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_programs_code'), 'programs', ['code'], unique=True)
    op.create_index(op.f('ix_programs_department_id'), 'programs', ['department_id'], unique=False)

    # 5. Courses
    op.create_table(
        'courses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_code'), 'courses', ['code'], unique=True)
    op.create_index(op.f('ix_courses_department_id'), 'courses', ['department_id'], unique=False)

    # 6. Student Profiles
    op.create_table(
        'student_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('enrollment_no', sa.String(length=50), nullable=False),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('program_id', sa.String(length=36), nullable=True),
        sa.Column('branch', sa.String(length=100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('courses_enrolled', sa.Text(), nullable=False),
        sa.Column('sgpa', sa.Float(), nullable=False),
        sa.Column('cgpa', sa.Float(), nullable=False),
        sa.Column('attendance_pct', sa.Float(), nullable=False),
        sa.Column('backlogs', sa.Integer(), nullable=False),
        sa.Column('fee_status', sa.String(length=100), nullable=False),
        sa.Column('mobile_no', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_profiles_user_id'), 'student_profiles', ['user_id'], unique=True)
    op.create_index(op.f('ix_student_profiles_enrollment_no'), 'student_profiles', ['enrollment_no'], unique=True)
    op.create_index(op.f('ix_student_profiles_branch'), 'student_profiles', ['branch'], unique=False)
    op.create_index(op.f('ix_student_profiles_year'), 'student_profiles', ['year'], unique=False)

    # 7. Faculty Profiles
    op.create_table(
        'faculty_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('designation', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_faculty_profiles_user_id'), 'faculty_profiles', ['user_id'], unique=True)
    op.create_index(op.f('ix_faculty_profiles_employee_id'), 'faculty_profiles', ['employee_id'], unique=True)

    # 8. Admin Profiles
    op.create_table(
        'admin_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('designation', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_profiles_user_id'), 'admin_profiles', ['user_id'], unique=True)
    op.create_index(op.f('ix_admin_profiles_employee_id'), 'admin_profiles', ['employee_id'], unique=True)

    # 9. Enrollments
    op.create_table(
        'enrollments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_profile_id', sa.String(length=36), nullable=False),
        sa.Column('course_id', sa.String(length=36), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('grade', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_profile_id', 'course_id', 'academic_year', 'semester', name='uq_student_course_term')
    )
    op.create_index(op.f('ix_enrollments_student_profile_id'), 'enrollments', ['student_profile_id'], unique=False)
    op.create_index(op.f('ix_enrollments_course_id'), 'enrollments', ['course_id'], unique=False)

    # 10. Query Logs
    op.create_table(
        'query_logs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('is_fallback', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_logs_timestamp'), 'query_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_query_logs_username'), 'query_logs', ['username'], unique=False)
    op.create_index(op.f('ix_query_logs_user_id'), 'query_logs', ['user_id'], unique=False)

    # 11. Query Feedback
    op.create_table(
        'query_feedback',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('query_id', sa.String(length=64), nullable=False),
        sa.Column('is_positive', sa.Boolean(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['query_id'], ['query_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_feedback_query_id'), 'query_feedback', ['query_id'], unique=False)

    # 12. Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('actor_username', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_event_type'), 'audit_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_events_timestamp'), 'audit_events', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_events_user_id'), 'audit_events', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('query_feedback')
    op.drop_table('query_logs')
    op.drop_table('enrollments')
    op.drop_table('admin_profiles')
    op.drop_table('faculty_profiles')
    op.drop_table('student_profiles')
    op.drop_table('courses')
    op.drop_table('programs')
    op.drop_table('departments')
    op.drop_table('users')
    op.drop_table('roles')
