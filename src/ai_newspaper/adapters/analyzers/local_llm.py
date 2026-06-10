from __future__ import annotations

from ai_newspaper.domain.models import AnalysisResult, Article


class LocalLlmAnalyzer:
    """Placeholder for a future local LLM analyzer adapter."""

    def analyze(self, articles: list[Article]) -> list[AnalysisResult]:
        raise NotImplementedError("Local LLM analyzer is not implemented yet.")
