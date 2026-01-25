"""add_gateway_config_to_clusters

Revision ID: add_gateway_config
Revises: initial_schema
Create Date: 2026-01-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_gateway_config'
down_revision: Union[str, None] = 'initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add gateway configuration columns to clusters table
    op.add_column('clusters', sa.Column('gateway_namespace', sa.String(), nullable=True))
    op.add_column('clusters', sa.Column('gateway_name', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove gateway configuration columns from clusters table
    op.drop_column('clusters', 'gateway_name')
    op.drop_column('clusters', 'gateway_namespace')
