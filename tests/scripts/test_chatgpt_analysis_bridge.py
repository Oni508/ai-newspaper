from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from build_briefing_package import main as build_briefing_package_main
from chatgpt_analysis_bridge import (
    AnalysisValidationError,
    extract_analysis_json,
    extract_news_payload_json,
    load_schema,
    validate_analysis_payload,
    write_analysis_outputs,
)


def test_extract_analysis_json_requires_marker_and_fenced_json() -> None:
    payload = extract_analysis_json(
        """
        AI_NEWSPAPER_ANALYSIS_JSON

        ```json
        {"edition_id": "20260705-0800-jst", "topics": [{"topic_id": "t1"}]}
        ```
        """
    )

    assert payload["edition_id"] == "20260705-0800-jst"
    assert payload["topics"] == [{"topic_id": "t1"}]


def test_extract_news_payload_json_reads_issue_body_fenced_block() -> None:
    payload = extract_news_payload_json(
        """
        # ChatGPT Project briefing input

        ## news_payload.json

        ```json
        {"edition_id": "20260705-0800-jst", "articles": []}
        ```

        ## schema.json

        ```json
        {}
        ```
        """
    )

    assert payload["edition_id"] == "20260705-0800-jst"


def test_validate_analysis_payload_rejects_forbidden_policy_terms() -> None:
    payload = _valid_payload()
    payload["topics"][0]["what_happened"] = "This includes buy recommendation text."
    schema = load_schema(Path("schemas/chatgpt_analysis.schema.json"))

    with pytest.raises(AnalysisValidationError, match="policy violation"):
        validate_analysis_payload(payload, schema)


def test_write_analysis_outputs_renders_html(tmp_path: Path) -> None:
    payload = _valid_payload()
    output_dir = tmp_path / "rendered"

    analysis_path, html_path = write_analysis_outputs(
        payload,
        template_dir=Path("templates"),
        output_dir=output_dir,
        news_payload=_valid_news_payload(),
    )

    html = html_path.read_text(encoding="utf-8")
    assert analysis_path.read_text(encoding="utf-8").startswith("{")
    assert "<!doctype html>" in html
    assert "A001" in html
    assert "Example News" in html
    assert "AI chip policy update" in html
    assert "https://example.com/ai-chip-policy" in html
    assert 'href="#topic-1"' not in html


