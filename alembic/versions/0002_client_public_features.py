"""client public features

Revision ID: 0002_client_public_features
Revises: 0001_initial
Create Date: 2026-04-04 10:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_client_public_features"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_client_users_email", "client_users", ["email"])

    op.create_table(
        "client_merchant_applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_user_id", sa.Uuid(), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=False),
        sa.Column("business_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_user_id"], ["client_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_client_merchant_applications_client_user_id", "client_merchant_applications", ["client_user_id"])

    op.create_table(
        "client_merchant_inquiries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_user_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("inquiry_type", sa.String(length=32), nullable=False, server_default="contact"),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_user_id"], ["client_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_client_merchant_inquiries_client_user_id", "client_merchant_inquiries", ["client_user_id"])
    op.create_index("ix_client_merchant_inquiries_merchant_id", "client_merchant_inquiries", ["merchant_id"])


def downgrade() -> None:
    op.drop_index("ix_client_merchant_inquiries_merchant_id", table_name="client_merchant_inquiries")
    op.drop_index("ix_client_merchant_inquiries_client_user_id", table_name="client_merchant_inquiries")
    op.drop_table("client_merchant_inquiries")
    op.drop_index("ix_client_merchant_applications_client_user_id", table_name="client_merchant_applications")
    op.drop_table("client_merchant_applications")
    op.drop_index("ix_client_users_email", table_name="client_users")
    op.drop_table("client_users")
