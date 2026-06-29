---
name: live-e2e
description: Run or prepare a manual full-flow live end-to-end scenario against a public GitHub repository with repository pinning, authored task selection, execution evidence capture, and manual post-run quality reporting.
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
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals
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
11. run setup, stage, verify, and teardown commands from the target repository root
    with the installed `aidd` binary on `PATH`;
12. inherit the launching operator's `HOME` and provider environment during stage
    execution so native provider auth works without copying credentials;
13. plan step, execute through public operator surfaces, inspect artifacts/UI/API/logs,
   classify, and decide the next step for every stage from `idea -> qa`;
14. write `stage-audits/<stage-run-id>.json` and `.md` after every stage run;
15. for `product-evaluation`, stop after each successful stage with
    `awaiting-quality-review` and require the launching agent to write
    the exact `stage-quality-audits/<stage-run-id>.md` path named in
    `flow-state.json` before resuming the same `--run-id`;
16. for `product-evaluation`, preserve repeated development loops through stage-run
    ids, so a real remediation cycle such as `implement -> review -> implement ->
    review -> qa` does not overwrite earlier runner or manual audit evidence;
17. write final execution-only audit artifacts from the recorded step evidence.

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

When the evaluator returns `awaiting-quality-review`:

1. Open `flow-state.json` and read `quality_review_required_stage_run_id`,
   `quality_review_required_path`, `completed_stage_runs`, `current_iteration`,
   `pending_remediation`, and `stale_downstream_stages`.
2. Read the stage output, `stage-audits/<stage-run-id>.json`,
   `stage-audits/<stage-run-id>.md`,
   runtime logs, target workspace evidence, and relevant target repo diff.
3. Write `stage-quality-audits/<stage-run-id>.md` at the required path.
4. Use `Flow decision: continue` or `continue-with-risk` to allow resume,
   `request-remediation` only for `review` or `qa`, `operator-intervention` to keep
   the run waiting, or `stop-not-counted` to end the run as manual quality stop on the
   next resume.
5. Re-run the same black-box command with the same `--run-id` only after writing the
   stage quality audit file.

When a `review` or `qa` audit chooses `request-remediation`, include the remediation
request section. On resume, the runner uses the existing operator remediation surface
to create the durable request, run one new `implement`, mark downstream `review` and
`qa` stale, and then rerun each stale downstream stage one at a time with another
quality checkpoint after each stage run. Do not use `operator-intervention` for this
normal remediation loop; reserve it for human intervention that must happen outside
the automatic remediation path.

Use this stage audit template:

```markdown
# Stage Quality Audit: <stage-run-id>

## Decision
- Stage run id: <stage-run-id>
- Stage: idea | research | plan | review-spec | tasklist | implement | review | qa
- Iteration: 1
- Stage quality: strong | acceptable | weak | failed
- Flow decision: continue | continue-with-risk | request-remediation | stop-not-counted | operator-intervention
- Reason:

## Remediation Request
- Source stage: review | qa
- Source ids: RV-1, EV-1
- Operator note:

## Checks
- Product alignment:
- Evidence quality:
- Repository understanding:
- Missing questions or assumptions:
- Cross-stage consistency:
- Risk handling:
- Specific defects:

## Evidence Reviewed
- Stage artifacts:
- Runtime logs:
- Runner stage audit:
- Previous stage-run evidence:
- Target repo evidence:
- Stale downstream state:

## Notes For Final Report
- AIDD quality signal:
- Residual risks:
```

After any terminal product-evaluation run, the launching SWE agent must write
`flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md` in the
eval bundle before deciding counted-clean product quality. The runner does not create,
parse, validate, or score these files. Use this final report outline:

