"""rename_gateway_to_private_add_public

Revision ID: rename_gateway_public_private
Revises: add_namespace_to_applications
Create Date: 2026-01-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rename_gateway_public_private'
down_revision: Union[str, None] = 'add_namespace_to_apps'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename existing gateway columns to private_gateway
    op.alter_column('clusters', 'gateway_namespace', new_column_name='private_gateway_namespace')
    op.alter_column('clusters', 'gateway_name', new_column_name='private_gateway_name')
    
    # Add new public_gateway columns
    op.add_column('clusters', sa.Column('public_gateway_namespace', sa.String(), nullable=True))
    op.add_column('clusters', sa.Column('public_gateway_name', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove public_gateway columns
    op.drop_column('clusters', 'public_gateway_name')
    op.drop_column('clusters', 'public_gateway_namespace')
    
    # Rename private_gateway columns back to gateway
    op.alter_column('clusters', 'private_gateway_namespace', new_column_name='gateway_namespace')
    op.alter_column('clusters', 'private_gateway_name', new_column_name='gateway_name')
