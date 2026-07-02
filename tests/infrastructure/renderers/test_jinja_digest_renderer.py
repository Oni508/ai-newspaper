from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_newspaper.domain.models import (
    AnalysisResult,
    Article,
    Category,
    Digest,
    DigestEdition,
)
from ai_newspaper.infrastructure.renderers import JinjaDigestRenderer


def test_jinja_digest_renderer_outputs_newspaper_sections() -> None:
    digest = Digest(
        edition=DigestEdition(
            generated_at=datetime(2026, 7, 2, 18, 0),
            label="夕刊",
        ),
        articles=(
            Article(
                title="Central bank updates policy",
                url="https://example.com/policy",
                source_name="Example News",
                category=Category.POLITICS_ECONOMY,
                summary="Source summary",
            ),
            Article(
                title="Company launches AI product",
                url="https://example.com/ai",
                source_name="Tech News",
                category=Category.BUSINESS_TECHNOLOGY,
            ),
            Article(
                title="Diplomats meet for regional talks",
                url="https://example.com/world",
                source_name="World News",
                category=Category.INTERNATIONAL,
            ),
        ),
        analyses=(
            AnalysisResult(
                article_url="https://example.com/policy",
                summary="Policy summary",
                background="Policy background",
                business_explainer="Policy business context",
                conditional_scenarios=("If policy continues, markets adapt.",),
                uncertainty="Policy details remain incomplete.",
                next_checks=("Check official minutes.",),
            ),
        ),
    )

    html = JinjaDigestRenderer(Path("templates")).render(digest)

    for heading in (
        "1面サマリー",
        "政治・経済",
        "企業・技術",
        "国際",
        "企業理解補助",
        "今後の注視点",
        "参照ソース一覧",
    ):
        assert heading in html
    assert "Central bank updates policy" in html
    assert "digest_2026-07-02_1800" not in html
