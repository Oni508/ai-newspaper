from __future__ import annotations

import argparse
import json
from pathlib import Path

from chatgpt_analysis_bridge import (
    AnalysisValidationError,
    extract_analysis_json,
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
    args = parser.parse_args()

    try:
        event = json.loads(args.event_path.read_text(encoding="utf-8"))
        comment = event.get("comment", {})
        body = comment.get("body", "")
        if not isinstance(body, str):
            raise AnalysisValidationError("comment body must be a string")

        payload = extract_analysis_json(body)
        validate_analysis_payload(payload, load_schema(args.schema))
    except (AnalysisValidationError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
