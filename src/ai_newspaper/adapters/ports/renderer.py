from __future__ import annotations

from typing import Protocol

from ai_newspaper.domain.models import Digest


class DigestRendererPort(Protocol):
    def render(self, digest: Digest) -> str:
        """Render digest HTML."""
