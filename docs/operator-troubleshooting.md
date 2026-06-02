# Operator Troubleshooting Guide

## 1. Purpose

This guide explains how to diagnose the most common operator-visible failures in AIDD:

- UI onboarding and setup failures;
- runtime failures;
- validator failures;
- harness and eval failures.

It is aligned with the current local AIDD CLI, adapter, validator, and harness behavior as of
June 2, 2026.

## 2. Fast Triage Flow

1. Confirm environment and runtime detection.

```bash
uv run aidd doctor
```

2. Identify the failing lane:

- local UI onboarding (`aidd ui` before work-item selection);
- workflow/stage runtime gate (`aidd run`, `aidd stage run`, `aidd stage interact`);
- stage artifacts and validator state (`aidd stage summary`, `aidd stage questions`);
- eval lane (`python -m aidd.harness.live_e2e_black_box`, `aidd eval summary`).

3. Collect run and stage evidence before changing anything:

```bash
uv run aidd run show --work-item WI-001
uv run aidd run artifacts --work-item WI-001 --stage plan
uv run aidd run logs --work-item WI-001 --stage plan --tail --lines 80
```

## 3. UI Onboarding Failures

### 3.1 Project root is rejected

Symptoms:

- setup mode reports that the project path is missing, not a directory, or outside the
  allowed local root;
- work item discovery does not show the expected `.aidd/` workspace.

Actions:

1. Start `aidd ui` from the target local project root when possible.
2. Use an existing directory path, not a file path.
3. Avoid `..` traversal and symlinks that resolve outside the selected project root.
4. Confirm the `.aidd/` workspace should live inside the selected project, then retry setup.

### 3.2 Runner cards show unavailable runtimes

Symptoms:

- setup mode or the command center shows a runtime as unavailable;
- workflow launch remains disabled until a runtime is selected and ready.

Actions:

1. Run `aidd doctor` from the same project root and config path used by the UI.
2. Install the missing runtime binary or fix `PATH`.
3. Authenticate the provider CLI outside AIDD.
4. Check `aidd.example.toml` if the execution command is custom.
5. Select a ready runtime explicitly in the browser. The UI does not launch through a
   hidden `generic-cli` fallback.

### 3.3 Recent project points to stale state

Symptoms:

- a recent project entry no longer exists;
- the UI opens a project but work items, logs, or artifacts are missing.

Actions:

1. Re-enter the current project root manually in setup mode.
2. Confirm `.aidd/workitems/` exists in that project if you expect resumable work.
3. Treat recent projects as UI convenience only. Canonical workflow state remains in the
   selected project-local `.aidd/` workspace.

## 4. Runtime Failures

### 4.1 Runtime command is unavailable

Symptoms:

- `aidd doctor` shows `<runtime> available = no`.

Actions:

1. Install the runtime CLI binary.
2. Ensure the binary is visible in `PATH`.
3. If needed, set the runtime command in `aidd.example.toml` and rerun `uv run aidd doctor`.

### 4.2 Runtime version is `unknown`

Symptoms:

- `aidd doctor` reports `<runtime> version = unknown`.

Actions:

1. Verify the runtime binary works directly (`<runtime> --version`).
2. If the runtime command succeeds but AIDD still shows `unknown`, treat this as a probe-parsing gap and capture the full `aidd doctor` output for maintainer triage.

### 4.3 Workflow or stage runtime is not supported for execution

Symptoms:

- `aidd run --work-item <id>` fails with `Missing option '--runtime'`.
- `aidd stage run <stage> --work-item <id>` fails with `Missing option '--runtime'`.
- `aidd stage interact <stage> --work-item <id>` fails with `Missing option '--runtime'`.
- `aidd run --runtime <unknown>` fails with:
  `Unsupported runtime '<id>' for workflow execution.`
- `aidd stage run --runtime <unknown>` fails with:
  `Unsupported runtime '<id>'. Supported runtimes: generic-cli, claude-code, codex, opencode, qwen.`

Actions:

1. Use one of: `generic-cli`, `claude-code`, `codex`, `opencode`, `qwen`.
2. Use `aidd doctor` to verify probe availability and configured runtime commands.
3. If the runtime id is not in the supported list, treat it as unsupported until roadmap adds explicit adapter support.
4. For product onboarding, prefer a real configured runtime such as `codex`, `claude-code`, `opencode`, or experimental `qwen`; use `generic-cli` only for an explicit AIDD-compatible wrapper/test lane.

### 4.4 Intake context is missing

Symptoms:

- `aidd run` or `aidd stage run idea` fails with:
  `Input bundle preparation requires an existing input document: .../context/intake.md`.

Actions:

1. If this is a new work item, rerun init with request input:
   `aidd init --work-item WI-001 --request "Implement <specific task>" --root .aidd`.
