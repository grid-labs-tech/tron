"""add_environment_crossplane_config

Revision ID: env_crossplane_config
Revises: env_settings_single_json
Create Date: 2026-08-19

Store Crossplane config as a dedicated environment-scoped resource
instead of keys in the generic environment settings bag.
"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "env_crossplane_config"
down_revision: Union[str, None] = "env_settings_single_json"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STALE_SETTING_KEYS = {
    "crossplane_enabled",
    "crossplane_cluster_uuid",
    "crossplane_aws_region",
    "crossplane_provider_config",
}


def upgrade() -> None:
    op.create_table(
        "environment_crossplane_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("environment_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("cluster_uuid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("aws_region", sa.String(), nullable=False, server_default=""),
        sa.Column("aws_account_id", sa.String(), nullable=False, server_default=""),
        sa.Column("provider_config", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"], ["environments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["cluster_uuid"], ["clusters.uuid"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("environment_id", name="uq_crossplane_config_environment_id"),
        sa.UniqueConstraint("uuid", name="uq_crossplane_config_uuid"),
    )
    op.create_index(
        op.f("ix_environment_crossplane_configs_organization_id"),
        "environment_crossplane_configs",
        ["organization_id"],
        unique=False,
    )

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, settings FROM settings")).fetchall()
    for row in rows:
        settings = row[1]
        if isinstance(settings, str):
            settings = json.loads(settings)
        if not isinstance(settings, list):
            continue
        cleaned = [
            item
            for item in settings
            if not (isinstance(item, dict) and item.get("key") in _STALE_SETTING_KEYS)
        ]
        if cleaned == settings:
            continue
        conn.execute(
            sa.text(
                "UPDATE settings SET settings = CAST(:settings AS jsonb) WHERE id = :id"
            ),
            {"settings": json.dumps(cleaned), "id": row[0]},
        )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_environment_crossplane_configs_organization_id"),
        table_name="environment_crossplane_configs",
    )
    op.drop_table("environment_crossplane_configs")
