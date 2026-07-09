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

## Stale Downstream Rerun Slice

- Stale downstream states now get a central summary in the global next-action strip instead of relying on small rail badges and the Active Run sidebar.
- The summary names the invalidated stage chain, remediation request id, runtime readiness gate, and next operator step, and explicitly states that terminal QA handoff remains blocked until downstream evidence is refreshed.
- On 390px mobile, stale-downstream mode raises the cockpit before the stage rail so the rerun explanation is visible in the first viewport.
- Rendered verification used a temporary copy of `eval-live-007-codex-20260708T131815Z` with `request-0001` marking `review` and `qa` stale. Desktop QA confirmed the stale summary is visible in the first viewport. Mobile QA confirmed `scrollWidth=390`, shell display switches to `flex`, stale badges remain on the rail, and the summary shows `Runtime codex not ready` plus `Next step Select ready runtime` while the rerun button is disabled. Screenshot evidence: `/tmp/aidd-stale-downstream-desktop.png` and `/tmp/aidd-stale-downstream-mobile.png`.

## Approval Audit Decision Slice

- Approvals / Runtime Requests now leads with an approval decision spotlight before queue metrics and ledger history.
- The spotlight distinguishes no-waiting, pending, approved, denied/cancelled, and policy-blocked states, then states the primary operator action before showing counts.
- This targets the remaining first-time-user gap where approval state was audit-rich but forced operators to infer whether the runtime was waiting, blocked by policy, or already resolved.
- Rendered verification used a temporary copy of the live Hono target workspace with one pending QA shell approval. Desktop QA confirmed the pending spotlight is visible in the first viewport above the queue/audit ledger. Mobile 390px QA kept `scrollWidth=390`, showed the spotlight in the first viewport, and preserved the approval audit log below it. Screenshot evidence: `/tmp/aidd-approval-spotlight-desktop.png` and `/tmp/aidd-approval-spotlight-mobile.png`.

## Question Interview Decision Slice

- Questions / Interview Loop now leads with an interview decision spotlight before raw answer counters and question cards.
- The spotlight distinguishes no-question, blocking-required, partial/deferred, and fully-resolved states, then states the primary operator action before showing required/resolved/partial/deferred totals.
- This targets the US-05 non-happy path where a first-time operator must understand whether the runtime is blocked on answers, which answers are partial, and why `answers.md` must contain resolved answers before resume.
- Rendered verification used a temporary `plan` workspace blocked by two interview questions, with one partial saved answer in `answers.md`. Desktop QA confirmed the spotlight appears in the first viewport, names `Primary action: answer required questions`, and keeps the partial-answer resume button disabled. Mobile 390px QA kept `scrollWidth=390`, kept the question cards inside the viewport, showed the spotlight in the first viewport, and preserved the disabled resume state. Chrome DevTools reported no console messages and all page/API requests returned 200/204. Screenshot evidence: `/tmp/aidd-question-spotlight-desktop.png` and `/tmp/aidd-question-spotlight-mobile.png`.

## Refresh Run - 2026-07-08T15:40Z

- `eval-live-007-codex-20260708T154059Z`: terminal execution verdict `pass`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- Quality gates: all eight manual stage-quality audits chose `continue`.
- Self-repair: `tasklist` repaired missing T7/T8 verification-note coverage on attempt 2.
- Target implementation quality: `review` and `qa` both accepted the scoped Hono non-Error throw change; focused vitest and `tsc --noEmit` passed.
- Final manual reports: `.aidd/reports/evals/eval-live-007-codex-20260708T154059Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.

## Refresh Findings - 2026-07-08T15:40Z

- P1: Completed terminal runs without an explicit stage opened the operator UI on `Idea`, while the global handoff said `Review final artifacts` and QA was ready. This created a first-time-user contradiction between selected stage and actual run state.
- P2: The work-item rail showed `idea / 8/8` for a completed run whose final handoff was QA, reinforcing the same mismatch.
- P2: The successful tasklist repair was visible through the retry badge and Recovery evidence, but the actual repair reason remained easier to understand from Markdown artifacts than from the first viewport.
- P2: Long CLI-driven live stages still produced little runner stdout while work was active. The UI exposes progress/log surfaces, but the CLI-side live harness remains sparse during long provider calls.
- P3: QA low warnings (`STRUCT-OUTPUT-PROMOTED`) show successful recovery from misplaced output files, but canonical versus mirrored output artifacts still needs clearer operator wording.

## Terminal Default Stage Slice

- Completed terminal dashboard requests without a `stage` parameter now default to `qa` when a terminal handoff exists, even if the run metadata `stage_target` is an earlier stage.
- The frontend no longer sends the initial default `stage=idea` before the operator explicitly chooses a stage. URL-provided stages and operator stage clicks still pin the requested stage.
- Completed work-item cards now render `flow complete / 8/8` instead of an inherited stage label such as `idea / 8/8`.
- Browser verification used the completed `eval-live-007-codex-20260708T154059Z` target workspace. Opening `http://127.0.0.1:65211/` redirected to `?stage=qa&run_id=eval-live-007-codex-20260708T154059Z`, highlighted `QA`, showed `QA / Verify outcomes` in the stage cockpit, preserved the `Review final artifacts` terminal handoff, and showed `flow complete / 8/8` on the work-item card. Screenshot evidence: `/tmp/aidd-terminal-default-qa-after-fix.png`.

## Terminal Repair Reason Slice

- Terminal handoff API responses now include compact repair highlights in addition to aggregate repair counts.
- Flow Complete now surfaces resolved repair reason, stage, retry number, outcome, and direct repair/validator evidence links before next-flow actions.
- Mobile terminal handoffs with repair highlights add a compact repair cue to the global next-action strip and keep the page at the top instead of auto-scrolling to the stage rail.
- Browser verification used the completed `eval-live-007-codex-20260708T154059Z` target workspace. Desktop QA confirmed the `tasklist` repair reason is visible in the first viewport, evidence buttons point to `repair-brief.md` and `validator-report.md`, and no console warnings/errors were recorded. Mobile 390px QA confirmed the compact repair cue is visible in the first viewport, `scrollWidth=390`, the repair card stays within `46..347px`, and evidence buttons stay inside `57..336px`. Screenshot evidence: `/tmp/aidd-terminal-repair-highlight-desktop.png` and `/tmp/aidd-terminal-repair-highlight-mobile.png`.

