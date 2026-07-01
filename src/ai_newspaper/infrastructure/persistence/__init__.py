from __future__ import annotations

from ai_newspaper.infrastructure.persistence.article_repository import (
    SqliteArticleRepository,
)
from ai_newspaper.infrastructure.persistence.digest_repository import (
    SqliteDigestRepository,
)
from ai_newspaper.infrastructure.persistence.schema import initialize_database
from ai_newspaper.infrastructure.persistence.sqlite import connect, open_connection
from ai_newspaper.infrastructure.persistence.topic_repository import (
    SqliteTopicRepository,
)

__all__ = [
    "SqliteArticleRepository",
    "SqliteDigestRepository",
    "SqliteTopicRepository",
    "connect",
    "initialize_database",
    "open_connection",
]
