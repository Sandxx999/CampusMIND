"""Phase 6 Enterprise Governance & System Schema Migration.

Revision ID: 003_phase6_enterprise_governance_schema
Revises: 002_phase3_institutional_schema
Create Date: 2026-09-12 13:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_phase6_enterprise_governance_schema'
down_revision: Union[str, None] = '002_phase3_institutional_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. SSO Provider Configs
    op.create_table(
        'sso_provider_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('issuer_url', sa.String(length=255), nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('allow_jit_provisioning', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sso_provider_configs_is_active'), 'sso_provider_configs', ['is_active'], unique=False)

    # 2. System Tasks
    op.create_table(
        'system_tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('progress_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('initiated_by', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_tasks_task_type'), 'system_tasks', ['task_type'], unique=False)
    op.create_index(op.f('ix_system_tasks_status'), 'system_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_system_tasks_initiated_by'), 'system_tasks', ['initiated_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_system_tasks_initiated_by'), table_name='system_tasks')
    op.drop_index(op.f('ix_system_tasks_status'), table_name='system_tasks')
    op.drop_index(op.f('ix_system_tasks_task_type'), table_name='system_tasks')
    op.drop_table('system_tasks')
    op.drop_index(op.f('ix_sso_provider_configs_is_active'), table_name='sso_provider_configs')
    op.drop_table('sso_provider_configs')
