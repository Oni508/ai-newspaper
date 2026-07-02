from __future__ import annotations

from pathlib import Path

from ai_newspaper.infrastructure.renderers import JinjaDigestRenderer


class JinjaHtmlRenderer(JinjaDigestRenderer):
    """Adapter-compatible name for the Jinja digest renderer."""

    def __init__(
        self,
        template_dir: Path,
        template_name: str = "digest.html.j2",
    ) -> None:
        super().__init__(template_dir, template_name)
