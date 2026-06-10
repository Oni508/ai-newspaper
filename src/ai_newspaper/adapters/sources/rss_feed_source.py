from __future__ import annotations

from ai_newspaper.domain.models import Article


class RssFeedSource:
    """Placeholder RSS source adapter."""

    def fetch(self) -> list[Article]:
        return []
