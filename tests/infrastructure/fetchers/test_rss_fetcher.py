from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_newspaper.domain.models import Category
from ai_newspaper.infrastructure.fetchers import rss_fetcher
from ai_newspaper.infrastructure.fetchers.rss_fetcher import RssFetcher


def test_fetch_reads_enabled_rss_sources_and_converts_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources_path = tmp_path / "sources.yaml"
    sources_path.write_text(
        """
sources:
  - name: Enabled Feed
    type: rss
    url: https://example.com/rss
    enabled: true
    category: business_technology
  - name: Disabled Feed
    type: rss
    url: https://disabled.example.com/rss
    enabled: false
    category: politics_economy
  - name: Future API
    type: newsapi
    url: https://api.example.com/news
    enabled: true
    category: international_affairs
""",
        encoding="utf-8",
    )
    requested_urls: list[str] = []

    def fake_parse(url: str) -> SimpleNamespace:
        requested_urls.append(url)
        return SimpleNamespace(
            entries=[
                {
                    "title": "Company announces product",
                    "link": "https://example.com/articles/1#comments",
                    "summary": "Product summary",
                    "published_parsed": None,
                },
            ]
        )

    monkeypatch.setattr(rss_fetcher.feedparser, "parse", fake_parse)

    articles = RssFetcher(sources_path).fetch()

    assert requested_urls == ["https://example.com/rss"]
    assert len(articles) == 1
    assert articles[0].title == "Company announces product"
    assert articles[0].url == "https://example.com/articles/1"
    assert articles[0].source_name == "Enabled Feed"
    assert articles[0].category == Category.BUSINESS_TECHNOLOGY
    assert articles[0].summary == "Product summary"


def test_fetch_skips_missing_urls_and_duplicate_urls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources_path = tmp_path / "sources.yaml"
    sources_path.write_text(
        """
sources:
  - name: Example Feed
    type: rss
    url: https://example.com/rss
    enabled: true
    category: international_affairs
""",
        encoding="utf-8",
    )

    def fake_parse(url: str) -> SimpleNamespace:
        return SimpleNamespace(
            entries=[
                {"title": "No URL"},
                {"title": "First", "link": "https://example.com/articles/1/"},
                {"title": "Duplicate", "link": "https://example.com/articles/1"},
            ]
        )

    monkeypatch.setattr(rss_fetcher.feedparser, "parse", fake_parse)

    articles = RssFetcher(sources_path).fetch()

    assert [article.title for article in articles] == ["First"]
    assert [article.url for article in articles] == ["https://example.com/articles/1"]


def test_fetch_continues_when_one_source_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources_path = tmp_path / "sources.yaml"
    sources_path.write_text(
        """
sources:
  - name: Broken Feed
    type: rss
    url: https://broken.example.com/rss
    enabled: true
    category: politics_economy
  - name: Working Feed
    type: rss
    url: https://working.example.com/rss
    enabled: true
    category: politics_economy
""",
        encoding="utf-8",
    )

    def fake_parse(url: str) -> SimpleNamespace:
        if "broken" in url:
            raise OSError("network unavailable")
        return SimpleNamespace(entries=[{"title": "Policy", "link": url + "/article"}])

    monkeypatch.setattr(rss_fetcher.feedparser, "parse", fake_parse)

    articles = RssFetcher(sources_path).fetch()

    assert len(articles) == 1
    assert articles[0].title == "Policy"
    assert articles[0].source_name == "Working Feed"
