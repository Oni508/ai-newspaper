from __future__ import annotations

from pathlib import Path

from ai_newspaper.domain.models import Article
from ai_newspaper.infrastructure.fetchers import RssFetcher


class RssFeedSource:
    """RSS source adapter used by the fetch usecase."""

    def __init__(self, sources_path: Path | str = Path("config/sources.yaml")) -> None:
        self._fetcher = RssFetcher(sources_path)

    def fetch(self) -> list[Article]:
        return self._fetcher.fetch()
