from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection

from ai_newspaper.infrastructure.persistence.schema import initialize_database
from ai_newspaper.infrastructure.persistence.sqlite import (
    connect as _connect,
)
from ai_newspaper.infrastructure.persistence.sqlite import (
    open_connection,
)


def connect(database_path: Path) -> Connection:
    return _connect(database_path)


__all__ = ["connect", "initialize_database", "open_connection"]
