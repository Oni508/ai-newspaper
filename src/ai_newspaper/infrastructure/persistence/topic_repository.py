from __future__ import annotations

import sqlite3
from datetime import datetime

from ai_newspaper.adapters.ports import TopicRepositoryPort
from ai_newspaper.domain.models import (
    Article,
    Importance,
    Topic,
    category_from_value,
)
from ai_newspaper.infrastructure.persistence.article_repository import (
    SqliteArticleRepository,
)
from ai_newspaper.infrastructure.persistence.schema import initialize_database
from ai_newspaper.infrastructure.persistence.sqlite import DatabasePath, open_connection


class SqliteTopicRepository(TopicRepositoryPort):
    def __init__(self, database_path: DatabasePath) -> None:
        self._database_path = database_path

    def save_topics(self, topics: list[Topic]) -> None:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            connection.executemany(
                """
                INSERT INTO topics (name, category, importance, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name, category) DO UPDATE SET
                    importance = excluded.importance,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (topic.name, topic.category.value, topic.importance.value)
                    for topic in topics
                ],
            )
            connection.commit()

    def list_topics(self) -> list[Topic]:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            rows = connection.execute(
                """
                SELECT name, category, importance
                FROM topics
                ORDER BY category ASC, name ASC
                """
            ).fetchall()

        return [
            Topic(
                name=str(row["name"]),
                category=category_from_value(row["category"]),
                importance=Importance(str(row["importance"])),
            )
            for row in rows
        ]

    def save_topic_articles(self, topic: Topic, articles: list[Article]) -> None:
        self.save_topics([topic])
        SqliteArticleRepository(self._database_path).save_articles(articles)

        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            topic_id = _find_topic_id(connection, topic)
            connection.executemany(
                """
                INSERT OR IGNORE INTO topic_articles (topic_id, article_url)
                VALUES (?, ?)
                """,
                [(topic_id, article.url) for article in articles],
            )
            connection.commit()

    def list_articles_for_topic(self, topic: Topic) -> list[Article]:
        with open_connection(self._database_path) as connection:
            initialize_database(connection)
            topic_id = _find_topic_id(connection, topic)
            rows = connection.execute(
                """
                SELECT
                    articles.title,
                    articles.url,
                    articles.source_name,
                    articles.category,
                    articles.published_at,
                    articles.summary
                FROM topic_articles
                INNER JOIN articles ON articles.url = topic_articles.article_url
                WHERE topic_articles.topic_id = ?
                ORDER BY COALESCE(articles.published_at, '') DESC,
                    articles.title ASC,
                    articles.url ASC
                """,
                (topic_id,),
            ).fetchall()

        return [
            Article(
                title=str(row["title"]),
                url=str(row["url"]),
                source_name=str(row["source_name"]),
                category=category_from_value(row["category"]),
                published_at=(
                    None
                    if row["published_at"] is None
                    else datetime.fromisoformat(str(row["published_at"]))
                ),
                summary=str(row["summary"]),
            )
            for row in rows
        ]


def _find_topic_id(connection: sqlite3.Connection, topic: Topic) -> int:
    row = connection.execute(
        """
        SELECT id
        FROM topics
        WHERE name = ? AND category = ?
        """,
        (topic.name, topic.category.value),
    ).fetchone()
    if row is None:
        raise ValueError(f"topic is not stored: {topic.name}")
    return int(row["id"])
