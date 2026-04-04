from __future__ import annotations

import re

IMAGE_DATA_URI_PATTERN = re.compile(r"^data:image\/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+$")


def validate_optional_image_base64(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None
    if not IMAGE_DATA_URI_PATTERN.match(normalized):
        raise ValueError("Image base64 must be a valid data URI")
    return normalized


def require_image_source(url_value: str | None, base64_value: str | None) -> None:
    if url_value or base64_value:
        return
    raise ValueError("Provide image URL or image base64")


def resolve_image_source(url_value: str | None, base64_value: str | None) -> str:
    return base64_value or url_value or ""
