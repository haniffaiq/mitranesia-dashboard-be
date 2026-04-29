"""merchant images gallery

Revision ID: 0006_merchant_images
Revises: 0005_merchant_official_partner
Create Date: 2026-04-29 09:40:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_merchant_images"
down_revision = "0005_merchant_official_partner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "merchant_images",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "merchant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("image_base64", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("merchant_images_merchant_id_idx", "merchant_images", ["merchant_id"])


def downgrade() -> None:
    op.drop_index("merchant_images_merchant_id_idx", table_name="merchant_images")
    op.drop_table("merchant_images")
