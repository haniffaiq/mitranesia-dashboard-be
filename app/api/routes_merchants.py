from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, selectinload

from app.dependencies.auth import get_db, require_roles
from app.models.merchant import Merchant
from app.models.merchant_image import MerchantImage
from app.models.merchant_package import MerchantPackage
from app.schemas.common import DetailResponse, ListResponse, MetaData
from app.schemas.merchant import MerchantCreate, MerchantRead, MerchantStatusUpdate, MerchantUpdate
from app.services.image_storage import materialize
from app.services.serializers import serialize_merchant

router = APIRouter(prefix="/dashboard/merchants", tags=["dashboard-merchants"])

ALLOWED_SORT_FIELDS = {
    "created_at": Merchant.created_at,
    "updated_at": Merchant.updated_at,
    "name": Merchant.name,
    "category": Merchant.category,
    "type": Merchant.type,
    "bep_months": Merchant.bep_months,
}


def get_merchant_or_404(db: Session, merchant_id: uuid.UUID, include_deleted: bool = False) -> Merchant:
    statement = (
        select(Merchant)
        .options(selectinload(Merchant.packages), selectinload(Merchant.images))
        .where(Merchant.id == merchant_id)
    )
    if not include_deleted:
        statement = statement.where(Merchant.deleted_at.is_(None))
    merchant = db.scalar(statement)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return merchant


def validate_unique_merchant_slug(db: Session, slug: str, merchant_id: uuid.UUID | None = None) -> None:
    statement = select(Merchant).where(Merchant.slug == slug)
    if merchant_id:
        statement = statement.where(Merchant.id != merchant_id)
    if db.scalar(statement):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Slug already exists")


def sync_packages(merchant: Merchant, packages_payload: list) -> None:
    existing_by_id = {str(item.id): item for item in merchant.packages}
    kept: list[MerchantPackage] = []

    for item in packages_payload:
        if item.id:
            package = existing_by_id.pop(item.id, None)
            if not package:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Package {item.id} not found")
            package.name = item.name
            package.price = item.price
            package.description = item.description
            package.sort_order = item.sort_order
            kept.append(package)
        else:
            kept.append(
                MerchantPackage(
                    name=item.name,
                    price=item.price,
                    description=item.description,
                    sort_order=item.sort_order,
                )
            )

    merchant.packages[:] = kept


def sync_images(merchant: Merchant, images_payload: list) -> None:
    existing_by_id = {str(item.id): item for item in merchant.images}
    kept: list[MerchantImage] = []
    gallery_prefix = f"merchants/{merchant.slug}/gallery"

    for item in images_payload:
        url_value, base64_value = materialize(
            str(item.image_url) if item.image_url else None,
            item.image_base64,
            gallery_prefix,
        )
        item_id = getattr(item, "id", None)
        if item_id:
            image = existing_by_id.pop(item_id, None)
            if not image:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Image {item_id} not found")
            image.label = item.label
            image.image_url = url_value
            image.image_base64 = base64_value
            image.sort_order = item.sort_order
            kept.append(image)
        else:
            kept.append(
                MerchantImage(
                    label=item.label,
                    image_url=url_value,
                    image_base64=base64_value,
                    sort_order=item.sort_order,
                )
            )

    merchant.images[:] = kept


