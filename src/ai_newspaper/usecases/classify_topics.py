from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from ai_newspaper.domain.models import (
    Category,
    ClassifiedTopic,
    Importance,
    Topic,
    TopicCluster,
)

POLITICS_ECONOMY_TERMS = frozenset(
    {
        "bank",
        "budget",
        "central bank",
        "economy",
        "election",
        "fiscal",
        "inflation",
        "minister",
        "policy",
        "politics",
        "rate",
        "regulation",
        "tax",
    }
)
BUSINESS_TECHNOLOGY_TERMS = frozenset(
    {
        "ai",
        "business",
        "chip",
        "cloud",
        "company",
        "earnings",
        "margin",
        "product",
        "revenue",
        "semiconductor",
        "software",
        "startup",
        "strategy",
        "supply chain",
        "technology",
    }
)
INTERNATIONAL_TERMS = frozenset(
    {
        "alliance",
        "china",
        "diplomacy",
        "eu",
        "foreign",
        "global",
        "international",
        "japan",
        "sanctions",
        "security",
        "trade",
        "treaty",
        "ukraine",
        "united states",
        "war",
    }
)
FORECAST_ALLOWED_TERMS = frozenset(
    {
        "corporate strategy",
        "diplomacy",
        "international relations",
        "policy",
        "product announcement",
        "regulation",
        "sanctions",
        "strategy",
        "technology announcement",
    }
)
FORECAST_FORBIDDEN_TERMS = frozenset(
    {
        "buy recommendation",
        "buy timing",
        "crime outcome",
        "disaster damage",
        "hold recommendation",
        "portfolio",
        "sell recommendation",
        "sell timing",
        "stock price",
        "target price",
        "trading timing",
    }
)
BUSINESS_EXPLAINER_TERMS = frozenset(
    {
        "business",
        "company",
        "competition",
        "earnings",
        "margin",
        "product",
        "revenue",
        "startup",
        "strategy",
        "supply chain",
    }
)


@dataclass(frozen=True)
class ClassifyTopicsUseCase:
    """Classify clustered topics with deterministic first-version rules."""

    def execute(self, clusters: Sequence[TopicCluster]) -> list[ClassifiedTopic]:
        return [self._classify_cluster(cluster) for cluster in clusters]

    def _classify_cluster(self, cluster: TopicCluster) -> ClassifiedTopic:
        text = _cluster_text(cluster)
        category = self._classify_category(cluster, text)
        topic = Topic(
            name=cluster.name,
            category=category,
            importance=_importance_for_size(len(cluster.articles)),
        )
        return ClassifiedTopic(
            topic=topic,
            articles=cluster.articles,
            forecast_allowed=_allows_forecast_subject(text),
            business_explainer_required=_requires_business_explainer(
                category=category,
                text=text,
            ),
        )

    def _classify_category(self, cluster: TopicCluster, text: str) -> Category:
        scores = Counter[Category]()

        for article in cluster.articles:
            scores[article.category] += 2

        scores[Category.POLITICS_ECONOMY] += _keyword_score(
            text,
            POLITICS_ECONOMY_TERMS,
        )
        scores[Category.BUSINESS_TECHNOLOGY] += _keyword_score(
            text,
            BUSINESS_TECHNOLOGY_TERMS,
        )
        scores[Category.INTERNATIONAL] += _keyword_score(text, INTERNATIONAL_TERMS)

        category_order = (
            Category.BUSINESS_TECHNOLOGY,
            Category.POLITICS_ECONOMY,
            Category.INTERNATIONAL,
        )
        return max(category_order, key=lambda category: scores[category])


def _cluster_text(cluster: TopicCluster) -> str:
    article_text = " ".join(
        f"{article.title} {article.summary} {article.source_name}"
        for article in cluster.articles
    )
    return f"{cluster.name} {article_text}".casefold()


def _keyword_score(text: str, terms: frozenset[str]) -> int:
    return sum(1 for term in terms if _contains_term(text, term))


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text
    return re.search(rf"(?<![0-9a-z]){re.escape(term)}(?![0-9a-z])", text) is not None


def _allows_forecast_subject(text: str) -> bool:
    return (
        _keyword_score(text, FORECAST_ALLOWED_TERMS) > 0
        and _keyword_score(text, FORECAST_FORBIDDEN_TERMS) == 0
    )


def _requires_business_explainer(category: Category, text: str) -> bool:
    return category == Category.BUSINESS_TECHNOLOGY or (
        _keyword_score(text, BUSINESS_EXPLAINER_TERMS) > 0
    )


def _importance_for_size(article_count: int) -> Importance:
    if article_count >= 3:
        return Importance.HIGH
    return Importance.MEDIUM
