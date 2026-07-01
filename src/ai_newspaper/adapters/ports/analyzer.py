from __future__ import annotations

from typing import Protocol

from ai_newspaper.domain.models import AnalysisResult, Article


class NewsAnalyzerPort(Protocol):
    def analyze(self, articles: list[Article]) -> list[AnalysisResult]:
        """Analyze candidate articles."""
