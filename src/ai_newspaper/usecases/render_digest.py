from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_newspaper.domain.models import Digest, DigestEdition
from ai_newspaper.usecases.ports import (
    ArticleRepositoryPort,
    ClockPort,
    DigestRendererPort,
    DigestStorePort,
)


@dataclass(frozen=True)
class RenderDigest:
    repository: ArticleRepositoryPort
    renderer: DigestRendererPort
    store: DigestStorePort
    clock: ClockPort

    def execute(self) -> Path:
        generated_at = self.clock.now()
        digest = Digest(
            edition=DigestEdition(generated_at=generated_at, label="stub edition"),
            articles=tuple(self.repository.list_articles()),
            analyses=tuple(self.repository.list_analyses()),
        )
        html = self.renderer.render(digest)
        return self.store.write_html(generated_at, html)