## Artifact Ownership Slice

- Stage `output/*.md` files now appear in the operator artifact workbench and evidence graph as `mirror` rows under `Published output mirrors`, not as canonical source documents.
- Workbench and artifact-table copy now distinguishes `canonical source` from `handoff mirror`, explains that `output/` copies are downstream handoff mirrors, and keeps mirror actions to `Open` and `Copy path` instead of unsupported document downloads.
- Mobile workbench rendering now stacks the sidebar at 390px and wraps long markdown/contract paths, avoiding local overflow while reviewing the same artifact evidence.
- Browser verification used the completed `eval-live-007-codex-20260708T154059Z` target workspace on the `plan` Evidence tab. Desktop QA confirmed `output/plan.md` and related mirrors render as `handoff mirror`, page `scrollWidth=1280`, and no console errors were recorded. Mobile 390px QA confirmed `Published output mirrors`, `output/plan.md`, and `handoff mirror` remain visible, root `scrollWidth=390`, sidebar grid is single-column, and internal visible overflow is empty. Screenshot evidence: `/tmp/aidd-artifact-ownership-desktop.png` and `/tmp/aidd-artifact-ownership-mobile.png`.

## External Running Stage Slice

- Externally started or CLI-started stages that report dashboard `wait-for-stage` now get a central running strip even when no UI job is active.
- The strip explicitly says the stage is running outside UI control, shows status, attempt, run id, and runtime, and offers `Open runtime logs` plus `Refresh status` without a misleading cancel action.
- On 390px mobile, external-running-stage mode raises the cockpit and progress explanation before the stage rail so the live wait state is visible in the first viewport.
- Browser verification used a temporary `codex` run in `/tmp/aidd-external-running-ui-qa` with `plan` marked `executing`. Desktop QA confirmed the strip is readable, uses one copy column, keeps `scrollWidth=1280`, opens `RUNTIME LOGS / LIVE CONSOLE`, and records no console errors. Mobile 390px QA confirmed the strip starts in the first viewport at `top=457`, keeps `scrollWidth=390`, keeps buttons inside the viewport, and records no console errors.

## Refresh Run - 2026-07-08T19:06Z

- `eval-live-007-codex-20260708T190645Z`: interrupted during `implement` after the provider wrote implementation artifacts and before AIDD published the stage.
- Stage path reached: `idea -> research -> plan -> review-spec -> tasklist -> implement`.
- Frontend running-stage checkpoints passed for the observed long stages: the dashboard exposed the active running stage, disabled `wait-for-stage` action, and runtime-log affordance. Remaining quiet-runner ambiguity now belongs mostly to CLI/harness stdout and post-provider status reporting, not the browser operator UI.
- Stage-quality audits chose `continue` for `idea`, `research`, `review-spec`, and `tasklist`; `plan` chose `continue-with-risk` because `stage-result.md` skipped the immediate canonical `review-spec` next stage in its copy.
- `tasklist` self-repaired missing T6 verification-note coverage and then passed validation.
- `implement` generated a valid scoped Hono change and verification evidence, but AIDD remained in `validating` while the semantic validator consumed CPU inside implementation command-evidence regex matching.

## Refresh Findings - 2026-07-08T19:06Z

- P1: A valid implementation report can leave the operator stuck in a perpetual `validating` state. The trigger was a cache-absence verification command such as ``test ! -e .pytest_cache && test ! -e .ruff_cache``: artifact-word filtering removed the closing backtick before `IMPLEMENT_COMMAND_PATTERN.search`, causing catastrophic regex backtracking.
- P1: Interruption evidence is not robust enough under repeated interrupt. The harness caught the first interrupt, then a second `KeyboardInterrupt` landed while serializing `steps.json`, so resumable interruption evidence may be incomplete.
- P2: The external running-stage UI did its job: browser affordances made the active stage and logs visible. The weak spot is now the CLI/live-harness status surface when the provider has finished but AIDD post-processing is still validating.
- P2: Ignored-residue evidence prompts still encourage broad `git status --ignored --short --untracked-files=all` output in repositories with installed dependencies. The validation contract needs bounded evidence wording so operators and logs do not drown in setup-owned ignored files.

## Validator Regex Stability Slice

- Implementation command-evidence detection now removes non-command artifact prose only outside inline-code spans, preserving backticked shell commands that mention `.pytest_cache`, `.ruff_cache`, `coverage`, or similar cache paths.
- The command regex is guarded against unbalanced backticks before search, preventing the validator from spinning when malformed or filtered verification text contains an unmatched inline-code delimiter.
- Regression coverage validates that a cache-absence command with `.pytest_cache` and `.ruff_cache` is accepted without hanging, while the existing cleanup-prose case still does not get mistaken for executable command evidence.
- Replay verification against the interrupted live `implement` artifact now completes with `0` findings and advances the stage to `succeeded` with published output mirrors.

## Refresh Run - 2026-07-08T19:55Z

- `eval-live-007-codex-20260708T195548Z`: terminal execution verdict `fail`.
- The run stopped during the `idea` stage frontend running-stage checkpoint, before the later workflow stages could execute.
- The public page, run API, stage API, and logs API all returned `200`, and the `idea` post-stage checkpoint passed after the stage settled.
- The running-stage `/api/dashboard?stage=idea&run_id=eval-live-007-codex-20260708T195548Z` probe timed out, so the checkpoint could not observe the active running stage or disabled `wait-for-stage` action.

## Refresh Findings - 2026-07-08T19:55Z

- P1: The running-stage dashboard path is too expensive or race-prone for the first active-stage probe. A first-time operator can lose the most important state during a long stage: "this stage is running; wait, refresh, or open logs."
- P2: The post-stage dashboard path remains healthy, which narrows the gap to active-stage rendering rather than general UI/API availability.
- P2: The running-stage checkpoint currently needs only run context, stage rail, `wait-for-stage`, and log affordance; full artifact previews, recent activity, validation findings, and recovery summaries are lower-value until the stage settles.

## Running Dashboard Fast Path Slice

