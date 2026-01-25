"""add_namespace_to_applications

Revision ID: add_namespace_to_apps
Revises: add_gateway_config
Create Date: 2026-01-24 14:00:00.000000

This migration adds the 'namespace' column to the applications table.
For existing applications (legacy), the namespace is set to the application name.
New applications will have namespace set to 'tron-ns-{name}'.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_namespace_to_apps'
down_revision: Union[str, None] = 'add_gateway_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add namespace column (nullable initially for migration)
    op.add_column('applications', sa.Column('namespace', sa.String(), nullable=True))

    # Create unique index for namespace
    op.create_index('ix_applications_namespace', 'applications', ['namespace'], unique=True)

    # For existing applications, set namespace = name (legacy mode, no prefix)
    # This ensures backward compatibility - existing apps keep working
    op.execute("""
        UPDATE applications
        SET namespace = name
        WHERE namespace IS NULL
    """)


def downgrade() -> None:
    # Remove the index first
    op.drop_index('ix_applications_namespace', table_name='applications')
    # Remove namespace column
    op.drop_column('applications', 'namespace')
