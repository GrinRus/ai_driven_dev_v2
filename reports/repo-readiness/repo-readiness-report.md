# Repository Readiness Report

## 1. Executive summary

The repository is locally healthy for deterministic development: lint, typecheck, targeted docs tests, and the full pytest suite pass. Wave 15 is no longer an unstarted readiness-recovery wave: `W15-E1-S1-T1` and `W15-E2-S1-T1` are complete and committed, while the two external evidence tasks are correctly blocked by missing non-repository prerequisites. Overall readiness level: **3/4**. Ready for the current next slice: **No active local slice remains; Wave 15 is blocked only on external live/release prerequisites**.

## 2. Audit scope and method

- Source-of-truth files used: `AGENTS.md`, `README.md`, `docs/product/user-stories.md`, `docs/backlog/backlog.md`, `docs/backlog/roadmap.md`, `docs/architecture/target-architecture.md`, `.agents/skills/live-e2e/SKILL.md`, `.agents/skills/aidd-eval/SKILL.md`, `.github/workflows/release.yml`, and `docs/release-checklist.md`.
- Repository instructions used: root `AGENTS.md`, `docs/backlog/AGENTS.md`, and `tests/AGENTS.md`.
- Commands run: `uv run ruff check .`, `uv run mypy src`, `uv run pytest tests/test_docs_consistency.py -q`, `uv run pytest`, `uv run aidd doctor`, release/live preflight env checks, `git tag --points-at HEAD`, and the Wave 12/13 marker check.
- Key constraints: no public-repository live E2E run was forced without an AIDD-compatible runtime wrapper; no release verification was forced without a release tag and publish context.

## 3. Source-of-truth inventory

| Artifact | Expected path | Found? | Role | Notes |
| --- | --- | --- | --- | --- |
| Root instructions | `AGENTS.md` | yes | Global project rules | Requires backlog-first work, Markdown contracts, adapter isolation, validation/repair, logs, and tests. |
| Product stories | `docs/product/user-stories.md` | yes | Product outcomes | Stories `US-01` through `US-10` remain the traceability baseline. |
| Active backlog | `docs/backlog/backlog.md` | yes | Local execution queue | `Next`, `Soon`, and `Parking lot` are all `none`; Wave 15 sync notes explain why. |
| Roadmap | `docs/backlog/roadmap.md` | yes | Canonical planning hierarchy | Wave 15 is `blocked`; `W15-E1-S1-T1` and `W15-E2-S1-T1` are `done`; `W15-E3-S1-T1` and `W15-E3-S2-T1` are `blocked`. |
| Target architecture | `docs/architecture/target-architecture.md` | yes | Architecture commitments | No Wave 15 changes altered runtime/core boundaries or public contracts. |
| Live runbook | `.agents/skills/live-e2e/SKILL.md` | yes | Manual live prerequisites | Requires `AIDD_EVAL_CODEX_COMMAND` or `AIDD_EVAL_OPENCODE_COMMAND`; both were unset in this environment. |
| Release workflow | `.github/workflows/release.yml` | yes | Published-channel verification | Release evidence requires a tag-triggered publish/verification path; no tag points at current `HEAD`. |
| Tests | `tests/` | yes | Deterministic verification | `575 passed in 57.65s`; ruff and mypy also pass. |

## 4. User-story readiness

Core user-story readiness is unchanged and remains strong for deterministic repository work. `US-07` and `US-09` still need external evidence before fresh live/release success can be claimed, but the missing evidence is now represented as explicit Wave 15 blockers rather than hidden gaps. See `reports/repo-readiness/user-story-traceability.md`.

## 5. Roadmap/backlog readiness

Wave 15 planning is internally consistent. `W15-E1-S1-T1` closed the lint-gate recovery, `W15-E2-S1-T1` normalized Wave 12/13 task markers, and the active queue is empty because `W15-E3-S1-T1` and `W15-E3-S2-T1` are blocked by external prerequisites. See `reports/repo-readiness/backlog-coverage.md`.

