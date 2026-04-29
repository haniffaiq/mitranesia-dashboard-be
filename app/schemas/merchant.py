from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.schemas.common import APIModel
from app.schemas.image_asset import require_image_source, validate_optional_image_base64

MerchantType = Literal["Self Managed", "Semi-Autopilot", "Full-Autopilot", "Auto Pilot"]


class MerchantPackageBase(BaseModel):
    name: str = Field(min_length=1)
    price: int = Field(gt=0)
    description: str = Field(min_length=1)
    sort_order: int = 0


class MerchantPackageCreate(MerchantPackageBase):
    pass


class MerchantPackageUpdate(MerchantPackageBase):
    id: str | None = None


class MerchantPackageRead(APIModel):
    id: str
    name: str
    price: int
    description: str
    sort_order: int
    created_at: str
    updated_at: str


class MerchantImageBase(BaseModel):
    label: str | None = None
    image_url: HttpUrl | None = None
    image_base64: str | None = None
    sort_order: int = 0

    @field_validator("image_base64")
    @classmethod
    def validate_image_base64(cls, value: str | None) -> str | None:
        return validate_optional_image_base64(value)

    @model_validator(mode="after")
    def validate_image_source(self) -> "MerchantImageBase":
        require_image_source(str(self.image_url) if self.image_url else None, self.image_base64)
        return self


class MerchantImageCreate(MerchantImageBase):
    pass


class MerchantImageUpdate(MerchantImageBase):
    id: str | None = None


class MerchantImageRead(APIModel):
    id: str
    label: str | None = None
    image_url: str | None = None
    image_base64: str | None = None
    sort_order: int
    created_at: str
    updated_at: str


class MerchantBase(BaseModel):
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    category: str = Field(min_length=1)
    type: MerchantType
    logo_url: HttpUrl | None = None
    logo_base64: str | None = None
    bep_months: int = Field(gt=0)
    rating: float | None = Field(default=None, ge=0, le=5)
    is_active: bool = True
    is_top_merchant: bool = False
    is_official_partner: bool = False
    description: str | None = None

    @field_validator("logo_base64")
    @classmethod
    def validate_logo_base64(cls, value: str | None) -> str | None:
        return validate_optional_image_base64(value)

    @model_validator(mode="after")
    def validate_logo_source(self) -> "MerchantBase":
        require_image_source(str(self.logo_url) if self.logo_url else None, self.logo_base64)
        return self


class MerchantCreate(MerchantBase):
    packages: list[MerchantPackageCreate] = Field(min_length=1)
    images: list[MerchantImageCreate] = Field(default_factory=list, max_length=3)


class MerchantUpdate(MerchantBase):
    packages: list[MerchantPackageUpdate] = Field(min_length=1)
    images: list[MerchantImageUpdate] = Field(default_factory=list, max_length=3)


class MerchantStatusUpdate(BaseModel):
    is_active: bool


class MerchantRead(APIModel):
    id: str
    name: str
    slug: str
    category: str
    type: MerchantType
    logo_url: str
    logo_base64: str | None = None
    bep_months: int
    rating: float | None = None
    is_active: bool
    is_top_merchant: bool
    is_official_partner: bool
    description: str | None = None
    packages: list[MerchantPackageRead]
    images: list[MerchantImageRead] = []
    created_at: str
    updated_at: str


class MerchantListQuery(BaseModel):
    search: str | None = None
    category: str | None = None
    type: MerchantType | None = None
    is_active: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
