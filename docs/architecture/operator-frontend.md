# Operator Frontend Contract

## 1. Purpose

The operator frontend is a user-facing surface for the existing governed AIDD
workflow.

It must let an operator:

- start and resume the full `idea -> qa` flow;
- run or inspect an individual stage;
- request a stage-scoped correction or additional analysis without leaving the
  document-first workflow;
- answer blocking questions;
- inspect stage artifacts, validation reports, repair history, and runner logs;
- keep enough provenance visible to compare the frontend action with the CLI action.

The frontend is not a second workflow engine. It must use the same stage graph,
contracts, validators, repair policy, run state, and adapter boundary as the CLI.

## 2. Source of truth

The frontend must not introduce a new canonical artifact format.

Canonical state remains in the repository-local AIDD workspace:

- work-item and stage documents under `.aidd/workitems/<id>/`;
- run and attempt reports under `.aidd/reports/runs/<id>/`;
- eval bundles under `.aidd/reports/evals/<run_id>/`;
- runtime logs, normalized events, validator reports, repair history, and prompt
  provenance already written by the core and harness.

The frontend may render cached views for usability, but cached UI state is not a
workflow authority and must be rebuildable from AIDD artifacts.

## 3. Required operator flows

The first frontend contract covers these flows:

1. **Full workflow run**
   - choose a work item and runtime;
   - start or resume `idea -> qa` through the workflow run application service;
   - show the current stage, terminal state, and next required operator action.

2. **Stage run and resume**
   - choose a stage from the canonical stage list;
   - execute the selected stage through the same single-stage path as `aidd stage run`;
   - show eligibility, missing prerequisites, blocked questions, failed validation,
     repair attempts, and final state;
   - never allow stage progression that the core would reject.

3. **Question answering**
   - show unresolved questions from the standard `questions.md`;
   - write UI answers to the standard `answers.md` as `[resolved]`,
     `[partial]`, or `[deferred]` according to the operator-selected resolution;
   - preserve blocking vs non-blocking question semantics;
   - resume only through the normal core path after answers are present.
   - when blocking questions exist, make the answer form the selected-stage
     cockpit priority and use the current run id when resuming the selected stage.

4. **Runner log viewing**
   - show live runtime stdout/stderr chunks for UI-started jobs when the adapter can stream;
   - show saved `runtime.log` attempt artifacts after execution;
   - show normalized events when available;
   - keep adapter/runtime labels visible so operators can distinguish native
     runtime output from AIDD summaries.

5. **Artifact browsing**
   - render stage input and output Markdown from known artifact-index document keys;
   - show `validator-report.md`, `stage-result.md`, and repair evidence;
   - show run/eval metadata, prompt paths, Git SHA, hashes, runtime id, and adapter id.

6. **Runtime approval handling**
   - show pending runtime operator requests from attempt-level `operator-requests.jsonl`;
   - show auto-approved, denied, or cancelled decisions from `operator-decisions.jsonl`;
   - write approval decisions only through the local job approval API;
   - keep runtime approvals separate from product questions in `questions.md` and
     `answers.md`.

7. **Operator intervention**
   - accept a selected-stage request through UI, CLI, or another operator integration;
   - persist the request as
     `.aidd/workitems/<id>/stages/<stage>/operator-requests/request-0001.md`;
   - run a new attempt in the current run id with `attempt_mode=intervention`;
   - include required inputs, existing same-stage outputs, the latest operator request,
     and available `questions.md` / `answers.md` in the input bundle;
   - validate and publish through the normal post-runtime chain;
   - reject the request when downstream stages have already succeeded in the same run
     until a downstream invalidation/rerun policy exists.

## 4. Write boundaries

Frontend writes are intentionally narrow:

- answer documents may be written through the same durable question/answer path
  used by the CLI;
- operator intervention requests may be written through the durable
  `operator-requests/request-000N.md` path and then executed by the same stage
  runner used by the CLI;
- run or stage execution may be requested only through core workflow commands or
  equivalent application services;
- runtime-authored stage outputs, validator reports, repair briefs, runtime logs,
  and eval artifacts must not be edited by the frontend.

The frontend must not silently rewrite generated evidence. Correction workflows use
explicit operator request documents, which become runtime input for a new attempt and
remain auditable in Evidence Refs and Activity.

## 5. Runtime and adapter boundary

Runtime-specific behavior remains inside adapters.

The frontend may display runtime capabilities, provider availability, execution
mode, and log/event support, but it must not encode provider-specific workflow
semantics. Unsupported or degraded runtime behavior should be shown as core or
adapter readiness state, not patched in the UI.

## 6. Minimum implementation surface

The first implementation should expose:

- work-item selection;
- runtime selection from registered runtimes;
- full-flow start/resume;
- per-stage status;
- blocking question answer form;
- raw log viewer;
- artifact viewer for Markdown documents and run/eval reports.

Anything beyond those flows is follow-up work and should be split into separate
local tasks.

