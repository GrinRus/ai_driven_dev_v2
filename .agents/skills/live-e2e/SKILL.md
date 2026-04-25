---
name: live-e2e
description: Run or prepare a manual full-flow live end-to-end scenario against a public GitHub repository with repository pinning, curated issue selection, quality checks, and full log capture.
---

# live-e2e

## Use when

- You need to execute or author a scenario from `docs/e2e/live-e2e-catalog.md`.
- You need to compare live provider behavior on a real repository.
- You need to prove the installed operator flow from `idea` through `qa` as a manual external audit.
- You need a **local source-checkout runbook** for manual live E2E, not just the abstract eval contract.

## This skill vs `aidd-eval`

- Use `live-e2e` when the main question is: "How do I make a local live run work from this checkout?"
- Use `aidd-eval` when the main question is: "How do I audit artifacts, validation, grading, and failure classification across eval lanes?"
- `live-e2e` is the primary local operator playbook for live runs.
- `aidd-eval` remains the generic eval and artifact-analysis skill.

## Read first

This skill is intended to be sufficient for a prepared local run, but these files
remain the authoritative deeper references:

1. `docs/e2e/live-e2e-catalog.md`
2. `docs/e2e/scenario-matrix.md`
3. `docs/operator-handbook.md`
4. the selected manifest in `harness/scenarios/live/`

## What must already exist

If you only use this skill from the current project, the run still needs these
external prerequisites to already be true:

- you are in a prepared local **source checkout** of this repository;
- `uv sync --extra dev` has already completed successfully;
- the selected live manifest exists under `harness/scenarios/live/`;
- the requested runtime appears in the scenario's `runtime_targets`;
- the machine has network access to clone the pinned public target repository;
- the selected provider is already authenticated and runnable on the machine;
- you already have an **AIDD-compatible wrapper command** for the chosen live runtime.

This skill does **not** provision runtime authentication, wrapper scripts, or provider setup for you.

## Runtime-command contract

For local manual live runs, you must provide a runtime-command override through environment variables:

- `AIDD_EVAL_CODEX_COMMAND` for `codex`
- `AIDD_EVAL_OPENCODE_COMMAND` for `opencode`

The value must point to an **AIDD-compatible wrapper command**:

- it must be invokable from the shell on the current machine;
- it must accept the adapter flags AIDD passes for that runtime;
- it may be a wrapper around the upstream provider CLI rather than the raw provider binary;
- `aidd doctor` probing a provider binary does **not** prove the configured execution command is valid for live execution.

There are no repo-local wrapper templates in this wave. The operator must already have a working execution surface.

## Local preflight checklist

Before the live run, confirm all of these:

1. `uv sync --extra dev`
2. `uv run aidd doctor`
3. the selected scenario is under `harness/scenarios/live/`
4. the scenario has `automation_lane: manual`
5. the scenario forces `stage_scope: idea -> qa`
6. the runtime you plan to use appears in `runtime_targets`
7. the matching runtime-command env var is exported in the current shell
8. the runtime command resolves on the machine and uses the expected auth state

Recommended local preflight:

```bash
uv sync --extra dev
uv run aidd doctor
export AIDD_EVAL_CODEX_COMMAND='<aidd-compatible codex wrapper>'
```

or:

```bash
export AIDD_EVAL_OPENCODE_COMMAND='<aidd-compatible opencode wrapper>'
```

## Canonical local launch

The primary execution path for this skill is a local run from the AIDD source checkout:

```bash
uv run aidd eval run harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex
```

or:

```bash
uv run aidd eval run harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime opencode
```

The GitHub `manual-live-e2e` workflow is a secondary alternate entrypoint, not the primary flow described by this skill.

## What the harness will do

During a successful local live run, the harness will:

1. load the selected scenario and validate the live-lane contract;
2. resolve and record the pinned target repository commit;
3. prepare a clean working copy of the target repository;
4. select the **first listed issue** from the curated issue pool;
5. write issue-selection evidence to the eval bundle and target-repo context;
6. seed `.aidd/` inside the target repository;
7. write a live `aidd.example.toml` with the runtime command for the chosen provider;
8. build and install the AIDD artifact under test with `uv tool`;
9. run installed `aidd` from the target repository root with explicit workflow bounds `idea -> qa`;
10. run setup, verify, and quality commands and write the final audit artifacts.

## Validations and blockers

The live run can be rejected or downgraded at several layers:

- manifest validation rejects non-live scenarios, non-manual live scenarios, missing `quality`, invalid `runtime_targets`, or any live scenario that is not bounded to `idea -> qa`;
- runtime admission rejects a requested runtime that is not declared in `runtime_targets`;
- stage execution stays bounded to `idea -> qa`;
- stage outputs must validate against Markdown document contracts;
- repair loops are allowed to run when validation failures are repairable;
- interview scenarios block when required answers are missing;
- repo-local `verify.commands` must pass;
- repo-local `quality.commands` must pass for a clean quality result;
- execution `pass` is impossible if any stage in scope is missing required validated artifacts.

Live execution verdicts remain:

- `pass`
- `fail`
- `blocked`
- `infra-fail`

Quality is additive:

- `pass`
- `warn`
- `fail`
- `none`

## Output locations and success criteria

The canonical eval bundle for a local live run lives under:

- `.aidd/reports/evals/<run_id>/`

Expected live artifacts include:

- `issue-selection.json`
- `install-transcript.json`
- `runtime.log`
- `validator-report.md`
- `repair-history.md`
- `log-analysis.md`
- `grader.json`
- `verdict.md`
- `quality-report.md`
- `quality-transcript.json`

A live run is only "clean" when execution evidence exists, verification output is present, and the bundle includes `quality-report.md` plus `quality-transcript.json`.

## First triage for common failures

- Missing runtime-command env var: export `AIDD_EVAL_CODEX_COMMAND` or `AIDD_EVAL_OPENCODE_COMMAND` before rerunning.
- Runtime launches but immediately fails: the configured command is probably not an AIDD-compatible wrapper command.
- `unsupported-runtime`: the runtime is not declared in the scenario's `runtime_targets`.
- `blocked`: inspect `questions.md` / `answers.md` expectations for interview scenarios.
- `fail` after run success: inspect `verify-transcript.json`, `quality-transcript.json`, and the stage-local validator reports.
- Missing clean execution despite zero exit codes: inspect `verdict.md` and `grader.json` for pass-guard failures caused by missing `stage-result.md` or `validator-report.md`.

## Procedure

1. Confirm the selected scenario is in `harness/scenarios/live/`, has `automation_lane: manual`, and declares the requested runtime in `runtime_targets`.
2. Export the matching local runtime-command env var and confirm it points to an AIDD-compatible wrapper command.
3. Run the local preflight checks from this skill.
4. Launch `uv run aidd eval run <manifest> --runtime <runtime>`.
5. Preserve the resulting bundle and inspect `verdict.md`, `grader.json`, `quality-report.md`, and transcripts before judging the run.
6. If the setup, provider coverage, size classification, quality recipe, or verification recipe had to change, update the scenario manifest, matrix doc, and catalog after the run as separate follow-up work.

## Hard rules

- Never treat live E2E as a CI or release lane.
- Never assume this skill provisions runtime auth, wrappers, or provider setup.
- Never dispatch the manual GitHub workflow without the runtime-command secret for the selected provider.
- Never run a live scenario without storing the resolved repo pin.
- Never run a live scenario without storing the selected issue snapshot.
- Never treat a live scenario as canonical unless it executes `idea -> qa`.
- Never treat a live scenario as passed without install evidence and verification output.
- Never treat a live scenario as clean without `quality-report.md` and `quality-transcript.json`.
- Preserve all runtime logs.
- Keep `.aidd` rooted inside the target repository for installed live runs.
