# Operator UI Local-Project E2E Lane

This lane proves the local operator UI path. It is separate from the public-repository
live E2E catalog.

## Purpose

Operator UI E2E answers one question:

> Can an operator install or run AIDD locally, enter a local project root, open `aidd ui`,
> and inspect or continue a governed `.aidd/` work item without moving workflow state
> outside that project?

This lane does not use GitHub issue intake. Public GitHub repositories remain inputs for
manual live E2E evals only.

Authenticated native-provider UI smokes build on this lane and are documented in
[`Real-Provider UI E2E Lane`](./real-provider-ui-e2e.md). They remain manual,
Codex-first, and outside CI/CD.

## Supported Operator Path

The local-project UI lane follows the product operator path:

1. Install or run AIDD locally.
2. Change into the target local project root.
3. Run `aidd doctor` with the intended config.
4. Start `aidd ui` without `--work-item` for clean setup mode, validate the project
   root, create or resume a work item, seed the request, inspect runner readiness, and
   select a runtime explicitly.
5. Use **Run workflow** for full progression or **Run selected stage** for a bounded
   active-stage run from the command center.
6. For scripted setup, `aidd init --work-item <id> --request "<task>" --root .aidd`
   remains supported before opening `aidd ui --work-item <id>`.
7. Run a single selected stage through the UI or `aidd stage run <stage>` when the
   operator needs a bounded retry.
8. Request a stage-scoped correction through the UI `Request change` panel or
   `aidd stage interact <stage>` when the operator needs a documented intervention.
9. Inspect live UI job logs, persisted logs, and rendered artifacts through the UI or
   `aidd run logs` / `aidd run artifacts`.
10. Keep `.aidd/` inside the local project root.

`aidd init --github-issue <url>` is out of product scope for this lane.

## Scope

The maintained operator UI lane covers:

- page load for the local operator-console shell with top status bar, stage rail,
  stage cockpit, and the four top-level modes: Work, Recovery, Evidence, and History;
- recovery-first layout for blocked-question, failed-validation, intervention-review,
  and runtime-log states, with one visible primary recovery action and raw
  logs/evidence/activity demoted behind Evidence or History;
- dashboard read-model payload shape through `/api/dashboard`, including selected
  stage, next action, blockers, evidence refs, recent activity, and recent artifacts;
- global next-action classification that routes operators to blocked questions or
  validation evidence even when a different stage is currently selected;
- completed-run Flow Complete handoff state after terminal `qa`, including final QA
  artifacts, blockers, evidence counts, repair counts, approval counts, answered
  questions, and recommended next-flow actions;
- Start Next Flow source selection, follow-up draft definition, launch preflight, and
  archive decision surfaces without continuing or mutating the completed source run;
- Run History / Lineage visibility for source run, current run, baseline, child work
  item candidates, archive state, linked artifacts, and run actions;
- workflow-run request delegation through the same core service used by the CLI;
- selected-stage run request delegation through the same stage execution path used by
  `aidd stage run`;
- selected-stage intervention request delegation through `/api/stage/interact`, with
  request text and current-stage target documents passed to the CLI-equivalent
  intervention path;
- explicit runtime selection before workflow-run or stage-run request dispatch;
- blocking answer persistence to `answers.md` with `resolved`, `partial`, and
  `deferred` resolution states;
- editable latest-answer behavior for previously saved answers, including resolved
  answers that are corrected or downgraded back to partial/deferred before resume;
- answer-and-resume behavior that persists the selected answer and resumes the
  selected stage with the current run id only after blocking questions are resolved;
- structured live runtime chunk rendering through UI job polling, with stdout,
  stderr, system filters and a raw toggle;
- persisted `runtime.log` fallback rendering from attempt artifacts;
- normalized operator activity from run manifests, stage metadata, repair history,
  durable `operator.request.created` events, live job chunks, and `events.jsonl`
  from all attempted stages when present;
