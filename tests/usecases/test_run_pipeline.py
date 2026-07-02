from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_newspaper.domain.models import (
    AnalysisResult,
    Article,
    Category,
    ClassifiedTopic,
    Digest,
    Importance,
    Topic,
    TopicCluster,
)
from ai_newspaper.usecases.run_pipeline import RunDigestPipelineUseCase


class FakeSource:
    def __init__(self, calls: list[str], articles: list[Article]) -> None:
        self._calls = calls
        self._articles = articles

    def fetch(self) -> list[Article]:
        self._calls.append("fetch")
        return self._articles


class FakeArticleRepository:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls
        self._articles: list[Article] = []
        self._analyses: list[AnalysisResult] = []

    def save_articles(self, articles: list[Article]) -> None:
        self._calls.append("save_articles")
        self._articles = list(articles)

    def list_articles(self) -> list[Article]:
        return list(self._articles)

    def save_analyses(self, analyses: list[AnalysisResult]) -> None:
        self._calls.append("save_analyses")
        self._analyses = list(analyses)

    def list_analyses(self) -> list[AnalysisResult]:
        return list(self._analyses)


class FakeTopicRepository:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls
        self.topics: list[Topic] = []

    def save_topics(self, topics: list[Topic]) -> None:
        self._calls.append("save_topics")
        self.topics = list(topics)

    def list_topics(self) -> list[Topic]:
        return list(self.topics)


class FakeNormalizer:
    def __init__(self, calls: list[str], articles: list[Article]) -> None:
        self._calls = calls
        self._articles = articles

    def execute(self, articles: list[Article]) -> list[Article]:
        self._calls.append("normalize")
        assert articles
        return self._articles


class FakeClusterTopics:
    def __init__(self, calls: list[str], clusters: list[TopicCluster]) -> None:
        self._calls = calls
        self._clusters = clusters

    def execute(self, articles: list[Article]) -> list[TopicCluster]:
        self._calls.append("cluster_topics")
        assert articles
        return self._clusters


class FakeClassifyTopics:
    def __init__(
        self,
        calls: list[str],
        classified_topics: list[ClassifiedTopic],
    ) -> None:
        self._calls = calls
        self._classified_topics = classified_topics

    def execute(self, clusters: list[TopicCluster]) -> list[ClassifiedTopic]:
        self._calls.append("classify_topics")
        assert clusters
        return self._classified_topics


class FakeAnalyzer:
    def __init__(self, calls: list[str], analyses: list[AnalysisResult]) -> None:
        self._calls = calls
        self._analyses = analyses

    def analyze(self, articles: list[Article]) -> list[AnalysisResult]:
        self._calls.append("analyze")
        assert articles
        return self._analyses


class FakeDigestRepository:
    def __init__(self) -> None:
        self.saved_digest: Digest | None = None

    def save_digest(self, digest: Digest) -> None:
        self.saved_digest = digest

    def list_digests(self) -> list[Digest]:
        return []

    def delete_digest(self, generated_at: datetime, label: str) -> None:
        raise AssertionError("no digest metadata should be deleted in this test")


class FakeRenderer:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    def render(self, digest: Digest) -> str:
        self._calls.append("render")
        assert digest.articles
        assert digest.analyses
        return "<html>digest</html>"


class FakeStore:
    def __init__(self, calls: list[str], pruned: list[Path]) -> None:
        self._calls = calls
        self._pruned = pruned

    def write_html(self, generated_at: datetime, html: str) -> Path:
        assert html == "<html>digest</html>"
        return Path("data/digests/digest_2026-07-02_0800.html")

    def delete_html(self, generated_at: datetime) -> Path:
        raise AssertionError("no digest HTML should be deleted by metadata")

    def prune_older_than(self, now: datetime, retention: object) -> list[Path]:
        self._calls.append("prune")
        return self._pruned


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 2, 8, 0)


def test_run_digest_pipeline_executes_full_batch_pipeline() -> None:
    calls: list[str] = []
    fetched_article = _article(
        title=" Company launches AI product ",
        url="HTTPS://Example.com/news/?utm_source=rss",
    )
    normalized_article = _article(
        title="Company launches AI product",
        url="https://example.com/news",
    )
    topic = Topic(
        name="Company launches AI product",
        category=Category.BUSINESS_TECHNOLOGY,
        importance=Importance.MEDIUM,
    )
    cluster = TopicCluster(name=topic.name, articles=(normalized_article,))
    analysis = AnalysisResult(
        article_url=normalized_article.url,
        summary="summary",
        background="background",
        business_explainer="business",
    )
    article_repository = FakeArticleRepository(calls)
    topic_repository = FakeTopicRepository(calls)
    digest_repository = FakeDigestRepository()

    result = RunDigestPipelineUseCase(
        source=FakeSource(calls, [fetched_article]),
        article_repository=article_repository,
        topic_repository=topic_repository,
        analyzer=FakeAnalyzer(calls, [analysis]),
        digest_repository=digest_repository,
        renderer=FakeRenderer(calls),
        store=FakeStore(calls, [Path("data/digests/old.html")]),
        clock=FakeClock(),
        normalizer=FakeNormalizer(calls, [normalized_article]),
        cluster_topics=FakeClusterTopics(calls, [cluster]),
        classify_topics=FakeClassifyTopics(
            calls,
            [
                ClassifiedTopic(
                    topic=topic,
                    articles=(normalized_article,),
                    forecast_allowed=False,
                    business_explainer_required=True,
                )
            ],
        ),
    ).execute()

    assert calls == [
        "fetch",
        "normalize",
        "save_articles",
        "cluster_topics",
        "classify_topics",
        "save_topics",
        "analyze",
        "save_analyses",
        "render",
        "prune",
    ]
    assert article_repository.list_articles() == [normalized_article]
    assert topic_repository.list_topics() == [topic]
    assert digest_repository.saved_digest is not None
    assert result.fetched_count == 1
    assert result.saved_count == 1
    assert result.normalized_count == 1
    assert result.topic_count == 1
    assert result.classified_topic_count == 1
    assert result.analyzed_count == 1
    assert result.digest_path == Path("data/digests/digest_2026-07-02_0800.html")
    assert result.pruned_count == 1


def _article(*, title: str, url: str) -> Article:
    return Article(
        title=title,
        url=url,
        source_name="Example News",
        category=Category.BUSINESS_TECHNOLOGY,
    )
