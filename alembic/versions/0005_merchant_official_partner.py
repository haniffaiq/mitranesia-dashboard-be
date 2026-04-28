"""merchant official partner

Revision ID: 0005_merchant_official_partner
Revises: 0004_image_base64_assets
Create Date: 2026-04-28 02:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_merchant_official_partner"
down_revision = "0004_image_base64_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "merchants",
        sa.Column(
            "is_official_partner",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("merchants", "is_official_partner")