- artifact index rendering for stage documents and logs, including read-only document
  preview/source rendering, with Recent Artifacts and Evidence Refs navigating into
  inspection views instead of only opening local folders, and compact path rendering
  for dense evidence lanes;
- validation visibility through validator pass/fail counts, validator report paths, and
  the primary failing validator finding directly in the recovery / next-action surface;
- repair status correctness where `repair-available` and `repair-exhausted` come from
  backend diagnostics and are not inferred from the existence of repair history alone;
- repair-history visibility through `repair-brief.md` paths;
- operator request visibility through Evidence Refs and Recent Artifacts;
- declared project-set roots through `project-set.md` artifact visibility;
- loopback-only local convenience actions for opening allowlisted `.aidd/` folders
  and stopping the UI server without claiming runtime job cancellation.

The lane is intentionally deterministic and service-level. It does not add a new harness
scenario class, and it does not start real provider runtimes in CI.

## Deterministic Coverage

Current deterministic coverage lives in:

- `tests/cli/test_ui.py::test_operator_ui_local_project_e2e_lane_covers_core_operator_flow`
- `tests/cli/test_ui.py::test_ui_dashboard_endpoint_exposes_operator_console_payload`
- `tests/cli/test_ui.py::test_ui_open_folder_endpoint_allows_workspace_stage_and_artifact_paths`
- `tests/cli/test_ui.py::test_ui_server_stop_endpoint_is_local_server_action_only`
- `tests/cli/test_ui.py::test_operator_ui_artifacts_include_declared_project_set_roots`
- `tests/cli/test_ui.py::test_ui_stage_run_endpoint_delegates_selected_stage_and_streams_live_logs`
- `tests/cli/test_ui.py::test_ui_stage_interact_endpoint_delegates_request_and_streams_logs`
- `tests/cli/test_ui.py::test_ui_artifact_document_endpoint_reads_known_document_content`
- `tests/cli/test_ui.py::test_ui_completed_run_next_action_service_regression_sequence`
- `tests/cli/test_ui.py::test_operator_ui_local_project_terminal_fixture_creates_follow_up_without_runtime`
- `tests/core/test_operator_frontend.py::test_operator_terminal_handoff_next_action_contract_survives_archive_decision`
- `tests/cli/test_ui_assets_contracts.py::test_operator_flow_complete_static_contract_covers_terminal_handoff_actions`
- `tests/cli/test_ui_assets_contracts.py::test_operator_next_flow_wizard_static_contract_covers_controls_and_preflight`
- `tests/cli/test_ui_assets_contracts.py::test_operator_run_history_static_contract_covers_lineage_and_archive_labels`
- `tests/core/test_operator_frontend.py`

These tests exercise `OperatorUiService` and the runtime-agnostic operator read/write
services directly. Workflow-run, stage-run, and stage-intervention endpoints are
tested through injected execution seams so they prove request shape, UI/Core
delegation, and live log polling without invoking real runtimes.

## Completed-Run Required Checks

A local-project UI E2E pass is incomplete unless it records completed-flow evidence.
The evidence may come from an installed local smoke, a deterministic seeded workspace,
or the service-level UI regression path, but it must stay inside the local project and
must not use public-repository live E2E as a substitute.

Required completed-flow checks:

- reach or seed a terminal `qa` run and verify **Flow Complete** appears in the
  command center;
- inspect final QA artifacts from the handoff and verify they remain readable after
  refresh;
- open **Start Next Flow** and verify source findings include QA findings, review notes,
  failed evidence, and manual request groups;
- create or preview a follow-up draft with acceptance criteria, required evidence,
  inherited context toggles, and first-stage input preview;
- run launch preflight with an explicit runtime and record pass, warning, or blocking
  status plus resolved baseline;
- inspect Run History / Lineage for source run, current run, baseline, child work item
  candidates, linked artifacts, and run actions;
- record the Archive Run decision path and verify archived runs remain readable through
  dashboard, history, and artifact inspection.

