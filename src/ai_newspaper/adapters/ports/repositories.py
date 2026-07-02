from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ai_newspaper.domain.models import AnalysisResult, Article, Digest, Topic


class ArticleRepositoryPort(Protocol):
    def save_articles(self, articles: list[Article]) -> None:
        """Persist fetched articles."""

    def list_articles(self) -> list[Article]:
        """List stored candidate articles."""

    def save_analyses(self, analyses: list[AnalysisResult]) -> None:
        """Persist analysis results."""

    def list_analyses(self) -> list[AnalysisResult]:
        """List stored analysis results."""


class TopicRepositoryPort(Protocol):
    def save_topics(self, topics: list[Topic]) -> None:
        """Persist configured or discovered topics."""

    def list_topics(self) -> list[Topic]:
        """List stored topics."""


class DigestRepositoryPort(Protocol):
    def save_digest(self, digest: Digest) -> None:
        """Persist digest metadata and content references."""

    def list_digests(self) -> list[Digest]:
        """List stored digests."""

    def delete_digest(self, generated_at: datetime, label: str) -> None:
        """Delete one digest metadata row."""
