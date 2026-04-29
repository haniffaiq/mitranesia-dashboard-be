"""newsletter subscribers

Revision ID: 0009_newsletter
Revises: 0008_soft_delete
Create Date: 2026-04-29 10:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_newsletter"
down_revision = "0008_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "newsletter_subscribers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("subscribed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("unsubscribed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("newsletter_subscribers_email_idx", "newsletter_subscribers", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("newsletter_subscribers_email_idx", table_name="newsletter_subscribers")
    op.drop_table("newsletter_subscribers")
