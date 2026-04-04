from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db, require_roles
from app.models.carousel_item import CarouselItem
from app.schemas.carousel import CarouselItemCreate, CarouselItemRead, CarouselItemUpdate, CarouselStatusUpdate
from app.schemas.common import DetailResponse, ListResponse, MetaData
from app.services.serializers import serialize_carousel

router = APIRouter(prefix="/dashboard/carousels", tags=["dashboard-carousels"])


def get_carousel_or_404(db: Session, carousel_id: uuid.UUID) -> CarouselItem:
    carousel = db.get(CarouselItem, carousel_id)
    if not carousel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carousel item not found")
    return carousel


@router.get("", response_model=ListResponse[CarouselItemRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def list_carousels(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(CarouselItem)
    count_query = select(func.count()).select_from(CarouselItem)

    if search:
        term = f"%{search.lower()}%"
        criteria = func.lower(CarouselItem.title).like(term) | func.lower(CarouselItem.tag).like(term)
        query = query.where(criteria)
        count_query = count_query.where(criteria)
    if is_active is not None:
        query = query.where(CarouselItem.is_active.is_(is_active))
        count_query = count_query.where(CarouselItem.is_active.is_(is_active))

    total = db.scalar(count_query) or 0
    rows = db.scalars(
        query.order_by(CarouselItem.sort_order.asc(), CarouselItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return ListResponse(data=[serialize_carousel(item) for item in rows], meta=MetaData.from_pagination(page, page_size, total))


@router.post("", response_model=DetailResponse[CarouselItemRead], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def create_carousel(payload: CarouselItemCreate, db: Session = Depends(get_db)):
    carousel = CarouselItem(
        title=payload.title,
        image_url=str(payload.image_url) if payload.image_url else None,
        image_base64=payload.image_base64,
        tag=payload.tag,
        icon=payload.icon,
        highlight=payload.highlight,
        description=payload.description,
        color=payload.color,
        cta_label=payload.cta_label,
        cta_href=payload.cta_href,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(carousel)
    db.commit()
    db.refresh(carousel)
    return DetailResponse(data=serialize_carousel(carousel))


@router.get("/{carousel_id}", response_model=DetailResponse[CarouselItemRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def get_carousel(carousel_id: uuid.UUID, db: Session = Depends(get_db)):
    return DetailResponse(data=serialize_carousel(get_carousel_or_404(db, carousel_id)))


@router.put("/{carousel_id}", response_model=DetailResponse[CarouselItemRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def update_carousel(carousel_id: uuid.UUID, payload: CarouselItemUpdate, db: Session = Depends(get_db)):
    carousel = get_carousel_or_404(db, carousel_id)
    carousel.title = payload.title
    carousel.image_url = str(payload.image_url) if payload.image_url else None
    carousel.image_base64 = payload.image_base64
    carousel.tag = payload.tag
    carousel.icon = payload.icon
    carousel.highlight = payload.highlight
    carousel.description = payload.description
    carousel.color = payload.color
    carousel.cta_label = payload.cta_label
    carousel.cta_href = payload.cta_href
    carousel.sort_order = payload.sort_order
    carousel.is_active = payload.is_active
    db.commit()
    db.refresh(carousel)
    return DetailResponse(data=serialize_carousel(carousel))


@router.patch("/{carousel_id}/status", response_model=DetailResponse[CarouselItemRead], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def update_carousel_status(carousel_id: uuid.UUID, payload: CarouselStatusUpdate, db: Session = Depends(get_db)):
    carousel = get_carousel_or_404(db, carousel_id)
    carousel.is_active = payload.is_active
    db.commit()
    db.refresh(carousel)
    return DetailResponse(data=serialize_carousel(carousel))


@router.delete("/{carousel_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def delete_carousel(carousel_id: uuid.UUID, db: Session = Depends(get_db)):
    carousel = get_carousel_or_404(db, carousel_id)
    db.delete(carousel)
    db.commit()
