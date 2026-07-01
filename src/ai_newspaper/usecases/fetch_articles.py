from __future__ import annotations

from dataclasses import dataclass

from ai_newspaper.adapters.ports import ArticleFetcherPort, ArticleRepositoryPort
from ai_newspaper.domain.models import Article


@dataclass(frozen=True)
class FetchArticles:
    source: ArticleFetcherPort
    repository: ArticleRepositoryPort

    def execute(self) -> list[Article]:
        articles = self.source.fetch()
        self.repository.save_articles(articles)
        return articles
