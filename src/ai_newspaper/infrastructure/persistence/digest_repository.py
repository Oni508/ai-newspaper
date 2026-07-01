from __future__ import annotations

import json
from datetime import datetime

from ai_newspaper.adapters.ports import DigestRepositoryPort
from ai_newspaper.domain.models import Digest, DigestEdition
from ai_newspaper.infrastructure.persistence.article_repository import (
    SqliteArticleRepository,
)
from ai_newspaper.infrastructure.persistence.schema import initialize_database
from ai_newspaper.infrastructure.persistence.sqlite import DatabasePath, open_connection


class SqliteDigestRepository(DigestRepositoryPort):
    def __init__(self, database_path: DatabasePath) -> None:
        self._database_path = database_path

    def save_digest(self, digest: Digest) -> None:
        article_repository = SqliteArticleRepository(self._database_path)
        article_repository.save_articles(list(digest.articles))
        article_repository.save_analyses(list(digest.analyses))

        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            connection.execute(
                """
                INSERT INTO digests (
                    generated_at,
                    label,
                    article_urls_json,
                    analysis_article_urls_json
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(generated_at, label) DO UPDATE SET
                    article_urls_json = excluded.article_urls_json,
                    analysis_article_urls_json = excluded.analysis_article_urls_json
                """,
                (
                    digest.edition.generated_at.isoformat(),
                    digest.edition.label,
                    json.dumps([article.url for article in digest.articles]),
                    json.dumps([analysis.article_url for analysis in digest.analyses]),
                ),
            )
            connection.commit()

    def list_digests(self) -> list[Digest]:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            rows = connection.execute(
                """
                SELECT
                    generated_at,
                    label,
                    article_urls_json,
                    analysis_article_urls_json
                FROM digests
                ORDER BY generated_at DESC, label ASC
                """
            ).fetchall()

        article_repository = SqliteArticleRepository(self._database_path)
        articles_by_url = {
            article.url: article for article in article_repository.list_articles()
        }
        analyses_by_url = {
            analysis.article_url: analysis
            for analysis in article_repository.list_analyses()
        }

        digests: list[Digest] = []
        for row in rows:
            article_urls = _load_string_list(str(row["article_urls_json"]))
            analysis_urls = _load_string_list(str(row["analysis_article_urls_json"]))
            digests.append(
                Digest(
                    edition=DigestEdition(
                        generated_at=datetime.fromisoformat(str(row["generated_at"])),
                        label=str(row["label"]),
                    ),
                    articles=tuple(
                        articles_by_url[url]
                        for url in article_urls
                        if url in articles_by_url
                    ),
                    analyses=tuple(
                        analyses_by_url[url]
                        for url in analysis_urls
                        if url in analyses_by_url
                    ),
                )
            )
        return digests


def _load_string_list(payload: str) -> list[str]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("expected JSON list")
    return [str(item) for item in data]
