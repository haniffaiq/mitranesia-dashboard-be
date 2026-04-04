from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.models.admin_user import AdminUser
from app.models.carousel_item import CarouselItem
from app.models.insight_article import InsightArticle
from app.models.merchant import Merchant
from app.models.merchant_package import MerchantPackage
from app.schemas.admin_user import AdminUserRead
from app.schemas.auth import AuthUser
from app.schemas.carousel import CarouselItemRead
from app.schemas.insight import InsightArticleRead
from app.schemas.merchant import MerchantPackageRead, MerchantRead


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_package(model: MerchantPackage) -> MerchantPackageRead:
    return MerchantPackageRead(
        id=str(model.id),
        name=model.name,
        price=model.price,
        description=model.description,
        sort_order=model.sort_order,
        created_at=iso(model.created_at) or "",
        updated_at=iso(model.updated_at) or "",
    )


def serialize_merchant(model: Merchant) -> MerchantRead:
    rating = float(model.rating) if isinstance(model.rating, Decimal) else model.rating
    return MerchantRead(
        id=str(model.id),
        name=model.name,
        slug=model.slug,
        category=model.category,
        type=model.type,
        logo_url=model.logo_url or "",
        logo_base64=model.logo_base64,
        bep_months=model.bep_months,
        rating=rating,
        is_active=model.is_active,
        is_top_merchant=model.is_top_merchant,
        description=model.description,
        packages=[serialize_package(pkg) for pkg in model.packages],
        created_at=iso(model.created_at) or "",
        updated_at=iso(model.updated_at) or "",
    )


def serialize_admin_user(model: AdminUser) -> AdminUserRead:
    return AdminUserRead(
        id=str(model.id),
        username=model.username,
        role=model.role,
        is_active=model.is_active,
        created_at=iso(model.created_at) or "",
        updated_at=iso(model.updated_at) or "",
    )


def serialize_auth_user(model: AdminUser) -> AuthUser:
    return AuthUser(**serialize_admin_user(model).model_dump())


def serialize_insight(model: InsightArticle) -> InsightArticleRead:
    return InsightArticleRead(
        id=str(model.id),
        title=model.title,
        slug=model.slug,
        category=model.category,
        author=model.author,
        image=model.image or "",
        image_base64=model.image_base64,
        excerpt=model.excerpt,
        read_time=model.read_time,
        content=model.content,
        status=model.status,
        published_at=model.published_at,
        created_at=iso(model.created_at) or "",
        updated_at=iso(model.updated_at) or "",
    )


def serialize_carousel(model: CarouselItem) -> CarouselItemRead:
    return CarouselItemRead(
        id=str(model.id),
        title=model.title,
        image_url=model.image_url or "",
        image_base64=model.image_base64,
        tag=model.tag,
        icon=model.icon,
        highlight=model.highlight,
        description=model.description,
        color=model.color,
        cta_label=model.cta_label,
        cta_href=model.cta_href,
        sort_order=model.sort_order,
        is_active=model.is_active,
        created_at=iso(model.created_at) or "",
        updated_at=iso(model.updated_at) or "",
    )