@router.get("", response_model=ListResponse[MerchantRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def list_merchants(
    search: str | None = None,
    category: str | None = None,
    type: str | None = Query(default=None),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    sort_column = ALLOWED_SORT_FIELDS.get(sort_by)
    if sort_column is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid sort_by field")

    query = (
        select(Merchant)
        .options(selectinload(Merchant.packages), selectinload(Merchant.images))
        .where(Merchant.deleted_at.is_(None))
    )
    count_query = select(func.count()).select_from(Merchant).where(Merchant.deleted_at.is_(None))

    if search:
        term = f"%{search.lower()}%"
        fts_expr = text(
            "to_tsvector('simple', coalesce(merchants.name,'') || ' ' || coalesce(merchants.slug,'') || ' ' || "
            "coalesce(merchants.category,'') || ' ' || coalesce(merchants.description,'')) @@ plainto_tsquery('simple', :search)"
        ).bindparams(search=search)
        criteria = or_(
            func.lower(Merchant.name).like(term),
            func.lower(Merchant.slug).like(term),
            fts_expr,
        )
        query = query.where(criteria)
        count_query = count_query.where(criteria)
    if category:
        query = query.where(Merchant.category == category)
        count_query = count_query.where(Merchant.category == category)
    if type:
        query = query.where(Merchant.type == type)
        count_query = count_query.where(Merchant.type == type)
    if is_active is not None:
        query = query.where(Merchant.is_active.is_(is_active))
        count_query = count_query.where(Merchant.is_active.is_(is_active))

    total = db.scalar(count_query) or 0
    order_expr = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    merchants = db.scalars(query.order_by(order_expr).offset((page - 1) * page_size).limit(page_size)).all()
    return ListResponse(data=[serialize_merchant(item) for item in merchants], meta=MetaData.from_pagination(page, page_size, total))


@router.post("", response_model=DetailResponse[MerchantRead], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("superadmin", "admin"))])
def create_merchant(payload: MerchantCreate, db: Session = Depends(get_db)):
    validate_unique_merchant_slug(db, payload.slug)
    logo_url, logo_base64 = materialize(
        str(payload.logo_url) if payload.logo_url else None,
        payload.logo_base64,
        f"merchants/{payload.slug}",
    )
    gallery_prefix = f"merchants/{payload.slug}/gallery"
    images = []
    for item in payload.images:
        img_url, img_base64 = materialize(
            str(item.image_url) if item.image_url else None,
            item.image_base64,
            gallery_prefix,
        )
        images.append(
            MerchantImage(
                label=item.label,
                image_url=img_url,
                image_base64=img_base64,
                sort_order=item.sort_order,
            )
        )
    merchant = Merchant(
        name=payload.name,
        slug=payload.slug,
        category=payload.category,
        type=payload.type,
        logo_url=logo_url,
        logo_base64=logo_base64,
        bep_months=payload.bep_months,
        rating=payload.rating,
        is_active=payload.is_active,
        is_top_merchant=payload.is_top_merchant,
        is_official_partner=payload.is_official_partner,
        description=payload.description,
        packages=[
            MerchantPackage(
                name=item.name,
                price=item.price,
                description=item.description,
                sort_order=item.sort_order,
            )
            for item in payload.packages
        ],
        images=images,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    merchant = get_merchant_or_404(db, merchant.id)
    return DetailResponse(data=serialize_merchant(merchant))


@router.get("/{merchant_id}", response_model=DetailResponse[MerchantRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def get_merchant(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    return DetailResponse(data=serialize_merchant(get_merchant_or_404(db, merchant_id)))


@router.put("/{merchant_id}", response_model=DetailResponse[MerchantRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def update_merchant(merchant_id: uuid.UUID, payload: MerchantUpdate, db: Session = Depends(get_db)):
    merchant = get_merchant_or_404(db, merchant_id)
    validate_unique_merchant_slug(db, payload.slug, merchant_id)

    merchant.name = payload.name
    merchant.slug = payload.slug
    merchant.category = payload.category
    merchant.type = payload.type
    logo_url, logo_base64 = materialize(
        str(payload.logo_url) if payload.logo_url else None,
        payload.logo_base64,
        f"merchants/{payload.slug}",
    )
    merchant.logo_url = logo_url
    merchant.logo_base64 = logo_base64
    merchant.bep_months = payload.bep_months
    merchant.rating = payload.rating
    merchant.is_active = payload.is_active
    merchant.is_top_merchant = payload.is_top_merchant
    merchant.is_official_partner = payload.is_official_partner
    merchant.description = payload.description
    sync_packages(merchant, payload.packages)
    sync_images(merchant, payload.images)

    db.commit()
    db.refresh(merchant)
    merchant = get_merchant_or_404(db, merchant_id)
    return DetailResponse(data=serialize_merchant(merchant))


@router.patch("/{merchant_id}/status", response_model=DetailResponse[MerchantRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def update_merchant_status(merchant_id: uuid.UUID, payload: MerchantStatusUpdate, db: Session = Depends(get_db)):
    merchant = get_merchant_or_404(db, merchant_id)
    merchant.is_active = payload.is_active
    db.commit()
    db.refresh(merchant)
    return DetailResponse(data=serialize_merchant(get_merchant_or_404(db, merchant_id)))


@router.delete("/{merchant_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("superadmin", "admin"))])
def delete_merchant(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    merchant = get_merchant_or_404(db, merchant_id)
    from datetime import datetime, timezone

    merchant.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/trash/list", response_model=ListResponse[MerchantRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def list_trashed_merchants(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        select(Merchant)
        .options(selectinload(Merchant.packages), selectinload(Merchant.images))
        .where(Merchant.deleted_at.is_not(None))
        .order_by(Merchant.deleted_at.desc())
    )
    count_query = select(func.count()).select_from(Merchant).where(Merchant.deleted_at.is_not(None))
    total = db.scalar(count_query) or 0
    merchants = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return ListResponse(
        data=[serialize_merchant(item) for item in merchants],
        meta=MetaData.from_pagination(page, page_size, total),
    )


@router.post("/{merchant_id}/restore", response_model=DetailResponse[MerchantRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def restore_merchant(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    merchant = get_merchant_or_404(db, merchant_id, include_deleted=True)
    if merchant.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Merchant not deleted")
    merchant.deleted_at = None
    db.commit()
    db.refresh(merchant)
    return DetailResponse(data=serialize_merchant(get_merchant_or_404(db, merchant_id)))


@router.delete("/{merchant_id}/hard", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("superadmin"))])
def hard_delete_merchant(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    merchant = get_merchant_or_404(db, merchant_id, include_deleted=True)
    db.delete(merchant)
    db.commit()
