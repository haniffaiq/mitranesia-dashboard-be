from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class ClientMerchantInquiryCreate(BaseModel):
    merchant_id: str
    package_name: str | None = Field(default=None, max_length=255)
    inquiry_type: str = Field(default="contact", max_length=32)
    message: str | None = Field(default=None, max_length=5000)


class ClientMerchantInquiryRead(APIModel):
    id: str
    merchant_id: str
    package_name: str | None = None
    inquiry_type: str
    full_name: str
    email: str
    phone: str
    message: str | None = None
    status: str
    created_at: str
    updated_at: str


class ClientMerchantApplicationCreate(BaseModel):
    contact_name: str = Field(min_length=3, max_length=255)
    business_name: str = Field(min_length=3, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    phone: str = Field(min_length=8, max_length=32)
    category: str = Field(min_length=2, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    message: str | None = Field(default=None, max_length=5000)


class ClientMerchantApplicationRead(APIModel):
    id: str
    contact_name: str
    business_name: str
    email: str
    phone: str
    category: str
    city: str
    message: str | None = None
    status: str
    created_at: str
    updated_at: str
