from __future__ import annotations

from datetime import datetime, timedelta

from ai_newspaper.domain.models import Article, Category, TopicCluster
from ai_newspaper.usecases.classify_topics import ClassifyTopicsUseCase
from ai_newspaper.usecases.cluster_topics import ClusterTopicsUseCase
from ai_newspaper.usecases.normalize_articles import (
    NormalizeArticlesUseCase,
    normalize_article_url,
)


def test_normalize_articles_removes_duplicate_urls() -> None:
    first = _article(
        title=" Company announces AI product ",
        url="HTTPS://Example.com/news/ai-product/?utm_source=rss&id=10#comments",
        category=Category.BUSINESS_TECHNOLOGY,
    )
    duplicate = _article(
        title="Duplicate",
        url="https://example.com/news/ai-product?id=10",
        category=Category.BUSINESS_TECHNOLOGY,
    )

    articles = NormalizeArticlesUseCase().execute([first, duplicate])

    assert articles == [
        _article(
            title="Company announces AI product",
            url="https://example.com/news/ai-product?id=10",
            category=Category.BUSINESS_TECHNOLOGY,
        )
    ]


def test_normalize_article_url_drops_default_port_and_tracking_query() -> None:
    assert (
        normalize_article_url("https://EXAMPLE.com:443/a/?b=2&utm_campaign=x&a=1#top")
        == "https://example.com/a?a=1&b=2"
    )


def test_cluster_topics_groups_similar_titles_near_in_time() -> None:
    published_at = datetime(2026, 7, 2, 8, 0)
    articles = [
        _article(
            title="Company unveils AI chip strategy",
            url="https://example.com/1",
            category=Category.BUSINESS_TECHNOLOGY,
            published_at=published_at,
        ),
        _article(
            title="Company unveils new AI chip strategy",
            url="https://example.com/2",
            category=Category.BUSINESS_TECHNOLOGY,
            published_at=published_at + timedelta(hours=2),
        ),
    ]

    clusters = ClusterTopicsUseCase().execute(articles)

    assert len(clusters) == 1
    assert [article.url for article in clusters[0].articles] == [
        "https://example.com/1",
        "https://example.com/2",
    ]


def test_cluster_topics_splits_similar_titles_when_time_is_far() -> None:
    articles = [
        _article(
            title="Central bank updates policy",
            url="https://example.com/1",
            category=Category.POLITICS_ECONOMY,
            published_at=datetime(2026, 7, 1, 8, 0),
        ),
        _article(
            title="Central bank updates policy",
            url="https://example.com/2",
            category=Category.POLITICS_ECONOMY,
            published_at=datetime(2026, 7, 3, 9, 0),
        ),
    ]

    clusters = ClusterTopicsUseCase().execute(articles)

    assert len(clusters) == 2


def test_classify_topics_covers_supported_categories() -> None:
    classified = ClassifyTopicsUseCase().execute(
        [
            TopicCluster(
                name="Central bank policy update",
                articles=(
                    _article(
                        title="Central bank policy update",
                        url="https://example.com/policy",
                        category=Category.POLITICS_ECONOMY,
                    ),
                ),
            ),
            TopicCluster(
                name="Company launches cloud AI product",
                articles=(
                    _article(
                        title="Company launches cloud AI product",
                        url="https://example.com/business",
                        category=Category.BUSINESS_TECHNOLOGY,
                    ),
                ),
            ),
            TopicCluster(
                name="Japan and United States discuss sanctions",
                articles=(
                    _article(
                        title="Japan and United States discuss sanctions",
                        url="https://example.com/world",
                        category=Category.INTERNATIONAL,
                    ),
                ),
            ),
        ]
    )

    assert [topic.topic.category for topic in classified] == [
        Category.POLITICS_ECONOMY,
        Category.BUSINESS_TECHNOLOGY,
        Category.INTERNATIONAL,
    ]


def test_classify_topics_marks_forecast_allowed_and_forbidden_cases() -> None:
    classified = ClassifyTopicsUseCase().execute(
        [
            TopicCluster(
                name="Government policy may affect chip regulation",
                articles=(
                    _article(
                        title="Government policy may affect chip regulation",
                        url="https://example.com/policy",
                        category=Category.POLITICS_ECONOMY,
                    ),
                ),
            ),
            TopicCluster(
                name="Analysts discuss stock price target price",
                articles=(
                    _article(
                        title="Analysts discuss stock price target price",
                        url="https://example.com/stock",
                        category=Category.BUSINESS_TECHNOLOGY,
                    ),
                ),
            ),
        ]
    )

    assert classified[0].forecast_allowed
    assert not classified[1].forecast_allowed


def test_classify_topics_marks_business_explainer_targets() -> None:
    classified = ClassifyTopicsUseCase().execute(
        [
            TopicCluster(
                name="Company launches supply chain software product",
                articles=(
                    _article(
                        title="Company launches supply chain software product",
                        url="https://example.com/company",
                        category=Category.BUSINESS_TECHNOLOGY,
                    ),
                ),
            ),
            TopicCluster(
                name="Central bank policy update",
                articles=(
                    _article(
                        title="Central bank policy update",
                        url="https://example.com/policy",
                        category=Category.POLITICS_ECONOMY,
                    ),
                ),
            ),
        ]
    )

    assert classified[0].business_explainer_required
    assert not classified[1].business_explainer_required


def _article(
    *,
    title: str,
    url: str,
    category: Category,
    published_at: datetime | None = None,
) -> Article:
    return Article(
        title=title,
        url=url,
        source_name="Example News",
        category=category,
        published_at=published_at,
        summary="",
    )
