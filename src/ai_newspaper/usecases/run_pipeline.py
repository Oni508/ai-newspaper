from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ai_newspaper.adapters.ports import (
    ArticleFetcherPort,
    ArticleRepositoryPort,
    ClockPort,
    DigestRendererPort,
    DigestRepositoryPort,
    FileStoragePort,
    NewsAnalyzerPort,
    TopicRepositoryPort,
)
from ai_newspaper.usecases.classify_topics import ClassifyTopicsUseCase
from ai_newspaper.usecases.cluster_topics import ClusterTopicsUseCase
from ai_newspaper.usecases.generate_digest import GenerateDigest
from ai_newspaper.usecases.normalize_articles import NormalizeArticlesUseCase
from ai_newspaper.usecases.prune_digests import PruneDigests


@dataclass(frozen=True)
class RunDigestPipelineResult:
    fetched_count: int
    saved_count: int
    normalized_count: int
    topic_count: int
    classified_topic_count: int
    analyzed_count: int
    digest_path: Path
    pruned_count: int


@dataclass(frozen=True)
class RunDigestPipelineUseCase:
    source: ArticleFetcherPort
    article_repository: ArticleRepositoryPort
    topic_repository: TopicRepositoryPort
    analyzer: NewsAnalyzerPort
    digest_repository: DigestRepositoryPort
    renderer: DigestRendererPort
    store: FileStoragePort
    clock: ClockPort
    normalizer: NormalizeArticlesUseCase = field(
        default_factory=NormalizeArticlesUseCase
    )
    cluster_topics: ClusterTopicsUseCase = field(default_factory=ClusterTopicsUseCase)
    classify_topics: ClassifyTopicsUseCase = field(
        default_factory=ClassifyTopicsUseCase
    )

    def execute(self) -> RunDigestPipelineResult:
        fetched_articles = self.source.fetch()
        normalized_articles = self.normalizer.execute(fetched_articles)
        self.article_repository.save_articles(normalized_articles)

        topic_clusters = self.cluster_topics.execute(normalized_articles)
        classified_topics = self.classify_topics.execute(topic_clusters)
        self.topic_repository.save_topics(
            [classified_topic.topic for classified_topic in classified_topics]
        )

        analyses = self.analyzer.analyze(normalized_articles)
        self.article_repository.save_analyses(analyses)

        digest_path = GenerateDigest(
            repository=self.article_repository,
            digest_repository=self.digest_repository,
            renderer=self.renderer,
            store=self.store,
            clock=self.clock,
        ).execute()
        pruned = PruneDigests(
            store=self.store,
            digest_repository=self.digest_repository,
            clock=self.clock,
        ).execute()
        return RunDigestPipelineResult(
            fetched_count=len(fetched_articles),
            saved_count=len(normalized_articles),
            normalized_count=len(normalized_articles),
            topic_count=len(topic_clusters),
            classified_topic_count=len(classified_topics),
            analyzed_count=len(analyses),
            digest_path=digest_path,
            pruned_count=len(pruned),
        )


PipelineResult = RunDigestPipelineResult
RunPipeline = RunDigestPipelineUseCase
