# Live medium Codex/Claude run report — 2026-08-27

## Scope and claim boundary

This report records the Codex and Claude `AIDD-LIVE-007` medium runs and the
UI target audit. It is Codex/Claude live evidence only; it makes no Claude
acceptance, cross-provider beta-readiness, or human-session claim.

## Codex lane

- Run: `eval-live-007-codex-20260827T093650Z`
- Scenario: `AIDD-LIVE-007`
- Runtime: `codex`
- Status: `pass`
- Bundle: `.aidd/reports/evals/eval-live-007-codex-20260827T093650Z`
- Verdict: `.aidd/reports/evals/eval-live-007-codex-20260827T093650Z/verdict.md`
- Checkpoint: `.aidd/reports/evals/eval-live-007-codex-20260827T093650Z/task-flow-checkpoint.json` and `.md`

The flow completed `idea → research → plan → review-spec → tasklist →
implement → review → qa`. The schema-v1 task-aware checkpoint confirms the
run/revision identity, task order and dependencies, succeeded attempts,
matching tasklist/ledger hashes, aggregate finalization, and `Review eligible:
True`. Target implementation verification passed: 238 focused Vitest tests,
TypeScript compilation, and the exact four-file scope check.

The Codex quality audits marked `idea` through `implement` strong. Review and
QA were accepted with a retained control-plane note: an intermittent
stage-result validator discrepancy was observed even though the canonical
review content was present. It did not identify a product defect.

## Claude lane

### Initial attempt

- Run: `eval-live-007-claude-code-20260827T102206Z`
- Status: `fail`
- Bundle: `.aidd/reports/evals/eval-live-007-claude-code-20260827T102206Z`
- First failing stage: `implement`

The target Hono patch itself was correct and its focused tests passed, but the
runtime reported prerequisite changes under the wrong task-local scope. The
fail-closed implementation validator correctly stopped that attempt with
`SEM-TASK-DIFF-MISMATCH` and `SEM-TASK-SCOPE-MISMATCH`.

### Fresh rerun

- Run: `eval-live-007-claude-code-20260827T120324Z`
- Status: `fail`
- Bundle: `.aidd/reports/evals/eval-live-007-claude-code-20260827T120324Z`
- Verdict: `.aidd/reports/evals/eval-live-007-claude-code-20260827T120324Z/verdict.md`
- First failing stage: `qa`

After the rerun's automatic repairs, all five implementation tasks succeeded,
review was approved, TypeScript passed, and the targeted Vitest suite passed
(235 tests). The terminal QA stage exhausted its three attempts on the
blocking `CROSS-QA-UPSTREAM-EVIDENCE` finding: two QA evidence entries still
did not resolve to an exact upstream evidence id or artifact path. This is a
control-plane QA-report/evidence-link failure, not a Hono product defect; the
run therefore remains fail-closed and is not a clean Claude pass.

The final target diff was bounded to `src/compose.ts`, `src/hono-base.ts`,
`src/compose.test.ts`, and `src/hono.test.ts`. No target-repository code was
copied into this repository as part of the live evidence run.

## UI result

The provider-free browser audit is recorded in
`docs/e2e/live-medium-codex-claude-ui-target-audit-2026-08-27.md`. It covered
40 screenshots across eight journeys and five viewports, with no material
target-design mismatch, console error, overflow, or accessibility failure.
Consequently no UI code change was warranted.

## Final disposition

Codex has a passing live medium lane and the UI target audit is green. Claude
reached implementation and review successfully but its end-to-end run is
blocked by the final QA evidence-link contract. The exact failure is retained
for a future control-plane follow-up; it must be resolved before claiming a
clean two-runtime or beta-ready flow. No human session, Claude acceptance, or
cross-provider readiness is claimed here.