- Dashboard resolution now short-circuits when any stage is in `preparing`, `executing`, or `validating` state.
- The running-state response keeps the run summary, stage rail, and disabled `wait-for-stage` next action, while deferring active-stage previews, primary artifacts, recent activity, recent artifacts, validation findings, recovery actions, and terminal handoff until the stage settles.
- This preserves the operator's essential live state while making the first active-stage `/api/dashboard` probe cheap and less sensitive to files being written concurrently by the runtime.
- Regression coverage creates a running implementation stage with a large `events.jsonl` and asserts that the dashboard still returns `wait-for-stage` without loading heavy activity or artifact sections.

## Refresh Run - 2026-07-08T20:08Z

- `eval-live-007-codex-20260708T200843Z`: terminal execution verdict `pass`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- Frontend checkpoints: all running-stage and post-stage checkpoints passed. The previous `idea` running-stage `/api/dashboard` timeout did not recur; `idea`, `research`, `plan`, `review-spec`, `tasklist`, `implement`, `review`, and `qa` all exposed running stage, disabled `wait-for-stage`, and runtime-log affordance.
- Quality gates: `idea`, `research`, `tasklist`, `implement`, `review`, and `qa` chose `continue`; `plan` and `review-spec` chose `continue-with-risk` because stage-result next-action copy did not clearly name the immediate canonical next stage.
- Self-repair: `tasklist` repaired missing T5 verification-note coverage on attempt 2.
- Target implementation quality: review approved the four-file Hono patch; QA reported `ready` / `proceed`; focused Vitest and `tsc --noEmit` passed.
- Final manual reports: `.aidd/reports/evals/eval-live-007-codex-20260708T200843Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.
- Manual UI evidence: terminal Flow Complete desktop and mobile screenshots at `/tmp/aidd-terminal-flow-complete-desktop-200843.png` and `/tmp/aidd-terminal-flow-complete-mobile-200843.png`.

## Refresh Findings - 2026-07-08T20:08Z

- P1: Stage-result next-action wording still fails first-time-operator clarity in non-terminal middle stages. `plan` pointed to downstream implementation planning/implementation instead of `review-spec`; `review-spec` produced a runner warning because it did not name immediate `tasklist`.
- P1: CLI/live-harness progress remains too quiet during native-provider calls. Multiple stages took roughly 2-6 minutes with no useful launching-terminal stdout before the provider turn completed, even though the browser UI exposed a running wait state and log affordance.
- P2: Manual screenshot evidence now exists for the terminal screen, but the live runner did not import it into `manual-frontend-evidence/`; final `quality-report.md` has to reference `/tmp` paths outside the bundle.
- P2: The terminal Flow Complete UI is healthy on desktop and 390px mobile: QA ready, repair cue, next action, next-flow actions, and stage rail are readable with no horizontal overflow.
- P2: Tasklist self-repair is understandable in artifacts and visible in the terminal UI through `retry 2x` and the repair resolved cue.

## Next UX Plan

- Fix stage-result next-action wording so every successful non-terminal stage names the immediate canonical next stage in user-facing copy.
- Add a CLI/live-harness heartbeat or progress summary for long native-provider intervals before runtime logs appear, without pretending the model has made progress it has not emitted.
- Import manual frontend screenshots or browser notes into the live bundle for terminal UI/UX review evidence instead of leaving `/tmp` references outside the eval artifact tree.
- Add bounded ignored-residue wording to the implementation prompt/contract so live logs cite the evidence command without dumping full dependency trees.
- Harden live E2E interruption recording so a repeated interrupt cannot corrupt or skip the interrupted-resumable evidence step.

## Canonical Stage Next Action Slice

- `stage-result.md` now gives a full immediate-next-stage map for the canonical chain:
  `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- The `plan` contract and prompt now require successful next-action copy to point to
  `review-spec`, preventing first-time operators from skipping the review-spec screen and
  jumping mentally to task decomposition or implementation.
- The `review-spec` contract and prompt now require successful next-action copy to point to
  `tasklist`, preventing the reviewed-plan handoff from skipping decomposition.
- The live AIDD-LIVE-007 audit rubric now names the observed middle-stage checks explicitly:
  `plan -> review-spec`, `review-spec -> tasklist`, and `implement -> review`.
- Focused verification covered prompt quality, scenario loader model tests, docs consistency, ruff, and `git diff --check`.

## Refresh Run - 2026-07-08T21:02Z