The foundation implementation exposes UI-neutral Python services for run
metadata, stage summaries, logs, artifacts, question status, and answer writes.
The first UI shell must use those services instead of parsing CLI tables or
writing workflow documents directly.

Current W20 implementation status:

- workflow run/start/resume orchestration lives in a reusable core service, with
  the CLI delegating to it;
- `aidd ui --work-item <id> --root <path> --config <path> --host 127.0.0.1 --port 0`
  starts a local-only Python-packaged web UI;
- workflow and selected-stage launch requests require an explicit operator-selected
  runtime and do not fall back to `generic-cli`;
- UI launch requests create process-local jobs; `/api/jobs/<job_id>` exposes
  `running`, `completed`, or `failed` status and `/api/jobs/<job_id>/logs` exposes
  cursor-based live chunks;
- selected-stage launch uses the CLI-equivalent single-stage execution path, not a
  workflow range shortcut;
- the private local JSON API enforces a small request-body limit and deterministic
  malformed-body errors; non-loopback binds remain allowed but warn because this
  release has no UI authentication;
- private JSON endpoints expose run, dashboard, stage, questions, answer writes,
  persisted logs, artifact summaries, artifact document content, workflow run
  requests, stage run requests, stage intervention requests, and job status/log
  polling over the operator services;
- `POST /api/workflow/run` accepts optional `{run_id}`; when present, the UI asks the
  workflow service to continue that run through normal stage eligibility and the same
  backend config snapshot used by CLI launches;
- UI job state includes `waiting-for-operator`, with
  `GET /api/jobs/<job_id>/operator-requests` and
  `POST /api/jobs/<job_id>/operator-requests/<request_id>/decision` for local runtime
  approvals; these runtime approvals remain attempt artifacts and are separate from
  product/operator questions in `questions.md` and `answers.md`;
- approval decisions are loopback-only by default; non-loopback binds must opt in with
  `--allow-remote-approvals`;
- `POST /api/stage/interact` accepts `{stage, runtime, run_id, request,
  target_documents, log_follow}`, validates the request shape, and starts a
  process-local intervention job; the durable request artifact and attempt semantics
  are handled by core/CLI services, not by JavaScript state;
- `GET /api/dashboard?stage=<stage>&run_id=<run_id?>` returns an
  `OperatorDashboardView` containing project/work-item/run summary, canonical
  stage rail, selected-stage cockpit data, next action, blockers, evidence refs,
  recent activity, and recent artifacts derived from existing `.aidd/` state;
- dashboard `next_action` is run-global, not only selected-stage-local: unresolved
  blocking questions are surfaced before runnable-stage suggestions, failed
  validation points to validation inspection, and only existing artifact files are
  shown in Recent Artifacts;
- the static UI is organized as an operator console: top status bar, canonical
  stage rail, selected-stage cockpit with Overview/Questions/Validation/Artifacts/Logs
  tabs, right-side Next Action/Blockers/Evidence/Runtime Root/Safety panels, and a
  bottom Activity/Events plus Recent Artifacts dock;
- Recent Activity includes run/stage metadata and `events.jsonl` entries across
  all attempted stages plus `operator.request.created` entries for durable
  intervention requests; the static UI overlays process-local live job chunks into
  the Activity table while a UI-started run is active;
- Evidence Refs and Recent Artifacts include the latest operator request for the
  selected stage when present;
- the selected-stage cockpit includes a `Request change` tab with an escaped
  textarea and current-stage target document selector; submitting switches to the
  Logs tab and follows the intervention job through the same polling path as stage
  runs;
- long workspace-relative paths are retained in payloads and element titles, but
  rendered in compact form so evidence lanes stay scannable in the right sidebar
  and bottom dock;
- workflow and stage launches are primarily routed through the right-side Next
  Action button so the top bar stays status/control-plane focused;
- `POST /api/open-folder` is a loopback-only convenience action for allowlisted
  workspace, stage, and artifact folders inside `.aidd/`; it does not create or
  mutate workflow artifacts;
- `POST /api/server/stop` stops only the local UI server. It explicitly reports
  that runtime job cancellation is not provided by this redesign because current
  UI jobs are thread/subprocess executions without a core cancel token;
- the UI shell serves static HTML, CSS, and JavaScript from the Python package,
  without a Node or Vite dependency;
- dynamic question text, stage metadata, artifact labels and paths, runtime-derived
  values, artifact document content, and logs are rendered through escaped UI text paths;
- local smoke evidence covers page load, dashboard payload shape, blocking answer
  persistence to `answers.md`, answer-and-resume with the current run id, persisted
  log reads, structured live job log chunks, artifact document rendering, local-only
  open-folder/server-stop actions, stage intervention request dispatch, and
  workflow-run delegation through the internal service seam.

## 7. Onboarding-first startup

