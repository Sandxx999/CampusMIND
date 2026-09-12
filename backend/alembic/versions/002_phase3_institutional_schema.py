"""Phase 3 Institutional Schema Migration.

Revision ID: 002_phase3_institutional_schema
Revises: 001_initial_canonical_schema
Create Date: 2026-09-12 12:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_phase3_institutional_schema'
down_revision: Union[str, None] = '001_initial_canonical_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Academic Terms
    op.create_table(
        'academic_terms',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_terms_code'), 'academic_terms', ['code'], unique=True)
    op.create_index(op.f('ix_academic_terms_academic_year'), 'academic_terms', ['academic_year'], unique=False)
    op.create_index(op.f('ix_academic_terms_is_current'), 'academic_terms', ['is_current'], unique=False)

    # 2. Course Offerings
    op.create_table(
        'course_offerings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('course_id', sa.String(length=36), nullable=False),
        sa.Column('term_id', sa.String(length=36), nullable=False),
        sa.Column('faculty_profile_id', sa.String(length=36), nullable=True),
        sa.Column('section', sa.String(length=20), nullable=False, server_default='A'),
        sa.Column('room', sa.String(length=50), nullable=True),
        sa.Column('schedule', sa.String(length=100), nullable=True),
        sa.Column('max_capacity', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['faculty_profile_id'], ['faculty_profiles.id'], ),
        sa.ForeignKeyConstraint(['term_id'], ['academic_terms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'term_id', 'section', name='uq_course_term_section')
    )
    op.create_index(op.f('ix_course_offerings_course_id'), 'course_offerings', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_offerings_term_id'), 'course_offerings', ['term_id'], unique=False)
    op.create_index(op.f('ix_course_offerings_faculty_profile_id'), 'course_offerings', ['faculty_profile_id'], unique=False)

    # 3. Add course_offering_id to Enrollments
    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('course_offering_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key('fk_enrollments_course_offering_id', 'course_offerings', ['course_offering_id'], ['id'])
        batch_op.create_index('ix_enrollments_course_offering_id', ['course_offering_id'], unique=False)

    # 4. Attendance Records
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_profile_id', sa.String(length=36), nullable=False),
        sa.Column('course_offering_id', sa.String(length=36), nullable=True),
        sa.Column('course_id', sa.String(length=36), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('recorded_by_id', sa.String(length=36), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['course_offering_id'], ['course_offerings.id'], ),
        sa.ForeignKeyConstraint(['recorded_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_profile_id', 'course_offering_id', 'date', name='uq_student_offering_date')
    )
    op.create_index(op.f('ix_attendance_records_student_profile_id'), 'attendance_records', ['student_profile_id'], unique=False)
    op.create_index(op.f('ix_attendance_records_course_offering_id'), 'attendance_records', ['course_offering_id'], unique=False)
    op.create_index(op.f('ix_attendance_records_course_id'), 'attendance_records', ['course_id'], unique=False)
    op.create_index(op.f('ix_attendance_records_date'), 'attendance_records', ['date'], unique=False)

    # 5. Assessments
    op.create_table(
        'assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('assessment_type', sa.String(length=30), nullable=False),
        sa.Column('max_marks', sa.Float(), nullable=False),
        sa.Column('weightage', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('assessment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('course_offering_id', sa.String(length=36), nullable=True),
        sa.Column('course_id', sa.String(length=36), nullable=True),
        sa.Column('created_by_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='published'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['course_offering_id'], ['course_offerings.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessments_course_offering_id'), 'assessments', ['course_offering_id'], unique=False)
    op.create_index(op.f('ix_assessments_course_id'), 'assessments', ['course_id'], unique=False)
    op.create_index(op.f('ix_assessments_status'), 'assessments', ['status'], unique=False)

    # 6. Assessment Grades
    op.create_table(
        'assessment_grades',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('assessment_id', sa.String(length=36), nullable=False),
        sa.Column('student_profile_id', sa.String(length=36), nullable=False),
        sa.Column('obtained_marks', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(length=5), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('evaluator_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ),
        sa.ForeignKeyConstraint(['evaluator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id', 'student_profile_id', name='uq_assessment_student')
    )
    op.create_index(op.f('ix_assessment_grades_assessment_id'), 'assessment_grades', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_assessment_grades_student_profile_id'), 'assessment_grades', ['student_profile_id'], unique=False)

    # 7. Announcements
    op.create_table(
        'announcements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('audience', sa.String(length=30), nullable=False, server_default='all'),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('program_id', sa.String(length=36), nullable=True),
        sa.Column('course_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='published'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('publish_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_announcements_author_id'), 'announcements', ['author_id'], unique=False)
    op.create_index(op.f('ix_announcements_audience'), 'announcements', ['audience'], unique=False)
    op.create_index(op.f('ix_announcements_department_id'), 'announcements', ['department_id'], unique=False)
    op.create_index(op.f('ix_announcements_program_id'), 'announcements', ['program_id'], unique=False)
    op.create_index(op.f('ix_announcements_status'), 'announcements', ['status'], unique=False)

    # 8. Campus Events
    op.create_table(
        'campus_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=150), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organizer_id', sa.String(length=36), nullable=False),
        sa.Column('audience', sa.String(length=30), nullable=False, server_default='all'),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('requires_registration', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='scheduled'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campus_events_start_time'), 'campus_events', ['start_time'], unique=False)
    op.create_index(op.f('ix_campus_events_organizer_id'), 'campus_events', ['organizer_id'], unique=False)
    op.create_index(op.f('ix_campus_events_audience'), 'campus_events', ['audience'], unique=False)
    op.create_index(op.f('ix_campus_events_department_id'), 'campus_events', ['department_id'], unique=False)
    op.create_index(op.f('ix_campus_events_status'), 'campus_events', ['status'], unique=False)

    # 9. Event Registrations
    op.create_table(
        'event_registrations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='registered'),
        sa.Column('registered_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['campus_events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'user_id', name='uq_event_user_registration')
    )
    op.create_index(op.f('ix_event_registrations_event_id'), 'event_registrations', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_registrations_user_id'), 'event_registrations', ['user_id'], unique=False)

    # 10. Knowledge Documents
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('audience', sa.String(length=30), nullable=False, server_default='all'),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('uploader_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_documents_title'), 'knowledge_documents', ['title'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_category'), 'knowledge_documents', ['category'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_department_id'), 'knowledge_documents', ['department_id'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_audience'), 'knowledge_documents', ['audience'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_is_active'), 'knowledge_documents', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_table('knowledge_documents')
    op.drop_table('event_registrations')
    op.drop_table('campus_events')
    op.drop_table('announcements')
    op.drop_table('assessment_grades')
    op.drop_table('assessments')
    op.drop_table('attendance_records')
    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        batch_op.drop_index('ix_enrollments_course_offering_id')
        batch_op.drop_constraint('fk_enrollments_course_offering_id', type_='foreignkey')
        batch_op.drop_column('course_offering_id')
    op.drop_table('course_offerings')
    op.drop_table('academic_terms')
