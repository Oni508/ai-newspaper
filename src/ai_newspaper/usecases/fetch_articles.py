from __future__ import annotations

from dataclasses import dataclass, field

from ai_newspaper.adapters.ports import ArticleFetcherPort, ArticleRepositoryPort
from ai_newspaper.domain.models import Article
from ai_newspaper.usecases.normalize_articles import NormalizeArticlesUseCase


@dataclass(frozen=True)
class FetchArticles:
    source: ArticleFetcherPort
    repository: ArticleRepositoryPort
    normalizer: NormalizeArticlesUseCase = field(
        default_factory=NormalizeArticlesUseCase
    )

    def execute(self) -> list[Article]:
        articles = self.normalizer.execute(self.source.fetch())
        self.repository.save_articles(articles)
        return articles
