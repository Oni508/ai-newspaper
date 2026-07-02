from __future__ import annotations

import os
from datetime import datetime, timedelta
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


def test_filesystem_digest_store_deletes_digest_html_by_generated_time(
    tmp_path: Path,
) -> None:
    digest_dir = tmp_path / "digests"
    store = FilesystemDigestStore(digest_dir)
    generated_at = datetime(2026, 7, 2, 8, 0)
    output_path = store.write_html(generated_at, "<html>digest</html>")

    deleted_path = store.delete_html(generated_at)

    assert deleted_path == output_path
    assert not output_path.exists()


def test_filesystem_digest_store_treats_missing_digest_html_as_deleted(
    tmp_path: Path,
) -> None:
    digest_dir = tmp_path / "digests"
    generated_at = datetime(2026, 7, 2, 8, 0)

    deleted_path = FilesystemDigestStore(digest_dir).delete_html(generated_at)

    assert deleted_path == digest_dir / "digest_2026-07-02_0800.html"


def test_filesystem_digest_store_legacy_prune_uses_html_mtime(
    tmp_path: Path,
) -> None:
    digest_dir = tmp_path / "digests"
    store = FilesystemDigestStore(digest_dir)
    old_path = store.write_html(datetime(2026, 6, 30, 8, 0), "<html>old</html>")
    recent_path = store.write_html(
        datetime(2026, 7, 2, 8, 0),
        "<html>recent</html>",
    )
    old_mtime = datetime(2026, 6, 30, 7, 59).timestamp()
    recent_mtime = datetime(2026, 7, 2, 8, 0).timestamp()
    os.utime(old_path, (old_mtime, old_mtime))
    os.utime(recent_path, (recent_mtime, recent_mtime))

    deleted = store.prune_older_than(
        datetime(2026, 7, 2, 8, 0),
        timedelta(hours=48),
    )

    assert deleted == [old_path]
    assert not old_path.exists()
    assert recent_path.exists()
