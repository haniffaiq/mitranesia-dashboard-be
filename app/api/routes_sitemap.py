from __future__ import annotations

from datetime import datetime, timezone
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.models.insight_article import InsightArticle
from app.models.merchant import Merchant

router = APIRouter()

BASE_URL = "https://mitranesia.id"

STATIC_PATHS: tuple[tuple[str, str, float], ...] = (
    # path, changefreq, priority
    ("/", "daily", 1.0),
    ("/merchants", "daily", 0.9),
    ("/insight", "weekly", 0.8),
    ("/become-merchant", "monthly", 0.6),
)


def _fmt(dt: datetime | None) -> str:
    if dt is None:
        dt = datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _url_xml(loc: str, lastmod: str, changefreq: str, priority: float) -> str:
    return (
        "  <url>\n"
        f"    <loc>{escape(loc)}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority:.1f}</priority>\n"
        "  </url>\n"
    )


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(db: Session = Depends(get_db)) -> Response:
    now_iso = _fmt(None)
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
    ]
    for path, freq, prio in STATIC_PATHS:
        parts.append(_url_xml(f"{BASE_URL}{path}", now_iso, freq, prio))

    merchants = db.execute(
        select(Merchant.slug, Merchant.updated_at).where(Merchant.is_active.is_(True))
    ).all()
    for slug, updated_at in merchants:
        parts.append(_url_xml(f"{BASE_URL}/merchants/{slug}", _fmt(updated_at), "weekly", 0.7))

    insights = db.execute(
        select(InsightArticle.slug, InsightArticle.updated_at).where(InsightArticle.status == "published")
    ).all()
    for slug, updated_at in insights:
        parts.append(_url_xml(f"{BASE_URL}/insight/{slug}", _fmt(updated_at), "monthly", 0.6))

    parts.append("</urlset>\n")
    return Response("".join(parts), media_type="application/xml")
