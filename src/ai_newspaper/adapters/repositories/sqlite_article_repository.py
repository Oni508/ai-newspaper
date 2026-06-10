from __future__ import annotations

from ai_newspaper.domain.models import AnalysisResult, Article


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


class SqliteArticleRepository:
    """Placeholder for the SQLite article repository adapter."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def save_articles(self, articles: list[Article]) -> None:
        raise NotImplementedError("SQLite article repository is not implemented yet.")

    def list_articles(self) -> list[Article]:
        raise NotImplementedError("SQLite article repository is not implemented yet.")

    def save_analyses(self, analyses: list[AnalysisResult]) -> None:
        raise NotImplementedError("SQLite article repository is not implemented yet.")

    def list_analyses(self) -> list[AnalysisResult]:
        raise NotImplementedError("SQLite article repository is not implemented yet.")