The recommended first-run operator path starts in the local UI, but existing CLI
subcommands remain compatible scripted surfaces. Bare `aidd` and `aidd --help` keep their
current help behavior in this release. `aidd ui` can start without `--work-item` and then
serves setup mode; `aidd ui --work-item <id> --root <path>` bypasses setup mode and opens
the existing command center for initialized work items.

Setup mode is a launcher over the same repository-local state model, not a separate
workflow authority. It must let the operator:

- enter or confirm a local project root;
- validate that the selected path is a directory and does not escape the local filesystem
  root through parent traversal or symlink resolution;
- resolve the project-local `.aidd/` workspace;
- discover existing work items in that workspace;
- create a new work item through the same workspace bootstrap and request-seeding behavior
  as `aidd init --work-item ... --request ... --root .aidd`;
- resume an existing work item without creating duplicate workspace state;
- inspect runtime readiness before any workflow run exists;
- explicitly select a runtime before workflow, stage, intervention, follow-up, or clone
  execution starts.

Runtime readiness remains observational. The UI may preselect a project-local runtime
preference as a convenience, but every launch request must still include the operator-selected
runtime id. There is no hidden `generic-cli` fallback.

One UI process may maintain a noncanonical recent-project list, but each active workflow,
job, answer write, log read, artifact read, and `.aidd/` workspace mutation is scoped to one
selected project root. Multiple roots inside a monorepo or related local workspace use the
existing declared `project_set` model. Unrelated repositories must not be combined into one
governed `.aidd/` workspace unless a future architecture decision introduces a multi-context
job registry.

## 8. Accepted next-generation UX direction

The accepted operator frontend direction is a Mission Control console. It keeps the
canonical stage timeline visible, gives the run-global next action primary weight, and
keeps documents, validation evidence, artifacts, approvals, and logs one click away.

The locked screen inventory is:

1. Project Setup / Work Item Picker with optional previous-run context.
2. Active Run Command Center for in-progress `idea -> qa` execution.
3. Stage Document Workbench for Markdown preview/source/diff and contract checks.
4. Questions / Interview Loop for unresolved model questions and persisted answers.
5. Validation / Repair Center for validation failures, repair attempts, and explicit stop.
6. Runtime Logs / Live Console for raw adapter/runtime logs and correlated events.
7. Artifacts / Evidence Graph for provenance between documents, logs, reports, and stages.
8. Approvals / Request Change for runtime approvals and stage-scoped interventions.
9. Run History / Scenario Matrix / Eval Reports for comparisons and systemic issues.
10. Start Next Flow Wizard for completed-run handoff.
11. Define Follow-up Work Item for new work item scope and inherited context.
12. Confirm and Launch Next Flow for preflight, audit preview, and launch.

The visual references for this direction are stored in
`docs/architecture/assets/operator-ui-mission-control/`:

- `01-project-setup-previous-run.png`
- `02-active-run-command-center.png`
- `02b-flow-complete-start-next-flow.png`
- `03-stage-document-workbench.png`
- `04-questions-interview-loop.png`
- `05-validation-repair-center.png`
- `06-runtime-logs-live-console.png`
- `07-artifacts-evidence-graph.png`
- `08-approvals-request-change.png`
- `09-run-history-lineage.png`
- `10-start-next-flow-source-findings.png`
- `11-define-follow-up-work-item.png`
- `12-confirm-launch-next-flow.png`

When the current run is active, the command center prioritizes blocked questions,
validation failures, approvals, resumable stages, and log visibility. When the run reaches
a terminal state after `qa`, the same command center switches to **Flow Complete** and the
primary action band becomes **Start Next Flow**.

The accepted completed-flow actions are:

- **Create New Work Item**: starts a fresh work item without previous-run context.
- **Start Follow-up Flow**: creates a new work item from selected QA findings, review
  notes, failed evidence, or a manual request.
- **Clone This Flow**: creates a new flow from the same runtime, prompt pack, contracts,
  branch, and baseline configuration, with optional edits before launch.
- **Run Eval / Scenario Batch**: sends the completed run into comparison or scenario
  evidence workflows without changing the completed run.
- **Archive Run**: marks the completed run as closed for operator navigation.

Follow-up and cloned flows are independent work items and runs. They may inherit selected
context references, but they must not continue or mutate the completed source run. The UI
must show source run, source work item, baseline, inherited artifacts, and audit preview
before launch.

## 9. UX validation checklist for the accepted direction

Before implementation is considered done, the local UI evidence lane must prove:

- setup mode can create or resume a work item from a selected project root without changing
  existing CLI command behavior;
- runtime selection remains explicit before any workflow, stage, intervention, follow-up,
  or clone launch;
- a completed `qa` run renders the Flow Complete state and handoff summary;
- Start Next Flow actions are visible without hiding final artifacts, logs, approvals,
  and validation evidence;
- follow-up creation records selected source findings and inherited context explicitly;
- launch preflight creates a new work item/run identity and source-run lineage evidence;
- run history can show parent and child relationships and still open raw logs/artifacts;
- mobile and keyboard paths can reach completed-run actions and the wizard controls.
