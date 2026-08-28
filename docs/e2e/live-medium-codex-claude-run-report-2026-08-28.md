# Live medium Codex + Claude run reconciliation — 2026-08-28

## Goal and scope

This report records the fresh medium `AIDD-LIVE-007` flow runs requested for the Codex and
Claude Code runtimes. Each run was executed from AIDD `main` revision
`17d2b903c58c9c34ec3f355431184a41375cf23b`, against the pinned Hono revision
`cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`, through the complete `idea → qa` flow.

The run is medium provider smoke evidence. It is not a human-session, large-flow, Wave 36,
Claude beta, cross-runtime comparison, or general beta-readiness claim.

## Run outcomes

| Runtime | Run ID | Stages | Verdict | Duration | First failure |
| --- | --- | --- | --- | ---: | --- |
| Codex | `eval-live-007-codex-20260828T164346Z` | `idea → qa` | `pass` | 2463.914 s | none |
| Claude Code | `eval-live-007-claude-code-20260828T173201Z` | `idea → qa` | `pass` | 2915.798 s | none |

Both runs passed setup/readiness, all eight canonical stages, target verification, review, QA,
terminal handoff, and the schema-v1 task-aware checkpoint. Claude Code reported the configured
model profile as `kimi-for-coding`; the harness runtime/provider lane remains `claude-code`.

## Checkpoint and quality evidence

For each run, the retained bundle contains:

- `verdict.md`, `summary.md`, `flow-report.md`, `flow-state.json`, and `flow-steps.json`;
- manual quality audits for stages `idea` through `qa`;
- `task-flow-checkpoint.json/.md` with matching tasklist/ledger hashes, successful TL-1..TL-5,
  aggregate finalization, and `Review eligible: True`;
- `frontend-checkpoints.md` with passing running and post-stage public UI/API checks;
- `flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`, all ending in
  `counted-clean`.

The Claude implementation aggregate needed a second finalization attempt after one evidence-only
prose claim was corrected to include its exact command. The correction changed durable live-run
evidence only; it did not change the target product source or the AIDD repository.

## UI/design comparison

The current AIDD UI was not changed by either target-specific run. Fresh provider-free UI/API
checkpoints passed for every running and post-stage state (operator shell, Work Item/run context,
active stage/status, next action, logs, and artifacts).

The retained visual audit
[`live-medium-codex-claude-ui-target-audit-2026-08-27.md`](live-medium-codex-claude-ui-target-audit-2026-08-27.md)
compares the target UI reference set across eight journeys and five viewports (40 screenshots).
It reports no material mismatch in task-centered hierarchy, server-owned grouping, primary-action
placement, responsive composition, focus/accessibility, console errors, or horizontal overflow.
No separate UI-fix task is justified by these runs.

## Reconciliation

No product or UI defect was found, so no implementation task was opened and no roadmap/backlog
promotion was required. The existing deferred items remain visible, including the uncoached human
observation, future cross-runtime comparison, and Wave 36 acceptance work. No default-renderer or
human-usability gate is silently marked complete by this medium evidence.

## Evidence locations

- Codex bundle: `.aidd/reports/evals/eval-live-007-codex-20260828T164346Z/`
- Claude Code bundle: `.aidd/reports/evals/eval-live-007-claude-code-20260828T173201Z/`
- UI audit: `docs/e2e/live-medium-codex-claude-ui-target-audit-2026-08-27.md`

