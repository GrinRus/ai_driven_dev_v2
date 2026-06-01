---
name: live-e2e
description: Run or prepare a manual full-flow live end-to-end scenario against a public GitHub repository with repository pinning, authored task selection, quality checks, and full log capture.
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
- the selected provider CLI is available, or you have an AIDD-compatible wrapper
  command override for the chosen live runtime.

This skill does **not** provision runtime authentication, wrapper scripts, or provider setup for you.
Public-repository live E2E always builds a local wheel from clean tracked `HEAD`.
Published-package install proof belongs to the separate release/install lane.

## Runtime-command contract

For local manual live runs, `claude-code`, `codex`, and `opencode` use native provider CLI
commands by default. You may provide a runtime-command override through
environment variables when you need a custom wrapper:

- `AIDD_EVAL_CLAUDE_CODE_COMMAND` for `claude-code`
- `AIDD_EVAL_CODEX_COMMAND` for `codex`
- `AIDD_EVAL_OPENCODE_COMMAND` for `opencode`

When set, the value must point to an **AIDD-compatible wrapper command**:

- it must be invokable from the shell on the current machine;
- it must accept the adapter flags AIDD passes for that runtime;
- it may be a wrapper around the upstream provider CLI rather than the raw provider binary;
- `aidd doctor` distinguishes provider probe readiness from execution command readiness.

There are no repo-local wrapper templates in this wave. The operator must already
have provider auth and a working provider CLI or wrapper execution surface.

## Local preflight checklist

Before the live run, confirm all of these:

1. `uv sync --extra dev`
2. `uv run aidd doctor`
3. the selected scenario is under `harness/scenarios/live/`
4. the scenario has `automation_lane: manual`
5. the scenario forces `stage_scope: idea -> qa`
6. the runtime you plan to use appears in `runtime_targets`
7. `uv run aidd eval doctor <manifest> --runtime <runtime>` reports execution readiness
8. any wrapper env var you choose to set resolves on the machine and uses the expected auth state
9. for native `codex` live runs, `aidd eval doctor` also confirms `codex login status`
   from the operator environment that live stage execution will inherit

Recommended local preflight:

```bash
uv sync --extra dev
uv run aidd doctor
uv run aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex
```

Optional wrapper override:

```bash
export AIDD_EVAL_CODEX_COMMAND='<aidd-compatible codex wrapper>'
export AIDD_EVAL_OPENCODE_COMMAND='<aidd-compatible opencode wrapper>'
export AIDD_EVAL_CLAUDE_CODE_COMMAND='<aidd-compatible claude-code wrapper>'
```

## Canonical local launch

The primary execution path for this skill is a local run from the AIDD source checkout:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex
```

or:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime opencode
```

or:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime claude-code
```

The default execution layout is:

- `--work-root ${TMPDIR:-/tmp}/aidd-live-e2e` for mutable execution state;
- `--report-root .aidd/reports/evals` for durable evidence bundles;
- `--run-id <id>` only when you need to resume an existing blocked run.

Use explicit paths when the audit needs stable local references:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/typer-boolean-help-rendering.yaml --runtime codex --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals
```

There is no GitHub Actions live E2E entrypoint. Live E2E is local manual operator audit
evidence only.

## What the harness will do

During a successful local live run, the evaluator will:

1. load the selected scenario and validate the live-lane contract;
2. fail as an infra/config blocker if the tracked AIDD source checkout is dirty;
3. snapshot tracked AIDD `HEAD` into `<work-root>/<run_id>/source/aidd`;
4. build the wheel in `<work-root>/<run_id>/build/dist`;
5. install with isolated `HOME=<work-root>/<run_id>/install-home` and
   `UV_CACHE_DIR=<work-root>/<run_id>/uv-cache`;
6. clone the pinned target repository into `<work-root>/<run_id>/target/<repo-slug>`;
7. select the **first listed authored task** from the manifest task pool;
8. write feature-selection evidence to the eval bundle and target-repo context;
9. seed `.aidd/` inside the target repository;
10. write a live `aidd.example.toml` with the runtime command and execution mode for the chosen provider;
11. run setup, stage, verify, and quality commands from the target repository root
    with the installed `aidd` binary on `PATH`;
12. inherit the launching operator's `HOME` and provider environment during stage
    execution so native provider auth works without copying credentials;
13. plan step, execute through public operator surfaces, inspect artifacts/UI/API/logs,
   classify, and decide the next step for every stage from `idea -> qa`;
14. write `stage-audits/<stage>.json` and `.md` after every stage;
15. run setup, verify, quality, and teardown commands and write final audit artifacts
    from the recorded step evidence.

