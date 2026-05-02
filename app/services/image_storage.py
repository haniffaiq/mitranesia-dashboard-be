"""Image storage helper: decode base64 data URI -> file di /srv/uploads, return public URL.

Dipakai di route create/update merchant/insight/carousel: kalau payload kasih `*_base64`,
auto-write ke disk + populate `*_url` + clear `*_base64`. Cegah DB bloat.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
from pathlib import Path

UPLOAD_ROOT = Path(os.environ.get("UPLOAD_ROOT", "/srv/uploads")).resolve()
PUBLIC_PREFIX = "/uploads"

DATA_URI_RE = re.compile(r"^data:image/(?P<mime>[^;]+);base64,(?P<data>.+)$")
MIME_EXT = {
    "png": "png",
    "jpeg": "jpg",
    "jpg": "jpg",
    "webp": "webp",
    "gif": "gif",
    "svg+xml": "svg",
}


def _safe_segment(value: str) -> str:
    """Sanitize path segment: only [a-z0-9-_]. Cegah path traversal."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return cleaned or "untitled"


def _decode_data_uri(data_uri: str) -> tuple[str, bytes] | None:
    match = DATA_URI_RE.match(data_uri.strip())
    if not match:
        return None
    ext = MIME_EXT.get(match.group("mime").lower())
    if ext is None:
        return None
    try:
        raw = base64.b64decode(match.group("data"), validate=True)
    except Exception:
        return None
    return ext, raw


def save_data_uri(data_uri: str, prefix: str) -> str | None:
    """Decode + tulis file ke {UPLOAD_ROOT}/cms/{prefix}/{sha16}.{ext}.
    Return public URL kalau sukses, None kalau base64 invalid.
    Idempotent: kalau file dengan sha16 sama sudah ada, skip write."""
    decoded = _decode_data_uri(data_uri)
    if decoded is None:
        return None
    ext, raw = decoded
    digest = hashlib.sha256(raw).hexdigest()[:16]
    safe_prefix = "/".join(_safe_segment(part) for part in prefix.split("/") if part)
    folder = UPLOAD_ROOT / "cms" / safe_prefix
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest}.{ext}"
    if not path.exists():
        path.write_bytes(raw)
    return f"{PUBLIC_PREFIX}/cms/{safe_prefix}/{digest}.{ext}"


def materialize(
    url_value: str | None,
    base64_value: str | None,
    prefix: str,
) -> tuple[str | None, str | None]:
    """Pre-save image normalization untuk POST/PUT route.

    Kalau base64 valid -> tulis disk + return (saved_url, None).
    Kalau base64 invalid (validation upstream sudah reject biasanya) -> pass-through (url, base64).
    Kalau base64 None -> pass-through (url, None).

    Pemanggil tinggal assign tuple ke (model.*_url, model.*_base64).
    """
    if base64_value:
        saved = save_data_uri(base64_value, prefix)
        if saved is not None:
            return saved, None
    return url_value, base64_value