def test_build_briefing_package_creates_expected_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "ai_newspaper.sqlite3"
    _seed_database(database)
    output_root = tmp_path / "briefing_inputs"
    sources_path = tmp_path / "sources.yaml"
    sources_path.write_text(
        """
sources:
  - name: Example News
    type: rss
    url: https://example.com/rss
    enabled: true
    category: business_technology
    region: jp
    priority: 5
  - name: Global News
    type: rss
    url: https://global.example.com/rss
    enabled: true
    category: business_technology
    region: global
    priority: 1
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_briefing_package.py",
            "--database",
            str(database),
            "--schema",
            "schemas/chatgpt_analysis.schema.json",
            "--output-root",
            str(output_root),
            "--sources",
            str(sources_path),
            "--edition-id",
            "20260705-0800-jst",
        ],
    )

    assert build_briefing_package_main() == 0

    output_dir = output_root / "20260705-0800-jst"
    assert (output_dir / "prompt.md").is_file()
    assert (output_dir / "news_payload.json").is_file()
    assert (output_dir / "schema.json").is_file()
    assert (output_dir / "issue_body.md").is_file()
    payload = json.loads((output_dir / "news_payload.json").read_text())
    assert payload["articles"][0]["source_ref"] == "A001"
    assert payload["articles"][0]["source_region"] == "jp"
    assert payload["articles"][0]["source_priority"] == 5
    assert payload["sources"][0] == {
        "source_ref": "A001",
        "source_name": "Example News",
        "source_region": "jp",
        "source_priority": 5,
        "title": "AI chip policy update",
        "url": "https://example.com/ai-chip-policy",
    }


def _valid_payload() -> dict[str, object]:
    return {
        "edition_id": "20260705-0800-jst",
        "edition_label": "朝刊",
        "generated_at_jst": "2026-07-05T08:00:00+09:00",
        "topics": [
            {
                "topic_id": "topic-1",
                "category": "business_technology",
                "headline": "AI chip supply chain policy changes",
                "what_happened": "A technology company changed its supply chain plan.",
                "why_it_matters": "The change may affect competition and regulation.",
                "key_facts": ["The article discusses policy and supply chains."],
                "perspectives": [
                    {
                        "persona": "Policy reader",
                        "analysis": "The main issue is regulatory uncertainty.",
                    }
                ],
                "forecast": {
                    "enabled": True,
                    "one_week": (
                        "If regulators respond, companies may adjust messaging."
                    ),
                    "one_month": "If supply constraints persist, strategy may shift.",
                    "conditions": ["Only if the reported policy remains in force."],
                },
                "business_explainer": {
                    "enabled": True,
                    "why_notable": "The product is central to AI infrastructure.",
                    "business_impact": (
                        "It may affect margins and supply chain planning."
                    ),
                    "beginner_checks": ["Check official company statements."],
                },
                "uncertainties": ["The article does not settle long-term demand."],
                "source_refs": ["A001"],
            }
        ],
    }


def _valid_news_payload() -> dict[str, object]:
    return {
        "edition_id": "20260705-0800-jst",
        "generated_at_jst": "2026-07-05T08:00:00+09:00",
        "sources": [
            {
                "source_ref": "A001",
                "source_name": "Example News",
                "source_region": "jp",
                "source_priority": 5,
                "title": "AI chip policy update",
                "url": "https://example.com/ai-chip-policy",
            }
        ],
        "articles": [
            {
                "source_ref": "A001",
                "title": "AI chip policy update",
                "url": "https://example.com/ai-chip-policy",
                "source_name": "Example News",
                "source_region": "jp",
                "source_priority": 5,
                "category": "business_technology",
                "published_at": "2026-07-05T08:00:00",
                "summary": "Policy and semiconductor supply chain context.",
                "topic_name": "AI chip policy update",
                "topic_importance": "high",
                "importance_score": 144,
            }
        ],
    }


def _seed_database(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE articles (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_name TEXT NOT NULL,
                category TEXT NOT NULL,
                published_at TEXT,
                summary TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                importance TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, category)
            );
            CREATE TABLE topic_articles (
                topic_id INTEGER NOT NULL,
                article_url TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(topic_id, article_url)
            );
            """
        )
        connection.execute(
            """
            INSERT INTO articles (
                url,
                title,
                source_name,
                category,
                published_at,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "https://example.com/ai-chip-policy",
                "AI chip policy update",
                "Example News",
                "business_technology",
                datetime(2026, 7, 5, 8, 0).isoformat(),
                "Policy and semiconductor supply chain context.",
            ),
        )
        connection.execute(
            """
            INSERT INTO articles (
                url,
                title,
                source_name,
                category,
                published_at,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "https://global.example.com/revenue-update",
                "Revenue update",
                "Global News",
                "business_technology",
                datetime(2026, 7, 5, 9, 0).isoformat(),
                "Revenue and supply chain context.",
            ),
        )
        connection.execute(
            """
            INSERT INTO topics (name, category, importance)
            VALUES (?, ?, ?)
            """,
            ("AI chip policy update", "business_technology", "high"),
        )
        connection.execute(
            """
            INSERT INTO topic_articles (topic_id, article_url)
            VALUES (1, ?)
            """,
            ("https://example.com/ai-chip-policy",),
        )
        connection.execute(
            """
            INSERT INTO topic_articles (topic_id, article_url)
            VALUES (1, ?)
            """,
            ("https://global.example.com/revenue-update",),
        )
