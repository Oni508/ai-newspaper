from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_newspaper.domain.models import (
    AnalysisResult,
    Article,
    Category,
    Digest,
    DigestEdition,
    DigestReference,
    category_from_value,
)
from ai_newspaper.infrastructure.renderers.jinja_digest_renderer import (
    JinjaDigestRenderer,
)

MARKER = "AI_NEWSPAPER_ANALYSIS_JSON"
FENCED_BLOCK_RE = re.compile(
    r"```(?:json)?\s*(?P<body>.*?)\s*```",
    re.DOTALL | re.IGNORECASE,
)
FORBIDDEN_OUTPUT_TERMS = (
    "buy recommendation",
    "sell recommendation",
    "hold recommendation",
    "target price",
    "trading timing",
    "stock price prediction",
    "portfolio advice",
    "買い推奨",
    "売り推奨",
    "保有推奨",
    "目標株価",
    "売買タイミング",
    "株価予測",
    "ポートフォリオ助言",
)


class AnalysisValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SourceReference:
    source_ref: str
    source_name: str
    title: str
    url: str
    category: str
    published_at: str | None
    summary: str


def extract_analysis_json(comment_body: str) -> dict[str, Any]:
    if MARKER not in comment_body:
        raise AnalysisValidationError(f"comment must contain {MARKER}")

    marked_body = comment_body[comment_body.index(MARKER) :]
    matches = list(FENCED_BLOCK_RE.finditer(marked_body))
    if not matches:
        raise AnalysisValidationError("comment must contain a fenced JSON block")

    errors: list[str] = []
    for match in matches:
        try:
            payload = json.loads(match.group("body"))
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(payload, dict):
            errors.append("top-level JSON value must be an object")
            continue
        return payload

    raise AnalysisValidationError("; ".join(errors) or "valid JSON block not found")


def extract_news_payload_json(issue_body: str) -> dict[str, Any]:
    marker = "## news_payload.json"
    if marker not in issue_body:
        raise AnalysisValidationError("issue body must contain ## news_payload.json")

    section = issue_body[issue_body.index(marker) :]
    next_section = re.search(r"\n##\s+", section[len(marker) :])
    if next_section:
        section = section[: len(marker) + next_section.start()]

    errors: list[str] = []
    for match in FENCED_BLOCK_RE.finditer(section):
        try:
            payload = json.loads(match.group("body"))
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(payload, dict):
            errors.append("top-level news_payload JSON value must be an object")
            continue
        return payload

    raise AnalysisValidationError(
        "; ".join(errors) or "news_payload.json fenced JSON block not found"
    )


def load_schema(schema_path: Path) -> dict[str, Any]:
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AnalysisValidationError("schema must be a JSON object")
    return data


