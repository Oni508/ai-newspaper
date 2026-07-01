from __future__ import annotations

from ai_newspaper.domain.models import AnalysisResult, Article
from ai_newspaper.infrastructure.persistence.article_repository import (
    SqliteArticleRepository,
)


class InMemoryArticleRepository:
    """Temporary repository used until the SQLite adapter is implemented."""

    def __init__(self) -> None:
        self._articles: list[Article] = []
        self._analyses: list[AnalysisResult] = []

    def save_articles(self, articles: list[Article]) -> None:
        self._articles = list(articles)

    def list_articles(self) -> list[Article]:
        return list(self._articles)

    def save_analyses(self, analyses: list[AnalysisResult]) -> None:
        self._analyses = list(analyses)

    def list_analyses(self) -> list[AnalysisResult]:
        return list(self._analyses)

__all__ = ["InMemoryArticleRepository", "SqliteArticleRepository"]
