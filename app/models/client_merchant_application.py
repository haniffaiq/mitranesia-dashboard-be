from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ClientMerchantApplication(TimestampMixin, Base):
    __tablename__ = "client_merchant_applications"

    client_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("client_users.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new", server_default="new")

    client_user = relationship("ClientUser", back_populates="merchant_applications")
