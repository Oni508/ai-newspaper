from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    config_dir: Path
    template_dir: Path
    database_dir: Path
    digest_dir: Path
    log_dir: Path


def default_paths() -> AppPaths:
    root = Path.cwd()
    return AppPaths(
        root=root,
        config_dir=root / "config",
        template_dir=root / "templates",
        database_dir=root / "data" / "db",
        digest_dir=root / "data" / "digests",
        log_dir=root / "data" / "logs",
    )