def validate_analysis_payload(
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    errors: list[str] = []
    _validate_against_schema(payload, schema, "$", errors)
    _validate_policy(payload, errors)
    if errors:
        raise AnalysisValidationError("\n".join(errors))


def render_analysis_html(
    payload: dict[str, Any],
    *,
    template_dir: Path,
    news_payload: dict[str, Any] | None = None,
) -> str:
    renderer = JinjaDigestRenderer(template_dir)
    return renderer.render(_payload_to_digest(payload, news_payload=news_payload))


def write_analysis_outputs(
    payload: dict[str, Any],
    *,
    template_dir: Path,
    output_dir: Path,
    news_payload: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = output_dir / "analysis_output.json"
    html_path = output_dir / "digest.html"
    analysis_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    html_path.write_text(
        render_analysis_html(
            payload,
            template_dir=template_dir,
            news_payload=news_payload,
        ),
        encoding="utf-8",
    )
    return analysis_path, html_path


def _validate_against_schema(
    value: Any,
    schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if isinstance(key, str) and key not in value:
                    errors.append(f"{path}: missing required key {key}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            if schema.get("additionalProperties") is False:
                allowed = set(properties)
                for key in value:
                    if key not in allowed:
                        errors.append(f"{path}: unexpected key {key}")
            for key, child_schema in properties.items():
                if key in value and isinstance(child_schema, dict):
                    _validate_against_schema(
                        value[key],
                        child_schema,
                        f"{path}.{key}",
                        errors,
                    )
        return

    if schema_type == "array":
        if not isinstance(value, list):
            errors.append(f"{path}: expected array")
            return
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: expected at least {min_items} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_against_schema(item, item_schema, f"{path}[{index}]", errors)
        return

    if schema_type == "string":
        if not isinstance(value, str):
            errors.append(f"{path}: expected string")
            return
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value.strip()) < min_length:
            errors.append(f"{path}: expected minLength {min_length}")
        return

    if schema_type == "boolean" and not isinstance(value, bool):
        errors.append(f"{path}: expected boolean")


def _validate_policy(payload: dict[str, Any], errors: list[str]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).casefold()
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term.casefold() in serialized:
            errors.append(f"policy violation: forbidden output term {term!r}")


def _payload_to_digest(
    payload: dict[str, Any],
    *,
    news_payload: dict[str, Any] | None = None,
) -> Digest:
    generated_at = _parse_generated_at(payload.get("generated_at_jst"))
    edition_label = str(payload.get("edition_label") or _edition_label(generated_at))
    topics = payload.get("topics", [])
    source_lookup = _source_reference_lookup(news_payload)
    articles: list[Article] = []
    analyses: list[AnalysisResult] = []
    references: list[DigestReference] = []
    seen_reference_keys: set[str] = set()

    if isinstance(topics, list):
        for index, topic in enumerate(topics, start=1):
            if not isinstance(topic, dict):
                continue
            topic_id = str(topic.get("topic_id") or f"topic-{index}")
            source_refs = _string_list(topic.get("source_refs"))
            resolved_sources = tuple(
                source
                for ref in source_refs
                if (source := source_lookup.get(ref)) is not None
            )
            primary_source = resolved_sources[0] if resolved_sources else None
            article_url = (
                primary_source.url
                if primary_source is not None
                else _first_url(source_refs) or f"#{topic_id}"
            )
            article = Article(
                title=(
                    str(topic.get("headline") or "").strip()
                    or (primary_source.title if primary_source is not None else "")
                    or topic_id
                ),
                url=article_url,
                source_name=(
                    _source_name(resolved_sources, source_refs)
                ),
                category=_category(topic.get("category")),
                published_at=_parse_optional_datetime(
                    primary_source.published_at if primary_source else None
                ),
                summary=str(topic.get("what_happened") or ""),
                source_ref=", ".join(source_refs),
            )
            articles.append(article)
            analyses.append(_analysis_for_topic(article.url, topic))
            for source in resolved_sources:
                if source.source_ref in seen_reference_keys:
                    continue
                seen_reference_keys.add(source.source_ref)
                references.append(
                    DigestReference(
                        source_ref=source.source_ref,
                        source_name=source.source_name,
                        title=source.title,
                        url=source.url,
                    )
                )
            for ref in source_refs:
                if ref in seen_reference_keys or ref in source_lookup:
                    continue
                seen_reference_keys.add(ref)
                references.append(
                    DigestReference(
                        source_ref=ref,
                        source_name="Unresolved source",
                        title=ref,
                        url=_first_url((ref,)) or "",
                    )
                )

    return Digest(
        edition=DigestEdition(generated_at=generated_at, label=edition_label),
        articles=tuple(articles),
        analyses=tuple(analyses),
        references=tuple(references),
    )


def _source_reference_lookup(
    news_payload: dict[str, Any] | None,
) -> dict[str, SourceReference]:
    if news_payload is None:
        return {}
    source_items = news_payload.get("sources")
    articles = news_payload.get("articles")
    if isinstance(source_items, list):
        items = source_items
    elif isinstance(articles, list):
        items = articles
    else:
        return {}

    references: dict[str, SourceReference] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        source_ref = str(item.get("source_ref") or "").strip()
        url = str(item.get("url") or "").strip()
        if not source_ref or not url:
            continue
        published_at = item.get("published_at")
        references[source_ref] = SourceReference(
            source_ref=source_ref,
            source_name=str(item.get("source_name") or "").strip(),
            title=str(item.get("title") or "").strip(),
            url=url,
            category=str(item.get("category") or "").strip(),
            published_at=(
                str(published_at).strip()
                if published_at is not None and str(published_at).strip()
                else None
            ),
            summary=str(item.get("summary") or "").strip(),
        )
    return references


def _source_name(
    resolved_sources: tuple[SourceReference, ...],
    source_refs: tuple[str, ...],
) -> str:
    if resolved_sources:
        names = tuple(
            source.source_name or source.source_ref for source in resolved_sources
        )
        return ", ".join(dict.fromkeys(names))
    if source_refs:
        return ", ".join(source_refs)
    return "ChatGPT analysis"


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def _analysis_for_topic(article_url: str, topic: dict[str, Any]) -> AnalysisResult:
    forecast = topic.get("forecast")
    business = topic.get("business_explainer")
    perspectives = topic.get("perspectives")

    return AnalysisResult(
        article_url=article_url,
        summary=_join_paragraphs(
            str(topic.get("what_happened") or ""),
            str(topic.get("why_it_matters") or ""),
            *_string_list(topic.get("key_facts")),
        ),
        background=_format_perspectives(perspectives),
        business_explainer=_format_business_explainer(business),
        conditional_scenarios=_format_forecast(forecast),
        uncertainty="\n".join(_string_list(topic.get("uncertainties"))),
        next_checks=_business_beginner_checks(business),
    )


def _parse_generated_at(value: object) -> datetime:
    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.now(UTC).replace(tzinfo=None)
        if parsed.tzinfo is not None:
            return parsed.replace(tzinfo=None)
        return parsed
    return datetime.now(UTC).replace(tzinfo=None)


def _edition_label(generated_at: datetime) -> str:
    if generated_at.hour < 12:
        return "朝刊"
    if generated_at.hour < 18:
        return "日中版"
    return "夕刊"


def _category(value: object) -> Category:
    try:
        return category_from_value(value)
    except ValueError:
        return Category.INTERNATIONAL


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _first_url(values: tuple[str, ...]) -> str | None:
    for value in values:
        if value.startswith(("http://", "https://")):
            return value
    return None


def _join_paragraphs(*values: str) -> str:
    return "\n\n".join(value.strip() for value in values if value.strip())


def _format_perspectives(value: object) -> str:
    if not isinstance(value, list):
        return ""
    paragraphs: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        persona = str(item.get("persona") or "").strip()
        analysis = str(item.get("analysis") or "").strip()
        if persona and analysis:
            paragraphs.append(f"{persona}: {analysis}")
        elif analysis:
            paragraphs.append(analysis)
    return "\n\n".join(paragraphs)


def _format_business_explainer(value: object) -> str:
    if not isinstance(value, dict) or value.get("enabled") is not True:
        return ""
    return _join_paragraphs(
        str(value.get("why_notable") or ""),
        str(value.get("business_impact") or ""),
    )


def _format_forecast(value: object) -> tuple[str, ...]:
    if not isinstance(value, dict) or value.get("enabled") is not True:
        return ()
    scenarios = [
        str(value.get("one_week") or "").strip(),
        str(value.get("one_month") or "").strip(),
    ]
    scenarios.extend(_string_list(value.get("conditions")))
    return tuple(scenario for scenario in scenarios if scenario)


def _business_beginner_checks(value: object) -> tuple[str, ...]:
    if not isinstance(value, dict) or value.get("enabled") is not True:
        return ()
    return _string_list(value.get("beginner_checks"))