2. If the request lives in a file, use:
   `aidd init --work-item WI-001 --request-file /path/to/request.md --root .aidd`.
3. If context docs already exist and should be replaced, add `--force-context`.
4. Confirm these files exist before rerunning:
   `context/intake.md`, `context/user-request.md`, and `context/repository-state.md`.

### 4.5 Run lookup errors in inspection commands

Symptoms:

- `No runs found for work item '<id>'`
- `Ambiguous latest run for work item '<id>'`

Actions:

1. For missing runs: verify the correct `--work-item` and `--root`.
2. For ambiguous runs: pass explicit `--run-id` and, for logs/artifacts, explicit `--attempt`.

### 4.6 Next-flow launch preflight is blocked

Symptoms:

- the **Flow Complete** screen is visible, but **Launch Flow Now** is disabled;
- the Start Next Flow wizard shows a blocked launch preflight;
- follow-up or clone draft creation succeeds, but launch does not create a child work item
  or run;
- archive state is visible, but final artifacts remain read-only and no new flow starts.

Actions:

1. Confirm the source run is terminal after `qa` and still readable in Run History /
   Lineage. Archive decisions must not delete artifacts or mutate the completed source run.
2. Verify the preflight inputs: writable `.aidd/` workspace, explicit runtime selection,
   contracts path availability, source-run existence, source work item id, and baseline
   availability.
3. Open the source findings step and confirm at least one QA finding, review note, failed
   evidence item, or manual request is selected for a follow-up draft. Clone drafts should
   show editable runtime, prompt pack, resource, commit, and baseline configuration before
   launch.
4. If the blocker is runtime readiness, run `aidd doctor` and select a configured runtime
   in the browser. The UI does not launch through a hidden `generic-cli` fallback.
5. If the blocker is missing source-run or baseline metadata, inspect
   `aidd run show --work-item <id> --root .aidd` and the final QA artifacts before creating
   the next-flow draft again.
6. Keep local UI troubleshooting separate from public-repository live E2E evidence. Live
   E2E records `next-flow-checkpoint.json` and `next-flow-checkpoint.md` after terminal
   `qa`; it does not require launching a second public-repository flow by default.

### 4.7 UI job appears silent for a long time

Symptoms:

- the **Active Run** panel shows `No output for N minutes`;
- the job is still `running`, but the Logs tab has not received new chunks;
- the stage timeout has not yet expired.

Actions:

1. Open the **Logs** tab and inspect the last runtime line.
2. Check the **Active Run** panel for runner command and timeout summary.
3. Confirm the provider CLI is still expected to stream output; some tools are quiet while
   planning or waiting on a long subprocess.
4. If the command is clearly stuck, use **Cancel job** in the UI. Cancellation requests are
   best-effort against the UI-started job and preserve the log evidence already captured.
5. If the same runtime repeatedly goes silent before writing artifacts, run the configured
   provider command directly and collect the raw `runtime.log` for maintainer triage.

### 4.8 Implement Review diff is missing or truncated

Symptoms:

- **Implement Review** reports that repository diff is unavailable;
- changed files are visible, but a diff hunk is marked truncated;
- `.aidd/` artifacts appear separately from source changes;
- a file is marked `changed but not mentioned`, `mentioned but unchanged`, or `outside scope`.

Actions:

1. Confirm the selected project root is a git repository. The diff service reads git status
   and diff output from the selected project root only.
2. Keep `.aidd/` project-local, but do not treat `.aidd/` artifacts as source changes. The
   UI separates them intentionally.
3. For truncated hunks, open the file or run local git commands outside AIDD if you need the
   full diff. The UI API uses bounded reads.
4. If a changed source file is not mentioned in `implementation-report.md`, treat it as an
   operator warning and ask the runtime to update the report or rerun implement.
5. If a file is outside allowed scope, verify `allowed-write-scope.md` and decide whether to
   remediate before review.

### 4.9 Review/QA remediation or stale downstream rerun is blocked

Symptoms:

- **Send selected to implement** is disabled;
- remediation launch fails with `runtime is required`;
- `review` or `qa` shows a stale badge after a remediation attempt;
- terminal handoff is not visible even though `qa` previously succeeded.

Actions:

1. Select a ready runtime explicitly in the top bar. Remediation launches never use a hidden
   `generic-cli` fallback.
2. Select at least one review finding or QA risk/issue before sending to implement.
3. Add a concise operator note explaining what the new implement attempt should fix.
4. Wait for the remediation `implement` job to complete successfully. Downstream stages are
   marked stale only after that successful implement attempt.
5. Use the run-global next action **Rerun stale downstream** to explicitly run `review -> qa`.
6. Treat stale `qa` as not ready for terminal handoff until the downstream rerun succeeds.

## 5. Validator Failures

### 5.1 Determine validator state for a stage

Use:

```bash
uv run aidd stage summary plan --work-item WI-001
```

