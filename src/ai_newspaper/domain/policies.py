from __future__ import annotations

from datetime import timedelta

from ai_newspaper.domain.models import Category

DIGEST_RETENTION = timedelta(hours=48)

SUPPORTED_CATEGORIES: frozenset[Category] = frozenset(
    {
        Category.POLITICS_ECONOMY,
        Category.BUSINESS_TECHNOLOGY,
        Category.INTERNATIONAL_AFFAIRS,
    }
)

FORBIDDEN_INVESTMENT_ADVICE_TERMS: tuple[str, ...] = (
    "buy recommendation",
    "sell recommendation",
    "hold recommendation",
    "target price",
    "trading timing",
    "portfolio advice",
    "margin trading",
)


def is_supported_category(category: Category) -> bool:
    return category in SUPPORTED_CATEGORIES
