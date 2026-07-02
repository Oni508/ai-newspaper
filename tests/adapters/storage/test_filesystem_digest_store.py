from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_newspaper.adapters.storage.filesystem_digest_store import FilesystemDigestStore


def test_filesystem_digest_store_uses_required_digest_filename(
    tmp_path: Path,
) -> None:
    digest_dir = tmp_path / "digests"
    output_path = FilesystemDigestStore(digest_dir).write_html(
        datetime(2026, 7, 2, 18, 0),
        "<html>digest</html>",
    )

    assert output_path == digest_dir / "digest_2026-07-02_1800.html"
    assert output_path.read_text(encoding="utf-8") == "<html>digest</html>"
