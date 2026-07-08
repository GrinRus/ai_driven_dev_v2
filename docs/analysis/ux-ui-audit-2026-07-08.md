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
- Current follow-up: repaired `stage-result.md` rendering now preserves declared primary outputs already present in the stage directory, so repaired summaries do not hide `plan.md`, `implementation-report.md`, `review-report.md`, `qa-report.md`, or equivalent primary reports.
- Current follow-up: validation-pass reconciliation now replaces stale terminal notes that still claim a stage ended as `failed`, `blocked`, or `needs-input`. The summary can say artifact publication succeeded while preserving product-quality decisions such as `review-report.md` rejection in the primary report.
- Current follow-up: the active run panel now surfaces a live running-stage progress notice with elapsed time, runtime-output freshness, live log chunk count, and a direct log shortcut. Rendered QA covered desktop no-output and mobile live-output states via `/tmp/aidd-running-progress-desktop.png` and `/tmp/aidd-running-progress-mobile.png`.
- Current follow-up: `stage-result.md` next-action guidance is now flow-aware for implementation handoff. The document contract, implement prompt/repair prompt, and AIDD-LIVE-007 audit rubric require successful `implement` summaries to point to `review`, not directly to `qa`.
- Current follow-up: live stage audits now add a non-gating `stage-result-next-action-skips-canonical-stage` consistency finding when generated `stage-result.md` next actions mention a later downstream stage without the immediate canonical next stage. The finding is written to `stage-audits/*` and `grader.json`, giving future live E2E reports repeatable evidence for the observed `implement -> qa` wording regression.
- Current follow-up: first-launch runner selection now visually distinguishes the deterministic baseline from native provider runners. The onboarding card grid adds a baseline guidance strip, a recommended-style `generic-cli` card treatment, native-provider guidance copy, and static asset coverage so real provider cards remain available without looking equally safe for first setup checks. Rendered QA covered desktop and 390px mobile onboarding states via `/tmp/aidd-onboarding-runner-desktop.png` and `/tmp/aidd-onboarding-runner-mobile.png`.
- Current follow-up: Flow Complete now leads the Start Next Flow band with a dedicated recommended next-decision summary and reason before showing the full action grid. This gives first-time operators a clear post-QA decision while preserving final artifacts, blockers, baseline, and immutable source-run evidence. Rendered QA covered desktop and 390px mobile Flow Complete states via `/tmp/aidd-flow-complete-decision-desktop.png` and `/tmp/aidd-flow-complete-decision-mobile.png`.
- Current follow-up: `frontend-checkpoints.md` now opens with a manual visual review checklist for visible next action, active stage, desktop/mobile topbar readability, failure-appropriate recovery action, reachable logs/artifacts/questions/answers/next-flow controls, and overflow risks. The checkpoint remains run-integrity evidence and a prompt for manual `quality-report.md` evidence, not screenshot proof or an automated UI/UX quality gate.
- Current follow-up: live E2E frontend checkpoints now record an observed `running-stage` phase while a public stage command is still alive. The phase checks the disabled `wait-for-stage` next action, active running-stage visibility, and runtime-log affordance, including the honest pending-log state before `runtime.log` exists; the existing `post-stage` phase still checks completed stage API and artifact reachability.
- Current follow-up: live E2E now accepts optional operator-supplied browser notes or screenshots through `--manual-frontend-evidence`. The runner copies that file or directory into `manual-frontend-evidence/` and references it from `frontend-checkpoints.*` as non-gating evidence for the manual `quality-report.md`, while still not generating screenshot proof or changing runner classifications.

## Deferred Work

- Refresh the medium live E2E run after the current evidence-hardening changes and update the final UI/UX reports with any imported `manual-frontend-evidence/` browser notes or screenshots. The latest accepted medium evidence predates this import path.

## Refresh Run - 2026-07-08T13:18Z

