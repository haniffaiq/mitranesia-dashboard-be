from __future__ import annotations

from decimal import Decimal

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Merchant(TimestampMixin, Base):
    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    bep_months: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_top_merchant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_official_partner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    packages = relationship(
        "MerchantPackage",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="MerchantPackage.sort_order",
    )
    images = relationship(
        "MerchantImage",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="MerchantImage.sort_order",
    )
