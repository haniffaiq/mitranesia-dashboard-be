from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.schemas.common import APIModel
from app.schemas.image_asset import require_image_source, validate_optional_image_base64


class CarouselItemBase(BaseModel):
    title: str = Field(min_length=1)
    image_url: HttpUrl | None = None
    image_base64: str | None = None
    tag: str = Field(min_length=1)
    icon: str = Field(min_length=1)
    highlight: str = Field(min_length=1)
    description: str = Field(min_length=1)
    color: str = Field(min_length=1)
    cta_label: str = Field(min_length=1)
    cta_href: str = Field(min_length=1)
    sort_order: int = 0
    is_active: bool = True

    @field_validator("image_base64")
    @classmethod
    def validate_image_base64(cls, value: str | None) -> str | None:
        return validate_optional_image_base64(value)

    @model_validator(mode="after")
    def validate_image_source(self) -> "CarouselItemBase":
        require_image_source(str(self.image_url) if self.image_url else None, self.image_base64)
        return self


class CarouselItemCreate(CarouselItemBase):
    pass


class CarouselItemUpdate(CarouselItemBase):
    pass


class CarouselStatusUpdate(BaseModel):
    is_active: bool


class CarouselItemRead(APIModel):
    id: str
    title: str
    image_url: str
    image_base64: str | None = None
    tag: str
    icon: str
    highlight: str
    description: str
    color: str
    cta_label: str
    cta_href: str
    sort_order: int
    is_active: bool
    created_at: str
    updated_at: str