- `eval-live-007-codex-20260708T131815Z`: terminal execution verdict `pass`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- Quality gates: all eight manual stage-quality audits chose `continue`.
- Self-repair: `tasklist` repaired missing TL-6 verification-note coverage; `qa` repaired missing ignored-workspace residue evidence. Both repairs succeeded on attempt 2.
- Final reports: `.aidd/reports/evals/eval-live-007-codex-20260708T131815Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.
- Manual screenshots: `manual-frontend-evidence/operator-ui-terminal-desktop.png` and `manual-frontend-evidence/operator-ui-terminal-mobile.png`.

## Refresh Findings

- P1: Mobile terminal layout still is not first-time-user friendly. The page-level width is contained, but the stage rail behaved like a horizontal strip and long run/path/action labels were visually clipped in the mobile screenshot.
- P1: Long-running stages still need stronger live progress prominence. The flow has progress and log affordances, but several stages ran for multiple minutes with little external stdout, so the operator needs an always-visible summary of active attempt, elapsed time, last runtime signal, and log shortcut.
- P2: Repair details are evidence-rich but not visually dominant enough. The UI shows attempt counts, but the resolved validation reason and repair brief remain easier to understand from Markdown than from the main stage rail.
- P2: Terminal handoff is strong on desktop. `FLOW COMPLETE`, final artifacts, blockers, repair attempts, approvals, questions, recovery assistant, and next-flow actions are visible and coherent.

## Current Improvement Slice

- Harden 390px mobile terminal layout by replacing the horizontal stage rail with a two-column responsive grid.
- Let mobile topbar project paths wrap instead of clipping into unreadable fragments.
- Stack mobile next-action controls and keep the primary action full-width.
- Add a stage-attempt tooltip that points operators to Recovery for repair and retry history.
- Rendered verification after the slice used the completed `eval-live-007-codex-20260708T131815Z` target workspace at 390px width. The updated page kept `scrollWidth=390`, stage cards stayed within `maxStageRight=380`, the stage rail rendered as `181px 181px`, and topbar controls all fit inside the viewport. Screenshot evidence: `/tmp/aidd-ui-mobile-terminal-after-fix.png`.

## Retry Visibility Slice

- Repaired stages now have an explicit `retry Nx` rail badge and a subtle amber stage-card marker instead of only a terse attempt count.
- The active-stage header now exposes a `Retry history` badge button that opens Recovery / Validation for the selected stage.
- Recovery / Validation now shows a resolved-retry summary for stages that are clean after a retry, with direct validator-report and repair-brief evidence before the full timeline.
- This targets the refresh-run P2 finding that repair details were present in Markdown but not visually dominant enough in the main operator UI.
- Rendered verification used the completed `eval-live-007-codex-20260708T131815Z` target workspace. Desktop DOM QA confirmed `tasklist` and `qa` rail cards show `retry 2x`, the `Retry history` button opens Recovery, and the resolved summary says `1 retry resolved across 2 validation attempts` with two timeline cards. Mobile 390px QA kept `scrollWidth=390`, stage cards inside `10..380px`, `Retry history` inside the viewport, and the recovery summary inside the viewport. Screenshot evidence: `/tmp/aidd-ui-retry-mobile-work-ready.png` and `/tmp/aidd-ui-retry-mobile-recovery.png`.

## Live Progress Prominence Slice

- UI-started live jobs now promote progress into the central next-action strip, not only the right Active Run panel.
- The live strip shows stage/job status, elapsed time, last runtime output age, live log chunk count, an `Open live logs` shortcut, and the cancel action.
- On 390px mobile, active-job mode raises the cockpit/live progress area before the stage rail so monitoring is visible in the first viewport.
- Rendered verification used a temporary `generic-cli` sleep runtime in `/tmp/aidd-live-progress-ui-qa2`, started through the actual UI. Desktop QA confirmed a real UI-started workflow job rendered `Idea: Running now`, live metrics, `Open live logs`, and `Cancel job`. Mobile QA kept `scrollWidth=390`, placed the cockpit before the stage rail, kept the strip inside `30..360px`, and showed the live strip inside the first viewport. Screenshot evidence: `/tmp/aidd-ui-live-progress-desktop-after-order.png` and `/tmp/aidd-ui-live-progress-mobile-after-order.png`.

## Review / QA Decision Clarity Slice

- `Review Findings` and `QA Verdict` now lead with decision summaries instead of dropping first-time operators directly into tables and remediation notes.
- The summaries state the current approval/verdict, primary action, blocking/follow-up counts, and whether the operator should proceed, send selected items back to implement, or request intervention.
- On 390px mobile, review/QA decision detail mode raises the cockpit before the stage rail and adds a compact decision cue to the global next-action strip, so the decision is visible in the first viewport while the full evidence table remains below.
- Terminal next-action copy now says `Review final artifacts` instead of the ambiguous `Review complete`, avoiding a QA-screen contradiction after the workflow has already reached terminal handoff.
- Rendered verification used the completed `eval-live-007-codex-20260708T131815Z` target workspace. Desktop QA confirmed full decision summaries are visible in the first viewport. Mobile QA confirmed shell display switches to `flex`, the decision cue is visible in the first viewport, and the full summary remains reachable below it. Screenshot evidence: `/tmp/aidd-review-decision-desktop.png`, `/tmp/aidd-review-decision-mobile.png`, `/tmp/aidd-qa-decision-desktop.png`, and `/tmp/aidd-qa-decision-mobile.png`.
