"""
Decode image_base64 columns ke file di /srv/uploads/migrated, populate image_url, clear image_base64.

Run di VPS:
  podman exec mitranesia-api python /app/scripts/migrate_base64_to_disk.py

Idempotent: kalau image_url sudah set, skip row.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.carousel_item import CarouselItem
from app.models.insight_article import InsightArticle
from app.models.merchant import Merchant
from app.models.merchant_image import MerchantImage

UPLOAD_ROOT = Path(os.environ.get("UPLOAD_ROOT", "/srv/uploads")).resolve()
PUBLIC_PREFIX = "/uploads"

DATA_URI_PATTERN = re.compile(r"^data:image/(?P<mime>[^;]+);base64,(?P<data>.+)$")
MIME_EXT = {
    "png": "png",
    "jpeg": "jpg",
    "jpg": "jpg",
    "webp": "webp",
    "gif": "gif",
    "svg+xml": "svg",
}


def decode_data_uri(uri: str | None) -> tuple[str, bytes] | None:
    if not uri:
        return None
    match = DATA_URI_PATTERN.match(uri.strip())
    if not match:
        return None
    mime = match.group("mime").lower()
    ext = MIME_EXT.get(mime)
    if ext is None:
        return None
    try:
        raw = base64.b64decode(match.group("data"), validate=True)
    except Exception:
        return None
    return ext, raw


def write_file(prefix: str, raw: bytes, ext: str) -> str:
    digest = hashlib.sha256(raw).hexdigest()[:16]
    folder = UPLOAD_ROOT / "migrated" / prefix
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest}.{ext}"
    if not path.exists():
        path.write_bytes(raw)
    rel = path.relative_to(UPLOAD_ROOT)
    return f"{PUBLIC_PREFIX}/{rel.as_posix()}"


def migrate_merchants(session) -> int:
    rows = session.scalars(
        select(Merchant).where(
            Merchant.logo_base64.isnot(None), Merchant.logo_url.is_(None)
        )
    ).all()
    n = 0
    for m in rows:
        decoded = decode_data_uri(m.logo_base64)
        if decoded is None:
            print(f"  [skip] merchant {m.slug}: invalid base64", file=sys.stderr)
            continue
        ext, raw = decoded
        url = write_file(f"merchants/{m.slug}", raw, ext)
        m.logo_url = url
        m.logo_base64 = None
        print(f"  merchant {m.slug} logo -> {url} ({len(raw)}B)")
        n += 1
    return n


def migrate_merchant_images(session) -> int:
    rows = session.scalars(
        select(MerchantImage).where(
            MerchantImage.image_base64.isnot(None), MerchantImage.image_url.is_(None)
        )
    ).all()
    n = 0
    for img in rows:
        decoded = decode_data_uri(img.image_base64)
        if decoded is None:
            print(f"  [skip] merchant_image {img.id}: invalid base64", file=sys.stderr)
            continue
        ext, raw = decoded
        merchant = session.get(Merchant, img.merchant_id)
        slug = merchant.slug if merchant else str(img.merchant_id)
        url = write_file(f"merchants/{slug}/gallery", raw, ext)
        img.image_url = url
        img.image_base64 = None
        print(f"  merchant_image {img.id} -> {url} ({len(raw)}B)")
        n += 1
    return n


def migrate_insights(session) -> int:
    rows = session.scalars(
        select(InsightArticle).where(
            InsightArticle.image_base64.isnot(None), InsightArticle.image.is_(None)
        )
    ).all()
    n = 0
    for art in rows:
        decoded = decode_data_uri(art.image_base64)
        if decoded is None:
            print(f"  [skip] insight {art.slug}: invalid base64", file=sys.stderr)
            continue
        ext, raw = decoded
        url = write_file(f"insights/{art.slug}", raw, ext)
        art.image = url
        art.image_base64 = None
        print(f"  insight {art.slug} -> {url} ({len(raw)}B)")
        n += 1
    return n


def migrate_carousels(session) -> int:
    rows = session.scalars(
        select(CarouselItem).where(
            CarouselItem.image_base64.isnot(None), CarouselItem.image_url.is_(None)
        )
    ).all()
    n = 0
    for c in rows:
        decoded = decode_data_uri(c.image_base64)
        if decoded is None:
            print(f"  [skip] carousel {c.id}: invalid base64", file=sys.stderr)
            continue
        ext, raw = decoded
        url = write_file(f"carousels/{c.id}", raw, ext)
        c.image_url = url
        c.image_base64 = None
        print(f"  carousel {c.id} -> {url} ({len(raw)}B)")
        n += 1
    return n


def main() -> None:
    print(f"=== Migrate base64 -> disk (UPLOAD_ROOT={UPLOAD_ROOT}) ===")
    session = SessionLocal()
    try:
        m = migrate_merchants(session)
        mi = migrate_merchant_images(session)
        ia = migrate_insights(session)
        c = migrate_carousels(session)
        session.commit()
        print(
            f"\nDone. merchants={m} merchant_images={mi} insights={ia} carousels={c}"
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