## Manual Installed Smoke

A manual installed UI smoke should use a disposable local fixture project:

1. Install or run the AIDD artifact under test locally.
2. Change into the local fixture project root.
3. Run `aidd doctor` with the fixture config.
4. Start `aidd ui --config <fixture-config> --host 127.0.0.1 --port <port>` without
   `--work-item`.
5. In setup mode, validate the absolute fixture project root, confirm the runner picker
   visually distinguishes the deterministic baseline from native provider runners,
   select the deterministic runtime explicitly, then create a work item and request
   through the onboarding form. Verify the create action becomes enabled even when
   the runtime was selected before the work item id and request text were entered.
6. Confirm `.aidd/workitems/<id>/context/user-request.md` is created inside the fixture
   project without running `aidd init`.
7. From the command center, use **Run selected stage** for `idea`, wait until
   `/api/jobs/<job_id>` reports `completed`, and verify the stage rail reports
   `idea` as `succeeded`.
8. Run `research` through **Run selected stage** or the next-action continue path, wait
   until the UI job reports `completed`, and verify the stage rail reports `research`
   as `succeeded`.
9. Verify the page loads, the dashboard shell renders the four-mode operator navigation,
   runtime selection is required before `/api/workflow/run` and `/api/stage/run`
   dispatch, blocking answers persist, answer-and-resume keeps the same run id,
   `Request change -> Submit & run` creates a durable operator request and switches
   to live logs, persisted logs remain readable after completion, Markdown artifacts
   render as preview/source, validation state is visible, repair and operator-request
   evidence is linked, and recent activity/artifact rows remain reachable through
   Evidence or History after refresh.
10. For a blocked or failed `plan` stage, submit a request such as
   `Add migration rollback risks`, verify `/api/stage/interact` returns a job id,
   the Logs tab stays visible while polling `/api/jobs/<id>/logs`, and the latest
   request appears as `operator.request.created` in Activity plus an Evidence Ref.
11. For completed-run handoff proof, use a terminal `qa` run or deterministic seeded
   terminal workspace, open Flow Complete, start the follow-up wizard, create or preview
   a follow-up draft, run launch preflight, inspect Run History / Lineage, and record
   the Archive Run decision path.
12. Remove the disposable fixture project. Do not commit `.aidd/` artifacts.

Manual smoke evidence is recorded in `docs/backlog/roadmap.md`; generated `.aidd/`
state stays local to the fixture project.

## Completed-Run Manual Smoke Evidence Template

When recording completed-run local UI smoke evidence in roadmap notes, include all of
these fields:

- Run id: `<terminal-run-id>`
- Source work item: `<source-work-item-id>`
- Child work item: `<created-or-previewed-follow-up-id, or none>`
- Browser: `<browser name and version>`
- Viewport: `<desktop/tablet/mobile dimensions>`
- Initial scroll position: `<x, y>`
- Primary-action bounds: `<x, y, width, height; fully in first viewport: yes | no>`
- Header footprint: `<height in px>`
- Smallest touch target: `<width x height in px; control name>`
- Text contrast: `<minimum ratio; foreground/background pair>`
- Control/focus contrast: `<minimum ratio; control/focus indicator>`
- Focus order: `<ordered primary controls; first unexpected stop or none>`
- Overflow: `<none | axis, element, measured overflow>`
- Clipping: `<none | element and clipped content>`
- Overlap: `<none | overlapping elements and bounds>`
- Scroll ownership: `<page | named bounded region; nested-scroll issue or none>`
- Runtime id: `<runtime selected in the UI>`
- Flow Complete status: `<completed | completed-with-warning | failed | blocked>`
- Start Next Flow result: `<source findings | follow-up draft | preflight status>`
- Run History / Lineage result: `<source/current/child lineage observed>`
- Archive decision: `<archived | intentionally not archived>`
- Blockers: `<none, provider unavailable, missing fixture, manual operator blocker>`
- Cleanup: `<fixture project removed | .aidd removed | retained outside git with reason>`

