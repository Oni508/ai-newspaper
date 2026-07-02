from __future__ import annotations

from dataclasses import dataclass, replace
from urllib.parse import parse_qsl, urldefrag, urlencode, urlsplit, urlunsplit

from ai_newspaper.domain.models import Article

TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = frozenset(
    {
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
    }
)


@dataclass(frozen=True)
class NormalizeArticlesUseCase:
    """Normalize fetched articles and remove duplicate URLs."""

    def execute(self, articles: list[Article]) -> list[Article]:
        normalized_articles: list[Article] = []
        seen_urls: set[str] = set()

        for article in articles:
            normalized_url = normalize_article_url(article.url)
            if not normalized_url or normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            normalized_articles.append(
                replace(
                    article,
                    title=article.title.strip(),
                    url=normalized_url,
                    source_name=article.source_name.strip(),
                    summary=article.summary.strip(),
                )
            )

        return normalized_articles


def normalize_article_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""

    defragged_url, _fragment = urldefrag(cleaned)
    parts = urlsplit(defragged_url)
    scheme = parts.scheme.lower()
    netloc = _normalize_netloc(parts.hostname, parts.port, scheme)
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = _normalize_query(parts.query)

    return urlunsplit((scheme, netloc, path, query, ""))


def _normalize_netloc(hostname: str | None, port: int | None, scheme: str) -> str:
    if hostname is None:
        return ""

    host = hostname.lower()
    if port is None or (scheme, port) in {("http", 80), ("https", 443)}:
        return host
    return f"{host}:{port}"


def _normalize_query(query: str) -> str:
    pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        normalized_key = key.strip()
        if not normalized_key:
            continue
        key_lower = normalized_key.lower()
        if key_lower in TRACKING_QUERY_KEYS:
            continue
        if any(key_lower.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES):
            continue
        pairs.append((normalized_key, value))

    return urlencode(sorted(pairs))
