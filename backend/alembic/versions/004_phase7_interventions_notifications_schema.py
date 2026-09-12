"""Phase 7 Intelligent Interventions, Action Plans & Notifications Schema Migration.

Revision ID: 004_phase7_interventions_notifications_schema
Revises: 003_phase6_enterprise_governance_schema
Create Date: 2026-09-12 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_phase7_interventions_notifications_schema'
down_revision: Union[str, None] = '003_phase6_enterprise_governance_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Academic Interventions
    op.create_table(
        'academic_interventions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_profile_id', sa.String(length=36), nullable=False),
        sa.Column('issued_by_id', sa.String(length=36), nullable=False),
        sa.Column('risk_category', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ),
        sa.ForeignKeyConstraint(['issued_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_interventions_student_profile_id'), 'academic_interventions', ['student_profile_id'], unique=False)
    op.create_index(op.f('ix_academic_interventions_issued_by_id'), 'academic_interventions', ['issued_by_id'], unique=False)
    op.create_index(op.f('ix_academic_interventions_risk_category'), 'academic_interventions', ['risk_category'], unique=False)
    op.create_index(op.f('ix_academic_interventions_status'), 'academic_interventions', ['status'], unique=False)

    # 2. Student Action Plans
    op.create_table(
        'student_action_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_profile_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('target_attendance_pct', sa.Float(), nullable=True),
        sa.Column('target_sgpa', sa.Float(), nullable=True),
        sa.Column('milestones', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_action_plans_student_profile_id'), 'student_action_plans', ['student_profile_id'], unique=False)
    op.create_index(op.f('ix_student_action_plans_status'), 'student_action_plans', ['status'], unique=False)

    # 3. Notification Alerts
    op.create_table(
        'notification_alerts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=40), nullable=False, server_default='academic'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='info'),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('link', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_alerts_user_id'), 'notification_alerts', ['user_id'], unique=False)
    op.create_index(op.f('ix_notification_alerts_category'), 'notification_alerts', ['category'], unique=False)
    op.create_index(op.f('ix_notification_alerts_severity'), 'notification_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_notification_alerts_is_read'), 'notification_alerts', ['is_read'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notification_alerts_is_read'), table_name='notification_alerts')
    op.drop_index(op.f('ix_notification_alerts_severity'), table_name='notification_alerts')
    op.drop_index(op.f('ix_notification_alerts_category'), table_name='notification_alerts')
    op.drop_index(op.f('ix_notification_alerts_user_id'), table_name='notification_alerts')
    op.drop_table('notification_alerts')

    op.drop_index(op.f('ix_student_action_plans_status'), table_name='student_action_plans')
    op.drop_index(op.f('ix_student_action_plans_student_profile_id'), table_name='student_action_plans')
    op.drop_table('student_action_plans')

    op.drop_index(op.f('ix_academic_interventions_status'), table_name='academic_interventions')
    op.drop_index(op.f('ix_academic_interventions_risk_category'), table_name='academic_interventions')
    op.drop_index(op.f('ix_academic_interventions_issued_by_id'), table_name='academic_interventions')
    op.drop_index(op.f('ix_academic_interventions_student_profile_id'), table_name='academic_interventions')
    op.drop_table('academic_interventions')
