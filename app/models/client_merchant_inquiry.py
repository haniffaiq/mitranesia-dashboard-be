from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ClientMerchantInquiry(TimestampMixin, Base):
    __tablename__ = "client_merchant_inquiries"

    client_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("client_users.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inquiry_type: Mapped[str] = mapped_column(String(32), nullable=False, default="contact", server_default="contact")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new", server_default="new")

    client_user = relationship("ClientUser", back_populates="merchant_inquiries")
    merchant = relationship("Merchant")
