from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_newspaper.domain.models import AnalysisResult, Article, Category, Digest
from ai_newspaper.usecases.generate_digest import GenerateDigest


class FakeRepository:
    def list_articles(self) -> list[Article]:
        return [
            Article(
                title="Policy update",
                url="https://example.com/policy",
                source_name="Example News",
                category=Category.POLITICS_ECONOMY,
            )
        ]

    def list_analyses(self) -> list[AnalysisResult]:
        return [
            AnalysisResult(
                article_url="https://example.com/policy",
                summary="Policy summary",
                background="Policy background",
                business_explainer="Business context",
            )
        ]

    def save_articles(self, articles: list[Article]) -> None:
        raise NotImplementedError

    def save_analyses(self, analyses: list[AnalysisResult]) -> None:
        raise NotImplementedError


class FakeRenderer:
    def __init__(self) -> None:
        self.digest: Digest | None = None

    def render(self, digest: Digest) -> str:
        self.digest = digest
        return "<html>digest</html>"


class FakeStore:
    def __init__(self) -> None:
        self.generated_at: datetime | None = None
        self.html = ""

    def write_html(self, generated_at: datetime, html: str) -> Path:
        self.generated_at = generated_at
        self.html = html
        return Path("data/digests/digest_2026-07-02_0800.html")


class FakeDigestRepository:
    def __init__(self) -> None:
        self.saved_digest: Digest | None = None

    def save_digest(self, digest: Digest) -> None:
        self.saved_digest = digest

    def list_digests(self) -> list[Digest]:
        raise NotImplementedError

    def delete_digest(self, generated_at: datetime, label: str) -> None:
        raise NotImplementedError


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 2, 8, 0)


def test_generate_digest_renders_and_stores_current_digest() -> None:
    renderer = FakeRenderer()
    store = FakeStore()
    digest_repository = FakeDigestRepository()

    output_path = GenerateDigest(
        repository=FakeRepository(),
        digest_repository=digest_repository,
        renderer=renderer,
        store=store,
        clock=FakeClock(),
    ).execute()

    assert output_path == Path("data/digests/digest_2026-07-02_0800.html")
    assert store.generated_at == datetime(2026, 7, 2, 8, 0)
    assert store.html == "<html>digest</html>"
    assert renderer.digest is not None
    assert renderer.digest.edition.label == "朝刊"
    assert len(renderer.digest.articles) == 1
    assert len(renderer.digest.analyses) == 1
    assert digest_repository.saved_digest == renderer.digest
