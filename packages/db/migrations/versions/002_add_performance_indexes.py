"""Add performance indexes

Revision ID: 002_perf_indexes
Revises: 001_initial
Create Date: 2025-11-08 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_perf_indexes'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite indexes for common query patterns
    
    # Projects: owner + status
    op.create_index(
        'idx_projects_owner_status',
        'projects',
        ['owner_id', 'status'],
        unique=False
    )
    
    # Tasks: project + status + priority
    op.create_index(
        'idx_tasks_project_status_priority',
        'tasks',
        ['project_id', 'status', 'priority'],
        unique=False
    )
    
    # Tasks: assigned user + status
    op.create_index(
        'idx_tasks_assigned_status',
        'tasks',
        ['assigned_to_user_id', 'status'],
        unique=False
    )
    
    # Agents: status + type
    op.create_index(
        'idx_agents_status_type',
        'agents',
        ['status', 'type'],
        unique=False
    )
    
    # Skill executions: skill + status + created_at
    op.create_index(
        'idx_skill_executions_skill_status_created',
        'skill_executions',
        ['skill_id', 'status', 'created_at'],
        unique=False
    )
    
    # Audit logs: user + action + created_at
    op.create_index(
        'idx_audit_logs_user_action_created',
        'audit_logs',
        ['user_id', 'action', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_audit_logs_user_action_created', table_name='audit_logs')
    op.drop_index('idx_skill_executions_skill_status_created', table_name='skill_executions')
    op.drop_index('idx_agents_status_type', table_name='agents')
    op.drop_index('idx_tasks_assigned_status', table_name='tasks')
    op.drop_index('idx_tasks_project_status_priority', table_name='tasks')
    op.drop_index('idx_projects_owner_status', table_name='projects')

