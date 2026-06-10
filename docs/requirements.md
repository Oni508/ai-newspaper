# Requirements

## Purpose

This project is a personal AI newspaper generator for a MacBook Air M4.
It creates a twice-daily HTML digest that helps the user understand important
news without building a real-time news application.

The tool is a local-first, low-cost personal research assistant. It should be
usable without paid APIs and should prefer local LLM integration when analysis
requires a language model.

## Product Scope

The first version is a batch tool, not a Web application.

It generates HTML newspapers at the following update windows:

- Morning edition: 08:00
- Evening edition: 18:00

The generated HTML files are stored in:

```text
data/digests/
```

Generated HTML files older than 48 hours must be deleted by the pruning
workflow.

## Target User

The target user is an individual who wants a compact, explanatory newspaper for
personal research. The system should help the user understand background,
business context, policy context, technology context, and uncertainty.

The tool must not present itself as:

- A real-time breaking news service
- An investment advisory tool
- A trading assistant
- A stock prediction system

## Supported Categories

The first version supports only:

- Politics and economy
- Business and technology
- International affairs

The first version should not prioritize:

- Entertainment
- Sports
- Gossip
- Crime details
- Individual accidents
- Flame wars
- Disaster live tracking

## Inputs

Expected inputs include:

- RSS feeds or other public, no-cost feeds
- Local configuration files for feed sources and category mapping
- Previously stored article metadata in SQLite, if available

Paid APIs must not be required for normal operation.

## Outputs

The primary output is an HTML newspaper file.

Each digest should include:

- Edition timestamp
- Supported categories
- Article summaries
- Important background context
- Business explanations for company-related news
- Conditional scenarios where forecasts are allowed
- Uncertainty and beginner-friendly next-check points

The first version does not need a Web server. Opening the generated HTML file in
a browser is sufficient.

## Business Explainer Policy

For company-related news, explain:

- Why the company or product is attracting attention
- Which business, product, or technology is involved
- Whether the news may relate to revenue, margins, competition, regulation,
  brand, or supply chain
- Whether it is a short-term or medium-to-long-term issue
- What a beginner should check next
- What remains uncertain

The system must not provide:

- Buy recommendations
- Sell recommendations
- Hold recommendations
- Target prices
- Trading timing
- Portfolio advice
- Leverage or margin trading suggestions

## Forecast Policy

Forecasts are allowed only for:

- Policy
- Corporate strategy
- Technology announcements
- International relations

Forecasts must be written as conditional scenarios. They must not be
deterministic predictions.

The system must not predict:

- Stock prices
- Buy or sell timing
- Crime outcomes
- Individual responsibility
- Disaster damage expansion without evidence

## Analyzer Requirements

The system must support at least two analyzer implementations:

- Dummy Analyzer for development and tests
- Local LLM Analyzer as the preferred real analyzer path

The Dummy Analyzer must work without network access, paid APIs, or external LLM
services.

The local LLM analyzer should be implemented behind a port so that concrete
local runtime choices, such as Ollama or another local service, do not leak into
usecase code.

## Storage Requirements

Prefer SQLite for local storage.

SQLite may store:

- Feed source metadata
- Fetched article metadata
- Article analysis results
- Digest generation history

SQLite logic must live in infrastructure or adapter code, not in domain or
usecase logic.

HTML digest files must be stored in `data/digests/`.

## Scheduling Requirements

The application must support scheduled execution at 08:00 and 18:00.

The initial implementation may provide CLI commands and documentation for
scheduling. A later task may add a launchd configuration or another
Mac-compatible scheduler setup.

## CLI Requirements

Expected commands are:

```bash
uv run ai-newspaper run
uv run ai-newspaper fetch
uv run ai-newspaper analyze
uv run ai-newspaper render
uv run ai-newspaper prune
```

The `run` command should execute the normal pipeline:

1. Fetch source articles
2. Analyze articles
3. Render HTML digest
4. Prune old generated HTML

## Development Requirements

Use:

- Nix for the development environment
- uv for Python dependency management
- Python for application code
- pytest for tests
- ruff for linting
- mypy for type checking

Expected development commands:

```bash
nix develop
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
```

## Non-Goals

The first version will not implement:

- A Web application
- Real-time push updates
- Paid API integration as a requirement
- Stock price APIs
- Stock price forecasting
- Buy, sell, or hold recommendations
- Trading timing advice
- Portfolio advice
- Disaster live tracking
- Detailed crime or accident coverage

## Open Questions

- Which RSS or public feeds should be enabled by default
- Whether scheduled execution should be implemented with launchd in the first
  implementation pass
- Which local LLM runtime should be the first real analyzer adapter
- Whether article deduplication should be rule-based only in the first version
  or assisted by a local LLM