## Operator-agent responsibilities

For local manual live runs, the launching agent is the operator-agent. Do not
delegate blocking questions to a separate external actor when you are running the
lane yourself.

When the evaluator returns `blocked`:

1. Open `operator-action-request.md`.
2. Open the referenced `questions.md`.
3. write standard `[resolved]` answers to the referenced `answers.md`.
   Use exact answer lines such as `- Q1 [resolved] answer text`; do not insert a
   colon after `[resolved]`.
4. Write `answer-analysis.md` in the eval bundle, explaining the choices and how
   they satisfy the authored task constraints.
5. Re-run the same black-box command for the same manifest/runtime so the
   evaluator resumes the existing blocked run.

After any terminal live run, the launching operator-agent must write
`operator-quality-analysis.md` in the eval bundle before counting the run. Use
this template:

```markdown
# Operator Quality Analysis

## Run
- Runtime: `<runtime>`
- Manifest: `<manifest>`
- Run ID: `<run_id>`
- Bundle: `<bundle path>`

## Machine Result
- Execution verdict: `<pass|fail|blocked|infra-fail>`
- Quality gate: `<pass|warn|fail|none>`
- QA verdict: `<ready|ready-with-risks|not-ready|missing>`
- Review status: `<approved|approved-with-conditions|rejected|missing>`

## Flow Fidelity
- Stages reached:
- Repair/interview behavior:
- Evidence completeness:

## Artifact Quality
- Stage outputs:
- Validator reports:
- Review/QA evidence:
- Unresolved findings:

## Code Quality
- Diff scope:
- Tests:
- Docs/examples:
- Acceptance criteria:

## Decision
- Decision: `<counted-clean|not-counted|blocked/infra|blocked/provider|blocked/model-quality|blocked/product-defect>`

## Blockers
- `<explicit blockers, or none>`
```

The operator audit cannot upgrade machine `fail` or `warn` to a counted clean
pass. It can only reject or downgrade a machine-clean run after inspecting the
artifacts.

## Next-flow terminal checkpoint

After terminal `qa`, inspect the completed-run handoff before writing the final
operator decision:

1. Open the loopback UI or recorded UI/API checkpoint evidence.
2. Confirm **Flow Complete** is visible for the terminal run.
3. Record final QA status, blockers, final artifacts, approval counts, repair counts,
   answered-question counts, and recommended next-flow actions.
4. Record the operator next-flow decision as `no-follow-up`, `follow-up-draft`,
   `clone-draft`, `eval-batch`, `archive`, or `blocked`.
5. If a draft/eval/archive decision is recorded, preserve source-run references and
   selected source artifact links as evidence.

Do not launch a second public-repository flow by default. Child-flow proof is a
separate manual-only option when the evaluator explicitly supports it; it must stay
outside CI/CD and release automation and must write separate lineage evidence instead
of mutating the completed source run.

The evaluator option `--enable-next-flow-follow-up-proof` is off by default. Use it
only for a deliberate manual maintained-scenario proof after terminal passing `qa`.
When enabled, the evaluator creates a follow-up draft from the terminal QA report and
writes `next-flow-lineage.json`; it still must not launch a child public-repository
flow.

## Validations and blockers

The live run can be rejected or downgraded at several layers:

- manifest validation rejects non-live scenarios, non-manual live scenarios, missing `quality`, invalid `runtime_targets`, or any live scenario that is not bounded to `idea -> qa`;
- runtime admission rejects a requested runtime that is not declared in `runtime_targets`;
- stage execution stays bounded to `idea -> qa`;
- stage outputs must validate against Markdown document contracts;
- repair loops are allowed to run when validation failures are repairable;
- any live scenario may block when required answers are missing;
- `live-full-flow-interview` scenarios are coverage cases where a blocking
  interview path is expected by the manifest;
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

- `flow-state.json`
- `flow-steps.json`
- `flow-report.md`
- `operator-actions.jsonl`
- `frontend-checkpoints.json`
- `frontend-checkpoints.md`
- `ui-ux-checkpoints.json`
- `ui-ux-checkpoints.md`
- `acceptance-coverage.json`
- `acceptance-coverage.md`
- `operator-quality-analysis-validation.json`
- `next-flow-checkpoint.json`
- `next-flow-checkpoint.md`
- `next-flow-lineage.json` only when `--enable-next-flow-follow-up-proof` is explicitly enabled
- `stage-audits/<stage>.json`
- `stage-audits/<stage>.md`
- `feature-selection.json`
- `install-transcript.json`
- `runtime.log`
- `validator-report.md`
- `repair-history.md`
- `log-analysis.md`
- `grader.json`
- `verdict.md`
- `quality-report.md`
- `quality-transcript.json`
- `operator-quality-analysis.md` for counted manual clean-pass decisions
- `answer-analysis.md` when the run answered blocking questions

