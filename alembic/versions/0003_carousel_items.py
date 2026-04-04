"""carousel items

Revision ID: 0003_carousel_items
Revises: 0002_client_public_features
Create Date: 2026-04-04 16:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_carousel_items"
down_revision = "0002_client_public_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "carousel_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("tag", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=64), nullable=False, server_default="trending-up"),
        sa.Column("highlight", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("color", sa.String(length=128), nullable=False),
        sa.Column("cta_label", sa.String(length=100), nullable=False, server_default="Pelajari Lebih Lanjut"),
        sa.Column("cta_href", sa.Text(), nullable=False, server_default="/merchants"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        """
        INSERT INTO carousel_items (
            id, title, image_url, tag, icon, highlight, description, color, cta_label, cta_href, sort_order, is_active, created_at, updated_at
        ) VALUES
        (
            '11111111-1111-1111-1111-111111111111',
            'Bisnis Autopilot',
            'https://placehold.co/1600x720/png?text=Bisnis+Autopilot',
            'Trending 2025',
            'trending-up',
            '100% Keuntungan',
            'Mulai bisnismu sekarang dengan dukungan penuh dari tim ahli kami. Tanpa ribet, langsung profit.',
            'from-primary/95 via-primary/60',
            'Pelajari Lebih Lanjut',
            '/merchants',
            1,
            TRUE,
            NOW(),
            NOW()
        ),
        (
            '22222222-2222-2222-2222-222222222222',
            'Waralaba Kopi',
            'https://placehold.co/1600x720/png?text=Waralaba+Kopi',
            'F&B Terlaris',
            'coffee',
            'ROI Tinggi',
            'Bergabung dengan jaringan coffee shop dengan pertumbuhan tercepat di Indonesia. Konsep modern dan diminati.',
            'from-amber-900/95 via-amber-800/60',
            'Lihat Merchant',
            '/merchants?category=Food+%26+Beverage',
            2,
            TRUE,
            NOW(),
            NOW()
        ),
        (
            '33333333-3333-3333-3333-333333333333',
            'Pusat Kebugaran',
            'https://placehold.co/1600x720/png?text=Pusat+Kebugaran',
            'Gaya Hidup Sehat',
            'dumbbell',
            'Member Setia',
            'Bisnis gym modern dengan peralatan premium. Peluang emas di industri kesehatan yang sedang naik daun.',
            'from-slate-900/95 via-slate-800/60',
            'Eksplor Merchant',
            '/merchants?category=Fitness',
            3,
            TRUE,
            NOW(),
            NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM carousel_items WHERE id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333')")
    op.drop_table("carousel_items")
