from __future__ import annotations

import argparse
from collections.abc import Sequence

from ai_newspaper.adapters.analyzers.dummy import DummyAnalyzer
from ai_newspaper.adapters.renderers.jinja_html_renderer import JinjaHtmlRenderer
from ai_newspaper.adapters.sources.rss_feed_source import RssFeedSource
from ai_newspaper.adapters.storage.filesystem_digest_store import FilesystemDigestStore
from ai_newspaper.infrastructure.clock import SystemClock
from ai_newspaper.infrastructure.config import default_paths
from ai_newspaper.infrastructure.persistence import (
    SqliteArticleRepository,
    SqliteDigestRepository,
    SqliteTopicRepository,
)
from ai_newspaper.usecases.analyze_articles import AnalyzeArticles
from ai_newspaper.usecases.fetch_articles import FetchArticles
from ai_newspaper.usecases.prune_digests import PruneDigests
from ai_newspaper.usecases.render_digest import RenderDigest
from ai_newspaper.usecases.run_pipeline import RunDigestPipelineUseCase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-newspaper",
        description="Generate a local-first personal AI newspaper.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("run", "fetch", "analyze", "render", "prune"):
        subparsers.add_parser(command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    app = _build_app()

    if args.command == "fetch":
        articles = app.fetch_articles.execute()
        print(f"Fetched {len(articles)} articles.")
        return 0
    if args.command == "analyze":
        analyses = app.analyze_articles.execute()
        print(f"Analyzed {len(analyses)} articles.")
        return 0
    if args.command == "render":
        digest_path = app.render_digest.execute()
        print(f"Rendered digest: {digest_path}")
        return 0
    if args.command == "prune":
        deleted = app.prune_digests.execute()
        print(f"Pruned {len(deleted)} digest files.")
        return 0
    if args.command == "run":
        result = app.run_pipeline.execute()
        print(
            "Pipeline completed: "
            f"fetched={result.fetched_count}, "
            f"saved={result.saved_count}, "
            f"normalized={result.normalized_count}, "
            f"topics={result.topic_count}, "
            f"classified={result.classified_topic_count}, "
            f"analyzed={result.analyzed_count}, "
            f"digest={result.digest_path}, "
            f"pruned={result.pruned_count}"
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


class _Application:
    def __init__(self) -> None:
        paths = default_paths()
        repository = SqliteArticleRepository(
            paths.database_dir / "ai_newspaper.sqlite3"
        )
        topic_repository = SqliteTopicRepository(
            paths.database_dir / "ai_newspaper.sqlite3"
        )
        digest_repository = SqliteDigestRepository(
            paths.database_dir / "ai_newspaper.sqlite3"
        )
        source = RssFeedSource()
        analyzer = DummyAnalyzer()
        renderer = JinjaHtmlRenderer(paths.template_dir)
        store = FilesystemDigestStore(paths.digest_dir)
        clock = SystemClock()

        self.fetch_articles = FetchArticles(source=source, repository=repository)
        self.analyze_articles = AnalyzeArticles(
            repository=repository,
            analyzer=analyzer,
        )
        self.render_digest = RenderDigest(
            repository=repository,
            digest_repository=digest_repository,
            renderer=renderer,
            store=store,
            clock=clock,
        )
        self.prune_digests = PruneDigests(
            store=store,
            digest_repository=digest_repository,
            clock=clock,
        )
        self.run_pipeline = RunDigestPipelineUseCase(
            source=source,
            article_repository=repository,
            topic_repository=topic_repository,
            analyzer=analyzer,
            digest_repository=digest_repository,
            renderer=renderer,
            store=store,
            clock=clock,
        )


def _build_app() -> _Application:
    return _Application()


if __name__ == "__main__":
    raise SystemExit(main())
