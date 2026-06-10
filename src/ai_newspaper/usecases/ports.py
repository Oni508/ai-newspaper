from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

from ai_newspaper.domain.models import AnalysisResult, Article, Digest


class ArticleSourcePort(Protocol):
    def fetch(self) -> list[Article]:
        """Fetch candidate articles."""


class ArticleRepositoryPort(Protocol):
    def save_articles(self, articles: list[Article]) -> None:
        """Persist fetched articles."""

    def list_articles(self) -> list[Article]:
        """List stored candidate articles."""

    def save_analyses(self, analyses: list[AnalysisResult]) -> None:
        """Persist analysis results."""

    def list_analyses(self) -> list[AnalysisResult]:
        """List stored analysis results."""


class AnalyzerPort(Protocol):
    def analyze(self, articles: list[Article]) -> list[AnalysisResult]:
        """Analyze candidate articles."""


class DigestRendererPort(Protocol):
    def render(self, digest: Digest) -> str:
        """Render digest HTML."""


class DigestStorePort(Protocol):
    def write_html(self, generated_at: datetime, html: str) -> Path:
        """Write generated HTML and return the path."""

    def prune_older_than(self, now: datetime, retention: timedelta) -> list[Path]:
        """Delete old generated HTML files and return deleted paths."""


class ClockPort(Protocol):
    def now(self) -> datetime:
        """Return the current local time."""
