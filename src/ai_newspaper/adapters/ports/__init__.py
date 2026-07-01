from __future__ import annotations

from ai_newspaper.adapters.ports.analyzer import NewsAnalyzerPort
from ai_newspaper.adapters.ports.fetcher import ArticleFetcherPort
from ai_newspaper.adapters.ports.renderer import DigestRendererPort
from ai_newspaper.adapters.ports.repositories import (
    ArticleRepositoryPort,
    DigestRepositoryPort,
    TopicRepositoryPort,
)
from ai_newspaper.adapters.ports.system import ClockPort, FileStoragePort

__all__ = [
    "ArticleFetcherPort",
    "ArticleRepositoryPort",
    "ClockPort",
    "DigestRendererPort",
    "DigestRepositoryPort",
    "FileStoragePort",
    "NewsAnalyzerPort",
    "TopicRepositoryPort",
]
