from __future__ import annotations

from dataclasses import dataclass

from ai_newspaper.domain.models import AnalysisResult
from ai_newspaper.usecases.ports import AnalyzerPort, ArticleRepositoryPort


@dataclass(frozen=True)
class AnalyzeArticles:
    repository: ArticleRepositoryPort
    analyzer: AnalyzerPort

    def execute(self) -> list[AnalysisResult]:
        articles = self.repository.list_articles()
        analyses = self.analyzer.analyze(articles)
        self.repository.save_analyses(analyses)
        return analyses
