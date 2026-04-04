"""image base64 assets

Revision ID: 0004_image_base64_assets
Revises: 0003_carousel_items
Create Date: 2026-04-04 18:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_image_base64_assets"
down_revision = "0003_carousel_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("logo_base64", sa.Text(), nullable=True))
    op.alter_column("merchants", "logo_url", existing_type=sa.Text(), nullable=True)

    op.add_column("insight_articles", sa.Column("image_base64", sa.Text(), nullable=True))
    op.alter_column("insight_articles", "image", existing_type=sa.Text(), nullable=True)

    op.add_column("carousel_items", sa.Column("image_base64", sa.Text(), nullable=True))
    op.alter_column("carousel_items", "image_url", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column("carousel_items", "image_url", existing_type=sa.Text(), nullable=False)
    op.drop_column("carousel_items", "image_base64")

    op.alter_column("insight_articles", "image", existing_type=sa.Text(), nullable=False)
    op.drop_column("insight_articles", "image_base64")

    op.alter_column("merchants", "logo_url", existing_type=sa.Text(), nullable=False)
    op.drop_column("merchants", "logo_base64")
