"""full-text search GIN indexes

Revision ID: 0007_fts_indexes
Revises: 0006_merchant_images
Create Date: 2026-04-29 10:00:00
"""

from __future__ import annotations

from alembic import op

revision = "0007_fts_indexes"
down_revision = "0006_merchant_images"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS merchants_search_idx ON merchants
        USING GIN (
            to_tsvector(
                'simple',
                coalesce(name, '') || ' ' ||
                coalesce(slug, '') || ' ' ||
                coalesce(category, '') || ' ' ||
                coalesce(description, '')
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS insight_articles_search_idx ON insight_articles
        USING GIN (
            to_tsvector(
                'simple',
                coalesce(title, '') || ' ' ||
                coalesce(slug, '') || ' ' ||
                coalesce(category, '') || ' ' ||
                coalesce(excerpt, '')
            )
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS merchants_search_idx")
    op.execute("DROP INDEX IF EXISTS insight_articles_search_idx")
