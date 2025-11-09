"""Initial schema migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration runs the initial schema SQL file
    # The actual schema is defined in schema/*.sql files
    # This is a placeholder that references the SQL migration
    pass


def downgrade() -> None:
    # Drop all tables in reverse order
    pass

