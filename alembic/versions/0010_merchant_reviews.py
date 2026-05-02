"""merchant reviews + AggregateRating prep

Revision ID: 0010_merchant_reviews
Revises: 0009_newsletter
Create Date: 2026-05-02 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_merchant_reviews"
down_revision = "0009_newsletter"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "merchant_reviews",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("merchant_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewer_name", sa.String(120), nullable=False),
        sa.Column("reviewer_email", sa.String(320), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("is_verified_mitra", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="merchant_reviews_rating_range"),
        sa.CheckConstraint("status IN ('pending','approved','rejected')", name="merchant_reviews_status_enum"),
    )
    op.create_index("merchant_reviews_merchant_status_idx", "merchant_reviews", ["merchant_id", "status"])


def downgrade() -> None:
    op.drop_index("merchant_reviews_merchant_status_idx", table_name="merchant_reviews")
    op.drop_table("merchant_reviews")
