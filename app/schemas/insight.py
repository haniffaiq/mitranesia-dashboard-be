from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.schemas.common import APIModel
from app.schemas.image_asset import require_image_source, validate_optional_image_base64

InsightStatus = Literal["draft", "published", "archived"]


class InsightArticleBase(BaseModel):
    title: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    category: str = Field(min_length=1)
    author: str = Field(min_length=1)
    image: HttpUrl | None = None
    image_base64: str | None = None
    excerpt: str = Field(min_length=1)
    read_time: str = Field(min_length=1)
    content: list[str] = Field(min_length=1)
    status: InsightStatus

    @field_validator("image_base64")
    @classmethod
    def validate_image_base64(cls, value: str | None) -> str | None:
        return validate_optional_image_base64(value)

    @model_validator(mode="after")
    def validate_image_source(self) -> "InsightArticleBase":
        require_image_source(str(self.image) if self.image else None, self.image_base64)
        return self


class InsightArticleCreate(InsightArticleBase):
    pass


class InsightArticleUpdate(InsightArticleBase):
    pass


class InsightStatusUpdate(BaseModel):
    status: InsightStatus


class InsightArticleRead(APIModel):
    id: str
    title: str
    slug: str
    category: str
    author: str
    image: str
    image_base64: str | None = None
    excerpt: str
    read_time: str
    content: list[str]
    status: InsightStatus
    published_at: datetime | None = None
    created_at: str
    updated_at: str
