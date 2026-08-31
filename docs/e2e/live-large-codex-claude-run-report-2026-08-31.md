# Live large Codex + Claude run reconciliation — 2026-08-31

## Goal and scope

This report records the fresh large `AIDD-LIVE-012` flow runs for Codex and Claude Code. Both
runs started from the reconciled AIDD `main` revision `adbc73f621c3d4cfe782c7adb6e715bffac1ccca`
against the pinned `Kludex/starlette` target revision `e636c77b15d903ab3ff3968cd43aee1887dd1e48`,
and completed the full `idea → qa` product-evaluation flow. The target is backend-only, so it has
no product UI or target-design surface for a pixel-level comparison.

This is Codex + Claude Large evidence for the requested flow and target-task quality. It is not a
human-session, cross-runtime lower-capability, Claude beta, or general production-readiness claim.

## Run outcomes

| Runtime | Run ID | Stages | Verdict | First failure |
| --- | --- | --- | --- | --- |
| Codex | `eval-live-012-codex-20260830T220257Z` | `idea → qa` | `pass` | none |
| Claude Code | `eval-live-012-claude-code-20260831T001223Z` | `idea → qa` | `pass` | none |

Both counted runs reached terminal success, target verification, review, QA, Flow Complete, and
the task-aware checkpoint. Earlier failed or invalidated Claude attempts remain retained as
diagnostic history; they are not counted as the fresh result.

## Target-task quality

The selected Starlette change is bounded to:

- `starlette/middleware/base.py` — translate send-side `OSError` to `ClientDisconnect` for ASGI
  spec `>= 2.4`, while preserving debug-message and background-task behavior;
- `tests/middleware/test_base.py` — public ASGI regression coverage through
  `BaseHTTPMiddleware`.

The target verification result is `203 passed, 2 xfailed` in the focused pytest suite, `2 passed`
for the isolated regression, and Ruff `All checks passed!`. Review and QA report no code findings;
`git diff --check` is clean and no unrelated target product files are changed.

## Checkpoint and flow evidence

Each provider bundle retains `verdict.md`, `flow-state.json`, runtime logs/events, all eight stage
audits and manual quality audits, review/QA reports, target workspace evidence, frontend
checkpoints, and schema-v1 `task-flow-checkpoint.json/.md`.

| Runtime | Tasklist/ledger hash | Tasks | Finalization | Review eligibility |
| --- | --- | --- | --- | --- |
| Codex | `6da49be26042cff5d9a12fa14461e1bddb090e0ddaa41dcdc5050c5bf43f7acc` | TL-1..TL-3 succeeded | succeeded | true |
| Claude Code | `eb56cab26b40c86c19fdaf19e93f17d7c6dbde4b4bc5c6da35008724b05d5923` | TL-1..TL-3 succeeded | succeeded | true |

Both checkpoints report matching tasklist/ledger hashes, no fail-closed findings, and no pending
next-ready task after aggregate finalization.

## UI and design comparison

The AIDD operator UI/API checkpoints passed for running and post-stage states (shell, Work Item/run
context, active stage, next action, logs, and artifacts). No browser screenshots were supplied for
this run, so there is no new pixel-level claim. The existing retained visual audit
[`live-medium-codex-claude-ui-target-audit-2026-08-27.md`](live-medium-codex-claude-ui-target-audit-2026-08-27.md)
reports no material mismatch for the AIDD task-centered UI across its defined journeys and
viewports. No separate UI-fix task is justified by the Large target runs.

## Reconciliation

No target product, AIDD flow, or UI defect was found, so no implementation-fix task was opened and
no runtime behavior was changed during this evidence cycle. The deferred uncoached human
observation, future cross-runtime comparison, and Wave 36 acceptance tasks remain visible in the
parking lot.

## Evidence locations

- Codex bundle: `.aidd/reports/evals/eval-live-012-codex-20260830T220257Z/`
- Claude Code bundle: `.aidd/reports/evals/eval-live-012-claude-code-20260831T001223Z/`
- This tracked reconciliation: `docs/e2e/live-large-codex-claude-run-report-2026-08-31.md`
