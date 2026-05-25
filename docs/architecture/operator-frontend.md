# Operator Frontend Contract

## 1. Purpose

The operator frontend is a user-facing surface for the existing governed AIDD
workflow.

It must let an operator:

- start and resume the full `idea -> qa` flow;
- run or inspect an individual stage;
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
   - write UI answers to the standard `answers.md` as `[resolved]`;
   - preserve blocking vs non-blocking question semantics;
   - resume only through the normal core path after answers are present.
   - keep partial and deferred answer states as direct file-mode semantics until the UI
     exposes an explicit resolution selector.

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

## 4. Write boundaries

Frontend writes are intentionally narrow:

- answer documents may be written through the same durable question/answer path
  used by the CLI;
- run or stage execution may be requested only through core workflow commands or
  equivalent application services;
- runtime-authored stage outputs, validator reports, repair briefs, runtime logs,
  and eval artifacts must not be edited by the frontend.

If the frontend needs a correction workflow, it should create an explicit operator
document or task for the existing workflow instead of silently rewriting generated
evidence.

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
- private JSON endpoints expose run, stage, questions, answer writes, persisted logs,
  artifact summaries, artifact document content, workflow run requests, stage run
  requests, and job status/log polling over the operator services;
- UI job state includes `waiting-for-operator`, with
  `GET /api/jobs/<job_id>/operator-requests` and
  `POST /api/jobs/<job_id>/operator-requests/<request_id>/decision` for local runtime
  approvals;
- approval decisions are loopback-only by default; non-loopback binds must opt in with
  `--allow-remote-approvals`;
- the UI shell serves static HTML, CSS, and JavaScript from the Python package,
  without a Node or Vite dependency;
- dynamic question text, stage metadata, artifact labels and paths, runtime-derived
  values, artifact document content, and logs are rendered through escaped UI text paths;
- local smoke evidence covers page load, blocking answer persistence to
  `answers.md`, persisted log reads, selected-stage run delegation, live job log
  chunks, artifact document rendering, and workflow-run delegation through the
  internal service seam.
