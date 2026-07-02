from __future__ import annotations

from ai_newspaper.infrastructure.llm.dummy_news_analyzer import DummyNewsAnalyzer


class DummyAnalyzer(DummyNewsAnalyzer):
    """Adapter-compatible name for the deterministic offline analyzer."""
