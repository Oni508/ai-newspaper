from __future__ import annotations

from pathlib import Path

from ai_newspaper.usecases.run_pipeline import RunPipeline


class Step:
    def __init__(self, name: str, calls: list[str], result: object) -> None:
        self._name = name
        self._calls = calls
        self._result = result

    def execute(self) -> object:
        self._calls.append(self._name)
        return self._result


def test_run_pipeline_prunes_after_rendering_digest() -> None:
    calls: list[str] = []

    result = RunPipeline(
        fetch_articles=Step("fetch", calls, [object()]),
        analyze_articles=Step("analyze", calls, [object(), object()]),
        render_digest=Step("render", calls, Path("data/digests/digest.html")),
        prune_digests=Step("prune", calls, [Path("data/digests/old.html")]),
    ).execute()

    assert calls == ["fetch", "analyze", "render", "prune"]
    assert result.fetched_count == 1
    assert result.analyzed_count == 2
    assert result.digest_path == Path("data/digests/digest.html")
    assert result.pruned_count == 1