Rendered evidence passes only when the mobile header is at most `80 px`, every touch target
is at least `44x44 px`, body text contrast is at least `4.5:1`, control boundaries and focus
indicators are at least `3:1`, the primary decision is fully visible in the initial viewport,
and there is no page-level horizontal overflow, clipped primary label, or control overlap.
The evidence must identify the owner of every intentional nested scroll region.

For each observed operator journey, also record:

- Completion: `<completed | not completed>`
- Elapsed time: `<duration from entry to durable outcome or stop>`
- Wrong actions: `<count and first wrong action>`
- Assistance: `<none | type of assistance>`
- Operator confidence: `<1-5>`
- First decisive confusion: `<first confusion or none>`

These human timing and confidence fields are evidence, not a release threshold. The five-session
release bar remains owned by `W36-E7-S3`.

Cleanup rules:

- keep generated `.aidd/` state inside the disposable local fixture project;
- do not commit `.aidd/`, runtime logs, prompts, or generated child work items unless a
  separate repository policy explicitly allows it;
- if evidence must be retained, move it to a documented external evidence bundle and
  record only the non-sensitive run id, work item ids, runtime id, viewport, browser,
  and blocker summary in roadmap notes;
- if provider credentials or runtime binaries are unavailable, record the blocker
  instead of replacing the local-project smoke with public-repository live E2E.

## Canonical Operator State and Route Matrix

The local UI uses logical route intents rather than treating every recovery panel as a
destination. The only route intents in this contract are `setup`, `inbox`, `studio`, and
`history`. Recovery is a Studio context. The canonical query codec uses `mode=inbox`,
`mode=studio`, or `mode=history`, followed in stable order by the optional keys
`work_item`, `run_id`, `stage`, `attempt`, `task_attempt`, and `artifact`. Guided Setup is
server-owned state reached before a valid project/work-item context; it does not invent a
fourth persisted browser mode. `artifact` stores a bounded artifact/document key, never an
arbitrary path.

Writers emit only that canonical form. Readers temporarily accept legacy `tab` and `key`
aliases, report the legacy source, and normalize them without mutation. Invalid identifiers,
unknown stages, path-like artifact values, conflicting attempt/task-attempt detail, and stale
known work-item/run ids are dropped with stable warnings. History without a valid run falls
back to Studio when the work item survives and otherwise to Inbox.

Canonical context keys are `project`, `work_item`, `run`, `stage`, `document`, `attempt`,
`artifact`, `recovery_target`, and `history_frame`. A route uses only the keys that identify
durable objects needed by its decision surface.

| Operator state | Route intent | Required context keys | Primary decision surface |
| --- | --- | --- | --- |
| Guided Setup | `setup` | `project` when selected | Validate project, then create or resume a work item. |
| Inbox | `inbox` | `project` | Select the highest-priority durable decision or ready work item. |
| Active Studio | `studio` | `project`, `work_item`, `run`, `stage`, `document` when available | Observe the active attempt or perform the one eligible stage/task action. |
| Reconnecting Studio | `studio` | `project`, `work_item`, `run`, `stage`, `attempt` when available | Reconnect while preserving the durable run and live-log cursor; do not infer termination. |
| Question Recovery | `studio` | `project`, `work_item`, `run`, `stage`, `recovery_target` | Answer the blocking question through the canonical answer service. |
| Approval Recovery | `studio` | `project`, `work_item`, `run`, `stage`, `attempt`, `recovery_target` | Resolve the durable approval request; the server-side winner is authoritative. |
| Validation Recovery | `studio` | `project`, `work_item`, `run`, `stage`, `document`, `recovery_target` | Run eligible repair or request a scoped change while keeping findings visible. |
| Quality Gate | `studio` | `project`, `work_item`, `run`, `stage`, `document`, `artifact` when cited | Decide from Review or QA evidence without bypassing progression guards. |
| Flow Complete | `studio` | `project`, `work_item`, `run`, `stage`, `document` | Choose the recommended next-flow action while the completed run remains immutable. |
| History | `history` | `project`, `work_item`, `run`, `history_frame`; optional `artifact` | Inspect a retained frame, lineage, comparison, logs, or artifacts without mutation. |

