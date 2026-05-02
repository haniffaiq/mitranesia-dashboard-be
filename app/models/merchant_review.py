from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class MerchantReview(TimestampMixin, Base):
    __tablename__ = "merchant_reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="merchant_reviews_rating_range"),
        CheckConstraint("status IN ('pending','approved','rejected')", name="merchant_reviews_status_enum"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    reviewer_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    is_verified_mitra: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="reviews")
