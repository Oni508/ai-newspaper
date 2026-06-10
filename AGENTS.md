# AGENTS.md

## Project

This repository is for a personal AI newspaper generator.

The system generates an HTML newspaper twice a day, at 08:00 and 18:00.
It is not a real-time news app.
It is not an investment advisory tool.
It is a local-first, low-cost personal research assistant.

## Mandatory Workflow

Before starting any task, always create a section named `plan`.

The `plan` must include:

1. Goal of the task
2. Files to inspect
3. Files to create or modify
4. Step-by-step implementation plan
5. Validation method
6. Risks or open questions

After presenting the `plan`, wait for user approval.
Do not edit files, create files, delete files, or run commands before approval.

## Core Requirements

- Use Nix for the development environment.
- Use uv for Python dependency management.
- Use Python for the application.
- Follow Lightweight Clean Architecture.
- Prefer SQLite for local storage.
- Generate HTML output.
- Store generated digests in `data/digests/`.
- Delete generated HTML files older than 48 hours.
- Run as a batch tool, not as a Web application.
- Support scheduled execution at 08:00 and 18:00.
- Avoid paid API requirements.
- Prefer local LLM integration.
- Provide a Dummy Analyzer for development and tests.

## Categories

The first version only supports:

- Politics and economy
- Business and technology
- International affairs

Do not prioritize:

- Entertainment
- Sports
- Gossip
- Crime details
- Individual accidents
- Flame wars
- Disaster live tracking

## Forecast Policy

Forecasts are allowed only for:

- Policy
- Corporate strategy
- Technology announcements
- International relations

Forecasts must be conditional scenarios.
Do not produce deterministic predictions.

Do not predict:

- Stock prices
- Buy or sell timing
- Crime outcomes
- Individual responsibility
- Disaster damage expansion without evidence

## Business Explainer Policy

For company-related news, explain:

- Why the company or product is attracting attention
- Which business, product, or technology is involved
- Whether the news may relate to revenue, margins, competition, regulation, brand, or supply chain
- Whether it is a short-term or medium-to-long-term issue
- What a beginner should check next
- What remains uncertain

Do not provide:

- Buy recommendations
- Sell recommendations
- Hold recommendations
- Target prices
- Trading timing
- Portfolio advice
- Leverage or margin trading suggestions

## Architecture Rules

Follow this dependency direction:

- entrypoints -> usecases -> domain
- infrastructure -> adapters -> domain
- usecases -> adapter ports -> domain

Do not let usecases directly import infrastructure implementations.
Do not put external I/O inside domain.
Do not put SQLite logic inside usecases.
Do not put HTML rendering logic inside domain.
Do not call an LLM directly from a usecase implementation.
Use ports and adapters.

## Initial Stack

- Nix
- uv
- Python
- SQLite
- Jinja2
- PyYAML
- feedparser
- pytest
- ruff
- mypy

## Expected Commands

Prefer these commands:

```bash
nix develop
uv sync
uv run ai-newspaper run
uv run ai-newspaper fetch
uv run ai-newspaper analyze
uv run ai-newspaper render
uv run ai-newspaper prune
uv run pytest
uv run ruff check .
uv run mypy src