Context restoration is fail-closed and non-mutating. If a selected document, attempt,
artifact, recovery target, or history frame is stale, the UI falls back to the nearest valid
Studio context for the same run. If the run or work item is missing, it falls back to Inbox;
if the project itself is not valid, it falls back to Guided Setup. A fallback reports which
context was unavailable and never creates, resumes, repairs, archives, or launches work.

## Manual Browser Checklist

Run these checks in a real browser against the local URL printed by `aidd ui`. Use a
disposable `.aidd/` workspace and record the AIDD version, runtime id, browser, viewport,
and any blockers in roadmap evidence.

Manual provider evidence uses this checklist plus the Codex-first real-provider lane. The
provider-free executable browser lane follows
[`Browser Testing Policy`](../architecture/browser-testing.md): Python Playwright with one
Chromium target, development-only dependencies, and no Node/Vite product runtime. Capture
manual screenshots and API snapshots outside the repository unless they are deliberately
curated as docs assets.

### Dashboard Shell

- First launch shows the loading state before `/api/dashboard` resolves.
- Project Home loads from `/api/project-home` and shows selected project root, `.aidd`
  root, discovered work items, latest run, stage progress, blockers, terminal state, and
  project-set roots before the operator enters stage internals.
- Work Item Board cards can resume a work item through the standard setup/resume path
  without creating duplicate workspace state.
- No-run state explains the first action and exposes runtime-gated `Run workflow` and
  `Run selected stage` actions after a runtime is selected.
- The primary run-global Next Action strip appears above the selected-stage workbench and
  shows runnable copy when a runtime is already selected and ready.
- Work item, run chip, runtime readiness, stage rail, stage cockpit, right sidebar,
  Activity / Events, and Recent artifacts are visible after refresh.
- The active stage is marked in the rail and remains visible after selecting another
  stage.

### Cockpit Tabs

- Overview, Questions, Validation, Artifacts, Recovery, Logs, Approvals, and Request
  change tabs switch content without losing the selected stage.
- Implement Review, Review Findings, and QA Verdict tabs appear only when the selected
  stage or available run evidence makes them relevant.
- Tab semantics expose the selected tab and the cockpit panel remains keyboard-focusable.
- Quick links route to Project Home, Logs, Artifacts, Validation, and Questions
  consistently.

### Logs

- A running workflow, stage run, or intervention shows live stdout/stderr/system chunks.
- Cancelled or completed jobs keep their live log chunks visible.
- Saved `runtime.log` loads after completion and shows a truncation notice when bounded.
- Summary, Timeline, and Raw Runtime Log views remain switchable for live and saved logs.
- Raw mode and stdout/stderr/system filters do not hide the truncation notice.

### Artifacts

- Artifact list renders document and log artifacts for the selected stage.
- Stage Document Workbench groups artifacts by canonical stage documents, runtime inputs,
  validation evidence, runtime evidence, project evidence, and lineage evidence.
- The Artifacts tab opens with the Stage Document Workbench first; the evidence graph and
  artifact table stay in a secondary drill-down below it.
- Markdown preview and Source mode load through `/api/artifacts/document`.
- Preview, Source, and Diff modes remain available from known artifact keys only.
- Large artifacts show byte-range truncation states and keep Open folder available for
  full-file inspection.
- Evidence Refs and Recent Artifacts navigate into the artifact inspection view.

### Diagnostics / Recovery

- The right rail shows Recovery Assistant counts for questions, failures, and suggestions.
- First failure summarizes runtime exit/provider/timeout, validation, blocking questions,
  repair exhaustion, or stopped-stage evidence before raw log inspection.
