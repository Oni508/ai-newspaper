from __future__ import annotations

from dataclasses import dataclass

from ai_newspaper.domain.models import Article
from ai_newspaper.usecases.ports import ArticleRepositoryPort, ArticleSourcePort


@dataclass(frozen=True)
class FetchArticles:
    source: ArticleSourcePort
    repository: ArticleRepositoryPort

    def execute(self) -> list[Article]:
        articles = self.source.fetch()
        self.repository.save_articles(articles)
        return articles
