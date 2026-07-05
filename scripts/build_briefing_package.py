from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
DEFAULT_DATABASE = Path("data/db/ai_newspaper.sqlite3")
DEFAULT_SCHEMA = Path("schemas/chatgpt_analysis.schema.json")
DEFAULT_OUTPUT_ROOT = Path("artifacts/briefing_inputs")
MAX_ARTICLES = 15
IMPORTANCE_WEIGHT = {
    "critical": 100,
    "high": 80,
    "medium": 55,
    "low": 30,
}
KEYWORD_WEIGHTS = {
    "policy": 8,
    "election": 8,
    "regulation": 8,
    "central bank": 8,
    "inflation": 7,
    "tariff": 7,
    "sanctions": 7,
    "ai": 7,
    "semiconductor": 7,
    "chip": 7,
    "security": 7,
    "diplomacy": 7,
    "supply chain": 6,
    "earnings": 5,
    "revenue": 5,
}


@dataclass(frozen=True)
class BriefingArticle:
    source_ref: str
    title: str
    url: str
    source_name: str
    category: str
    published_at: str | None
    summary: str
    topic_name: str | None
    topic_importance: str | None
    importance_score: int


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build ChatGPT Project briefing inputs from SQLite articles.",
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--edition-id")
    parser.add_argument("--limit", type=int, default=MAX_ARTICLES)
    args = parser.parse_args()

    generated_at = datetime.now(JST)
    edition_id = args.edition_id or _edition_id(generated_at)
    output_dir = args.output_root / edition_id

    articles = _load_ranked_articles(args.database, limit=args.limit)
    if not articles:
        parser.error(
            f"no articles found in {args.database}; "
            "run `uv run ai-newspaper fetch` first"
        )

    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    payload = _build_news_payload(
        edition_id=edition_id,
        generated_at=generated_at,
        articles=articles,
    )
    prompt = _build_prompt(edition_id)
    issue_body = _build_issue_body(
        edition_id=edition_id,
        prompt=prompt,
        payload=payload,
        schema=schema,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    (output_dir / "news_payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "issue_body.md").write_text(issue_body, encoding="utf-8")

    print(f"edition_id={edition_id}")
    print(f"output_dir={output_dir}")
    return 0


def _load_ranked_articles(database: Path, *, limit: int) -> list[BriefingArticle]:
    if not database.exists():
        return []

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                articles.title,
                articles.url,
                articles.source_name,
                articles.category,
                articles.published_at,
                articles.summary,
                topics.name AS topic_name,
                topics.importance AS topic_importance
            FROM articles
            LEFT JOIN topic_articles
                ON topic_articles.article_url = articles.url
            LEFT JOIN topics
                ON topics.id = topic_articles.topic_id
            ORDER BY
                COALESCE(articles.published_at, articles.created_at) DESC,
                articles.title ASC,
                articles.url ASC
            """
        ).fetchall()

    deduped: dict[str, sqlite3.Row] = {}
    for row in rows:
        url = str(row["url"])
        current = deduped.get(url)
        if current is None or _topic_weight(row) > _topic_weight(current):
            deduped[url] = row

    ranked = sorted(
        deduped.values(),
        key=lambda row: (
            _importance_score(row),
            str(row["published_at"] or ""),
            str(row["title"]),
        ),
        reverse=True,
    )
    return [
        _briefing_article(index=index, row=row)
        for index, row in enumerate(ranked[: max(limit, 1)], start=1)
    ]


def _briefing_article(*, index: int, row: sqlite3.Row) -> BriefingArticle:
    return BriefingArticle(
        source_ref=f"A{index:03d}",
        title=str(row["title"]),
        url=str(row["url"]),
        source_name=str(row["source_name"]),
        category=str(row["category"]),
        published_at=(
            None if row["published_at"] is None else str(row["published_at"])
        ),
        summary=str(row["summary"]),
        topic_name=(
            None if row["topic_name"] is None else str(row["topic_name"])
        ),
        topic_importance=(
            None if row["topic_importance"] is None else str(row["topic_importance"])
        ),
        importance_score=_importance_score(row),
    )


def _importance_score(row: sqlite3.Row) -> int:
    score = _topic_weight(row)
    text = " ".join(
        (
            str(row["title"]),
            str(row["summary"]),
            str(row["source_name"]),
            str(row["category"]),
            str(row["topic_name"] or ""),
        )
    ).casefold()
    for keyword, weight in KEYWORD_WEIGHTS.items():
        if _contains_keyword(text, keyword):
            score += weight
    if str(row["category"]) == "business_technology":
        score += 4
    return score


def _topic_weight(row: sqlite3.Row) -> int:
    return IMPORTANCE_WEIGHT.get(str(row["topic_importance"] or "medium"), 55)


def _contains_keyword(text: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in text
    return (
        re.search(rf"(?<![0-9a-z]){re.escape(keyword)}(?![0-9a-z])", text)
        is not None
    )


def _build_news_payload(
    *,
    edition_id: str,
    generated_at: datetime,
    articles: list[BriefingArticle],
) -> dict[str, object]:
    return {
        "edition_id": edition_id,
        "generated_at_jst": generated_at.isoformat(timespec="seconds"),
        "selection_policy": {
            "max_articles": MAX_ARTICLES,
            "basis": (
                "SQLite articles ranked by stored topic importance when available, "
                "with deterministic keyword fallback after fetch-only runs."
            ),
        },
        "articles": [
            {
                "source_ref": article.source_ref,
                "title": article.title,
                "url": article.url,
                "source_name": article.source_name,
                "category": article.category,
                "published_at": article.published_at,
                "summary": article.summary,
                "topic_name": article.topic_name,
                "topic_importance": article.topic_importance,
                "importance_score": article.importance_score,
            }
            for article in articles
        ],
        "sources": [
            {
                "source_ref": article.source_ref,
                "source_name": article.source_name,
                "title": article.title,
                "url": article.url,
            }
            for article in articles
        ],
    }


def _build_prompt(edition_id: str) -> str:
    return f"""# AI Newspaper ChatGPT Analysis Request

You are preparing analysis for the personal AI Newspaper project.

Repository context:

- The ChatGPT Project chat must include GitHub repository `Oni508/ai-newspaper`.
- Do not use Deep Research.
- Use only these inputs: this `prompt.md`, `news_payload.json`, and `schema.json`.
- Return JSON only. Do not include Markdown, commentary, or code fences.
- The JSON must follow `schema.json`.
- Use `source_ref` values from `news_payload.json` in `source_refs`.

Edition:

- `edition_id`: `{edition_id}`

Policy constraints:

- Do not output stock price forecasts.
- Do not output buy, sell, or hold recommendations.
- Do not output target prices.
- Do not output trading timing.
- Do not output portfolio, leverage, or margin trading advice.
- Forecasts are allowed only as conditional scenarios about policy, corporate
  strategy, technology announcements, or international relations.
- Business explainers may discuss revenue, margins, competition, regulation,
  brand, and supply chain, but must not become investment advice.

Task:

1. Read `news_payload.json`.
2. Select the most important topics from the provided articles.
3. Produce concise explanatory analysis for a beginner-friendly personal newspaper.
4. Preserve uncertainty and cite article references with `source_refs`.
5. Return only a JSON object that conforms to `schema.json`.
"""


def _build_issue_body(
    *,
    edition_id: str,
    prompt: str,
    payload: dict[str, object],
    schema: dict[str, object],
) -> str:
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2)
    schema_text = json.dumps(schema, ensure_ascii=False, indent=2)
    return f"""# ChatGPT Project briefing input

Edition: `{edition_id}`

Use a ChatGPT Project chat that includes the GitHub repository `Oni508/ai-newspaper`.
Do not use Deep Research.

Paste the following `prompt.md` into ChatGPT, and use the included
`news_payload.json` and `schema.json` as the only analysis inputs.

## prompt.md

```markdown
{prompt.rstrip()}
```

## news_payload.json

```json
{payload_text}
```

## schema.json

```json
{schema_text}
```

## Expected Issue comment format

After ChatGPT returns JSON, paste it into a comment on this Issue in this form:

````markdown
AI_NEWSPAPER_ANALYSIS_JSON

```json
{{}}
```
````
"""


def _edition_id(generated_at: datetime) -> str:
    if generated_at.hour < 12:
        edition = "0800"
    elif generated_at.hour < 18:
        edition = "1200"
    else:
        edition = "1800"
    return f"{generated_at:%Y%m%d}-{edition}-jst"


if __name__ == "__main__":
    raise SystemExit(main())
