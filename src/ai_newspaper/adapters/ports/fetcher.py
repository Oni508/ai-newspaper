from __future__ import annotations

from typing import Protocol

from ai_newspaper.domain.models import Article


class ArticleFetcherPort(Protocol):
    def fetch(self) -> list[Article]:
        """Fetch candidate articles."""
