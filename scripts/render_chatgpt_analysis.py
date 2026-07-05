from __future__ import annotations

import argparse
import json
from pathlib import Path

from chatgpt_analysis_bridge import (
    AnalysisValidationError,
    load_schema,
    validate_analysis_payload,
    write_analysis_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render validated ChatGPT analysis JSON to an HTML digest.",
    )
    parser.add_argument("--analysis-json", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--template-dir", type=Path, default=Path("templates"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    try:
        payload = json.loads(args.analysis_json.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise AnalysisValidationError("analysis JSON must be an object")
        validate_analysis_payload(payload, load_schema(args.schema))
        analysis_path, html_path = write_analysis_outputs(
            payload,
            template_dir=args.template_dir,
            output_dir=args.output_dir,
        )
    except (AnalysisValidationError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(f"analysis_output={analysis_path}")
    print(f"html_digest={html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
