from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import APIModel

AdminRole = Literal["superadmin", "admin", "editor"]


class AdminUserBase(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    role: AdminRole
    is_active: bool = True


class AdminUserCreate(AdminUserBase):
    password: str = Field(min_length=8)


class AdminUserUpdate(AdminUserBase):
    pass


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminUserResetPassword(BaseModel):
    new_password: str = Field(min_length=8)


class AdminUserRead(APIModel):
    id: str
    username: str
    role: AdminRole
    is_active: bool
    created_at: str
    updated_at: str
