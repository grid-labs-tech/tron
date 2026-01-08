"""initial_schema

Revision ID: initial_schema
Revises:
Create Date: 2026-01-03 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create webapptype ENUM type if it doesn't exist
    conn = op.get_bind()
    conn.execute(sa.text("DO $$ BEGIN CREATE TYPE webapptype AS ENUM ('webapp', 'worker', 'cron'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))

    # Create environments table
    op.create_table(
        'environments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_environments_id'), 'environments', ['id'], unique=False)
    op.create_index(op.f('ix_environments_name'), 'environments', ['name'], unique=True)

    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('repository', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uix_application_name'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
    op.create_index(op.f('ix_applications_name'), 'applications', ['name'], unique=True)

    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('environment_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', 'environment_id', name='uq_key_environment'),
        sa.UniqueConstraint('uuid')
    )

    # Create clusters table
    op.create_table(
        'clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('api_address', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('environment_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_address'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('uuid', name='uix_cluster_uuid')
    )
    op.create_index(op.f('ix_clusters_id'), 'clusters', ['id'], unique=False)
    op.create_index(op.f('ix_clusters_name'), 'clusters', ['name'], unique=True)

    # Create templates table
    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('variables_schema', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_templates_id'), 'templates', ['id'], unique=False)
    op.create_index(op.f('ix_templates_name'), 'templates', ['name'], unique=False)
    op.create_index(op.f('ix_templates_category'), 'templates', ['category'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=False)

    # Create tokens table
    op.create_table(
        'tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_tokens_id'), 'tokens', ['id'], unique=False)
    op.create_index(op.f('ix_tokens_token_hash'), 'tokens', ['token_hash'], unique=True)

    # Create component_template_configs table
    op.create_table(
        'component_template_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('component_type', sa.String(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('render_order', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('component_type', 'template_id', name='uix_component_type_template'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_component_template_configs_id'), 'component_template_configs', ['id'], unique=False)
    op.create_index(op.f('ix_component_template_configs_component_type'), 'component_template_configs', ['component_type'], unique=False)

    # Create instances table
    op.create_table(
        'instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('environment_id', sa.Integer(), nullable=False),
        sa.Column('image', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', 'environment_id', name='uix_application_environment'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_instances_id'), 'instances', ['id'], unique=False)

    # Create application_components table
    op.create_table(
        'application_components',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', postgresql.ENUM('webapp', 'worker', 'cron', name='webapptype', create_type=False), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_application_components_id'), 'application_components', ['id'], unique=False)

    # Create cluster_instances table
    op.create_table(
        'cluster_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_component_id', sa.Integer(), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_component_id'], ['application_components.id'], ),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cluster_id', 'application_component_id', name='cluster_instance_cluster_id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_cluster_instances_id'), 'cluster_instances', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of dependencies
    op.drop_index(op.f('ix_cluster_instances_id'), table_name='cluster_instances')
    op.drop_table('cluster_instances')

    op.drop_index(op.f('ix_application_components_id'), table_name='application_components')
    op.drop_table('application_components')

    op.drop_index(op.f('ix_instances_id'), table_name='instances')
    op.drop_table('instances')

    op.drop_index(op.f('ix_component_template_configs_component_type'), table_name='component_template_configs')
    op.drop_index(op.f('ix_component_template_configs_id'), table_name='component_template_configs')
    op.drop_table('component_template_configs')

    op.drop_index(op.f('ix_tokens_token_hash'), table_name='tokens')
    op.drop_index(op.f('ix_tokens_id'), table_name='tokens')
    op.drop_table('tokens')

    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

    op.drop_index(op.f('ix_templates_category'), table_name='templates')
    op.drop_index(op.f('ix_templates_name'), table_name='templates')
    op.drop_index(op.f('ix_templates_id'), table_name='templates')
    op.drop_table('templates')

    op.drop_table('settings')

    op.drop_index(op.f('ix_clusters_name'), table_name='clusters')
    op.drop_index(op.f('ix_clusters_id'), table_name='clusters')
    op.drop_table('clusters')

    op.drop_index(op.f('ix_applications_name'), table_name='applications')
    op.drop_index(op.f('ix_applications_id'), table_name='applications')
    op.drop_table('applications')

    op.drop_index(op.f('ix_environments_name'), table_name='environments')
    op.drop_index(op.f('ix_environments_id'), table_name='environments')
    op.drop_table('environments')

    # Drop ENUM type
    op.execute(sa.text("DROP TYPE IF EXISTS webapptype"))

