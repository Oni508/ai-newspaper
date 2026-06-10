from __future__ import annotations

from ai_newspaper.domain.models import AnalysisResult, Article


class DummyAnalyzer:
    """Deterministic offline analyzer for development and tests."""

    def analyze(self, articles: list[Article]) -> list[AnalysisResult]:
        return [
            AnalysisResult(
                article_url=article.url,
                summary=f"Stub summary for: {article.title}",
                background="Background context is not implemented yet.",
                business_explainer=(
                    "This is a development stub and does not provide investment advice."
                ),
                conditional_scenarios=(
                    "If the topic remains relevant, later editions may add context.",
                ),
                uncertainty="Real analysis is not implemented yet.",
                next_checks=("Check the original source.",),
            )
            for article in articles
        ]
