# Contributing to ai_driven_dev_v2

Thanks for your interest in contributing to AIDD.

This project is building a runtime-agnostic, document-first orchestration system for AI-driven software delivery. Contributions are welcome in code, contracts, prompt packs, docs, harness scenarios, and eval tooling.

## Before you start

Read these files first:

1. `README.md`
2. `AGENTS.md`
3. `docs/product/user-stories.md`
4. `docs/backlog/roadmap.md`
5. `docs/architecture/target-architecture.md`
6. the nearest nested `AGENTS.md` for the area you want to change

## Ways to contribute

You can help by:

- implementing roadmap tasks,
- improving architecture and contract docs,
- tightening prompt packs,
- adding validators and tests,
- adding runtime adapters,
- improving live E2E manifests,
- improving contributor experience and docs.

## Development setup

### Requirements

- Python 3.12+
- `uv`
- optional runtime CLIs for adapter work, such as Claude Code

### Local setup

```bash
uv sync --extra dev
uv run aidd --help
uv run aidd doctor
uv run pytest
```

## Planning model

This repository plans work in four levels:

`wave -> epic -> slice -> local task`

Definitions:

- **Wave** — a broad delivery phase.
- **Epic** — a coherent product or engineering theme inside a wave.
- **Slice** — the smallest meaningful outcome that should still be visible in review.
- **Local task** — one reviewable implementation step, usually one PR-sized change.

Planning files:

- `docs/backlog/roadmap.md` — canonical full roadmap
- `docs/backlog/backlog.md` — short actionable queue

## How to take a task

1. Open `docs/backlog/backlog.md`.
2. Pick the first local task marked `next`.
3. Confirm that you understand the linked user story and slice goal.
4. Read the nearest nested `AGENTS.md` files for the area you will touch.
5. Implement the smallest change that satisfies the task.
6. Update docs, contracts, or manifests when behavior changes.
7. Mark follow-up work in the roadmap/backlog if you discovered new work.

## How to create or split tasks

Create or split work when:

- a task is too large for one PR,
- a task spans more than one visible outcome,
- a task mixes architecture work with runtime-specific work,
- the verification strategy is unclear.

Rules for new planning items:

- put the work under the correct epic and slice,
- prefer splitting into a new **local task** before creating a new **slice**,
- create a new slice when the outcome is meaningfully distinct,
- include linked user stories,
- include clear exit evidence or verification commands,
- keep wording present-tense and action-oriented.

## Design rules contributors must preserve

- Keep the core runtime-agnostic.
- Put runtime-specific logic only inside adapters.
- Keep stage inputs and outputs as Markdown documents.
- Do not replace document contracts with runtime-authored JSON schemas.
- Keep user questions first-class workflow artifacts.
- Preserve native runtime log visibility.
- Treat eval and harness support as product code, not optional add-ons.

## Quality bar

Before opening a PR, run the smallest relevant checks:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

If your change affects contracts, prompts, adapters, harness behavior, or eval logic, also update the matching docs and scenario/manifests.

## Pull request checklist

A good PR should:

- reference the local task id(s),
- explain the behavior change,
- mention any updated docs/contracts/prompts,
- note any new follow-up tasks,
- keep the diff focused.

Use the PR template in `.github/pull_request_template.md`.

## Large changes

For larger changes, open an issue or draft PR first if possible.

Update architecture docs before implementation when the change alters:

- stage semantics,
- adapter protocol,
- workspace layout,
- validation/repair behavior,
- harness/eval artifacts,
- distribution or release flow.

## Contribution licensing

By submitting a contribution, you agree that your contribution will be licensed under the Apache License 2.0 for inclusion in this project, unless explicitly stated otherwise.
