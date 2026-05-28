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

## Supported Operator Path

The local-project UI lane follows the product operator path:

1. Install or run AIDD locally.
2. Change into the target local project root.
3. Run `aidd doctor` with the intended config.
4. Run `aidd init --work-item <id> --request "<task>" --root .aidd`.
5. Run the workflow through `aidd run --runtime <runtime>` or continue through `aidd ui`.
6. Run a single selected stage through the UI or `aidd stage run <stage>` when the
   operator needs a bounded retry.
7. Request a stage-scoped correction through the UI `Request change` panel or
   `aidd stage interact <stage>` when the operator needs a documented intervention.
8. Inspect live UI job logs, persisted logs, and rendered artifacts through the UI or
   `aidd run logs` / `aidd run artifacts`.
9. Keep `.aidd/` inside the local project root.

`aidd init --github-issue <url>` is out of product scope for this lane.

## Scope

The maintained operator UI lane covers:

- page load for the local operator-console shell with top status bar, stage rail,
  stage cockpit, right sidebar, and bottom activity/artifact dock;
- dashboard read-model payload shape through `/api/dashboard`, including selected
  stage, next action, blockers, evidence refs, recent activity, and recent artifacts;
- global next-action classification that routes operators to blocked questions or
  validation evidence even when a different stage is currently selected;
- workflow-run request delegation through the same core service used by the CLI;
- selected-stage run request delegation through the same stage execution path used by
  `aidd stage run`;
- selected-stage intervention request delegation through `/api/stage/interact`, with
  request text and current-stage target documents passed to the CLI-equivalent
  intervention path;
- explicit runtime selection before workflow-run or stage-run request dispatch;
- blocking answer persistence to `answers.md` with `resolved`, `partial`, and
  `deferred` resolution states;
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
- validation visibility through validator pass/fail counts and validator report paths;
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
- `tests/core/test_operator_frontend.py`

These tests exercise `OperatorUiService` and the runtime-agnostic operator read/write
services directly. Workflow-run, stage-run, and stage-intervention endpoints are
tested through injected execution seams so they prove request shape, UI/Core
delegation, and live log polling without invoking real runtimes.

## Manual Installed Smoke

A manual installed UI smoke should use a disposable local fixture project:

1. Install or run the AIDD artifact under test locally.
2. Change into the local fixture project root.
3. Run `aidd doctor` with the fixture config.
4. Run `aidd init --work-item <id> --request "<task>" --root .aidd` so `.aidd/` and intake context are created inside the fixture project.
5. Seed request context with `--request` or `--request-file`, then execute a local deterministic work item through `aidd run --runtime <runtime>`.
6. Start `aidd ui --work-item <id> --root .aidd --host 127.0.0.1 --port <port>`.
7. Verify the page loads, the dashboard shell renders stage rail/sidebar/bottom dock,
   runtime selection is required before `/api/workflow/run` and `/api/stage/run`
   dispatch, blocking answers persist, answer-and-resume keeps the same run id,
   `Request change -> Submit & run` creates a durable operator request and switches
   to live logs, persisted logs remain readable after completion, Markdown artifacts
   render as preview/source, validation state is visible, repair and operator-request
   evidence is linked, and recent activity/artifact rows remain visible after refresh.
8. For a blocked or failed `plan` stage, submit a request such as
   `Add migration rollback risks`, verify `/api/stage/interact` returns a job id,
   the Logs tab stays visible while polling `/api/jobs/<id>/logs`, and the latest
   request appears as `operator.request.created` in Activity plus an Evidence Ref.
9. Remove the disposable fixture project. Do not commit `.aidd/` artifacts.

Manual smoke evidence is recorded in `docs/backlog/roadmap.md`; generated `.aidd/`
state stays local to the fixture project.

## Manual Browser Checklist

Run these checks in a real browser against the local URL printed by `aidd ui`. Use a
disposable `.aidd/` workspace and record the AIDD version, runtime id, browser, viewport,
and any blockers in roadmap evidence.

### Dashboard Shell

- First launch shows the loading state before `/api/dashboard` resolves.
- No-run state explains the first action and exposes a runtime-gated `Run workflow`
  action after a runtime is selected.
- Work item, run chip, runtime readiness, stage rail, stage cockpit, right sidebar,
  Activity / Events, and Recent artifacts are visible after refresh.
- The active stage is marked in the rail and remains visible after selecting another
  stage.

### Cockpit Tabs

- Overview, Questions, Validation, Artifacts, Logs, Approvals, and Request change tabs
  switch content without losing the selected stage.
- Tab semantics expose the selected tab and the cockpit panel remains keyboard-focusable.
- Quick links route to Logs, Artifacts, Validation, and Questions consistently.

### Logs

- A running workflow, stage run, or intervention shows live stdout/stderr/system chunks.
- Cancelled or completed jobs keep their live log chunks visible.
- Saved `runtime.log` loads after completion and shows a truncation notice when bounded.
- Raw mode and stdout/stderr/system filters do not hide the truncation notice.

### Artifacts

- Artifact list renders document and log artifacts for the selected stage.
- Markdown preview and Source mode load through `/api/artifacts/document`.
- Large artifacts show byte-range truncation states and keep Open folder available for
  full-file inspection.
- Evidence Refs and Recent Artifacts navigate into the artifact inspection view.

### Questions

- Blocking questions appear in Overview and Questions.
- Saving a resolved answer writes `answers.md`, disables the answer controls, and shows
  the saved answer text in the resolved question card.
- Partial or deferred answers remain non-resolved and keep blocking policy visible.
- Answer & resume uses the selected runtime and current run id.

### Request Change / Intervention

- Request change shows current-stage target document checkboxes when available.
- Submit & run creates an operator request artifact, switches to Logs, and streams the
  intervention job.
- Activity and Evidence Refs show `operator.request.created` after refresh.
- Validation and repair evidence remain inspectable after the intervention attempt.

### Flow Complete Handoff

- A terminal `qa` run switches the command center from active-stage operation to
  **Flow Complete** without hiding stage rail, Activity / Events, or Recent artifacts.
- The handoff summary shows final QA status, runtime id, final artifacts, open blockers,
  evidence refs, repair counts, approval counts, and answered-question counts.
- Final artifacts open in the Artifacts view and remain readable in Preview and Source
  mode after refresh.
- The **Start Next Flow** action band shows Create New Work Item, Start Follow-up Flow,
  Clone This Flow, Run Eval / Scenario Batch, and Archive Run.
- Recommended next action badges match final QA status: completed runs without blockers
  recommend new work, while failed or blocked handoffs recommend follow-up work.
- Choosing Archive Run records the local archive decision and leaves final QA artifacts
  and run-history inspection available.

### Start Next Flow Wizard

- Start Follow-up Flow opens the source-finding step and groups QA findings, review
  notes, failed evidence, and manual request options.
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
