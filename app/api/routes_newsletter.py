from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db, require_roles
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.schemas.common import APIModel, DetailResponse, ListResponse, MetaData

client_router = APIRouter(prefix="/client/newsletter", tags=["client-newsletter"])
dashboard_router = APIRouter(prefix="/dashboard/newsletter", tags=["dashboard-newsletter"])


class NewsletterSubscribePayload(BaseModel):
    email: EmailStr
    source: str | None = None


class NewsletterSubscriberRead(APIModel):
    id: str
    email: str
    source: str | None = None
    subscribed_at: str
    unsubscribed_at: str | None = None


def _serialize(model: NewsletterSubscriber) -> NewsletterSubscriberRead:
    return NewsletterSubscriberRead(
        id=str(model.id),
        email=model.email,
        source=model.source,
        subscribed_at=model.subscribed_at.isoformat() if model.subscribed_at else "",
        unsubscribed_at=model.unsubscribed_at.isoformat() if model.unsubscribed_at else None,
    )


@client_router.post("/subscribe", response_model=DetailResponse[NewsletterSubscriberRead], status_code=status.HTTP_201_CREATED)
def subscribe(payload: NewsletterSubscribePayload, request: Request, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    existing = db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.email == email))
    if existing:
        if existing.unsubscribed_at is not None:
            existing.unsubscribed_at = None
            existing.subscribed_at = datetime.now(timezone.utc)
            existing.source = payload.source or existing.source
            db.commit()
            db.refresh(existing)
        return DetailResponse(data=_serialize(existing))

    subscriber = NewsletterSubscriber(
        email=email,
        source=payload.source,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return DetailResponse(data=_serialize(subscriber))


@client_router.post("/unsubscribe", response_model=DetailResponse[NewsletterSubscriberRead])
def unsubscribe(payload: NewsletterSubscribePayload, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    subscriber = db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.email == email))
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not subscribed")
    if subscriber.unsubscribed_at is None:
        subscriber.unsubscribed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(subscriber)
    return DetailResponse(data=_serialize(subscriber))


@dashboard_router.get("/subscribers", response_model=ListResponse[NewsletterSubscriberRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def list_subscribers(
    active_only: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(NewsletterSubscriber)
    count_query = select(func.count()).select_from(NewsletterSubscriber)
    if active_only:
        query = query.where(NewsletterSubscriber.unsubscribed_at.is_(None))
        count_query = count_query.where(NewsletterSubscriber.unsubscribed_at.is_(None))

    total = db.scalar(count_query) or 0
    query = query.order_by(NewsletterSubscriber.subscribed_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = db.scalars(query).all()
    return ListResponse(data=[_serialize(item) for item in rows], meta=MetaData.from_pagination(page, page_size, total))


@dashboard_router.delete("/subscribers/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("superadmin"))])
def hard_delete_subscriber(subscriber_id: uuid.UUID, db: Session = Depends(get_db)):
    subscriber = db.get(NewsletterSubscriber, subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscriber not found")
    db.delete(subscriber)
    db.commit()
