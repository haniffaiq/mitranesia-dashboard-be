from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class CarouselItem(TimestampMixin, Base):
    __tablename__ = "carousel_items"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(64), nullable=False, default="trending-up")
    highlight: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(String(128), nullable=False)
    cta_label: Mapped[str] = mapped_column(String(100), nullable=False, default="Pelajari Lebih Lanjut")
    cta_href: Mapped[str] = mapped_column(Text, nullable=False, default="/merchants")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
