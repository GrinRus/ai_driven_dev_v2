# AGENTS.md

Build and maintain `ai_driven_dev_v2`, a runtime-agnostic orchestration system for
document-first AI software delivery.

Keep this file short. Put local rules in nested `AGENTS.md` files and reusable workflows in `.agents/skills/`.

## Start here

Before editing, read only the context needed for the owning area:

1. `README.md`
2. `docs/product/user-stories.md`
3. the nearest nested `AGENTS.md`
4. the relevant section of `docs/architecture/target-architecture.md` or the owning contract
5. for behavior changes, the relevant roadmap slice and local task in
   `docs/backlog/roadmap.md` and `docs/backlog/backlog.md`

Use `.agents/skills/project-navigation/` when ownership is unclear. Do not load unrelated
documents or repeat instructions already supplied by a nearer `AGENTS.md`.

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
- Preserve existing behavior, routes, outputs, and evidence unless the accepted task changes
  them. Never delete or weaken required behavior merely to make a check pass.
- Behavior changes affecting orchestration, adapters, contracts, prompts, validators,
  harnesses, or evals must update tests and usually a scenario or grader.

## Agent operating policy

- For requests to explain, review, diagnose, research, or plan, inspect the relevant material
  and report the result. Do not implement changes unless the request also asks for them.
- For requests to change, build, or fix, make the smallest in-scope local change and run the
  nearest non-destructive validation without asking for routine confirmation.
- Ask a question only when an unresolved ambiguity would materially change the result and
  repository context cannot resolve it safely.
- Require explicit confirmation before external writes, destructive actions, releases,
  credential changes, or a material expansion of scope.
- Keep the current work layer explicit: research, planning, implementation, review, or external
  coordination. Do not silently cross into another layer.
- Use parallel agents only when the request or an applicable skill calls for them and the work
  splits into independent, non-overlapping streams. Assign ownership, cap concurrency, and
  synthesize one final result.

## Development loop

1. Map the request to one user story and owning area. For product behavior changes, select an
   accepted local task before code.
2. If behavior changes, update the relevant document or contract before code.
3. Implement the smallest vertical slice; keep unrelated cleanup out of the diff.
4. Run the narrowest useful checks, then broaden validation only when risk or release policy
   requires it.
5. Reconcile affected docs, prompts, contracts, scenarios, graders, and backlog notes before
   calling the change done.

## Prompt and model changes

- Keep prompts lean and outcome-oriented. State each durable instruction once; retain examples
  only when they encode a product requirement or prevent a measured regression.
- Change one prompt or model variable group at a time and compare representative traces or
  evals. Do not combine a model migration with a broad prompt rewrite.
- Keep model names, reasoning settings, and provider capabilities in runtime configuration,
  adapters, or harness profiles, never in runtime-agnostic core behavior.
- Treat model families by workload role rather than doing a global string replacement. For a
  GPT-5.6 migration, preserve the existing quality, latency, cost, endpoint, tool, and effective
  reasoning contracts before tuning.
- Do not enable Pro mode, maximum reasoning, persisted reasoning, explicit caching,
  Programmatic Tool Calling, or multi-agent execution as repository-wide defaults. Adopt an
  optional capability only for a measured need with compatibility checks and eval evidence.
- Record what changed, what stayed pinned, the validation evidence, and any remaining gap.

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
- `harness/scenarios/live/` — manual external eval manifests
- `docs/` — product, architecture, backlog, and E2E docs
- `.agents/skills/` — Codex-discoverable team skills

## Commands

Start with the narrowest relevant check. Use these full defaults for broad changes or when a
nested `AGENTS.md` requires them:

```bash
uv sync --locked --extra dev
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src scripts
uv run --extra dev pytest -q
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
- the user-visible outcome and required evidence were inspected, not merely the command exit,
- impacted user stories still make sense,
- backlog and scenario docs are updated when scope changed,
- no runtime-specific shortcut leaked into the core,
- the final report names validation performed and any unverified or blocked work.

## Nested instructions

This repository uses nested `AGENTS.md` files. Always prefer the nearest one for local rules.
