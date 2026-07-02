from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import timedelta
from difflib import SequenceMatcher

from ai_newspaper.domain.models import Article, TopicCluster

DEFAULT_TITLE_SIMILARITY_THRESHOLD = 0.62
DEFAULT_TIME_WINDOW = timedelta(hours=24)

_TOKEN_RE = re.compile(r"[0-9A-Za-z]+")


@dataclass(frozen=True)
class ClusterTopicsUseCase:
    """Cluster articles by title similarity and publication-time proximity."""

    title_similarity_threshold: float = DEFAULT_TITLE_SIMILARITY_THRESHOLD
    time_window: timedelta = DEFAULT_TIME_WINDOW

    def __post_init__(self) -> None:
        if not 0 <= self.title_similarity_threshold <= 1:
            raise ValueError("title_similarity_threshold must be between 0 and 1")
        if self.time_window <= timedelta(0):
            raise ValueError("time_window must be positive")

    def execute(self, articles: Sequence[Article]) -> list[TopicCluster]:
        clusters: list[TopicCluster] = []

        for article in articles:
            matching_index = self._find_matching_cluster(article, clusters)
            if matching_index is None:
                clusters.append(
                    TopicCluster(name=article.title.strip(), articles=(article,))
                )
                continue

            cluster = clusters[matching_index]
            clusters[matching_index] = replace(
                cluster,
                articles=(*cluster.articles, article),
            )

        return clusters

    def _find_matching_cluster(
        self,
        article: Article,
        clusters: Sequence[TopicCluster],
    ) -> int | None:
        best_index: int | None = None
        best_score = 0.0

        for index, cluster in enumerate(clusters):
            if not self._is_time_near(article, cluster):
                continue
            score = max(
                title_similarity(article.title, clustered_article.title)
                for clustered_article in cluster.articles
            )
            if score >= self.title_similarity_threshold and score > best_score:
                best_index = index
                best_score = score

        return best_index

    def _is_time_near(self, article: Article, cluster: TopicCluster) -> bool:
        if article.published_at is None:
            return True

        for clustered_article in cluster.articles:
            if clustered_article.published_at is None:
                return True
            delta = abs(article.published_at - clustered_article.published_at)
            if delta <= self.time_window:
                return True

        return False


def title_similarity(left: str, right: str) -> float:
    normalized_left = _normalize_title(left)
    normalized_right = _normalize_title(right)
    if not normalized_left or not normalized_right:
        return 0.0
    if normalized_left == normalized_right:
        return 1.0

    sequence_score = SequenceMatcher(None, normalized_left, normalized_right).ratio()
    token_score = _token_jaccard(normalized_left, normalized_right)
    return max(sequence_score, token_score)


def _normalize_title(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def _token_jaccard(left: str, right: str) -> float:
    left_tokens = frozenset(_TOKEN_RE.findall(left))
    right_tokens = frozenset(_TOKEN_RE.findall(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
