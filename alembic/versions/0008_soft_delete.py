"""soft delete deleted_at columns

Revision ID: 0008_soft_delete
Revises: 0007_fts_indexes
Create Date: 2026-04-29 10:15:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_soft_delete"
down_revision = "0007_fts_indexes"
branch_labels = None
depends_on = None


TABLES = ("merchants", "insight_articles", "admin_users")


def upgrade() -> None:
    for tbl in TABLES:
        op.add_column(tbl, sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
        op.create_index(
            f"{tbl}_deleted_at_idx",
            tbl,
            ["deleted_at"],
            postgresql_where=sa.text("deleted_at IS NOT NULL"),
        )


def downgrade() -> None:
    for tbl in TABLES:
        op.drop_index(f"{tbl}_deleted_at_idx", table_name=tbl)
        op.drop_column(tbl, "deleted_at")
