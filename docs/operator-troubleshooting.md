# Operator Troubleshooting Guide

## 1. Purpose

This guide explains how to diagnose the most common operator-visible failures in AIDD:

- runtime failures;
- validator failures;
- harness and eval failures.

It is aligned with the current bootstrap behavior of AIDD as of April 22, 2026.

## 2. Fast Triage Flow

1. Confirm environment and runtime detection.

```bash
uv run aidd doctor
```

2. Identify the failing lane:

- workflow/stage runtime gate (`aidd run`, `aidd stage run`);
- stage artifacts and validator state (`aidd stage summary`, `aidd stage questions`);
- eval lane (`aidd eval run`, `aidd eval summary`).

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

- `aidd run --runtime <non-generic>` prints:
  `Workflow execution is currently implemented for runtime 'generic-cli' only.`
- `aidd stage run --runtime <unknown>` fails with:
  `Unsupported runtime '<id>'.`

Actions:

1. Use `runtime=generic-cli` for workflow execution commands.
2. For stage execution, use one of: `generic-cli`, `claude-code`, `codex`, `opencode`.
3. Use `aidd doctor` to verify probe availability and configured runtime commands.
4. Track execution-parity progress in `docs/backlog/roadmap.md` before expecting non-generic workflow parity.

### 3.4 Run lookup errors in inspection commands

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
3. Re-run `stage questions` until it reports no unresolved blocking questions.

## 5. Harness and Eval Failures

### 5.1 Scenario path is invalid

Symptoms:

- `aidd eval run` fails with `Scenario not found: <path>`.

Actions:

1. Use a repository-relative scenario path under `harness/scenarios/`.
2. Confirm the path exists before running eval.

### 5.2 Harness eval run reports `fail`, `blocked`, or `infra-fail`

Symptoms:

- `aidd eval run` exits non-zero;
- or completes with `Status: fail`, `Status: blocked`, or `Status: infra-fail`.

Actions:

1. Capture the printed `Run id` and `Bundle root`.
2. Open bundle artifacts first:
   - `runtime.log`
   - `validator-report.md`
   - `verdict.md`
   - `log-analysis.md`
3. Classify failure source:
   - `infra-fail`: setup/teardown/repo-prep issue;
   - `blocked`: interview lane is waiting for required answers evidence;
   - `fail`: verification or run command failed.
4. Re-run the same scenario/runtime after fixing the first failure boundary.

### 5.3 Eval summary is missing

Symptoms:

- `aidd eval summary` fails with `No eval summary reports found.`

Actions:

1. Confirm `.aidd/reports/evals/` exists.
2. Confirm at least one `summary.md` was produced by an eval-capable run.
3. Run `uv run aidd eval run <scenario> --runtime <runtime>` once, then retry summary.

## 6. Evidence Checklist for Escalation

When reporting an operator-facing issue, include:

- exact command and full CLI output;
- work item id, runtime id, and stage id;
- `aidd doctor` table output;
- relevant paths from `aidd run artifacts`;
- tail from `aidd run logs` for the failing stage and attempt;
- `validator-report.md`, `repair-brief.md`, and `questions.md`/`answers.md` when applicable.