## 6. Architecture conformance findings

- **Runtime-agnostic core: operational.** No Wave 15 fix changed `src/aidd/` behavior or pushed runtime-specific logic into core.
- **Markdown-first contracts: operational.** Wave 15 touched planning/report artifacts only; no model-authored JSON contract drift was introduced.
- **Validation and self-repair model: operational.** Deterministic tests covering validators and repair continue to pass.
- **Interview loop: operational.** No Wave 15 change altered interview behavior; existing tests pass.
- **Runtime log visibility: operational.** No Wave 15 change altered adapter log behavior.
- **Harness/eval integration: operational locally, blocked externally.** Local harness/eval tests pass; manual live proof is blocked until a wrapper command is configured.
- **Distribution and development model: partially blocked.** Source checkout checks pass; release-channel proof is blocked until a release candidate tag and publish context exist.

## 7. Local developer loop findings

| Command | Result | What it proved | What it did not prove |
| --- | --- | --- | --- |
| `uv run ruff check .` | Pass | The repo is lint-clean after Wave 15 fixes. | Does not prove live/release external paths. |
| `uv run mypy src` | Pass: `Success: no issues found in 64 source files` | Source typing is clean. | Does not typecheck report Markdown. |
| `uv run pytest tests/test_docs_consistency.py -q` | Pass: `5 passed in 0.08s` | Docs consistency checks still pass. | Does not run all tests. |
| `uv run pytest` | Pass: `575 passed in 57.65s` | Deterministic test suite is green. | Does not execute public live E2E or tagged release verification. |
| Wave 12/13 marker check | Expected no matches | No Wave 12/13 local task bullets remain without `(done)`. | Does not prove the historical implementation again. |
| Live preflight | Blocked | Both required live wrapper env vars were unset. | Does not prove live scenario behavior. |
| Release preflight | Blocked | No release tag points at `HEAD`; local publish token env vars were unset. | Does not prove release channels. |

## 8. Top blockers

1. **Manual live evidence is blocked by missing wrapper command.** Evidence: `AIDD_EVAL_CODEX_COMMAND` and `AIDD_EVAL_OPENCODE_COMMAND` were unset, while `live-e2e` requires one of them for local live execution. Impact: `W15-E3-S1-T1` cannot be completed locally.
2. **Release-channel evidence is blocked by missing release candidate context.** Evidence: no tag points at `HEAD`, and no local publish credential env vars were set. Impact: `W15-E3-S2-T1` cannot be completed locally.
3. **Audit reports were stale before this pass.** Evidence: previous report text still named obsolete Wave 15 recommendations and the old ruff failure. Impact: fixed in this report regeneration.

## 9. Recommended next actions

1. `Wave 15 -> external evidence lanes -> fresh manual live evidence -> W15-E3-S1-T1`: export a valid `AIDD_EVAL_CODEX_COMMAND` or `AIDD_EVAL_OPENCODE_COMMAND`, confirm provider auth, then run one maintained live scenario.
2. `Wave 15 -> external evidence lanes -> release-channel evidence capture -> W15-E3-S2-T1`: create a release candidate tag that matches `pyproject.toml`, run the release workflow, and preserve PyPI, `uv tool`, and GHCR verification logs.
3. If those external prerequisites will not be provided soon, open the next implementation wave via the queue-restoration policy with a new roadmap-backed local task.

## 10. Final verdict

- Ready for current next slice: **No active local slice remains**; Wave 15 is blocked only by external evidence prerequisites.
- Ready for next wave: **Ready to open the next local wave if maintainers accept the external blockers as deferred**.
- Ready for external contributors: **Yes for deterministic local development**, because lint, mypy, and pytest pass; **not ready to claim fresh live/release evidence**.
- Ready for live E2E: **Not until an AIDD-compatible runtime wrapper env var is configured**.