A live run is only "clean" when execution evidence exists, verification output is
present, the machine `quality_gate` is `pass`, acceptance coverage is complete,
the UI/UX gate is not failed, and the bundle includes `quality-report.md`,
`quality-transcript.json`, and a valid operator-authored
`operator-quality-analysis.md` with decision `counted-clean`.

## Iteration loop contract

For live quality stabilization, the launching agent should repeat this external
operator loop instead of relying on a self-mutating product command:

1. Run one `>= medium` live scenario through the black-box evaluator.
2. Read the full evidence bundle, including every `stage-audits/<stage>.json`,
   `verdict.md`, `grader.json`, `quality-report.md`, transcripts, and logs.
3. Write `operator-quality-analysis.md` and classify the first unresolved decisive
   signal as infra/provider/auth/wrapper, adapter integration, orchestration,
   contract/validator, prompt/stagepack, harness/grader/rubric, target repo setup,
   or model artifact quality.
4. If AIDD needs a fix, change the smallest vertical slice, update tests/docs for
   touched orchestration/adapters/contracts/prompts/validators/harness/evals, run
   repo-local checks, and commit.
5. Rerun the same manifest/runtime until it is clean.
6. After one clean pass, switch to another maintained scenario/provider until the
   matrix has at least five counted clean `>= medium` passes with provider coverage.

## First triage for common failures

- Provider executable missing: install/login to the selected provider CLI, or export `AIDD_EVAL_CODEX_COMMAND` / `AIDD_EVAL_OPENCODE_COMMAND` for a wrapper.
- Codex native live auth missing: `aidd eval doctor` checks `codex login status`
  from the operator environment that live stage execution inherits.
- Runtime launches but immediately fails in native mode: inspect provider auth, model selection, and sandbox permissions.
- Runtime launches but immediately fails in `adapter-flags` mode: the configured command is probably not an AIDD-compatible wrapper command.
- `unsupported-runtime`: the runtime is not declared in the scenario's `runtime_targets`.
- `blocked`: inspect `operator-action-request.md`, `questions.md`, and
  `answers.md`; as the launching operator-agent, write `[resolved]` answers,
  using exact lines such as `- Q1 [resolved] answer text`, write
  `answer-analysis.md`, then rerun the same black-box command to resume.
- `fail` after run success: inspect `verify-transcript.json`, `quality-transcript.json`, and the stage-local validator reports.
- Missing clean execution despite zero exit codes: inspect `verdict.md` and `grader.json` for pass-guard failures caused by missing `stage-result.md` or `validator-report.md`.

## Procedure

1. Confirm the selected scenario is in `harness/scenarios/live/`, has `automation_lane: manual`, and declares the requested runtime in `runtime_targets`.
2. Run the local preflight checks from this skill, including `aidd eval doctor`.
3. Export a wrapper env var only when you intentionally want `adapter-flags` mode.
4. Launch `uv run python -m aidd.harness.live_e2e_black_box <manifest> --runtime <runtime>`.
5. Preserve the resulting bundle and inspect `verdict.md`, `grader.json`, `quality-report.md`, and transcripts before judging the run.
6. For `blocked` runs, answer questions yourself as the launching operator-agent,
   write `answer-analysis.md`, and rerun the same command to resume.
7. For terminal `qa`, inspect Flow Complete and record the next-flow terminal
   checkpoint decision before judging the run.
8. For terminal runs, write `operator-quality-analysis.md` before deciding
   counted/not-counted.
9. If the setup, provider coverage, size classification, quality recipe, or verification recipe had to change, update the scenario manifest, matrix doc, and catalog after the run as separate follow-up work.

## Hard rules

- Never treat live E2E as a CI or release lane.
- Never assume this skill provisions runtime auth, wrappers, or provider setup.
- Never route live E2E through GitHub Actions, CI/CD, or release workflows.
- Never require launching a second public-repository flow for a clean live E2E result.
- Never run a live scenario without storing the resolved repo pin.
- Never run a live scenario without storing the selected authored task snapshot.
- Never treat a live scenario as canonical unless it executes `idea -> qa`.
- Never treat a live scenario as passed without install evidence and verification output.
- Never treat a live scenario as clean without `quality-report.md`,
  `quality-transcript.json`, and `operator-quality-analysis.md`.
- Never let operator analysis upgrade a machine `fail` or `warn` quality gate to a
  counted clean pass.
- Preserve all runtime logs.
- Keep `.aidd` rooted inside the target repository for installed live runs.