```markdown
# Live E2E Quality Report

## Decision
- Run integrity decision: clean | defective | blocked-infra | blocked-provider | blocked-harness
- Operator UI/UX decision: acceptable | acceptable-with-risks | not-acceptable | not-applicable
- Final decision: counted-clean | not-counted | blocked-model-quality | blocked-product-defect

## Stage-by-stage Quality Summary
- <stage-run-id> / <stage> / iteration <n>:

## Iteration History
- Initial pass:
- Remediation requests:
- Stale downstream reruns:
- Fresh terminal QA state:

## Product Delivery Assessment
- Product request fit:
- Acceptance criteria coverage:
- Requirement/interview handling:
- Cross-stage consistency:
- Residual product risks:

## Code Quality Assessment
- Diff scope, including tracked and untracked files:
- Architecture/maintainability/API compatibility:
- Edge cases/security/performance risks:
- Code review defects:
- Code evidence links:

## Test And Verification Assessment
- Commands run:
- Baseline/before-after evidence:
- Regression relevance:
- Not-run or deferred checks:
- Verification gaps:

## Run Integrity
- Execution verdict:
- Stages reached:
- Evidence completeness:
- Runtime/provider/log issues:
- Repair/interview behavior:
- Timeout policy/evidence:
- Awaiting-quality-review checkpoints:

## UI/UX Quality
- Operator UI workflows inspected:
- Terminal flow visibility:
- Navigation and discoverability:
- State clarity:
- Readability/layout:
- Accessibility/keyboard/focus notes:
- Responsive behavior notes:
- Generated product UI applicability:
- Operator UI/UX evidence links:

## Evidence Reviewed
- Flow evidence:
- Runner stage audits:
- Stage quality audits:
- Logs/transcripts:
- Target repo diff:
- Review/QA artifacts:
- Operator UI/API checkpoints, next-flow checkpoint, or manual screenshot/browser evidence:
- Extra manual checks run by SWE agent:

## Notes
- Follow-ups:
- Residual risks:
```

Keep `Run Integrity` separate from artifact, code, test, and UI/UX quality.
API probes in `frontend-checkpoints.*` are raw surface evidence, not a UI/UX audit.
Screenshots and browser notes are optional manual evidence, not runner-generated artifacts.
The `Operator UI/UX decision` is a manual AIDD operator-UI sub-decision only; it
does not change `verdict.md`, `grader.json`, or any execution status. Inspect
terminal flow visibility, stage list navigation, artifact/log views, questions and
answers, repair evidence, next-flow handoff, state clarity, readability, keyboard
path, focus visibility, responsive behavior, and any manually captured screenshots
or browser notes. Mark generated product UI as `not-applicable` unless you
explicitly performed a separate product-UI review.

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

The live execution run can fail or block at several layers:

- manifest validation rejects non-live scenarios, non-manual live scenarios,
  manifests that still declare `quality:`, invalid `runtime_targets`, or any
  live scenario that is not bounded to `idea -> qa`;
- runtime admission rejects a requested runtime that is not declared in `runtime_targets`;
- stage execution stays bounded to `idea -> qa`;
- stage outputs must validate against Markdown document contracts;
- repair loops are allowed to run when validation failures are repairable;
- any live scenario may block when required answers are missing;
- `live-full-flow-interview` scenarios are coverage cases where a blocking
  interview path is expected by the manifest;
- repo-local `verify.commands` must pass;
- execution `pass` is impossible if any stage in scope is missing required validated artifacts.

Live execution verdicts remain:

- `pass`
- `fail`
- `blocked`
- `infra-fail`

Deliverable quality is manual post-run analysis in
`stage-quality-audits/<stage-run-id>.md`,
`flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`; it is
not a runner verdict and does not change the execution verdict.
When a stage audit chooses `Flow decision: stop-not-counted`, the next resume ends
as `manual-quality-stop`; inspect `manual-quality-stop.md` and
`manual-quality-stop.json` instead of expecting `verdict.md`/`grader.json`.

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
- `next-flow-checkpoint.json`
- `next-flow-checkpoint.md`
- `next-flow-lineage.json` only when `--enable-next-flow-follow-up-proof` is explicitly enabled
- `stage-audits/<stage-run-id>.json`
- `stage-audits/<stage-run-id>.md`
- `stage-quality-audits/<stage-run-id>.md` for every completed product-evaluation
  stage run
- `target-workspace-evidence.json`
- `target-workspace-evidence.md`
- `feature-selection.json`
- `install-transcript.json`
- `runtime.log`
- `validator-report.md`
- `repair-history.md`
- `log-analysis.md`
- `run-transcript.json` with `timeout_policy.scope: per-stage-command`
- `grader.json` for terminal execution verdicts only
- `verdict.md` for terminal execution verdicts only
- `manual-quality-stop.json` and `manual-quality-stop.md` only when a stage audit
  chooses `stop-not-counted`
