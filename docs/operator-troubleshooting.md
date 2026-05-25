# Operator Troubleshooting Guide

## 1. Purpose

This guide explains how to diagnose the most common operator-visible failures in AIDD:

- runtime failures;
- validator failures;
- harness and eval failures.

It is aligned with the current local AIDD CLI, adapter, validator, and harness behavior as of
May 4, 2026.

## 2. Fast Triage Flow

1. Confirm environment and runtime detection.

```bash
uv run aidd doctor
```

2. Identify the failing lane:

- workflow/stage runtime gate (`aidd run`, `aidd stage run`, `aidd stage interact`);
- stage artifacts and validator state (`aidd stage summary`, `aidd stage questions`);
- eval lane (`python -m aidd.harness.live_e2e_black_box`, `aidd eval summary`).

3. Collect run and stage evidence before changing anything:

```bash
uv run aidd run show --work-item WI-001
uv run aidd run artifacts --work-item WI-001 --stage plan
uv run aidd run logs --work-item WI-001 --stage plan --tail --lines 80
```

## 3. Runtime Failures

### 3.1 Runtime command is unavailable

Symptoms:

- `aidd doctor` shows `<runtime> available = no`.

Actions:

1. Install the runtime CLI binary.
2. Ensure the binary is visible in `PATH`.
3. If needed, set the runtime command in `aidd.example.toml` and rerun `uv run aidd doctor`.

### 3.2 Runtime version is `unknown`

Symptoms:

- `aidd doctor` reports `<runtime> version = unknown`.

Actions:

1. Verify the runtime binary works directly (`<runtime> --version`).
2. If the runtime command succeeds but AIDD still shows `unknown`, treat this as a probe-parsing gap and capture the full `aidd doctor` output for maintainer triage.

### 3.3 Workflow or stage runtime is not supported for execution

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

### 3.4 Intake context is missing

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

### 3.5 Run lookup errors in inspection commands

Symptoms:

- `No runs found for work item '<id>'`
- `Ambiguous latest run for work item '<id>'`

Actions:

1. For missing runs: verify the correct `--work-item` and `--root`.
2. For ambiguous runs: pass explicit `--run-id` and, for logs/artifacts, explicit `--attempt`.

## 4. Validator Failures

### 4.1 Determine validator state for a stage

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

### 4.2 Investigate failing validator verdicts

If `validator fail count > 0`:

1. Open `validator-report.md` from the path printed by `stage summary`.
2. Review finding codes, affected files, and missing sections.
3. Open `repair-brief.md` if present and compare required fixes to current stage documents.

### 4.3 Resolve blocking question gates

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

### 4.4 Stage intervention is rejected

Use intervention only for current-stage, document-first corrections:

```bash
uv run aidd stage interact plan --work-item WI-001 --runtime codex --request "Add rollback risks"
```

Common failures:

- `Operator request must not be empty.`: provide non-empty `--request` or `--request-file`.
- `Target document is outside current stage scope`: use a current-stage Markdown document
  such as `plan.md` or omit `--target-document`.
- `downstream stages already succeeded`: V1 does not invalidate completed downstream
  stages; start a new run or wait for downstream rerun policy work.

## 5. Harness and Eval Failures

### 5.1 Scenario path is invalid

Symptoms:

- `python -m aidd.harness.live_e2e_black_box` fails with `Scenario not found: <path>`.

Actions:

1. Use a repository-relative scenario path under `harness/scenarios/`.
2. Confirm the path exists before running eval.

### 5.2 Local-wheel live eval cannot locate source checkout

Symptoms:

- installed black-box live E2E fails before setup with a local-wheel install error.
- the error says local-wheel live eval requires a source checkout containing `pyproject.toml` and `contracts/`.
- the error says the local-wheel live eval requires a clean tracked source checkout.

Actions:

1. Run the command from an AIDD source checkout or pass a scenario path inside that checkout.
2. Commit or stash tracked source changes before the run. The evaluator snapshots
   tracked `HEAD` into `<work-root>/<run_id>/source/aidd` and builds the wheel
   from that temp snapshot.
3. If you are testing an already published artifact, set:
   `AIDD_EVAL_PUBLISHED_PACKAGE_SPEC="ai-driven-dev-v2==<version>"`.
4. Do not copy only the installed package's `site-packages` path into the
   scenario command; live local-wheel mode needs the source checkout to build
   the wheel.

The default mutable live work root is `${TMPDIR:-/tmp}/aidd-live-e2e`. Durable
evidence remains under `.aidd/reports/evals/<run_id>/` unless `--report-root`
overrides it.

### 5.3 Black-box live E2E reports `fail`, `blocked`, or `infra-fail`

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

### 5.4 Eval summary is missing

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