- `eval-live-007-codex-20260708T210223Z`: terminal execution verdict `pass`.
- Source revision: `fd8bad3e3fac2a007bba3caeddd8c475e06f301c`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- Quality gates: `idea`, `plan`, `review-spec`, `implement`, `review`, and `qa` chose `continue`; `research` and `tasklist` chose `continue-with-risk`.
- Self-repair and remediation: none.
- Frontend checkpoints: all running-stage and post-stage checkpoints passed.
- Manual browser evidence: copied into `manual-frontend-evidence/terminal-desktop-210223.png`, `manual-frontend-evidence/terminal-mobile-210223.png`, and `manual-frontend-evidence/terminal-ui-browser-notes-210223.json`.
- Browser QA: desktop `scrollWidth=1280`, mobile `scrollWidth=390`, no horizontal overflow, no console messages, Flow Complete/QA-ready/next action/runtime logs/manual evidence all present.
- Target implementation quality: review approved the four-file Hono patch; QA reported `ready` / `proceed`; focused Vitest, `tsc --noEmit`, and `git diff --check` passed.
- Final manual reports: `.aidd/reports/evals/eval-live-007-codex-20260708T210223Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.

## Refresh Findings - 2026-07-08T21:02Z

- P1: CLI/live-harness progress remains too quiet during native-provider calls. Browser running-state affordances are healthy, but the launching terminal still has long intervals with little useful operator feedback.
- P1: Exact next-stage copy is improved but not universal. `plan` now correctly names `review-spec`, and `review-spec` now correctly names `tasklist`; `research` still used generic `planning` wording instead of exact `plan`, and `tasklist` used generic `implementation stage` wording instead of exact `implement`.
- P2: One successful `research` stage result retained stale placeholder copy (`Stage not run yet`) above otherwise useful output, which weakens trust in the stage summary.
- P2: Manual frontend evidence import is usable, but evidence generated after the runner has already copied the directory needs an explicit post-run copy step. The current bundle was corrected manually after browser QA.
- P2: Terminal Flow Complete UI is healthy on desktop and 390px mobile: QA ready, final artifacts, evidence refs, recovery assistant, next action, and next-flow actions are readable with no horizontal overflow.

## Next UX Plan - 2026-07-08T21:02Z

- Add CLI/live-harness heartbeat output for long native-provider intervals, including active stage, elapsed time, last runtime signal, and log path.
- Extend exact next-action guidance and validation to all successful non-terminal stages, starting with `research -> plan` and `tasklist -> implement`.
- Remove stale placeholder/preamble copy when a successful `stage-result.md` is regenerated or repaired.
- Make manual frontend evidence timing explicit in the live E2E workflow so screenshots and browser notes reliably land in the final bundle.
- Keep interruption recording and bounded ignored-residue evidence on the backlog for the next non-happy-path audit pass.

## Exact Stage Result Hygiene Slice

- `research` contract and prompts now require successful `stage-result.md` next-action copy to name the exact immediate stage id `plan`, not generic `planning` wording.
- `tasklist` contract and prompts now require successful `stage-result.md` next-action copy to name the exact immediate stage id `implement`, not generic `implementation stage` wording.
- AIDD-generated repaired `stage-result.md` summaries now use an immediate canonical next-stage map instead of `Advance to the next stage`.
- Structural validation now flags stale bootstrap placeholder text such as `Stage not run yet.` in any completed `stage-result.md`.
- Live stage audits now record a non-gating `stage-result-next-action-missing-immediate-stage` consistency finding when `Next actions` exists but omits the exact immediate stage id.
- Verification covered prompt quality, structural validator tests, repair tests, scenario loader tests, targeted live harness next-action regressions, docs consistency, mypy, ruff, and `git diff --check`.

## Refresh Run - 2026-07-08T22:13Z

- `eval-live-007-codex-20260708T221353Z`: terminal execution verdict `pass`.
- Source revision under test: `5416c6a8d184cfd9db756a3a82ce68381892c688`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- Quality gates: `idea`, `research`, `plan`, `review-spec`, `implement`, and `review` chose `continue`; `tasklist` and `qa` chose `continue` after successful repair.
- Self-repair: `tasklist` repaired ordered-task formatting/T5 verification coverage on attempt 2; `qa` repaired missing ignored-residue evidence on attempt 2.
- Frontend checkpoints: all running-stage and post-stage checkpoints passed.
- Stage-audit consistency: all eight stages recorded empty `consistency_findings`; the previous `research -> plan` and `tasklist -> implement` next-action defects did not recur.
- Browser QA: desktop `scrollWidth=1280`, mobile `scrollWidth=390`, no horizontal overflow, no console messages, Flow Complete/QA-ready/repair cards/next action all visible.
- Manual browser evidence: `manual-frontend-evidence/terminal-desktop-221353.png`, `terminal-mobile-221353.png`, `terminal-evidence-desktop-221353.png`, `terminal-history-desktop-221353.png`, `terminal-ui-browser-notes-221353.json`, and `terminal-ui-log-affordance-221353.json`.
- Target implementation quality: review approved the four-file Hono patch; QA reported `ready` / `proceed`; focused Vitest, `tsc --noEmit`, and `git diff --check` passed.
- Final manual reports: `.aidd/reports/evals/eval-live-007-codex-20260708T221353Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.

## Refresh Findings - 2026-07-08T22:13Z

- P1: CLI/live-harness progress remains too quiet during native-provider calls. Stage timings show long `run-stage` intervals, including `research` at 330s, `tasklist` at 306s total across attempts, `implement` at 479s, and `qa` at 472s total across attempts, while the launching terminal had little useful progress feedback.
- P2: Exact next-stage copy is now healthy across the full stage chain. `research`, `plan`, `review-spec`, `tasklist`, `implement`, and `review` all named their immediate canonical next stage, and live stage audits recorded no next-action consistency findings.
- P2: Stale placeholder handling improved. The successful `research` result no longer retained `Stage not run yet`, and repaired `tasklist`/`qa` summaries no longer used generic next-stage wording.
- P2: Terminal Flow Complete UI is healthy on desktop and 390px mobile, including resolved repair cards and next-flow actions. Runtime/log evidence is reachable through Evidence, but the first viewport does not label runtime logs directly.
- P2: `tasklist` and `qa` still required predictable self-repairs for formatting/evidence completeness. The repairs are successful and visible, but the prompts could reduce repeat friction.

## Next UX Plan - 2026-07-08T22:13Z

- Add CLI/live-harness heartbeat output for long native-provider intervals before runtime logs or final artifacts appear.
- Promote a direct runtime-log/evidence affordance into the terminal Flow Complete first viewport.
- Tighten `tasklist` prompt/validator examples for ordered task bullet shape and complete per-task verification notes.
- Tighten QA prompt guidance so ready/proceed decisions cite ignored-residue evidence on the first attempt.

## UX Implementation Slice - 2026-07-08

- Completed the CLI/live-harness heartbeat slice for long public `aidd stage run` commands. The black-box live runner now emits a launching-terminal heartbeat every 30 seconds for active `run-stage` calls.
- Heartbeat content is intentionally factual: active stage label, elapsed time, last observed signal (`stdout`, `stderr`, watched stage files, or process start), signal age, hard timeout, no-progress timeout, and the expected first-attempt `runtime.log` path with present/not-yet-created status.
- The heartbeat writes to the harness process stderr and does not pollute the saved child command stdout/stderr transcript, preserving durable raw-runtime evidence semantics.
- Updated the live quality rubric so future manual UI/UX reviews treat long-stage terminal heartbeat as part of terminal flow visibility.
- Verification: `uv run --extra dev pytest tests/harness/test_live_e2e_black_box.py::test_black_box_command_emits_operator_heartbeat_without_polluting_transcript tests/harness/test_live_e2e_black_box.py::test_black_box_command_no_progress_stops_live_process tests/harness/test_live_e2e_black_box.py::test_black_box_command_no_progress_allows_live_artifact_heartbeats tests/harness/test_live_e2e_black_box.py::test_black_box_live_e2e_records_active_step_while_stage_runs -q`; `uv run --extra dev pytest tests/harness/test_live_e2e_black_box.py::test_black_box_live_e2e_marks_provider_no_progress_as_infra_fail -q`; `uv run --extra dev pytest tests/test_docs_consistency.py -q`; `uv run --extra dev ruff check src/aidd/harness/live_e2e_black_box_orchestration.py tests/harness/test_live_e2e_black_box.py`; `uv run --extra dev python -m mypy src/aidd/harness/live_e2e_black_box_orchestration.py`.

