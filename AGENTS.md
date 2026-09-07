# AGENTS.md

Build and maintain `ai_driven_dev_v2`, a runtime-agnostic orchestration system for
document-first AI software delivery.

Keep this file short. Use nested `AGENTS.md` only for distinct local constraints and
`.agents/skills/` for reusable workflows; do not copy the same rules into every leaf directory.

## Start here

Before editing, read only the context needed for the owning area:

1. `README.md`
2. `docs/product/user-stories.md`
3. every applicable `AGENTS.md` along each touched path, from the repository root to its directory
4. the relevant section of `docs/architecture/target-architecture.md` or the owning contract
5. for behavior changes, the relevant roadmap slice and local task in
   `docs/backlog/roadmap.md` and `docs/backlog/backlog.md`

Rules accumulate from root to leaf. A nearer file overrides a parent only for a direct conflict
in its own scope; it does not replace unrelated parent rules. Apply this separately to every
touched area, including tests and docs. Do not reload instructions already present in context.

Use `.agents/skills/project-navigation/` when ownership is unclear. The ownership and nearest-check
matrix is in `docs/agent-development.md`. Read targeted roadmap sections, not the entire history.

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
- External writes, destructive actions, releases, credential changes, or a material expansion
  of scope require explicit authorization. Authorization already given for the same action
  remains valid; do not ask for routine confirmation again.
- Keep the current work layer explicit: research, planning, implementation, review, or external
  coordination. Do not silently cross into another layer.
- Use parallel agents for independent, non-overlapping streams when they improve the work.
  Assign ownership, cap concurrency, avoid concurrent edits to the same files, and synthesize
  one final result.

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
- Treat model families by workload role rather than doing a global string replacement. Preserve
  quality, latency, cost, endpoint, tool, and effective reasoning contracts before tuning.
- Keep optional provider capabilities and multi-agent execution opt-in. Change defaults only
  for a measured need with compatibility checks and eval evidence; keep provider-specific
  migration details in configuration, profiles, adapters, or the accepted local task.
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
- `src/aidd/application/` — composition of core services, validation, and publication
- `src/aidd/cli/` and its `static/` directory — CLI, local operator HTTP surface, and packaged UI
- `src/aidd/adapters/` — runtime integration only
- `src/aidd/runtime_logs/` — retained raw-log and normalized-event models
- `src/aidd/validators/` — document validation
- `src/aidd/harness/`, `src/aidd/evals/` — scenario execution, graders, verdicts, and reports
- `contracts/`, `prompt-packs/` — durable Markdown contracts and file-based stage prompts
- `harness/scenarios/live/` — manual external eval manifests
- `docs/` — product, architecture, backlog, and E2E docs
- `.agents/skills/` — Codex-discoverable team skills
- `tests/`, `tests/frontend/`, `browser_tests/` — Python, Node DOM, and browser verification
- `scripts/`, `.github/workflows/`, `Makefile` — local checks, CI, packaging, and release tooling

## Commands

Start with the narrowest check in `docs/agent-development.md`. For broad changes:

```bash
uv sync --locked --extra dev
make check
```

`make check` runs instruction checks, Python lint/types/tests, JavaScript syntax, and Node DOM
tests. Browser journeys are a separate `make test-browser` target and require Playwright Chromium.
No provider credentials are needed for these local checks. Report an unavailable prerequisite
instead of treating an unrun check as passed.

## Done means

A change is done when:

- code and documents agree,
- the nearest relevant checks pass,
- the user-visible outcome and required evidence were inspected, not merely the command exit,
- impacted user stories still make sense,
- backlog and scenario docs are updated when scope changed,
- no runtime-specific shortcut leaked into the core,
- the final report names validation performed and any unverified or blocked work.