Read these fields first:

- `final state`
- `validator pass count`
- `validator fail count`
- `validator report`
- `repair outputs`

### 5.2 Investigate failing validator verdicts

If `validator fail count > 0`:

1. Open `validator-report.md` from the path printed by `stage summary`.
2. Review finding codes, affected files, and missing sections.
3. Open `repair-brief.md` if present and compare required fixes to current stage documents.

### 5.3 Resolve blocking question gates

Use:

```bash
uv run aidd stage questions plan --work-item WI-001
```

If status is `pending-blocking`:

1. Add answers in `answers.md`.
2. Mark resolved entries with `[resolved]`.
3. Use exact answer lines such as `- Q1 [resolved] answer text`; do not insert a
   colon after `[resolved]`.
4. Re-run `stage questions` until it reports no unresolved blocking questions.

### 5.4 Stage intervention is rejected

Use intervention only for current-stage, document-first corrections:

```bash
uv run aidd stage interact plan --work-item WI-001 --runtime codex --request "Add rollback risks"
```

Common failures:

- `Operator request must not be empty.`: provide non-empty `--request` or `--request-file`.
- `Target document is outside current stage scope`: use a current-stage Markdown document
  such as `plan.md` or omit `--target-document`.
- `downstream stages already succeeded`: stage-scoped intervention still cannot mutate a
  stage after downstream success. For review or QA problems, use UI remediation to send
  selected findings or risks back to `implement`, then rerun stale downstream stages.

## 6. Harness and Eval Failures

### 6.1 Scenario path is invalid

Symptoms:

- `python -m aidd.harness.live_e2e_black_box` fails with `Scenario not found: <path>`.

Actions:

1. Use a repository-relative scenario path under `harness/scenarios/`.
2. Confirm the path exists before running eval.

### 6.2 Local-wheel live eval cannot locate source checkout

Symptoms:

- installed black-box live E2E fails before setup with a local-wheel install error.
- the error says local-wheel live eval requires a source checkout containing `pyproject.toml` and `contracts/`.
- the error says the local-wheel live eval requires a clean tracked source checkout.

Actions:

1. Run the command from an AIDD source checkout or pass a scenario path inside that checkout.
2. Commit or stash tracked source changes before the run. The evaluator snapshots
   tracked `HEAD` into `<work-root>/<run_id>/source/aidd` and builds the wheel
   from that temp snapshot.
3. Do not copy only the installed package's `site-packages` path into the
   scenario command; live local-wheel mode needs the source checkout to build
   the wheel.

The default mutable live work root is `${TMPDIR:-/tmp}/aidd-live-e2e`. Durable
evidence remains under `.aidd/reports/evals/<run_id>/` unless `--report-root`
overrides it.

### 6.3 Black-box live E2E reports `fail`, `blocked`, or `infra-fail`

Symptoms:

- `python -m aidd.harness.live_e2e_black_box` exits non-zero;
- or completes with `Status: fail`, `Status: blocked`, or `Status: infra-fail`.

Actions:

1. Capture the printed `Run id` and `Bundle root`.
2. Open bundle artifacts first:
   - `runtime.log`
   - `validator-report.md`
   - `verdict.md`
   - `log-analysis.md`
   - `stage-audits/<stage>.json`
   - `stage-timing.md`
   - `self-repair-matrix.json`
   - `self-repair-matrix.md`
3. Classify failure source:
   - `infra-fail`: setup/teardown/repo-prep issue;
   - `blocked`: the live evaluator found unresolved blocking questions and is
     waiting for `answers.md` evidence requested in `operator-action-request.md`;
     when you launched the manual lane, you are the operator-agent, so write
     `[resolved]` answers with exact lines such as
     `- Q1 [resolved] answer text`, write `answer-analysis.md`, and rerun the
     same manifest/runtime command to resume;
   - `fail`: verification or run command failed.
4. Re-run the same scenario/runtime after fixing the first failure boundary.
5. For any terminal live run, inspect the full eval bundle and write
   `operator-quality-analysis.md` before marking the run counted or not counted.

### 6.4 Eval summary is missing

Symptoms:

- `aidd eval summary` fails with `No eval summary reports found.`

Actions:

1. Confirm `.aidd/reports/evals/` exists.
2. Confirm at least one `summary.md` was produced by an eval-capable run.
3. Run `uv run python -m aidd.harness.live_e2e_black_box <scenario> --runtime <runtime>`
   once, then retry summary.

## 6. Evidence Checklist for Escalation

When reporting an operator-facing issue, include:

- exact command and full CLI output;
- work item id, runtime id, and stage id;
- `aidd doctor` table output;
- relevant paths from `aidd run artifacts`;
- tail from `aidd run logs` for the failing stage and attempt;
- `validator-report.md`, `repair-brief.md`, and `questions.md`/`answers.md` when applicable.
