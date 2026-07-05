from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import mktime
from typing import Any
from urllib.parse import urldefrag, urlsplit, urlunsplit

import feedparser  # type: ignore[import-untyped]
import yaml  # type: ignore[import-untyped]

from ai_newspaper.domain.models import Article, Category, category_from_value


@dataclass(frozen=True)
class RssSource:
    name: str
    url: str
    category: Category
    enabled: bool = True
    region: str = "global"
    priority: int = 1


class RssFetcher:
    def __init__(self, sources_path: Path | str = Path("config/sources.yaml")) -> None:
        self._sources_path = Path(sources_path)

    def fetch(self) -> list[Article]:
        articles: list[Article] = []
        seen_urls: set[str] = set()

        for source in self._load_sources():
            if not source.enabled:
                continue
            for article in self._fetch_source(source):
                if article.url in seen_urls:
                    continue
                seen_urls.add(article.url)
                articles.append(article)

        return articles

    def _load_sources(self) -> list[RssSource]:
        if not self._sources_path.exists():
            return []

        with self._sources_path.open(encoding="utf-8") as file:
            payload = yaml.safe_load(file) or {}

        if not isinstance(payload, dict):
            return []

        raw_sources = payload.get("sources", [])
        if not isinstance(raw_sources, list):
            return []

        sources: list[RssSource] = []
        for raw_source in raw_sources:
            source = _source_from_config(raw_source)
            if source is not None:
                sources.append(source)

        return sources

    def _fetch_source(self, source: RssSource) -> list[Article]:
        try:
            feed = feedparser.parse(source.url)
        except Exception:
            return []

        entries = getattr(feed, "entries", [])
        if not isinstance(entries, list):
            return []

        articles: list[Article] = []
        for entry in entries:
            try:
                article = _article_from_entry(entry, source)
            except Exception:
                continue
            if article is not None:
                articles.append(article)

        return articles


def _source_from_config(raw_source: object) -> RssSource | None:
    if not isinstance(raw_source, dict):
        return None

    if str(raw_source.get("type", "rss")).lower() != "rss":
        return None

    name = _clean_text(raw_source.get("name"))
    url = _normalize_url(_clean_text(raw_source.get("url")))
    category = _category_from_config(raw_source.get("category"))
    enabled = _enabled_from_config(raw_source.get("enabled", True))
    region = _region_from_config(raw_source.get("region"))
    priority = _priority_from_config(raw_source.get("priority"))

    if not name or not _is_http_url(url) or category is None:
        return None

    return RssSource(
        name=name,
        url=url,
        category=category,
        enabled=enabled,
        region=region,
        priority=priority,
    )


def _article_from_entry(entry: Any, source: RssSource) -> Article | None:
    url = _normalize_url(_entry_text(entry, "link"))
    if not url:
        return None

    title = _entry_text(entry, "title") or url
    summary = _entry_text(entry, "summary") or _entry_text(entry, "description")

    return Article(
        title=title,
        url=url,
        source_name=source.name,
        category=source.category,
        published_at=_entry_datetime(entry),
        summary=summary,
    )


def _category_from_config(value: object) -> Category | None:
    try:
        return category_from_value(value)
    except ValueError:
        return None


def _enabled_from_config(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _region_from_config(value: object) -> str:
    region = _clean_text(value).lower()
    if region in {"jp", "global"}:
        return region
    return "global"


def _priority_from_config(value: object) -> int:
    try:
        priority = int(str(value).strip())
    except (TypeError, ValueError):
        return 1
    return max(0, min(priority, 10))


def _entry_datetime(entry: Any) -> datetime | None:
    published_parsed = getattr(entry, "published_parsed", None)
    if published_parsed is None:
        published_parsed = getattr(entry, "updated_parsed", None)
    if published_parsed is None:
        return None
    try:
        return datetime.fromtimestamp(mktime(published_parsed))
    except (OverflowError, TypeError, ValueError):
        return None


def _entry_text(entry: Any, key: str) -> str:
    if isinstance(entry, dict):
        return _clean_text(entry.get(key))
    return _clean_text(getattr(entry, key, ""))


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_url(value: str) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return ""

    defragged_url, _fragment = urldefrag(cleaned)
    parts = urlsplit(defragged_url)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")

    return urlunsplit((scheme, netloc, path, parts.query, ""))


def _is_http_url(value: str) -> bool:
    parts = urlsplit(value)
    return parts.scheme in {"http", "https"} and bool(parts.netloc)
