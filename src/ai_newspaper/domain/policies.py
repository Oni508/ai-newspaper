from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

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

ALLOWED_FORECAST_TOPIC_TERMS: tuple[str, ...] = (
    "policy",
    "corporate strategy",
    "technology announcement",
    "technology announcements",
    "international relations",
)

FORBIDDEN_FORECAST_TOPIC_TERMS: tuple[str, ...] = (
    "stock price",
    "buy or sell timing",
    "crime outcome",
    "individual responsibility",
    "disaster damage expansion",
)

CONDITIONAL_SCENARIO_MARKERS: tuple[str, ...] = (
    "if ",
    "assuming ",
    "provided ",
    "scenario",
    "may ",
    "could ",
    "might ",
)


def is_supported_category(category: Category) -> bool:
    return category in SUPPORTED_CATEGORIES


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized = text.casefold()
    return any(term.casefold() in normalized for term in terms)


@dataclass(frozen=True)
class ForecastPolicy:
    allowed_categories: frozenset[Category] = SUPPORTED_CATEGORIES
    allowed_topic_terms: tuple[str, ...] = ALLOWED_FORECAST_TOPIC_TERMS
    forbidden_topic_terms: tuple[str, ...] = FORBIDDEN_FORECAST_TOPIC_TERMS
    forbidden_investment_advice_terms: tuple[str, ...] = (
        FORBIDDEN_INVESTMENT_ADVICE_TERMS
    )
    conditional_markers: tuple[str, ...] = CONDITIONAL_SCENARIO_MARKERS

    def allows_category(self, category: Category) -> bool:
        return category in self.allowed_categories

    def is_allowed_topic(self, text: str) -> bool:
        return _contains_any(text, self.allowed_topic_terms)

    def is_forbidden_topic(self, text: str) -> bool:
        return _contains_any(text, self.forbidden_topic_terms)

    def contains_investment_advice(self, text: str) -> bool:
        return _contains_any(text, self.forbidden_investment_advice_terms)

    def is_conditional_scenario(self, text: str) -> bool:
        return _contains_any(text, self.conditional_markers)

    def allows_forecast(self, category: Category, text: str) -> bool:
        return (
            self.allows_category(category)
            and self.is_allowed_topic(text)
            and self.is_conditional_scenario(text)
            and not self.is_forbidden_topic(text)
            and not self.contains_investment_advice(text)
        )


@dataclass(frozen=True)
class RetentionPolicy:
    retention: timedelta = DIGEST_RETENTION

    def __post_init__(self) -> None:
        if self.retention <= timedelta(0):
            raise ValueError("retention must be positive")

    def expires_before(self, now: datetime) -> datetime:
        return now - self.retention