- Validation recovery shows the primary validator finding with duplicate occurrence count
  when applicable and an operator hint such as the command/check evidence required for
  `SEM-UNVERIFIABLE-CHECK-CLAIM`.
- When repair is available, **Run Repair** is the primary recovery action; when repair is
  exhausted, **Request Change** is the primary recovery action and raw logs/evidence stay
  reachable as secondary drill-downs.
- Recovery cards route to Questions, Validation, Request change, Logs, Review Findings,
  or QA Verdict while preserving runtime and stage eligibility gates.

### Questions

- Blocking questions appear in Overview and Questions.
- Saving a resolved answer writes `answers.md`, keeps the latest answer editable, and
  shows the saved answer text in the resolved question card.
- Partial or deferred answers remain non-resolved and keep blocking policy visible.
- Answer & resume uses the selected runtime and current run id.

### Request Change / Intervention

- Request change shows current-stage target document checkboxes when available.
- Submit & run creates an operator request artifact, switches to Logs, and streams the
  intervention job.
- Activity and Evidence Refs show `operator.request.created` after refresh.
- Validation and repair evidence remain inspectable after the intervention attempt.

### Wave 29 Operator Control States

- Onboarding shows project validation, work-item creation, runner cards with a visible
  deterministic-baseline cue, recent projects, and project-set validation without
  overlapping controls.
- Active Run shows runner, stage, run id, attempt, elapsed time, last output, status,
  cancel, and link to logs during long jobs.
- Timeline shows concrete milestones without fake progress and silence warnings clear
  after new runtime output.
- Implement Review shows source diff, untracked files, `.aidd` artifacts separately,
  claim-to-evidence warnings, and selected file diff.
- Review Findings shows approval status, selectable findings, evidence, and remediation
  action.
- QA Verdict shows quality verdict, residual risks, known issues, and remediation or
  follow-up actions.
- Remediation shows selected review/QA items sent back to `implement`, stale downstream
  badges for `review`/`qa`, and explicit rerun of `review -> qa`.

### Flow Complete Handoff

- A terminal `qa` run switches the command center from active-stage operation to
  **Flow Complete** without hiding stage rail, Activity / Events, or Recent artifacts.
- The handoff summary shows final QA status, runtime id, final artifacts, open blockers,
  evidence refs, repair counts, approval counts, and answered-question counts.
- Final artifacts open in the Artifacts view and remain readable in Preview and Source
  mode after refresh.
- The **Start Next Flow** action band shows Create New Work Item, Start Follow-up Flow,
  Clone This Flow, Run Eval / Scenario Batch, and Archive Run.
- The action band leads with a dedicated recommended next-decision summary, including
  the reason for choosing Create New Work Item or Start Follow-up Flow, before showing
  the full action grid.
- Recommended next action badges match final QA status: completed runs without blockers
  recommend new work, while failed or blocked handoffs recommend follow-up work.
- Choosing Archive Run first opens a confirmation state with a reason preview; confirming
  records the local archive decision and leaves final QA artifacts plus run-history
  inspection available.

### Start Next Flow Wizard

- Start Follow-up Flow opens the source-finding step and groups QA findings, review
  notes, failed evidence, and manual request options.
- Clean completed runs keep Create New Work Item as the recommended next action; the
  source-finding step shows `qa_report` as the primary optional follow-up source and
  collapses supporting QA artifacts until the operator needs them.
- Source-finding checkboxes can be toggled with pointer and keyboard input; Continue
  stays disabled until at least one source is selected.
- The follow-up work item definition step shows editable title, generated acceptance
  criteria, required evidence, inherited context toggles, and first-stage input preview.
- Back to sources returns to the source-finding step without losing selected sources.
- Continue to preflight shows launch preflight status, audit preview, resolved baseline,
  source artifact links, and a disabled Launch Flow Now button when preflight blocks.
- The wizard close/back controls return to the Flow Complete handoff without mutating
  the completed source run.

### Run History / Lineage

