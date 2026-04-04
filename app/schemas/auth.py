from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8)


class AuthUser(APIModel):
    id: str
    username: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


class LoginResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser
