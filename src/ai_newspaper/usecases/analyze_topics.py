from __future__ import annotations

from dataclasses import dataclass

from ai_newspaper.adapters.ports import ArticleRepositoryPort, NewsAnalyzerPort
from ai_newspaper.domain.models import AnalysisResult


@dataclass(frozen=True)
class AnalyzeTopics:
    repository: ArticleRepositoryPort
    analyzer: NewsAnalyzerPort

    def execute(self) -> list[AnalysisResult]:
        articles = self.repository.list_articles()
        analyses = self.analyzer.analyze(articles)
        self.repository.save_analyses(analyses)
        return analyses