- Run History shows parent/source run, current run, baseline, child work item candidates,
  archive status, and linked artifacts.
- Parent, current, and child lineage rows expose source run ids and work item ids without
  truncating the information needed for audit.
- Run actions in history match the Flow Complete action set and keep disabled states
  visible when an action is not launchable.
- Archived runs show the archive timestamp/reason while keeping linked artifacts and
  final handoff details inspectable.
- Refreshing the browser preserves selected run lineage and does not create child work
  items unless the operator explicitly launches a new flow.

### Viewports

- Desktop width shows stage rail, cockpit, right sidebar, and bottom dock together.
- Desktop completed-flow view keeps Flow Complete, Start Next Flow, final artifacts,
  and run-history lineage visible without overlapping panels.
- Tablet width keeps the right sidebar below the cockpit without overlapping content.
- Tablet completed-flow view keeps the wizard action row, source-finding groups, and
  launch preflight cards readable after wrapping.
- Mobile width turns the stage rail into horizontal navigation, auto-scrolls the active
  stage into view on load and stage switch, and preserves readable tab/action buttons.
- Mobile and tablet widths keep order as Next Action, selected-stage/document workbench,
  diagnostics/recovery, logs/evidence, and secondary history surfaces.
- Mobile completed-flow view keeps Flow Complete actions, wizard controls, lineage
  nodes, and artifact rows reachable without horizontal page scrolling.
- Keyboard focus is visible on runtime select, stage cards, cockpit tabs, action buttons,
  artifact rows, textareas, and source/preview controls.
- Keyboard-only traversal reaches Start Next Flow cards, source-finding checkboxes,
  follow-up fields, inherited context toggles, preflight back/launch buttons, Run
  History actions, and Archive Run.

## Brokered Approval Proof

For brokered runtime approval proof, keep the project disposable and run the stage
through the UI surface rather than non-TTY CLI execution:

1. Configure the selected runtime with `permission_policy = "brokered"`,
   `interaction_mode = "live"`, and `auto_approval_preset = "broad"`.
2. Start `aidd ui --work-item <id> --root .aidd --host 127.0.0.1 --port <port>`.
3. Dispatch `/api/stage/run` with an explicit runtime and run id.
4. Wait for `waiting-for-operator`, inspect
   `/api/jobs/<id>/operator-requests`, and post a decision to
   `/api/jobs/<id>/operator-requests/<request_id>/decision`.
5. Confirm the job resumes to `running` or `completed` and the attempt contains
   `operator-requests.jsonl`, `operator-decisions.jsonl`, and runtime logs.

## Source-Install Fixture Smoke

`harness/scenarios/smoke/installed-local-project-fixture.yaml` records the
source-install smoke path for local projects. It uses the existing
`harness/fixtures/minimal-python` fixture as the target project and keeps the
execution cwd as that fixture root.

The scenario uses `uv tool run --from /path/to/ai_driven_dev_v2 aidd` to model
installing or running AIDD from repository source. Operators replace
`/path/to/ai_driven_dev_v2` with the source checkout under test. The target
project remains the local fixture; public GitHub repositories and GitHub issue
URLs are not inputs.

The smoke path covers:

- `aidd doctor` against the fixture config;
- `aidd init --work-item <id> --request ... --root .aidd`;
- a bounded `aidd run` from `idea` to `plan` with `generic-cli`;
- `aidd run show`, `aidd run logs`, and `aidd run artifacts`;
- standard `questions.md` / `answers.md` inspection through `aidd stage questions`;
- optional `aidd stage interact <stage>` intervention smoke after a stage attempt,
  preserving the generated `operator-requests/request-0001.md` as evidence;
- `.aidd/` rooted inside the local fixture project.

## Out Of Scope

- `aidd init --github-issue <url>` is not part of this lane.
- Public-repository authored task selection belongs to live E2E manifests under
  `harness/scenarios/live/`.
- Provider readiness panels are covered separately by the runtime readiness slice.
