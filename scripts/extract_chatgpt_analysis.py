from __future__ import annotations

import argparse
import json
from pathlib import Path

from chatgpt_analysis_bridge import (
    AnalysisValidationError,
    extract_analysis_json,
    extract_news_payload_json,
    load_schema,
    validate_analysis_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract and validate ChatGPT analysis JSON from a GitHub event.",
    )
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--news-payload-output", type=Path)
    args = parser.parse_args()

    try:
        event = json.loads(args.event_path.read_text(encoding="utf-8"))
        comment = event.get("comment", {})
        body = comment.get("body", "")
        if not isinstance(body, str):
            raise AnalysisValidationError("comment body must be a string")

        payload = extract_analysis_json(body)
        validate_analysis_payload(payload, load_schema(args.schema))
        news_payload: dict[str, object] | None = None
        if args.news_payload_output is not None:
            issue = event.get("issue", {})
            issue_body = issue.get("body", "")
            if not isinstance(issue_body, str):
                raise AnalysisValidationError("issue body must be a string")
            news_payload = extract_news_payload_json(issue_body)
    except (AnalysisValidationError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.news_payload_output is not None and news_payload is not None:
        args.news_payload_output.parent.mkdir(parents=True, exist_ok=True)
        args.news_payload_output.write_text(
            json.dumps(news_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
