from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_newspaper.usecases.analyze_articles import AnalyzeArticles
from ai_newspaper.usecases.fetch_articles import FetchArticles
from ai_newspaper.usecases.prune_digests import PruneDigests
from ai_newspaper.usecases.render_digest import RenderDigest


@dataclass(frozen=True)
class PipelineResult:
    fetched_count: int
    analyzed_count: int
    digest_path: Path
    pruned_count: int


@dataclass(frozen=True)
class RunPipeline:
    fetch_articles: FetchArticles
    analyze_articles: AnalyzeArticles
    render_digest: RenderDigest
    prune_digests: PruneDigests

    def execute(self) -> PipelineResult:
        articles = self.fetch_articles.execute()
        analyses = self.analyze_articles.execute()
        digest_path = self.render_digest.execute()
        pruned = self.prune_digests.execute()
        return PipelineResult(
            fetched_count=len(articles),
            analyzed_count=len(analyses),
            digest_path=digest_path,
            pruned_count=len(pruned),
        )
