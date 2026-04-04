from __future__ import annotations

from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MetaData(APIModel):
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def from_pagination(cls, page: int, page_size: int, total: int) -> "MetaData":
        return cls(page=page, page_size=page_size, total=total, total_pages=ceil(total / page_size) if total else 0)


class DetailResponse(APIModel, Generic[T]):
    data: T


class ListResponse(APIModel, Generic[T]):
    data: list[T]
    meta: MetaData


class ErrorResponse(APIModel):
    message: str
    errors: dict[str, list[str]] | None = None


class StatusUpdate(APIModel):
    is_active: bool
