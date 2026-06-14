# Beta Readiness Source Audit

Date: 2026-06-11

## Purpose

This audit checks whether the beta-readiness release preparation can rely on the current
source-of-truth documents before changing release claims or process docs.

Reviewed sources:

- `README.md`
- `docs/product/user-stories.md`
- `docs/architecture/target-architecture.md`
- CLI command registration and package metadata
- CI, security, and release workflows
- maintained live scenario matrix and operator docs

## Findings

### README

- The source development package version matches the package state: `0.1.0a11.dev0`.
- The latest accepted published prerelease evidence is `0.1.0a10`.
- The source checkout may move to a later `.dev0` version after publication; README
  installation guidance stays pinned to the latest accepted package release.
- The documented public CLI commands match the registered command surface:
  `doctor`, `init`, `ui`, `stage`, `eval`, and `run`.
- The removed eval-run product command is not documented as a current product command.
- The README correctly states that live E2E is manual local operator audit evidence, not
  CI/CD, not a release workflow, not GitHub Actions, and not a release gate.
- The README correctly states that Docker/GHCR is outside the alpha release contract.

Required change: none after this release-prep slice; keep beta-readiness wording as a
preparation gate, not as a claim that AIDD is production-ready or ready for unattended
automation.

### User Stories

- `US-01` through `US-12` still describe product scope rather than implementation detail.
- The implemented runtime IDs, stage flow, Markdown contracts, validation/repair behavior,
  runtime logs, harness/eval artifacts, operator UI, project-set support, and install
  channels are consistent with the success signals.
- No new product scope is introduced by beta readiness hardening; it tightens release
  discipline and evidence boundaries.

Required change: no user-story rewrite is needed for this release-prep slice.

### Target Architecture

- The core/adapters boundary still matches the code layout: runtime-specific launch,
  streaming, and provider behavior stay in adapters.
- Stage IO remains Markdown-first; contracts and prompt packs are packaged resources.
- Validation still gates progression and failures route to repair or explicit stop.
- Runtime logs and eval artifacts are preserved as product evidence.
- The operator UI remains a surface over the same `.aidd/` workflow state, not a separate
  workflow engine.

Required change: no architecture rewrite is needed for this release-prep slice.

### Local Operator Flow

- A source-installed local-project smoke was run against a disposable copy of
  `harness/fixtures/minimal-python`.
- The smoke covered `aidd doctor`, `aidd init`, bounded `aidd run` from `idea` to `plan`,
  `aidd run show`, `aidd run logs`, `aidd run artifacts`, and `aidd stage questions`.
- The fixture runtime command is intentionally workspace-relative from `.aidd/` to the
  target project root: `python ../aidd_fixture_runtime.py`.

Required change: add scenario-loader coverage for the workspace-relative fixture runtime
command so future smoke refactors do not break source-installed local runs.

### CI/CD And Manual Live Boundary

- GitHub Actions workflows are deterministic and do not run live E2E.
- Release workflow publishes and verifies Python package installability only.
- Manual live E2E remains isolated to the local
  `uv run python -m aidd.harness.live_e2e_black_box` operator path; there is no GitHub
  Actions live E2E workflow.
- On 2026-05-24, `aidd eval doctor` reported execution readiness `pass` for the
  selected maintained manual-live beta evidence pairs: `AIDD-LIVE-002/codex`,
  `AIDD-LIVE-007/codex`, `AIDD-LIVE-007/claude-code`, `AIDD-LIVE-006/opencode`,
  and `AIDD-LIVE-008/opencode`.
- On 2026-05-24, terminal black-box bundles were refreshed and counted clean for the
  selected maintained manual-live beta evidence pairs:
  `w24-a4-live-002-codex-20260524`, `w24-a4-live-007-codex-20260524`,
  `w24-a4-live-007-claude-code-20260524`, `w24-a4-live-006-opencode-20260524-r2`,
  and `w24-a4-live-008-opencode-20260524`. The two interview scenarios include
  `answer-analysis.md` plus `manual quality-report.md`; all five counted bundles
  include `manual quality-report.md`.
- The `AIDD-LIVE-006/opencode` refresh first exposed an AIDD-owned repair-prompt clarity
  defect around malformed interview answer bullets. That defect was fixed in the
  candidate source before the counted rerun.
- Accepted `0.1.0a10` release/install evidence exists from the published GitHub Release,
  PyPI publish, `pipx` verification, and `uv tool` verification on 2026-06-11.
- Preflight readiness alone is not counted clean live evidence; the counted W24 refresh
  uses terminal black-box bundles and operator overlays.

Required change: keep workflow-shape tests preventing live E2E from entering GitHub
Actions, and run terminal black-box bundles separately before claiming refreshed counted
manual live evidence.

## Decision

Proceed with future publication only after recording release-branch dry-run evidence,
confirming the target version is unpublished, and receiving explicit approval to publish
the draft GitHub Release.

Do not claim beta completion solely from package publication; keep the beta decision tied
to maintained operator evidence, release/install evidence, and an explicit readiness call.
