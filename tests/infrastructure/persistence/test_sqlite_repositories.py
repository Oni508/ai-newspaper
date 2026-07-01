from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from ai_newspaper.domain.models import (
    AnalysisResult,
    Article,
    Category,
    Digest,
    DigestEdition,
    Importance,
    Topic,
)
from ai_newspaper.infrastructure.persistence import (
    SqliteArticleRepository,
    SqliteDigestRepository,
    SqliteTopicRepository,
    connect,
    initialize_database,
)


def test_initialize_database_creates_expected_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "news.db"

    with connect(database_path) as connection:
        initialize_database(connection)
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    table_names = {str(row["name"]) for row in rows}
    assert {
        "articles",
        "topics",
        "topic_articles",
        "analyses",
        "digests",
    }.issubset(table_names)


def test_article_repository_persists_articles_and_analyses(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "news.db"
    repository = SqliteArticleRepository(database_path)
    article = _article()
    analysis = _analysis(article.url)

    repository.save_articles([article])
    repository.save_analyses([analysis])

    assert repository.list_articles() == [article]
    assert repository.list_analyses() == [analysis]


def test_topic_repository_persists_topics_and_topic_article_links(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "news.db"
    repository = SqliteTopicRepository(database_path)
    topic = Topic(
        name="AI semiconductor policy",
        category=Category.BUSINESS_TECHNOLOGY,
        importance=Importance.HIGH,
    )
    article = _article()

    repository.save_topic_articles(topic, [article])

    assert repository.list_topics() == [topic]
    assert repository.list_articles_for_topic(topic) == [article]


def test_digest_repository_persists_digest_metadata_and_references(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "news.db"
    repository = SqliteDigestRepository(database_path)
    article = _article()
    analysis = _analysis(article.url)
    digest = Digest(
        edition=DigestEdition(
            generated_at=datetime(2026, 7, 1, 18, 0),
            label="evening",
        ),
        articles=(article,),
        analyses=(analysis,),
    )

    repository.save_digest(digest)

    assert repository.list_digests() == [digest]


def test_usecases_do_not_import_sqlite() -> None:
    for path in Path("src/ai_newspaper/usecases").glob("*.py"):
        assert "sqlite" not in path.read_text()


def test_repositories_use_a_temporary_database(tmp_path: Path) -> None:
    database_path = tmp_path / "news.db"
    repository = SqliteArticleRepository(database_path)

    repository.save_articles([_article()])

    with sqlite3.connect(database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    assert count == 1
    assert database_path.parent == tmp_path


def _article() -> Article:
    return Article(
        title="Company announces AI product",
        url="https://example.com/ai-product",
        source_name="Example News",
        category=Category.BUSINESS_TECHNOLOGY,
        published_at=datetime(2026, 7, 1, 8, 0),
        summary="Product announcement summary",
    )


def _analysis(article_url: str) -> AnalysisResult:
    return AnalysisResult(
        article_url=article_url,
        summary="The company announced a new AI product.",
        background="The product is part of a broader platform strategy.",
        business_explainer="Revenue impact remains uncertain.",
        conditional_scenarios=("If adoption grows, competition may increase.",),
        uncertainty="Pricing details are not public.",
        next_checks=("Check product availability.",),
    )
