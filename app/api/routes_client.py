from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.models.merchant import Merchant
from app.models.merchant_review import MerchantReview
from app.schemas.client import (
    ClientCarouselSlide,
    ClientHome,
    ClientInsightArticle,
    ClientInsightCategories,
    ClientMerchant,
    ClientMerchantList,
    ClientMerchantsFilters,
)
from app.schemas.merchant_review import ReviewCreate, ReviewRead
from app.services.client import (
    build_client_home,
    build_merchant_filters,
    find_client_insight,
    find_client_merchant,
    get_active_carousels,
    get_active_merchants,
    get_merchant_review_summary,
    get_published_insights,
    paginate_client_merchants,
    serialize_client_carousel,
    serialize_client_insight,
    serialize_client_merchant,
)

router = APIRouter(prefix="/client", tags=["client"])


@router.get("/home", response_model=ClientHome)
def get_home(db: Session = Depends(get_db)):
    return build_client_home(db)


@router.get("/carousels", response_model=list[ClientCarouselSlide])
def list_client_carousels(db: Session = Depends(get_db)):
    return [serialize_client_carousel(item) for item in get_active_carousels(db)]


@router.get("/merchants", response_model=ClientMerchantList)
def list_client_merchants(
    search: str | None = None,
    category: str | None = None,
    type: str | None = Query(default=None),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    is_top_merchant: bool | None = None,
    recommended: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    sort_by: str = Query(default="min_price"),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db),
):
    merchants = [serialize_client_merchant(item) for item in get_active_merchants(db)]

    if search:
        term = search.strip().lower()
        merchants = [item for item in merchants if term in item.name.lower() or term in item.slug.lower()]
    if category:
        merchants = [item for item in merchants if item.category == category]
    if type:
        merchants = [item for item in merchants if item.type == type]
    if min_price is not None:
        merchants = [item for item in merchants if item.maxPrice >= min_price]
    if max_price is not None:
        merchants = [item for item in merchants if item.minPrice <= max_price]
    if is_top_merchant is not None:
        merchants = [item for item in merchants if item.isTopMerchant is is_top_merchant]
    if recommended:
        merchants = [item for item in merchants if "Autopilot" in item.type or item.rating == 4.7]

    reverse = sort_order == "desc"
    if sort_by == "name":
        merchants.sort(key=lambda item: item.name.lower(), reverse=reverse)
    elif sort_by == "rating":
        merchants.sort(key=lambda item: item.rating or 0, reverse=reverse)
    elif sort_by == "max_price":
        merchants.sort(key=lambda item: item.maxPrice, reverse=reverse)
    else:
        merchants.sort(key=lambda item: item.minPrice, reverse=reverse)

    paged_data, meta = paginate_client_merchants(merchants, page, page_size)
    return ClientMerchantList(
        data=paged_data,
        meta=meta,
        filters=build_merchant_filters(get_active_merchants(db)),
    )


@router.get("/merchants/filters", response_model=ClientMerchantsFilters)
def get_client_merchant_filters(db: Session = Depends(get_db)):
    return build_merchant_filters(get_active_merchants(db))


@router.get("/merchants/{identifier}", response_model=ClientMerchant)
def get_client_merchant(identifier: str, db: Session = Depends(get_db)):
    merchant = find_client_merchant(db, identifier)
    if not merchant or not merchant.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    summary = get_merchant_review_summary(db, merchant.id)
    return serialize_client_merchant(merchant, review_summary=summary)


@router.get("/insights", response_model=list[ClientInsightArticle])
def list_client_insights(
    search: str | None = None,
    category: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    insights = [serialize_client_insight(item) for item in get_published_insights(db)]

    if search:
        term = search.strip().lower()
        insights = [item for item in insights if term in item.title.lower() or term in item.slug.lower()]
    if category:
        insights = [item for item in insights if item.category == category]

    start = (page - 1) * page_size
    end = start + page_size
    return insights[start:end]


@router.get("/insights/categories", response_model=ClientInsightCategories)
def get_client_insight_categories(db: Session = Depends(get_db)):
    categories = sorted({item.category for item in get_published_insights(db)})
    return ClientInsightCategories(categories=categories)


@router.get("/insights/{identifier}", response_model=ClientInsightArticle)
def get_client_insight(identifier: str, db: Session = Depends(get_db)):
    article = find_client_insight(db, identifier)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight article not found")
    return serialize_client_insight(article)


def _resolve_merchant_id(db: Session, identifier: str) -> uuid.UUID:
    """Accept UUID or slug, return merchant.id (only active+not-deleted)."""
    try:
        candidate_uuid = uuid.UUID(identifier)
        merchant = db.scalar(
            select(Merchant).where(Merchant.id == candidate_uuid, Merchant.deleted_at.is_(None))
        )
    except ValueError:
        merchant = db.scalar(
            select(Merchant).where(Merchant.slug == identifier, Merchant.deleted_at.is_(None))
        )
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return merchant.id


@router.get("/merchants/{identifier}/reviews", response_model=list[ReviewRead])
def list_merchant_reviews(
    identifier: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    merchant_id = _resolve_merchant_id(db, identifier)
    rows = db.scalars(
        select(MerchantReview)
        .where(MerchantReview.merchant_id == merchant_id, MerchantReview.status == "approved")
        .order_by(MerchantReview.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [ReviewRead.model_validate(r) for r in rows]


@router.post("/merchants/{identifier}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_merchant_review(
    identifier: str,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
):
    merchant_id = _resolve_merchant_id(db, identifier)
    review = MerchantReview(
        merchant_id=merchant_id,
        reviewer_name=payload.reviewer_name,
        reviewer_email=payload.reviewer_email,
        rating=payload.rating,
        comment=payload.comment,
        status="pending",
        is_verified_mitra=False,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return ReviewRead.model_validate(review)