- `answer-analysis.md` when the run answered blocking questions
- `flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md` only
  when the launching SWE agent manually writes the final product-quality reports

A live execution run is `pass` when execution evidence exists, all required
stages reached terminal success, and `verify.commands` passed. A clean deliverable
quality decision for product-evaluation requires every stage quality audit plus
`flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`.

For stepwise black-box live runs, manifest `limits.timeout_minutes` is the budget
for each public `aidd stage run` command. It is not a global flow timeout. Inspect
`run-transcript.json.timeout_policy`, `stage-timing.*`, and `log-analysis.md` for
timeout evidence, and inspect `stage-audits/<stage-run-id>.*` for non-gating
stage-result/validator consistency findings.
For live manifest authoring and audits, AIDD self-check verification commands must
call the installed `aidd` binary directly, for example `aidd stage questions ...`.
Do not use `uv run aidd ...` from the target repo: it can create package-manager
lockfiles after QA and pollute the final target workspace evidence. Keep target-project
tests on the package manager expected by the target repository.
Also inspect `target-workspace-evidence.*` for non-gating target workspace findings:
tracked product diff, setup-baseline untracked files, `aidd.example.toml` harness
config, top-level `workitems/...` pollution, stray `.aidd/` scratch files, and ignored
local artifacts such as `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pdm-build/`,
`coverage/`, build, dist, or dependency-cache files.
For `implement`, inspect the matching `stage-audits/<implement-stage-run-id>.*`
buckets for tracked changed
files, new untracked product files, known harness/config untracked files, and
setup-baseline untracked files. New untracked product files must be reviewed as
deliverable code, and JavaScript/TypeScript helper additions must be checked against
`package.json` `exports`, wildcard subpath exports, generated declarations, and
existing public import conventions before accepting internal-only claims. If
`product_untracked_files` is present, final `code-quality-report.md` and
`quality-report.md` must name those files and state how each was reviewed before a
`counted-clean` decision.
If manifest verification creates only new known ignored residue after QA, inspect
`verify-transcript.json.workspace_cleanup`; runner cleanup of that residue is
execution hygiene and does not replace manual deliverable-quality review.
New ignored files inside an ignored root that already existed at setup, such as
`.venv/.../__pycache__`, are setup-baseline ignored churn rather than pollution
findings.
In manual review, top-level `workitems/...` duplicates normally make manual deliverable quality `not-counted`;
`aidd.example.toml` is not product diff. Evidence that a runtime deleted/recreated the
prepared checkout or live harness run directories such as `install-home/`, `source/`,
`build/`, or `target/` normally makes deliverable quality `not-counted`.

## Iteration loop contract

For live stabilization, the launching agent should repeat this external
operator loop instead of relying on a self-mutating product command:

1. Run one `>= medium` product-evaluation live scenario through the black-box evaluator.
2. Read the full evidence bundle, including every `stage-audits/<stage-run-id>.json`,
   every `stage-quality-audits/<stage-run-id>.md`, `target-workspace-evidence.json`,
   `verdict.md`/`grader.json` for terminal execution verdicts or
   `manual-quality-stop.*` for manual quality stops, transcripts, and logs.
3. Write manual `flow-quality-report.md`, `code-quality-report.md`, and
   `quality-report.md` when deliverable quality must be judged, and
   classify the first unresolved decisive
   signal as infra/provider/auth/wrapper, adapter integration, orchestration,
   contract/validator, prompt/stagepack, harness/grader/rubric, target repo setup,
   or model artifact quality.
4. If AIDD needs a fix, change the smallest vertical slice, update tests/docs for
   touched orchestration/adapters/contracts/prompts/validators/harness/evals, run
   repo-local checks, and commit.
5. Rerun the same manifest/runtime until it is clean.
6. After one execution pass with acceptable manual quality, switch to another
   maintained scenario/provider until the matrix has sufficient provider coverage.

## First triage for common failures

- Provider executable missing: install/login to the selected provider CLI, or export `AIDD_EVAL_CODEX_COMMAND` / `AIDD_EVAL_OPENCODE_COMMAND` for a wrapper.
- Codex native live auth missing: `aidd eval doctor` checks `codex login status`
  from the operator environment that live stage execution inherits.
