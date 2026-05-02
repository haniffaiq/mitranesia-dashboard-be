from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db, require_roles
from app.models.merchant_review import MerchantReview
from app.schemas.common import DetailResponse, ListResponse, MetaData
from app.schemas.merchant_review import ReviewAdminRead, ReviewStatusUpdate

router = APIRouter(prefix="/dashboard/merchant-reviews", tags=["dashboard-merchant-reviews"])


def get_review_or_404(db: Session, review_id: uuid.UUID) -> MerchantReview:
    review = db.get(MerchantReview, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.get("", response_model=ListResponse[ReviewAdminRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def list_reviews(
    status_filter: str | None = Query(default=None, alias="status"),
    merchant_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(MerchantReview)
    count_query = select(func.count()).select_from(MerchantReview)
    if status_filter:
        query = query.where(MerchantReview.status == status_filter)
        count_query = count_query.where(MerchantReview.status == status_filter)
    if merchant_id:
        query = query.where(MerchantReview.merchant_id == merchant_id)
        count_query = count_query.where(MerchantReview.merchant_id == merchant_id)

    total = db.scalar(count_query) or 0
    rows = db.scalars(
        query.order_by(MerchantReview.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return ListResponse(data=[ReviewAdminRead.model_validate(r) for r in rows], meta=MetaData.from_pagination(page, page_size, total))


@router.patch("/{review_id}/status", response_model=DetailResponse[ReviewAdminRead], dependencies=[Depends(require_roles("superadmin", "admin"))])
def update_review_status(review_id: uuid.UUID, payload: ReviewStatusUpdate, db: Session = Depends(get_db)):
    review = get_review_or_404(db, review_id)
    review.status = payload.status
    if payload.is_verified_mitra is not None:
        review.is_verified_mitra = payload.is_verified_mitra
    db.commit()
    db.refresh(review)
    return DetailResponse(data=ReviewAdminRead.model_validate(review))


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("superadmin"))])
def delete_review(review_id: uuid.UUID, db: Session = Depends(get_db)):
    review = get_review_or_404(db, review_id)
    db.delete(review)
    db.commit()
