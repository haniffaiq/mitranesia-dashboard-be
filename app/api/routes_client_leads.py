from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.client_auth import get_current_client_user, get_db
from app.models.client_merchant_application import ClientMerchantApplication
from app.models.client_merchant_inquiry import ClientMerchantInquiry
from app.models.client_user import ClientUser
from app.models.merchant import Merchant
from app.schemas.client_leads import (
    ClientMerchantApplicationCreate,
    ClientMerchantApplicationRead,
    ClientMerchantInquiryCreate,
    ClientMerchantInquiryRead,
)
from app.schemas.common import DetailResponse
from app.services.serializers import iso

router = APIRouter(prefix="/client", tags=["client-leads"])


def serialize_inquiry(model: ClientMerchantInquiry) -> ClientMerchantInquiryRead:
    return ClientMerchantInquiryRead(
        id=str(model.id),
        merchant_id=str(model.merchant_id),
        package_name=model.package_name,
        inquiry_type=model.inquiry_type,
        full_name=model.full_name,
        email=model.email,
        phone=model.phone,
        message=model.message,
        status=model.status,
        created_at=iso(model.created_at) or "",
        updated_at=iso(model.updated_at) or "",
    )


def serialize_application(model: ClientMerchantApplication) -> ClientMerchantApplicationRead:
    return ClientMerchantApplicationRead(
        id=str(model.id),
        contact_name=model.contact_name,
        business_name=model.business_name,
        email=model.email,
        phone=model.phone,
        category=model.category,
        city=model.city,
        message=model.message,
        status=model.status,
        created_at=iso(model.created_at) or "",
        updated_at=iso(model.updated_at) or "",
    )


@router.post("/merchant-inquiries", response_model=DetailResponse[ClientMerchantInquiryRead], status_code=status.HTTP_201_CREATED)
def create_merchant_inquiry(
    payload: ClientMerchantInquiryCreate,
    db: Session = Depends(get_db),
    current_user: ClientUser = Depends(get_current_client_user),
):
    try:
        merchant_id = uuid.UUID(payload.merchant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid merchant_id") from exc

    merchant = db.get(Merchant, merchant_id)
    if not merchant or not merchant.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    inquiry = ClientMerchantInquiry(
        client_user_id=current_user.id,
        merchant_id=merchant.id,
        package_name=payload.package_name,
        inquiry_type=payload.inquiry_type,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        message=payload.message,
        status="new",
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return DetailResponse(data=serialize_inquiry(inquiry))


@router.post("/merchant-applications", response_model=DetailResponse[ClientMerchantApplicationRead], status_code=status.HTTP_201_CREATED)
def create_merchant_application(
    payload: ClientMerchantApplicationCreate,
    db: Session = Depends(get_db),
    current_user: ClientUser = Depends(get_current_client_user),
):
    application = ClientMerchantApplication(
        client_user_id=current_user.id,
        contact_name=payload.contact_name,
        business_name=payload.business_name,
        email=payload.email.lower(),
        phone=payload.phone,
        category=payload.category,
        city=payload.city,
        message=payload.message,
        status="new",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return DetailResponse(data=serialize_application(application))
