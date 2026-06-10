from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_newspaper.domain.models import Digest


class JinjaHtmlRenderer:
    def __init__(
        self,
        template_dir: Path,
        template_name: str = "digest.html.j2",
    ) -> None:
        self._environment = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml", "j2"]),
        )
        self._template_name = template_name

    def render(self, digest: Digest) -> str:
        template = self._environment.get_template(self._template_name)
        return template.render(digest=digest)
