from __future__ import annotations

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

type ArticleSourcePort = ArticleFetcherPort
type AnalyzerPort = NewsAnalyzerPort
type DigestStorePort = FileStoragePort

__all__ = [
    "AnalyzerPort",
    "ArticleFetcherPort",
    "ArticleRepositoryPort",
    "ArticleSourcePort",
    "ClockPort",
    "DigestRendererPort",
    "DigestRepositoryPort",
    "DigestStorePort",
    "FileStoragePort",
    "NewsAnalyzerPort",
    "TopicRepositoryPort",
]
