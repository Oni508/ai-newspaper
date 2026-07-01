from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_newspaper.adapters.ports import ClockPort, FileStoragePort
from ai_newspaper.domain.policies import DIGEST_RETENTION


@dataclass(frozen=True)
class PruneDigests:
    store: FileStoragePort
    clock: ClockPort

    def execute(self) -> list[Path]:
        return self.store.prune_older_than(self.clock.now(), DIGEST_RETENTION)
