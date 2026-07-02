# Architecture

## Overview

This project is a Python batch application that generates a personal HTML
newspaper twice a day. It follows Lightweight Clean Architecture so that core
business rules stay independent from feed parsing, SQLite, HTML rendering, and
local LLM runtime details.

The first implementation should stay small and testable. The Dummy Analyzer is
part of the architecture, not a temporary hack, because it enables development
and tests without network access or paid APIs.

## Dependency Rule

Allowed dependency direction:

```text
entrypoints -> usecases -> domain
infrastructure -> adapters -> domain
usecases -> adapter ports -> domain
```

Rules:

- Domain code must not perform external I/O.
- Domain code must not import infrastructure, adapters, or entrypoints.
- Usecases must not import concrete infrastructure implementations.
- SQLite logic must not live in usecases.
- HTML rendering logic must not live in domain.
- LLM calls must not be made directly from usecase implementations.
- Concrete tools such as feedparser, Jinja2, SQLite, and local LLM clients must
  be hidden behind adapters.

## Proposed Directory Layout

```text
src/ai_newspaper/
  domain/
    models.py
    policies.py
  usecases/
    fetch_articles.py
    analyze_articles.py
    render_digest.py
    prune_digests.py
    run_pipeline.py
  adapters/
    ports/
    analyzers/
      dummy.py
      local_llm.py
    repositories/
      sqlite_article_repository.py
    renderers/
      jinja_html_renderer.py
    sources/
      rss_feed_source.py
    storage/
      filesystem_digest_store.py
  infrastructure/
    persistence/
      sqlite.py
      schema.py
      article_repository.py
      topic_repository.py
      digest_repository.py
    config.py
    clock.py
  entrypoints/
    cli.py
templates/
  digest.html.j2
config/
  sources.yaml
data/
  digests/
tests/
```

This layout may be adjusted during implementation, but the dependency rule must
remain stable.

## Domain Layer

The domain layer contains business concepts and pure policies.

Possible domain objects:

- `Article`
- `ArticleSource`
- `Category`
- `AnalysisResult`
- `Digest`
- `DigestEdition`

Possible domain policies:

- Supported category filtering
- Forecast safety rules
- Investment-advice exclusion rules
- Business explainer requirements
- Digest retention duration of 48 hours

Domain objects should be plain Python objects or dataclasses. They should avoid
framework-specific behavior.

## Usecase Layer

Usecases coordinate application behavior through ports.

Initial usecases:

- `FetchArticles`
- `NormalizeArticlesUseCase`
- `ClusterTopicsUseCase`
- `ClassifyTopicsUseCase`
- `AnalyzeArticles`
- `RenderDigest`
- `PruneDigests`
- `RunPipeline`

Usecases should express workflow decisions but not concrete I/O.

Example responsibilities:

- Fetch article metadata through an article fetcher port
- Normalize article URLs and remove duplicate fetched articles
- Cluster articles by title similarity and publication-time proximity without a
  vector database
- Classify discovered topics into `politics_economy`,
  `business_technology`, or `international`, including forecast eligibility and
  business-explainer eligibility flags
- Save or load articles through repository ports
- Analyze articles through a news analyzer port
- Render HTML through a renderer port
- Store generated HTML through a file storage port
- Delete old HTML through a file storage port

## Ports

Adapter ports define interfaces for usecases and concrete adapters.

Expected ports:

- `ArticleFetcherPort`
- `ArticleRepositoryPort`
- `TopicRepositoryPort`
- `DigestRepositoryPort`
- `NewsAnalyzerPort`
- `DigestRendererPort`
- `ClockPort`
- `FileStoragePort`

The news analyzer port must support both Dummy Analyzer and local LLM analyzer
implementations.

## Adapters

Adapters implement ports.

Initial adapters:

- RSS feed source using feedparser
- SQLite article repository
- Dummy Analyzer
- Local LLM Analyzer
- Jinja2 HTML renderer
- Filesystem digest store
- System clock adapter
- YAML config adapter

Adapters may import external libraries and infrastructure helpers.

## Infrastructure Layer

Infrastructure contains low-level setup and implementation details.

Examples:

- SQLite connection creation and migrations
- YAML config loading
- Filesystem path configuration
- Local clock implementation
- Local LLM client setup

Infrastructure must not contain business policy. It should support adapters
rather than become the center of the application.

## Entrypoints

The first entrypoint is a CLI.

Expected commands:

```bash
uv run ai-newspaper run
uv run ai-newspaper fetch
uv run ai-newspaper analyze
uv run ai-newspaper render
uv run ai-newspaper prune
```

Command responsibilities:

- `fetch`: fetch and store candidate articles
- `analyze`: analyze stored candidate articles
- `render`: render the current edition to HTML
- `prune`: delete generated HTML files and digest metadata older than 48 hours
- `run`: execute fetch, analyze, render, and prune in order

The CLI should assemble concrete adapters and pass them into usecases.

## Analyzer Design

The analyzer is a port because analysis can be performed by different
implementations.

### Dummy Analyzer

The Dummy Analyzer must:

- Work offline
- Avoid paid APIs
- Produce deterministic output for tests
- Exercise the full fetch-analyze-render pipeline
- Respect the no-investment-advice policy in its generated text

### Local LLM Analyzer

The Local LLM Analyzer should:

- Be the preferred real analyzer path
- Be optional during development
- Stay behind `NewsAnalyzerPort`
- Avoid leaking local runtime details into usecases
- Support policy prompts that prohibit stock predictions and investment advice

Concrete local runtime selection is intentionally deferred.

## HTML Rendering

HTML rendering belongs in an adapter, not the domain layer.

The renderer should use Jinja2 and a template such as:

```text
templates/digest.html.j2
```

The rendered file should be written under:

```text
data/digests/
```

Suggested filename format:

```text
YYYY-MM-DD_HHMM.html
```

For example:

```text
2026-06-10_0800.html
2026-06-10_1800.html
```

## SQLite Storage

SQLite is preferred for local storage.

The repository adapter should own SQL details. Usecases should call repository
ports and should not know table names or SQL statements.

Initial tables:

- `articles`
- `topics`
- `topic_articles`
- `analyses`
- `digests`

Repository implementations live under `infrastructure/persistence/` and
implement adapter ports without exposing SQL details to usecases.

## Pruning

The prune workflow deletes generated HTML files older than 48 hours from
`data/digests/` and deletes the matching rows from the `digests` table.
It does not delete `articles`, `topics`, or `analyses` in the first version.

The retention rule is a business policy, but filesystem deletion is an adapter
responsibility.

Recommended split:

- Domain or usecase decides the cutoff duration
- Digest repository lists and deletes matching digest metadata
- Digest store adapter deletes matching files

## Scheduling

The application must support execution at:

- 08:00
- 18:00

The application itself should remain a batch CLI. Scheduling can be handled by a
Mac-compatible scheduler such as launchd, cron, or another external runner.

The first implementation should not require a long-running daemon or Web
server.

## Development Environment

Use Nix and uv together:

```bash
nix develop
uv sync
```

Python dependencies should be declared in `pyproject.toml` and locked with uv.

Expected quality checks:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

## Testing Strategy

Initial tests should cover:

- Domain policy behavior
- Dummy Analyzer output shape
- Usecase orchestration with fake ports
- HTML renderer smoke test
- Pruning behavior for files older than 48 hours
- CLI command wiring where practical

Tests should avoid network access by default.

## Security and Policy Constraints

The application must not provide:

- Stock price predictions
- Buy, sell, or hold recommendations
- Target prices
- Trading timing advice
- Portfolio advice
- Leverage or margin trading suggestions

Company-related explanations should stay educational and contextual.
