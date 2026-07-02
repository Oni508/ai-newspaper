from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_newspaper.adapters.ports import (
    ArticleRepositoryPort,
    ClockPort,
    DigestRendererPort,
    DigestRepositoryPort,
    FileStoragePort,
)
from ai_newspaper.domain.models import Digest, DigestEdition


@dataclass(frozen=True)
class GenerateDigest:
    repository: ArticleRepositoryPort
    digest_repository: DigestRepositoryPort
    renderer: DigestRendererPort
    store: FileStoragePort
    clock: ClockPort

    def execute(self) -> Path:
        generated_at = self.clock.now()
        digest = Digest(
            edition=DigestEdition(
                generated_at=generated_at,
                label=_edition_label(generated_at.hour),
            ),
            articles=tuple(self.repository.list_articles()),
            analyses=tuple(self.repository.list_analyses()),
        )
        html = self.renderer.render(digest)
        output_path = self.store.write_html(generated_at, html)
        self.digest_repository.save_digest(digest)
        return output_path


def _edition_label(hour: int) -> str:
    if hour < 12:
        return "朝刊"
    if hour < 18:
        return "日中版"
    return "夕刊"
