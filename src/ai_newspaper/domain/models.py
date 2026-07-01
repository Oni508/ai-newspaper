from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Category(StrEnum):
    POLITICS_ECONOMY = "politics_economy"
    BUSINESS_TECHNOLOGY = "business_technology"
    INTERNATIONAL_AFFAIRS = "international_affairs"


class Importance(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ArticleSource:
    name: str
    url: str
    category: Category


@dataclass(frozen=True)
class Topic:
    name: str
    category: Category
    importance: Importance = Importance.MEDIUM

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("topic name must not be empty")


@dataclass(frozen=True)
class AnalysisResult:
    article_url: str
    summary: str
    background: str
    business_explainer: str
    conditional_scenarios: tuple[str, ...] = ()
    uncertainty: str = ""
    next_checks: tuple[str, ...] = ()


@dataclass(frozen=True)
class DigestEdition:
    generated_at: datetime
    label: str


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    source_name: str
    category: Category
    published_at: datetime | None = None
    summary: str = ""


@dataclass(frozen=True)
class Digest:
    edition: DigestEdition
    articles: tuple[Article, ...] = field(default_factory=tuple)
    analyses: tuple[AnalysisResult, ...] = field(default_factory=tuple)
