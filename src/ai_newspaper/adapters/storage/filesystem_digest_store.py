from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path


class FilesystemDigestStore:
    def __init__(self, digest_dir: Path) -> None:
        self._digest_dir = digest_dir

    def write_html(self, generated_at: datetime, html: str) -> Path:
        self._digest_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._digest_dir / f"digest_{generated_at:%Y-%m-%d_%H%M}.html"
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def prune_older_than(self, now: datetime, retention: timedelta) -> list[Path]:
        if not self._digest_dir.exists():
            return []

        deleted: list[Path] = []
        threshold = now.timestamp() - retention.total_seconds()
        for path in self._digest_dir.glob("*.html"):
            if path.stat().st_mtime < threshold:
                path.unlink()
                deleted.append(path)
        return deleted