## Next UX Plan - After Heartbeat Slice

- Rerun a medium live E2E flow to verify the heartbeat appears during real native-provider silence and include the observed terminal lines in the next bundle/report.
- Promote a direct runtime-log/evidence affordance into the terminal Flow Complete first viewport.
- Tighten `tasklist` prompt/validator examples for ordered task bullet shape and complete per-task verification notes.
- Tighten QA prompt guidance so ready/proceed decisions cite ignored-residue evidence on the first attempt.

## Refresh Run - 2026-07-08T23:11Z

- `eval-live-007-codex-20260708T231146Z`: terminal execution verdict `pass`.
- Source revision under test: `eb1c3d0bdf9327485880f84b3b2eb8f85d0fcf62`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- Quality gates: `idea`, `research`, `plan`, `review-spec`, `implement`, and `review` chose `continue` with `strong` quality; `tasklist` and `qa` chose `continue` with `acceptable` quality after successful repair.
- Self-repair: `tasklist` repaired missing T7/T8 verification-note coverage on attempt 2; `qa` repaired missing ignored-residue evidence citation on attempt 2.
- Heartbeat evidence: launching-terminal heartbeat appeared across long native-provider intervals for all run-stage commands. The strongest observed transitions were `tasklist` and `qa`, where heartbeat changed from `runtime.log (... not yet created)` to `runtime.log (... present)`.
- Stage timings: run-stage durations included `tasklist` 282s, `implement` 346s, `review` 276s, and `qa` 393s; no timeout or provider no-progress failure occurred.
- Stage-audit consistency: all eight stages recorded empty `consistency_findings`.
- Target implementation quality: review approved the four-file Hono patch; QA reported `ready` / `proceed`; independent focused Vitest rerun passed with 234 tests, `tsc --noEmit` passed, and `git diff --check` was clean.
- Final manual reports: `.aidd/reports/evals/eval-live-007-codex-20260708T231146Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.

## Refresh Findings - 2026-07-08T23:11Z

- P1 resolved for CLI/live-harness progress: real medium live E2E showed heartbeat every 30 seconds during long native-provider silence, including active stage, elapsed time, last signal, timeout budgets, and runtime-log status.
- P2 remains: `tasklist` still needed a repair for complete per-task verification notes, now specifically missing T7/T8 in the first attempt's `Verification notes`.
- P2 remains: `qa` still needed a repair for ignored-residue evidence citation before `ready` / `proceed`.
- P2 remains: terminal Flow Complete first viewport still needs a direct runtime-log/evidence affordance; this rerun did not recapture browser visual evidence.

## Next UX Plan - After 23:11Z Refresh

- Tighten `tasklist` prompt/validator examples so the first attempt includes a separate `Verification notes` entry for every task id, especially command-only tasks such as T7/T8.
- Tighten QA prompt guidance so ready/proceed decisions cite `git status --ignored --short --untracked-files=all` on the first attempt whenever test/type/build checks are cited.
- Promote a direct runtime-log/evidence affordance into the terminal Flow Complete first viewport and recapture desktop/mobile browser evidence.
- Keep the heartbeat behavior as accepted unless a later run shows line length/readability problems in narrower terminals.

## Prompt Repair Prevention Slice - 2026-07-08

- `tasklist` contracts and prompts now state that the dedicated `Verification notes` section must include every task id from `Ordered tasks`, including command-only or verification-only tasks; checks embedded only in `Ordered tasks` are not enough.
- `qa` contracts and prompts now state that ready/proceed-style reports citing test/type/lint/docs/build commands must include post-QA `git status --ignored --short --untracked-files=all` evidence, cite it from `Verification summary` or `Readiness`, and classify ignored residue.
- AIDD-LIVE-007 now treats both repeat repair causes as stage-quality audit defects, keeping the medium live scenario aligned with the observed UX friction.
- Prompt-quality coverage now guards these instructions across stage contracts, document contracts, run prompts, repair prompts, and the live scenario manifest.
- Verification: `uv run --extra dev pytest tests/test_prompt_quality.py -q`; `uv run --extra dev pytest tests/harness/test_scenario_loader_model.py::test_hono_non_error_live_scenario_preserves_public_type_contracts -q`; `uv run --extra dev pytest tests/test_docs_consistency.py -q`; `uv run --extra dev ruff check tests/test_prompt_quality.py`; `git diff --check`.

## Next UX Plan - After Prompt Repair Prevention Slice

- Rerun the medium AIDD-LIVE-007 flow and check whether `tasklist` and `qa` now pass on the first attempt without repair.
- Promote a direct runtime-log/evidence affordance into the terminal Flow Complete first viewport and recapture desktop/mobile browser evidence.
- Expand unhappy-path UX coverage beyond successful repair: provider no-progress, repeated interrupt, missing verification artifacts, and `not-ready` QA terminal handoff.

## Refresh Run - 2026-07-09T00:02Z

- `eval-live-007-codex-20260709T000228Z`: terminal execution verdict `pass`.
- Source revision under test: `62f877ead92f717b79a18b43fbfacb28b1dcc4c6`.
- Stage path: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`.
- Runner repair attempts: `0` across all eight stages; quality remediation cycles: `0`.
- The prompt repair prevention slice was validated live: `tasklist` produced dedicated `Verification notes` coverage for every task id T1 through T7 on the first attempt, and `qa` cited post-QA `git status --ignored --short --untracked-files=all` evidence on the first attempt.
- Quality gates: `idea`, `tasklist`, `review`, and `qa` were strong; `research`, `plan`, `review-spec`, and `implement` were acceptable with risk because the selected Hono patch chose raw non-Error delivery rather than normalization.
- Target verification: focused Vitest passed with 234 tests, `./node_modules/.bin/tsc --noEmit` passed, and `git diff --check` was clean.
- Final manual reports: `.aidd/reports/evals/eval-live-007-codex-20260709T000228Z/flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.

## Refresh Findings - 2026-07-09T00:02Z

- P1 resolved for the immediate repair-friction slice: both previously repeated repair causes disappeared in a fresh medium live run.
- P2: The live flow exposed a selected-task context clarity gap. The scenario manifest has an internal `target_change` that says "Normalize non-Error thrown values at the error boundary," but the stage-visible `selected-task.md` only includes the visible product request and acceptance criteria. The model chose raw runtime value delivery, which is defensible from the visible request but not clearly aligned with the internal target-change wording.
- P2: Browser visual evidence was not recaptured in this iteration. Runner frontend checkpoints passed, but no fresh desktop/mobile Flow Complete screenshots were imported into the bundle.
- P2: Heartbeat remains useful, but several stages still spent multiple minutes with `runtime.log` not yet created. This is understandable now, but final UI should make runtime-log/evidence affordances more direct.

## Next UX Plan - After 2026-07-09 Refresh

- Decide whether authored live tasks should expose `target_change`, `intent`, and `quality_bar` in `context/selected-task.md` when those fields are expected to constrain implementation semantics.
- Promote a direct runtime-log/evidence affordance into the terminal Flow Complete first viewport and recapture desktop/mobile browser evidence.
- Add unhappy-path UX coverage for provider no-progress, repeated interrupt, missing verification artifacts, and `not-ready` QA terminal handoff.
- Keep the tasklist and QA prompt hardening accepted unless another maintained scenario shows a first-attempt repair regression.

## Selected Task Context Clarity Slice - 2026-07-09

- Live workspace bootstrap now keeps `user-request.md` focused on the visible product request while expanding `context/selected-task.md` to include authored task constraints even when `visible_request` exists.
- The stage-visible selected task now includes `summary`, `intent`, `target_change`, `expected_scope`, `quality_bar`, and `size_rationale`, reducing ambiguity when a maintained scenario expects implementation semantics beyond the short visible request.
- Live E2E docs now describe this split explicitly: `visible_request` is the user-facing request, and `selected-task.md` carries authored constraints for downstream stages.
- Focused regression coverage proves a visible-request task preserves the visible request and exposes the authored target change and quality bar in selected-task context without polluting `user-request.md`.
- Verification: `uv run --extra dev pytest tests/harness/test_live_workspace_bootstrap.py -q`; `uv run --extra dev pytest tests/test_docs_consistency.py -q`; `uv run --extra dev ruff check src/aidd/harness/live_workspace_bootstrap.py tests/harness/test_live_workspace_bootstrap.py`; `uv run --extra dev python -m mypy src/aidd/harness/live_workspace_bootstrap.py`; `git diff --check`.

## Next UX Plan - After Selected Task Context Slice

- Rerun or spot-check AIDD-LIVE-007 context bootstrap to confirm `selected-task.md` now exposes the Hono normalization target before model stages run.
- Promote a direct runtime-log/evidence affordance into the terminal Flow Complete first viewport and recapture desktop/mobile visual evidence.
- Add unhappy-path UX coverage for provider no-progress, repeated interrupt, missing verification artifacts, and `not-ready` QA terminal handoff.

## Terminal Evidence First Slice - 2026-07-09

- Flow Complete now promotes terminal evidence before next-flow decisions. The completed-run hero is followed by an `Evidence First` block that prioritizes `runtime_log`, `qa_report`, `validator_report`, and `stage_result` regardless of artifact ordering.
- The global `Run Next Action` strip now exposes first-viewport `Runtime log` and `QA report` shortcut buttons for terminal handoffs. They reuse the existing artifact inspector handler, so operators can inspect raw runtime and QA evidence before choosing `Review final artifacts`, follow-up, clone, archive, or batch actions.
- On 390px mobile terminal handoff screens, `terminal-handoff-mode` now raises the cockpit above the stage rail and disables active-stage autoscroll. This keeps the completed QA handoff and evidence shortcuts visible before navigation lists.
- Browser QA used `/tmp/aidd-ui-evidence-spotlight/.aidd` with a completed `run-ui` fixture served by `aidd ui`. Desktop verification kept `scrollWidth=1280`, showed `Runtime log` / `QA report` shortcuts at the top strip, placed the full evidence block before `Start Next Flow`, and recorded no overflow. Mobile verification kept `scrollWidth=390`, placed the cockpit before the stage rail, and kept both shortcut buttons inside the first viewport. Screenshot evidence: `/tmp/aidd-flow-complete-evidence-desktop.png` and `/tmp/aidd-flow-complete-evidence-mobile.png`.
- Verification: `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py::test_operator_script_modules_own_static_ui_surfaces tests/cli/test_ui_assets_contracts.py::test_operator_flow_complete_static_contract_covers_terminal_handoff_actions tests/cli/test_ui_assets_contracts.py::test_operator_css_keeps_focus_and_screen_reader_contracts -q`; `node --check src/aidd/cli/static/operator-next-flow-actions.js && node --check src/aidd/cli/static/operator-api-state.js && node --check src/aidd/cli/static/operator-shell-rendering.js`; `uv run --extra dev ruff check tests/cli/test_ui_assets_contracts.py`; `git diff --check`.

## Next UX Plan - After Terminal Evidence First Slice

- Add unhappy-path terminal UX coverage for `not-ready` QA handoff, missing verification artifacts, and failed terminal handoffs.
- Exercise provider no-progress and repeated interrupt flows with browser evidence, not only API checkpoints.
- Rerun or spot-check AIDD-LIVE-007 context bootstrap to confirm `selected-task.md` now exposes authored constraints before model stages run.

## Failed Terminal Handoff Slice - 2026-07-09

- Failed or blocked terminal handoffs no longer reuse the success framing. The hero mark now switches from green `OK` to a red/warning `!`, and the copy says that QA did not clear the run, the handoff is blocked, or QA completed with recorded risks.
- Failed/not-ready terminal surfaces now insert a `QA Did Not Clear` blocker spotlight before the evidence and next-flow sections. Risky completed handoffs use `Recorded QA Risks`. The spotlight reuses the existing blocker navigation rows so validation, QA, and risk blockers remain clickable instead of becoming static warning copy.
- Browser QA used `/tmp/aidd-ui-terminal-failed/.aidd` with `qa_stage_status=failed`, `qa_verdict=not-ready`, and `validator_verdict=fail`. Desktop verification confirmed the Work tab shows `Flow Needs Attention`, `not-ready`, `QA Did Not Clear`, the validation blocker before `Evidence First`, and no overflow at `1280px`. Mobile verification at `390px` confirmed the cockpit stays before the stage rail, the failed hero and blocker spotlight are visible in the first viewport, the blocker row fits inside `46..347px`, and `scrollWidth=390`. Screenshot evidence: `/tmp/aidd-terminal-failed-handoff-desktop.png` and `/tmp/aidd-terminal-failed-handoff-mobile.png`.
- Verification: `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py::test_operator_flow_complete_static_contract_covers_terminal_handoff_actions tests/cli/test_ui_assets_contracts.py::test_operator_css_keeps_focus_and_screen_reader_contracts -q`; `node --check src/aidd/cli/static/operator-next-flow-actions.js`; `git diff --check`.

## Next UX Plan - After Failed Terminal Handoff Slice

- Add missing-verification-artifact terminal UX coverage, including how final artifacts, absent evidence, and QA readiness copy behave when expected documents are unavailable.
- Exercise provider no-progress and repeated interrupt flows with browser evidence, not only API checkpoints.
- Rerun or spot-check AIDD-LIVE-007 context bootstrap to confirm `selected-task.md` now exposes authored constraints before model stages run.

## Missing Terminal Evidence Slice - 2026-07-09

- Terminal handoffs now compare available final artifacts with the expected evidence set: `runtime_log`, `qa_report`, `validator_report`, and `stage_result`.
- The `Evidence First` block now shows available artifacts and a `Missing Evidence` warning list when any expected evidence is absent. Each missing row explains the operator value of the absent artifact instead of leaving the user to infer why the list is short.
- The global `Run Next Action` strip now keeps first-viewport missing evidence visible. When `runtime_log` or `qa_report` is absent, it shows compact `Missing Runtime log` / `Missing QA report` badges in the same place where direct evidence shortcuts appear for available artifacts.
- Browser QA used `/tmp/aidd-ui-terminal-missing/.aidd` with a completed QA fixture where `qa-report.md` and the terminal `runtime.log` were removed after fixture creation. Desktop verification kept `scrollWidth=1280`, showed `Missing Runtime log` / `Missing QA report` in the top strip, listed `validator_report` and `stage_result` as available, and rendered two missing rows in `Evidence First`. Mobile verification at `390px` kept both missing badges inside the first viewport, kept missing rows inside `56..337px`, moved the stage rail below the cockpit, and kept `scrollWidth=390`. Screenshot evidence: `/tmp/aidd-terminal-missing-evidence-desktop.png` and `/tmp/aidd-terminal-missing-evidence-mobile.png`.
- Verification: `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py::test_operator_flow_complete_static_contract_covers_terminal_handoff_actions tests/cli/test_ui_assets_contracts.py::test_operator_css_keeps_focus_and_screen_reader_contracts -q`; `node --check src/aidd/cli/static/operator-next-flow-actions.js`; `git diff --check`.

## Live No-Progress Notice Slice - 2026-07-09

- The global live progress strip now makes provider silence explicit instead of hiding it inside the runtime-output metric. It renders a blue notice while waiting for the first runtime output, an amber notice when `silence_warning` is true, and an amber cancel-pending notice when `cancel_state` / `cancel_requested` indicates shutdown is in progress.
- The notices keep the operator action local to the strip: inspect `Open live logs`, wait for fresh output, or use the existing cancel action if the runtime is no longer making progress. Cancelling now states that the UI is waiting for final shutdown evidence instead of looking like a completed stop.
- Browser QA used `/tmp/aidd-live-progress-qa.html` served from localhost with production `operator.css` from the running UI. Desktop verification at `1280x720` measured a `1150px` live strip, `1128px` notices, no notice or strip overflow, and no browser console errors. Mobile verification at `390px` measured `336px` strips and `314px` notices, no overflow, and no browser console errors. Screenshot evidence: `/tmp/aidd-live-progress-no-output-desktop-1280.jpg` and `/tmp/aidd-live-progress-no-output-mobile.png`.
- Verification: `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py -q`; `uv run --extra dev pytest tests/cli/test_ui.py::test_ui_cancel_terminates_generic_cli_runtime_and_records_evidence -q` (passed on retry after the first run timed out waiting for the existing long-running runtime fixture to emit its start line before cancellation).

## Runtime/System Output Distinction Slice - 2026-07-09

- UI job status now keeps `last_output_*` for any live log entry while adding `runtime_output_*` and `runtime_log_chunk_count` for stdout/stderr provider evidence. System control messages such as `AIDD UI ... job started` and `[ui] cancel requested` no longer make the operator UI look like the runtime has produced useful output.
- The live progress strip and Active Run panel now render runtime-output freshness from the runtime-specific fields and show live log counts as `runtime / total` when system chunks are present. A quiet runtime with only system chunks now reads `No runtime output captured yet` and `0 runtime / 3 total` instead of being treated as fresh runtime activity.
- Browser QA used `/tmp/aidd-runtime-silence-ui` with a real UI-started `generic-cli` command that sleeps without stdout/stderr. Desktop verification at `1280x720` showed `0 runtime / 3 total`, kept the first-output notice visible, had `scrollWidth=1280`, and had no console errors. Mobile verification started the job from a `390x844` viewport, kept the live strip and first-output notice inside the first viewport, kept `scrollWidth=390`, and had no console errors. Screenshot evidence: `/tmp/aidd-runtime-output-distinction-desktop.jpg` and `/tmp/aidd-runtime-output-distinction-mobile.jpg`.
- Verification: `node --check src/aidd/cli/static/operator-api-state.js && node --check src/aidd/cli/static/operator-next-flow-actions.js && node --check src/aidd/cli/static/operator-control-center.js`; `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py::test_operator_control_center_asset_surfaces_running_stage_progress tests/cli/test_ui_assets_contracts.py::test_operator_global_next_action_surfaces_live_job_progress -q`; `uv run --extra dev pytest tests/cli/test_ui.py::test_ui_stage_run_endpoint_delegates_selected_stage_and_streams_live_logs tests/cli/test_ui.py::test_ui_live_job_status_distinguishes_system_logs_from_runtime_output -q`.

## Live Job Reload Recovery Slice - 2026-07-09

- `/api/dashboard` now exposes the latest non-terminal UI job as `active_job`, and the browser boot path restores `activeJobId`, the live log cursor, polling, the live progress strip, and cancel controls after a page reload.
- Reloading during a quiet runtime now stays in `live-job-mode` instead of degrading to the external-running-stage strip, preserving `No runtime output captured yet`, `0 runtime / 3 total`, the first-output notice, and the live cancel action.
- Browser QA used `/tmp/aidd-reload-recovery-ui` with a real UI-started quiet `generic-cli` runtime. Desktop reload verification at `1280x720` had `hasLive=true`, `hasExternal=false`, live cancel controls, `scrollWidth=1280`, and no console errors. Mobile reload verification at `390x844` had `hasLiveText=true`, `hasExternalText=false`, two `Cancel job` controls, `scrollWidth=390`, and no console errors. Screenshot evidence: `/tmp/aidd-live-job-reload-recovery-desktop.jpg` and `/tmp/aidd-live-job-reload-recovery-mobile.jpg`.
- Verification: `node --check src/aidd/cli/static/operator-api-state.js`; `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py -q`; `uv run --extra dev pytest tests/cli/test_ui.py::test_ui_stage_run_endpoint_delegates_selected_stage_and_streams_live_logs -q`; `uv run --extra dev ruff check src/aidd/cli/ui.py tests/cli/test_ui.py`; `git diff --check`; plus Chrome mobile reload QA against `job-9988440532d348abbbc5d412e0e16c6a`, cancelled cleanly with exit code `130`.

## Repeated Interrupt Evidence Slice - 2026-07-09

- Live E2E interruption recording now defers additional `SIGINT`/`SIGTERM` signals while it preserves resumable evidence. A second interrupt during `flow-steps.json`, `flow-state.json`, or `flow-report.md` recording no longer skips the `interrupted-resumable` evidence step.
- `flow-report.md` now uses the same atomic write helper as JSON evidence, reducing the chance of a partially written operator report after an interrupt or process-level disruption.
- This targets the earlier P1 repeated-interrupt finding from `eval-live-007-codex-20260708T190645Z`: the operator should be able to resume from a durable bundle after interruption instead of debugging a half-recorded eval state.
- Verification: `uv run --extra dev pytest tests/harness/test_live_e2e_black_box.py::test_black_box_live_e2e_interruption_rewrites_flow_report_status tests/harness/test_live_e2e_black_box.py::test_black_box_live_e2e_defers_repeated_interrupt_while_recording_evidence -q`; `uv run --extra dev ruff check src/aidd/harness/live_e2e_black_box_orchestration.py tests/harness/test_live_e2e_black_box.py`; `uv run --extra dev python -m mypy src/aidd/harness/live_e2e_black_box_orchestration.py`; `git diff --check`.

## Provider No-Progress Frontend Evidence Slice - 2026-07-09

- Live E2E no-progress runs no longer skip post-stage frontend checkpoint evidence after the provider process is stopped and the stage metadata is reconciled to `failed`.
- The bundle now records `frontend-checkpoints.json` and `frontend-checkpoints.md` for provider no-progress failures, proving that the loopback operator UI/API can still expose work item, run, failed stage, next action, runtime logs, and artifact surfaces while the execution verdict remains `infra-fail`.
- Running-stage checkpoints may still be skipped when the active stage disappears before probes finish, and hard command timeouts still skip post-stage frontend probing. The new behavior is scoped to provider no-progress because the process has been explicitly stopped and the failed stage state is inspectable.
- Verification: `uv run --extra dev pytest tests/harness/test_live_e2e_black_box.py::test_black_box_command_no_progress_stops_live_process tests/harness/test_live_e2e_black_box.py::test_black_box_command_no_progress_allows_live_artifact_heartbeats tests/harness/test_live_e2e_black_box.py::test_black_box_live_e2e_marks_provider_no_progress_as_infra_fail -q`; `uv run --extra dev ruff check src/aidd/harness/live_e2e_black_box_orchestration.py tests/harness/test_live_e2e_black_box.py`; `uv run --extra dev python -m mypy src/aidd/harness/live_e2e_black_box_orchestration.py`; `git diff --check`.

## AIDD-LIVE-007 Bootstrap Spot-check Slice - 2026-07-09

- The selected-task context clarity fix is now covered against the maintained medium `AIDD-LIVE-007` manifest, not only a synthetic authored task fixture.
- The regression proves live workspace bootstrap writes Hono's visible request to `user-request.md` while exposing the authored `target_change` and `quality_bar` in `context/selected-task.md` before any model stage runs.
- This closes the P2 ambiguity from `eval-live-007-codex-20260709T000228Z`: downstream stages now receive the non-Error normalization target and public type compatibility quality bar as first-class context instead of relying on the shorter visible request alone.
- Verification: `uv run --extra dev pytest tests/harness/test_live_workspace_bootstrap.py -q`; `uv run --extra dev ruff check tests/harness/test_live_workspace_bootstrap.py`.

## Provider No-Progress Manual Evidence Import Slice - 2026-07-09

- Provider no-progress `infra-fail` bundles now have regression coverage for imported manual browser evidence, not only API checkpoint evidence.
- The no-progress harness regression passes `manual_frontend_evidence`, verifies `frontend-checkpoints.json` records it as non-gating imported evidence, verifies `frontend-checkpoints.md` links `browser-notes.md`, and confirms `flow-state.json` / `harness-metadata.json` preserve the evidence source and bundle path.
- This protects the next real-provider/browser exercise from losing operator screenshots or notes when the run stops as `provider-no-progress before completed stage artifact`.
- Verification: `uv run --extra dev pytest tests/harness/test_live_e2e_black_box.py::test_black_box_live_e2e_marks_provider_no_progress_as_infra_fail -q`; `uv run --extra dev ruff check tests/harness/test_live_e2e_black_box.py`.

## Next UX Plan - After Provider No-Progress Manual Evidence Import

- Exercise real provider no-progress with manual browser evidence now that no-progress bundles retain frontend checkpoint evidence and imported browser notes/screenshots.
- Run another medium live E2E pass after the unhappy-path UI slices if provider time budget allows, importing the newest browser evidence into the live bundle.
