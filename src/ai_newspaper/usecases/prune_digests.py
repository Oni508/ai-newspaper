from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_newspaper.adapters.ports import ClockPort, DigestRepositoryPort, FileStoragePort
from ai_newspaper.domain.policies import DIGEST_RETENTION, RetentionPolicy


@dataclass(frozen=True)
class PruneDigests:
    store: FileStoragePort
    digest_repository: DigestRepositoryPort
    clock: ClockPort

    def execute(self) -> list[Path]:
        now = self.clock.now()
        expires_before = RetentionPolicy(DIGEST_RETENTION).expires_before(now)
        deleted_paths: list[Path] = []
        for digest in self.digest_repository.list_digests():
            if digest.edition.generated_at >= expires_before:
                continue
            deleted_path = self.store.delete_html(digest.edition.generated_at)
            self.digest_repository.delete_digest(
                digest.edition.generated_at,
                digest.edition.label,
            )
            deleted_paths.append(deleted_path)

        for deleted_path in self.store.prune_older_than(now, DIGEST_RETENTION):
            if deleted_path not in deleted_paths:
                deleted_paths.append(deleted_path)
        return deleted_paths
