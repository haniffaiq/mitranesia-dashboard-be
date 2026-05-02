from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import APIModel


class ReviewCreate(APIModel):
    reviewer_name: str = Field(min_length=2, max_length=120)
    reviewer_email: EmailStr | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewRead(APIModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    reviewer_name: str
    rating: int
    comment: str | None
    status: str
    is_verified_mitra: bool
    created_at: datetime


class ReviewAdminRead(ReviewRead):
    reviewer_email: str | None
    updated_at: datetime


class ReviewStatusUpdate(APIModel):
    status: str = Field(pattern=r"^(pending|approved|rejected)$")
    is_verified_mitra: bool | None = None


class ReviewSummary(APIModel):
    """Aggregated rating untuk merchant."""
    rating_value: float
    rating_count: int
