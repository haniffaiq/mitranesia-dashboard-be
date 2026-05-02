from __future__ import annotations

from app.schemas.common import APIModel, MetaData


class ClientMerchantPackage(APIModel):
    id: str
    name: str
    price: int
    description: str


class ClientMerchantImage(APIModel):
    id: str
    label: str | None = None
    url: str


class ClientMerchant(APIModel):
    id: str
    name: str
    slug: str
    category: str
    logoUrl: str
    bepMonths: int
    isTopMerchant: bool = False
    isOfficialPartner: bool = False
    rating: float | None = None
    type: str
    packages: list[ClientMerchantPackage]
    images: list[ClientMerchantImage] = []
    minPrice: int
    maxPrice: int
    reviewAverage: float | None = None
    reviewCount: int = 0


class ClientInsightArticle(APIModel):
    id: str
    title: str
    slug: str
    category: str
    date: str
    author: str
    image: str
    excerpt: str
    readTime: str
    content: list[str]


class ClientCarouselSlide(APIModel):
    id: str
    title: str
    image: str
    tag: str
    icon: str
    highlight: str
    description: str
    color: str
    ctaLabel: str
    ctaHref: str


class ClientMerchantsFilters(APIModel):
    categories: list[str]
    types: list[str]
    minPrice: int
    maxPrice: int


class ClientHome(APIModel):
    carouselSlides: list[ClientCarouselSlide]
    topMerchants: list[ClientMerchant]
    recommendedMerchants: list[ClientMerchant]
    otherMerchants: list[ClientMerchant]
    featuredInsight: ClientInsightArticle | None = None
    recentInsights: list[ClientInsightArticle]
    merchantFilters: ClientMerchantsFilters


class ClientMerchantList(APIModel):
    data: list[ClientMerchant]
    meta: MetaData
    filters: ClientMerchantsFilters


class ClientInsightCategories(APIModel):
    categories: list[str]
