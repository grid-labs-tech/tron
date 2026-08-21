"""add_template_slug_and_settings

Revision ID: add_template_slug_settings
Revises: env_settings_single_json
Create Date: 2026-08-21

Add slug (unique per organization) and template_settings JSON to templates.
"""

from typing import Sequence, Union
import re
from alembic import op
import sqlalchemy as sa

revision: str = "add_template_slug_settings"
down_revision: Union[str, None] = "env_settings_single_json"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = "template"
    if not slug[0].isalpha():
        slug = f"t_{slug}"
    return slug


def upgrade() -> None:
    op.add_column("templates", sa.Column("slug", sa.String(), nullable=True))
    op.add_column(
        "templates",
        sa.Column(
            "template_settings",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, name, organization_id FROM templates")
    ).fetchall()
    used: dict[int, set[str]] = {}
    for row in rows:
        template_id, name, organization_id = row[0], row[1], row[2]
        used.setdefault(organization_id, set())
        base = _slugify(name)
        slug = base
        i = 2
        while slug in used[organization_id]:
            slug = f"{base}_{i}"
            i += 1
        used[organization_id].add(slug)
        conn.execute(
            sa.text("UPDATE templates SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": template_id},
        )

    op.alter_column("templates", "slug", existing_type=sa.String(), nullable=False)
    op.create_unique_constraint(
        "uix_templates_organization_slug",
        "templates",
        ["organization_id", "slug"],
    )


def downgrade() -> None:
    op.drop_constraint("uix_templates_organization_slug", "templates", type_="unique")
    op.drop_column("templates", "template_settings")
    op.drop_column("templates", "slug")
