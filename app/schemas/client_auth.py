from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class ClientRegisterRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    phone: str = Field(min_length=8, max_length=32)
    password: str = Field(min_length=8)


class ClientLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8)


class ClientAuthUser(APIModel):
    id: str
    full_name: str
    email: str
    phone: str
    is_active: bool
    created_at: str
    updated_at: str


class ClientAuthResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: ClientAuthUser
