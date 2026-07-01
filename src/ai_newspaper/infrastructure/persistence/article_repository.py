from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from ai_newspaper.adapters.ports import ArticleRepositoryPort
from ai_newspaper.domain.models import AnalysisResult, Article, Category
from ai_newspaper.infrastructure.persistence.schema import initialize_database
from ai_newspaper.infrastructure.persistence.sqlite import DatabasePath, open_connection


class SqliteArticleRepository(ArticleRepositoryPort):
    def __init__(self, database_path: DatabasePath) -> None:
        self._database_path = database_path

    def save_articles(self, articles: list[Article]) -> None:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            connection.executemany(
                """
                INSERT INTO articles (
                    url,
                    title,
                    source_name,
                    category,
                    published_at,
                    summary,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    source_name = excluded.source_name,
                    category = excluded.category,
                    published_at = excluded.published_at,
                    summary = excluded.summary,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (
                        article.url,
                        article.title,
                        article.source_name,
                        article.category.value,
                        _datetime_to_text(article.published_at),
                        article.summary,
                    )
                    for article in articles
                ],
            )
            connection.commit()

    def list_articles(self) -> list[Article]:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            rows = connection.execute(
                """
                SELECT title, url, source_name, category, published_at, summary
                FROM articles
                ORDER BY COALESCE(published_at, '') DESC, title ASC, url ASC
                """
            ).fetchall()

        return [_article_from_row(row) for row in rows]

    def save_analyses(self, analyses: list[AnalysisResult]) -> None:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            connection.executemany(
                """
                INSERT INTO analyses (
                    article_url,
                    summary,
                    background,
                    business_explainer,
                    conditional_scenarios_json,
                    uncertainty,
                    next_checks_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(article_url) DO UPDATE SET
                    summary = excluded.summary,
                    background = excluded.background,
                    business_explainer = excluded.business_explainer,
                    conditional_scenarios_json = excluded.conditional_scenarios_json,
                    uncertainty = excluded.uncertainty,
                    next_checks_json = excluded.next_checks_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (
                        analysis.article_url,
                        analysis.summary,
                        analysis.background,
                        analysis.business_explainer,
                        json.dumps(list(analysis.conditional_scenarios)),
                        analysis.uncertainty,
                        json.dumps(list(analysis.next_checks)),
                    )
                    for analysis in analyses
                ],
            )
            connection.commit()

    def list_analyses(self) -> list[AnalysisResult]:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            rows = connection.execute(
                """
                SELECT
                    article_url,
                    summary,
                    background,
                    business_explainer,
                    conditional_scenarios_json,
                    uncertainty,
                    next_checks_json
                FROM analyses
                ORDER BY article_url ASC
                """
            ).fetchall()

        return [_analysis_from_row(row) for row in rows]


def _article_from_row(row: sqlite3.Row) -> Article:
    return Article(
        title=str(row["title"]),
        url=str(row["url"]),
        source_name=str(row["source_name"]),
        category=Category(str(row["category"])),
        published_at=_text_to_datetime(row["published_at"]),
        summary=str(row["summary"]),
    )


def _analysis_from_row(row: sqlite3.Row) -> AnalysisResult:
    return AnalysisResult(
        article_url=str(row["article_url"]),
        summary=str(row["summary"]),
        background=str(row["background"]),
        business_explainer=str(row["business_explainer"]),
        conditional_scenarios=_load_string_tuple(
            str(row["conditional_scenarios_json"])
        ),
        uncertainty=str(row["uncertainty"]),
        next_checks=_load_string_tuple(str(row["next_checks_json"])),
    )


def _datetime_to_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _text_to_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(str(value))


def _load_string_tuple(payload: str) -> tuple[str, ...]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("expected JSON list")
    return tuple(str(item) for item in data)
