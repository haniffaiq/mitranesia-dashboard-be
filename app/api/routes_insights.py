from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db, require_roles
from app.models.insight_article import InsightArticle
from app.schemas.common import DetailResponse, ListResponse, MetaData
from app.schemas.insight import InsightArticleCreate, InsightArticleRead, InsightArticleUpdate, InsightStatusUpdate
from app.services.serializers import serialize_insight

router = APIRouter(prefix="/dashboard/insights", tags=["dashboard-insights"])


def get_article_or_404(db: Session, article_id: uuid.UUID) -> InsightArticle:
    article = db.get(InsightArticle, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight article not found")
    return article


def validate_unique_slug(db: Session, slug: str, article_id: uuid.UUID | None = None) -> None:
    statement = select(InsightArticle).where(InsightArticle.slug == slug)
    if article_id:
        statement = statement.where(InsightArticle.id != article_id)
    if db.scalar(statement):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Slug already exists")


def sync_publish_state(article: InsightArticle, status_value: str) -> None:
    article.status = status_value
    if status_value == "published" and article.published_at is None:
        article.published_at = datetime.now(timezone.utc)
    if status_value != "published":
        article.published_at = None


@router.get("", response_model=ListResponse[InsightArticleRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def list_insights(
    search: str | None = None,
    category: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(InsightArticle)
    count_query = select(func.count()).select_from(InsightArticle)

    if search:
        term = f"%{search.lower()}%"
        criteria = func.lower(InsightArticle.title).like(term) | func.lower(InsightArticle.slug).like(term)
        query = query.where(criteria)
        count_query = count_query.where(criteria)
    if category:
        query = query.where(InsightArticle.category == category)
        count_query = count_query.where(InsightArticle.category == category)
    if status_filter:
        query = query.where(InsightArticle.status == status_filter)
        count_query = count_query.where(InsightArticle.status == status_filter)

    total = db.scalar(count_query) or 0
    rows = db.scalars(query.order_by(InsightArticle.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return ListResponse(data=[serialize_insight(item) for item in rows], meta=MetaData.from_pagination(page, page_size, total))


@router.post("", response_model=DetailResponse[InsightArticleRead], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def create_insight(payload: InsightArticleCreate, db: Session = Depends(get_db)):
    validate_unique_slug(db, payload.slug)
    article = InsightArticle(
        title=payload.title,
        slug=payload.slug,
        category=payload.category,
        author=payload.author,
        image=str(payload.image) if payload.image else None,
        image_base64=payload.image_base64,
        excerpt=payload.excerpt,
        read_time=payload.read_time,
        content=payload.content,
        status=payload.status,
    )
    sync_publish_state(article, payload.status)
    db.add(article)
    db.commit()
    db.refresh(article)
    return DetailResponse(data=serialize_insight(article))


@router.get("/{article_id}", response_model=DetailResponse[InsightArticleRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def get_insight(article_id: uuid.UUID, db: Session = Depends(get_db)):
    return DetailResponse(data=serialize_insight(get_article_or_404(db, article_id)))


@router.put("/{article_id}", response_model=DetailResponse[InsightArticleRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def update_insight(article_id: uuid.UUID, payload: InsightArticleUpdate, db: Session = Depends(get_db)):
    article = get_article_or_404(db, article_id)
    validate_unique_slug(db, payload.slug, article_id)

    article.title = payload.title
    article.slug = payload.slug
    article.category = payload.category
    article.author = payload.author
    article.image = str(payload.image) if payload.image else None
    article.image_base64 = payload.image_base64
    article.excerpt = payload.excerpt
    article.read_time = payload.read_time
    article.content = payload.content
    sync_publish_state(article, payload.status)

    db.commit()
    db.refresh(article)
    return DetailResponse(data=serialize_insight(article))


@router.patch("/{article_id}/status", response_model=DetailResponse[InsightArticleRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def update_insight_status(article_id: uuid.UUID, payload: InsightStatusUpdate, db: Session = Depends(get_db)):
    article = get_article_or_404(db, article_id)
    sync_publish_state(article, payload.status)
    db.commit()
    db.refresh(article)
    return DetailResponse(data=serialize_insight(article))


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def delete_insight(article_id: uuid.UUID, db: Session = Depends(get_db)):
    article = get_article_or_404(db, article_id)
    db.delete(article)
    db.commit()
