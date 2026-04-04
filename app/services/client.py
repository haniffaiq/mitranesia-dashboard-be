from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.carousel_item import CarouselItem
from app.models.insight_article import InsightArticle
from app.models.merchant import Merchant
from app.schemas.image_asset import resolve_image_source
from app.schemas.client import (
    ClientCarouselSlide,
    ClientHome,
    ClientInsightArticle,
    ClientMerchant,
    ClientMerchantPackage,
    ClientMerchantsFilters,
)
from app.schemas.common import MetaData

INDONESIAN_MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "Mei",
    6: "Jun",
    7: "Jul",
    8: "Agu",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Des",
}


def format_indonesian_date(value: datetime | None) -> str:
    if value is None:
        return ""
    return f"{value.day:02d} {INDONESIAN_MONTHS[value.month]} {value.year}"


def serialize_client_merchant(model: Merchant) -> ClientMerchant:
    packages = [
        ClientMerchantPackage(
            id=str(item.id),
            name=item.name,
            price=item.price,
            description=item.description,
        )
        for item in model.packages
    ]
    prices = [item.price for item in model.packages]
    rating = float(model.rating) if isinstance(model.rating, Decimal) else model.rating
    return ClientMerchant(
        id=str(model.id),
        name=model.name,
        slug=model.slug,
        category=model.category,
        logoUrl=resolve_image_source(model.logo_url, model.logo_base64),
        bepMonths=model.bep_months,
        isTopMerchant=model.is_top_merchant,
        rating=rating,
        type=model.type,
        packages=packages,
        minPrice=min(prices) if prices else 0,
        maxPrice=max(prices) if prices else 0,
    )


def serialize_client_insight(model: InsightArticle) -> ClientInsightArticle:
    date_value = model.published_at or model.created_at
    return ClientInsightArticle(
        id=str(model.id),
        title=model.title,
        slug=model.slug,
        category=model.category,
        date=format_indonesian_date(date_value),
        author=model.author,
        image=resolve_image_source(model.image, model.image_base64),
        excerpt=model.excerpt,
        readTime=model.read_time,
        content=model.content,
    )


def serialize_client_carousel(model: CarouselItem) -> ClientCarouselSlide:
    return ClientCarouselSlide(
        id=str(model.id),
        title=model.title,
        image=resolve_image_source(model.image_url, model.image_base64),
        tag=model.tag,
        icon=model.icon,
        highlight=model.highlight,
        description=model.description,
        color=model.color,
        ctaLabel=model.cta_label,
        ctaHref=model.cta_href,
    )


def get_active_merchants(db: Session) -> list[Merchant]:
    return (
        db.scalars(
            select(Merchant)
            .options(selectinload(Merchant.packages))
            .where(Merchant.is_active.is_(True))
            .order_by(Merchant.created_at.desc())
        )
        .unique()
        .all()
    )


def get_published_insights(db: Session) -> list[InsightArticle]:
    return db.scalars(
        select(InsightArticle)
        .where(InsightArticle.status == "published")
        .order_by(InsightArticle.published_at.desc(), InsightArticle.created_at.desc())
    ).all()


def get_active_carousels(db: Session) -> list[CarouselItem]:
    return db.scalars(
        select(CarouselItem)
        .where(CarouselItem.is_active.is_(True))
        .order_by(CarouselItem.sort_order.asc(), CarouselItem.created_at.desc())
    ).all()


def build_merchant_filters(merchants: list[Merchant]) -> ClientMerchantsFilters:
    categories = sorted({item.category for item in merchants})
    types = sorted({item.type for item in merchants})
    all_prices = [pkg.price for merchant in merchants for pkg in merchant.packages]
    return ClientMerchantsFilters(
        categories=categories,
        types=types,
        minPrice=min(all_prices) if all_prices else 0,
        maxPrice=max(all_prices) if all_prices else 0,
    )


def find_client_merchant(db: Session, identifier: str) -> Merchant | None:
    statement = select(Merchant).options(selectinload(Merchant.packages))
    try:
        merchant_id = uuid.UUID(identifier)
        return db.scalar(statement.where(Merchant.id == merchant_id))
    except ValueError:
        return db.scalar(statement.where(Merchant.slug == identifier))


def find_client_insight(db: Session, identifier: str) -> InsightArticle | None:
    statement = select(InsightArticle).where(InsightArticle.status == "published")
    try:
        article_id = uuid.UUID(identifier)
        return db.scalar(statement.where(InsightArticle.id == article_id))
    except ValueError:
        return db.scalar(statement.where(InsightArticle.slug == identifier))


def build_client_home(db: Session) -> ClientHome:
    merchants = get_active_merchants(db)
    serialized_merchants = [serialize_client_merchant(item) for item in merchants]
    top_merchants = [item for item in serialized_merchants if item.isTopMerchant][:8]
    recommended_merchants = [item for item in serialized_merchants if "Autopilot" in item.type or item.rating == 4.7][:4]

    insights = get_published_insights(db)
    serialized_insights = [serialize_client_insight(item) for item in insights]
    carousel_slides = [serialize_client_carousel(item) for item in get_active_carousels(db)]

    return ClientHome(
        carouselSlides=carousel_slides,
        topMerchants=top_merchants,
        recommendedMerchants=recommended_merchants,
        otherMerchants=serialized_merchants[:8],
        featuredInsight=serialized_insights[0] if serialized_insights else None,
        recentInsights=serialized_insights[1:7],
        merchantFilters=build_merchant_filters(merchants),
    )


def paginate_client_merchants(merchants: list[ClientMerchant], page: int, page_size: int) -> tuple[list[ClientMerchant], MetaData]:
    total = len(merchants)
    start = (page - 1) * page_size
    end = start + page_size
    return merchants[start:end], MetaData.from_pagination(page, page_size, total)
