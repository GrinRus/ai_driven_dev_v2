# AIDD-LIVE-007 Claude acceptance attempt — 2026-09-09

## Scope

This is a retained manual acceptance record for `W36-E7-S4-T4`. It records one fresh
Claude Code run from an independent provider root against the same AIDD and target pins used
by the Codex acceptance lane. The run is evidence, not a merge or release gate.

- AIDD source revision: `fbbd29d65b468bc3f01c249cfbc11951885b3615`.
- Scenario: `AIDD-LIVE-007`, `harness/scenarios/live/hono-non-error-throw-handling.yaml`.
- Target: Hono `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`.
- Runtime: native Claude Code `2.1.236`, routed through the configured `kimi-k2.7-code` model.
- Run id: `eval-live-007-claude-code-20260909T071417Z`.
- Provider roots: fresh independent external root; no Codex root, target state, answers, or
  evidence were reused. Credentials are intentionally not recorded.
- Adjacent UI refactor: outside this run and untouched.

## Outcome

The runner verdict is `fail`, with the first decisive failure at the public `implement` stage.
Setup, install, target readiness, `idea`, `research`, `plan`, `review-spec`, and `tasklist`
completed. `review` and `qa` were not reached, so this run is not counted as acceptance.

The implementation stage produced a focused target diff in `src/compose.ts`,
`src/hono-base.ts`, `src/compose.test.ts`, and `src/hono.test.ts`. Claude's intermediate TL-1,
TL-2, and TL-3 verification reached 240/240 tests and a passing TypeScript check. The final
repair restored a legacy test that encoded the old synchronous rethrow contract; the final
authored suite was therefore 239/240. The intended AC-1 regression tests remained green.

## Decisive finding

Canonical implement validation stopped progression with `SEM-TASK-DIFF-MISMATCH` and
`SEM-TASK-SCOPE-MISMATCH` while reconciling cumulative prerequisite edits with TL-3's local
scope. The global scenario scope allows all four changed files, but TL-3 declares only
`src/hono-base.ts`. A report-only repair and a source restoration repair produced opposite
metadata failures; the final terminal report still declared a net-zero `src/hono.test.ts`
repair edit in its `Touched files` section, which did not match the TL-3 baseline diff.

This is classified as model/stage-output quality evidence rather than a provider or target
setup failure. The product implementation itself is narrow and source-grounded, but the run
cannot be counted until the task report and cumulative scope are reconciled in a fresh run.

## Operator and artifact checks

- Claude isolation retained non-secret endpoint/model configuration and passed the private
  provider probe; no auth payload entered the target, bundle, or Git.
- Loopback operator API checkpoints passed for active stage, run/stage state, next action,
  logs, and artifacts. No screenshots or manual browser notes were imported, so visual UI/UX
  quality remains uninspected. The generated target UI is not applicable; adjacent AIDD UI work
  remains out of scope.
- No new untracked product files, top-level `workitems/` pollution, or direct `.aidd/*.py`
  scratch files were found. `aidd.example.toml` is harness configuration.
- The complete external bundle and manual reports are retained outside Git under the run's
  provider report root. Raw runtime logs and credential material are not copied here.

## Required follow-up

1. Keep `W36-E7-S4-T4` as the actionable task; do not mark it `done` or promote T5.
2. On the next fresh run, keep the TL-1 prerequisite test edits in the task baseline and make
   the TL-3 implementation report list only the net task-local file (`src/hono-base.ts`).
3. Complete `review`, `qa`, terminal verification, and the final manual quality reports before
   claiming Claude acceptance.
