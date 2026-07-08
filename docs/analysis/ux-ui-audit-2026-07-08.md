# UX/UI Audit - Operator Flow - 2026-07-08

## Scope

- Product surface: local AIDD operator UI served by `aidd ui`.
- User model: first-time operator running a governed document-first workflow, then recovering from blocked, failed, or completed runs.
- Live evidence: `AIDD-LIVE-007` / `codex` / `eval-live-007-codex-20260708T103154Z`, completed from `idea` through `qa` with one review-driven remediation cycle.
- Local visual evidence: onboarding, first command center, runtime failure recovery, completed flow, follow-up wizard, and mobile completed-flow screenshots captured under `/tmp/aidd-ui-ux-e9daBL`, `/tmp/aidd-ui-ux-good-e2DDAN`, and `/tmp/aidd-ui-terminal-GV58Fp`.

## Quality Summary

The operator UI has the right product concepts: project/work item/run context, stage rail, global next action, evidence/logs, recovery, and next-flow handoff. The workflow is inspectable, and the live E2E bundle shows stage artifacts and runtime logs can be reached through public surfaces.

The main UX gap is not missing capability; it is decision priority. A new operator can see many panels but may not know which one matters now. Recovery also needs stronger failure-specific guidance: runtime failures should lead with logs and runtime-exit evidence, while validation failures should lead with repair/request-change actions.

## Findings

- P1: Runtime failure recovery can point the user at `Request Change` before `Open logs`. In the failed fixture run, the central recovery hero showed `Runtime failure` but the primary action was `Request Change`; the better evidence path was only visible in the sidebar.
- P1: Mobile topbar status chips collapse to single letters on a 390px viewport. This makes work item, run, and readiness state unreadable at exactly the size where first-time operators need more context.
- P2: Long live stages have weak perceived progress before runtime logs appear. During `stage-0002-research`, the bundle showed active `run-stage` state for several minutes while no stage runtime log was yet present.
- P2: First launch shows several similarly weighted setup surfaces. The safe deterministic runner is not visually distinguished enough from real provider commands.
- P2: The automated frontend checkpoint proves HTTP/API availability but not visual clarity, responsive layout, or whether the next operator action is understandable.
- P3: Long artifact paths are truncated aggressively in compact mobile rows. This avoids page overflow but reduces evidence traceability.

## Live E2E Stage Notes

- `stage-0001-idea`: acceptable. The idea brief framed the Hono non-Error throw task correctly, preserved compatibility constraints, and had no blocking questions. The frontend checkpoint passed API/page reachability only.
- `stage-0002-research`: strong. The research found both Hono error gates, cited source/tests, reproduced current behavior, and identified the correct Vitest verification path.
- Both checkpoints exposed a meta-UX issue: the live frontend checkpoint lacks visual QA assertions.

## Full Live E2E Result

- `eval-live-007-codex-20260708T103154Z`: terminal execution verdict `pass`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> implement -> review -> qa`.
- Remediation: first `review` rejected implementation with `RV-001` because non-Error normalization dropped the original thrown value instead of preserving it through `Error.cause`; the public remediation UI/API created `request-0001`, reran `implement`, marked `review` and `qa` stale, and reran downstream stages to a clean `qa` verdict.
- Self-repair: `tasklist` repaired missing task-id references in verification notes; `qa` repaired missing ignored-workspace residue evidence.
- Final target checks: `vitest --run --coverage.enabled=false src/hono.test.ts src/compose.test.ts`, `tsc --noEmit`, `git diff --check`, and QA residue checks passed.
- Final reports: `.aidd/reports/evals/eval-live-007-codex-20260708T103154Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.

## New UX Findings

- P1: Repaired-stage summaries are too terse and can omit primary report artifacts such as `implementation-report.md`, `review-report.md`, or `qa-report.md`. The detailed report is present, but the first summary a user sees is less useful after repairs.
- P1: Review rejection created contradictory operator language: the stage result carried runner success framing while the review report correctly said `rejected`. A first-time operator needs a clearer distinction between "stage artifact publication succeeded" and "product review rejected the implementation."
- P2: One implementation stage result pointed the next action at QA even though review still had to run first. Stage next-action copy needs to be flow-aware.
- P2: Long provider stages and remediation jobs took several minutes. The UI exposes logs and last-output state, but the operator still needs stronger progress affordances and a prominent log shortcut.
- P2: Semantic frontend checkpoints now cover operator surface availability, but they still do not prove visual readability or responsive layout.

## First Improvement Plan

- Make runtime failure recovery prefer `Open logs` when `first_failure.kind` is a runtime failure and runtime evidence exists.
- Make the central recovery hero explain runtime evidence first: failure detail, runtime-exit metadata path, and raw log path.
- Fix mobile topbar status chip layout so run/work item/readiness labels remain readable instead of collapsing.
- Let mobile `.path-line` wrap within rows when necessary, preserving traceability without page-level horizontal scroll.
- Add static asset contract tests for these UX priorities.

## Iteration Log

- `69f7c7c Improve operator recovery UX`: completed the first improvement plan. Browser QA confirmed runtime-failure recovery now leads with `Open logs` and mobile status chips stay readable.
- Current iteration: strengthen live E2E frontend checkpoints with operator-surface semantic evidence for run context, stage context, next action, logs, artifacts, and recovery cues. This improves future UX audit evidence without treating the checkpoint as a screenshot or manual UI/UX quality gate.
- `eval-live-007-codex-20260708T102414Z`: fresh live evidence showed the new next-action check must read `/api/dashboard`, not `/api/run`, because the UI dashboard owns operator next-action state while `/api/run` is run metadata.
- `a48b1bd Fix live frontend next-action checkpoint`: fixed the checkpoint contract to probe `/api/dashboard`.
- `eval-live-007-codex-20260708T103154Z`: completed the medium live flow with review remediation and QA self-repair. Execution quality is strong; UX excellence still needs better repaired-stage summaries, flow-aware next-action text, progress affordances, and visual checks.

## Deferred Work

- Add visual frontend checkpoints for live E2E, including desktop/mobile screenshots and assertions for visible next action, active stage, recovery primary action, and absence of clipped topbar text. The current iteration adds non-visual operator-surface semantic evidence first.
- Rebalance first-launch onboarding so the recommended deterministic/safe path is visually dominant while real provider runners remain available.
- Add a more explicit in-progress/pre-runtime state to the UI for long live stages before runtime log chunks exist.
- Improve repaired-stage and terminal stage summaries so they always name the primary report artifact and clearly distinguish runner execution success from product-quality rejection.
- Make generated next-action copy flow-aware so stage summaries do not point to QA before review.
