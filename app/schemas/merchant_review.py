from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field

from app.schemas.common import APIModel


def _to_camel(s: str) -> str:
    head, *tail = s.split("_")
    return head + "".join(w.title() for w in tail)


class _CamelModel(APIModel):
    """Public client schema: camelCase aliases (konsisten ClientMerchant)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=_to_camel)


# Public client endpoints — camelCase
class ReviewCreate(_CamelModel):
    reviewer_name: str = Field(min_length=2, max_length=120)
    reviewer_email: EmailStr | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewRead(_CamelModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    reviewer_name: str
    rating: int
    comment: str | None
    status: str
    is_verified_mitra: bool
    created_at: datetime


# Admin/dashboard endpoints — snake_case (konsisten dashboard FE existing)
class ReviewAdminRead(APIModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    reviewer_name: str
    reviewer_email: str | None
    rating: int
    comment: str | None
    status: str
    is_verified_mitra: bool
    created_at: datetime
    updated_at: datetime


class ReviewStatusUpdate(APIModel):
    status: str = Field(pattern=r"^(pending|approved|rejected)$")
    is_verified_mitra: bool | None = None
