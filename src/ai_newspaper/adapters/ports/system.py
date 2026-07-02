from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol


class ClockPort(Protocol):
    def now(self) -> datetime:
        """Return the current local time."""


class FileStoragePort(Protocol):
    def write_html(self, generated_at: datetime, html: str) -> Path:
        """Write generated HTML and return the path."""

    def delete_html(self, generated_at: datetime) -> Path:
        """Delete generated HTML for a digest edition and return its path."""

    def prune_older_than(self, now: datetime, retention: timedelta) -> list[Path]:
        """Delete old generated HTML files and return deleted paths."""
