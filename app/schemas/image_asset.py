from __future__ import annotations

import base64
import re

IMAGE_DATA_URI_PATTERN = re.compile(r"^data:image\/(?P<mime>[a-zA-Z0-9.+-]+);base64,(?P<data>[A-Za-z0-9+/=]+)$")

ALLOWED_MIME = {"png", "jpeg", "jpg", "webp", "avif", "gif", "svg+xml"}

# magic bytes per mime
_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",  # need extra check (WEBP at offset 8)
}

MAX_BASE64_BYTES = 2 * 1024 * 1024  # 2MB raw bytes (~2.7MB base64 string)


def _detect_format(raw: bytes) -> str | None:
    for prefix, fmt in _MAGIC.items():
        if raw.startswith(prefix):
            if fmt == "webp":
                if len(raw) >= 12 and raw[8:12] == b"WEBP":
                    return "webp"
                continue
            return fmt
    if raw.lstrip().startswith(b"<?xml") or b"<svg" in raw[:200].lower():
        return "svg+xml"
    return None


def validate_optional_image_base64(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    match = IMAGE_DATA_URI_PATTERN.match(normalized)
    if not match:
        raise ValueError("Image base64 must be a valid data URI")

    declared_mime = match.group("mime").lower()
    if declared_mime not in ALLOWED_MIME:
        raise ValueError(f"Image mime '{declared_mime}' not allowed")

    try:
        raw = base64.b64decode(match.group("data"), validate=True)
    except Exception:
        raise ValueError("Image base64 payload is not valid base64")

    if len(raw) > MAX_BASE64_BYTES:
        raise ValueError(f"Image too large: {len(raw)} bytes (max {MAX_BASE64_BYTES})")

    detected = _detect_format(raw)
    if detected is None:
        raise ValueError("Image content does not match a supported format (PNG/JPEG/WebP/GIF/SVG)")

    expected = "jpeg" if declared_mime in {"jpeg", "jpg"} else declared_mime
    if expected != detected:
        raise ValueError(
            f"Image format mismatch: declared {declared_mime} but bytes look like {detected}"
        )

    return normalized


def require_image_source(url_value: str | None, base64_value: str | None) -> None:
    if url_value or base64_value:
        return
    raise ValueError("Provide image URL or image base64")


def resolve_image_source(url_value: str | None, base64_value: str | None) -> str:
    return base64_value or url_value or ""
