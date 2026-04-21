# AGENTS.md

Build and maintain `ai_driven_dev_v2`, a runtime-agnostic orchestration system for document-first AI software delivery.

Keep this file short. Put local rules in nested `AGENTS.md` files and reusable workflows in `.agents/skills/`.

## Start here

Before editing, read:

1. `README.md`
2. `docs/product/user-stories.md`
3. `docs/backlog/roadmap.md`
4. `docs/architecture/target-architecture.md`
5. the nearest nested `AGENTS.md`

## What this repo is for

AIDD runs a staged software-delivery workflow with:

- Markdown stage inputs and outputs,
- validation before progression,
- self-repair on invalid outputs,
- user interview loops when requirements are unclear,
- adapter-based runtime integration,
- harness and eval support from day one.

## Non-negotiable rules

- Keep the core runtime-agnostic.
- Keep runtime-specific logic inside adapters.
- Stage output contracts are Markdown files, not model-authored JSON schemas.
- Validation failures must trigger repair or explicit stop; never silently continue.
- If the model has questions, surface them in the CLI and save them as documents.
- The CLI must expose raw runtime logs when the adapter can stream them.
- Behavior changes affecting orchestration, adapters, contracts, prompts, validators, harnesses, or evals must update tests and usually a scenario or grader.

## Development loop

1. Pick a user story and a local task from `docs/backlog/backlog.md`.
2. If the behavior changes, update the relevant doc or contract before code.
3. Implement the smallest vertical slice.
4. Run the narrowest useful checks locally.
5. Update docs, prompts, contracts, scenario manifests, and backlog notes before calling the change done.

## Planning rules

The planning model is:

`wave -> epic -> slice -> local task`

Use these skills when touching planning files:

- `.agents/skills/backlog-ops/`
- `.agents/skills/task-slicing/`

Never add a task to `docs/backlog/backlog.md` unless it already exists in `docs/backlog/roadmap.md`.

## Quick repo map

- `src/aidd/core/` — orchestration, stage order, workspace logic
- `src/aidd/adapters/` — runtime integration only
- `src/aidd/validators/` — document validation
- `src/aidd/harness/` — scenario loading and execution scaffolding
- `src/aidd/evals/` — graders, verdicts, and reports
- `contracts/` — durable stage and document contracts
- `prompt-packs/` — file-based stage prompts
- `harness/scenarios/live/` — live E2E manifests
- `docs/` — product, architecture, backlog, and E2E docs
- `.agents/skills/` — Codex-discoverable team skills

## Commands

Use these defaults unless a nested `AGENTS.md` says otherwise:

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy src
uv run pytest
```

Useful bootstrap commands:

```bash
uv run aidd doctor
uv run aidd init --work-item WI-001
```

## Done means

A change is done when:

- code and documents agree,
- the nearest relevant checks pass,
- impacted user stories still make sense,
- backlog and scenario docs are updated when scope changed,
- no runtime-specific shortcut leaked into the core.

## Nested instructions

This repository uses nested `AGENTS.md` files. Always prefer the nearest one for local rules.