- Runtime launches but immediately fails in native mode: inspect provider auth, model selection, and sandbox permissions.
- Runtime launches but immediately fails in `adapter-flags` mode: the configured command is probably not an AIDD-compatible wrapper command.
- `provider-no-progress`: `provider-no-progress before completed stage artifact`
  means the public `aidd stage run` process stayed alive but stdout/stderr and
  watched stage artifacts stopped changing until
  `limits.no_progress_timeout_minutes` elapsed. Inspect `log-analysis.md`,
  `flow-steps.json`, `stage-timing.json`, and the no-progress reconciliation file;
  classify it as infra/provider blocker, not counted-clean, not
  `manual-quality-stop`, not unresolved-question `blocked`, and not product-quality
  failure.
- Unsupported `review-spec` claims: high-severity issues without direct evidence,
  contradictions with upstream `research` or `plan` without `Reconciliation`, or stale
  `stage-result.md` failure claims after canonical validation passes are AIDD
  stage-output/prompt/validator evidence. Do not classify them as provider no-progress,
  `manual-quality-stop`, unresolved-question `blocked`, or product-quality verdicts.
- `unsupported-runtime`: the runtime is not declared in the scenario's `runtime_targets`.
- `blocked`: inspect `operator-action-request.md`, `questions.md`, and
  `answers.md`; as the launching operator-agent, write `[resolved]` answers,
  using exact lines such as `- Q1 [resolved] answer text`, write
  `answer-analysis.md`, then rerun the same black-box command to resume.
- `fail` after run success: inspect `verify-transcript.json` and the stage-local validator reports.
- `manual-quality-stop`: inspect `manual-quality-stop.md`, the referenced
  `stage-quality-audits/<stage-run-id>.md`, `stage-audits/<stage-run-id>.*`, and
  `target-workspace-evidence.*`; do not classify it as infra/provider failure.
- Missing clean execution despite zero exit codes: inspect `verdict.md` and `grader.json` for pass-guard failures caused by missing `stage-result.md` or `validator-report.md`.

## Procedure

1. Confirm the selected scenario is in `harness/scenarios/live/`, has `automation_lane: manual`, and declares the requested runtime in `runtime_targets`.
2. Run the local preflight checks from this skill, including `aidd eval doctor`.
3. Export a wrapper env var only when you intentionally want `adapter-flags` mode.
4. Launch `uv run python -m aidd.harness.live_e2e_black_box <manifest> --runtime <runtime>`.
5. Preserve the resulting bundle and inspect `verdict.md`, `grader.json`, transcripts, and logs before judging execution. For `manual-quality-stop`, inspect `manual-quality-stop.*` instead of execution verdict artifacts.
6. For `blocked` runs, answer questions yourself as the launching operator-agent,
   write `answer-analysis.md`, and rerun the same command to resume.
7. For `awaiting-quality-review`, write the required stage audit before resume.
8. For terminal `qa`, inspect Flow Complete and record the next-flow terminal
   checkpoint decision before judging the run.
9. For terminal product-evaluation runs, write manual `flow-quality-report.md`,
   `code-quality-report.md`, and `quality-report.md` before deciding counted/not-counted
   deliverable quality.
10. If the setup, provider coverage, size classification, or verification recipe had to change, update the scenario manifest, matrix doc, and catalog after the run as separate follow-up work.

## Hard rules

- Never treat live E2E as a CI or release lane.
- Never assume this skill provisions runtime auth, wrappers, or provider setup.
- Never route live E2E through GitHub Actions, CI/CD, or release workflows.
- Never require launching a second public-repository flow for a clean live E2E result.
- Never run a live scenario without storing the resolved repo pin.
- Never run a live scenario without storing the selected authored task snapshot.
- Never treat a live scenario as canonical unless it executes `idea -> qa`.
- Never treat a live scenario as passed without install evidence and verification output.
- Never treat a live execution pass as a deliverable-quality pass without manual
  stage quality audits and final quality reports.
- Never let the manual quality report upgrade a failed execution verdict.
- Preserve all runtime logs.
- Keep `.aidd` rooted inside the target repository for installed live runs.
