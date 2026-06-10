from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_newspaper.domain.policies import DIGEST_RETENTION
from ai_newspaper.usecases.ports import ClockPort, DigestStorePort


@dataclass(frozen=True)
class PruneDigests:
    store: DigestStorePort
    clock: ClockPort

    def execute(self) -> list[Path]:
        return self.store.prune_older_than(self.clock.now(), DIGEST_RETENTION)
