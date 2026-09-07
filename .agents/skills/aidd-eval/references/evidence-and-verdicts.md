# Eval Evidence and Verdicts

Read the sections needed to audit an existing bundle. Deterministic and live runners
own execution reports; retain their original files and write maintainer analysis
separately. Missing optional event streams are a capability fact, not proof of failure.

## Bundle identity and ownership

Start from the run id and the roots printed by the command. The default bundle is
`.aidd/reports/evals/<run_id>/`; an explicit `--root` or `--report-root` changes it.
Inspect scenario identity, fixture/repository pin, runtime configuration, stage/attempt
identity, prompt paths/hashes, validator outcomes, and repair/interview history.

Preserve `runtime.log`, plus `runtime.jsonl` and `events.jsonl` when supported.
Keep `install-transcript.json` and `feature-selection.json` for live runs, and
fixture-seed metadata for deterministic runs. AIDD owns canonical `stage-result.md`,
`validator-report.md`, and runner-generated reports; raw runtime copies do not control
progression. Never hand-edit runtime-generated stage output documents during an eval run.
Operator-authored `answers.md`, stage quality audits, and final quality reports are
distinct from those runtime outputs.

For selected-task implementation also inspect `task-flow-checkpoint.json` and `.md`, tasklist and
ledger hashes, selected task/attempt identity, dependency status, and aggregate
finalization before accepting Review eligibility. Use the recorded schema version
and paths rather than inferring task success from the outer stage status.

## Live execution checks

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
- `manual-frontend-evidence/` only when `--manual-frontend-evidence` is provided
- `next-flow-checkpoint.json`
- `next-flow-checkpoint.md`
- `next-flow-lineage.json` only when `--enable-next-flow-follow-up-proof` is explicitly enabled
- `stage-audits/<stage-run-id>.json`
- `stage-audits/<stage-run-id>.md`
- `stage-quality-audits/<stage-run-id>.md` for every completed product-evaluation
  stage run
- `target-workspace-evidence.json`
- `target-workspace-evidence.md`
- `product-evaluation-bundle-summary.json` and
  `product-evaluation-bundle-summary.md` for terminal product-evaluation bundles
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
The generated bundle summary can point you to missing/stale evidence, but it is not
a runner-owned quality score and never replaces the manual final report.

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

## First triage for common failures

- Provider executable missing: record the missing prerequisite. Install/authenticate or configure a wrapper only within the operator-authorized setup scope; this workflow does not provision credentials.
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
  `answer-analysis.md`, then resume with the same manifest, runtime, work/report roots, and explicit `--run-id` from `flow-state.json`.
- `fail` after run success: inspect `verify-transcript.json` and the stage-local validator reports.
- `manual-quality-stop`: inspect `manual-quality-stop.md`, the referenced
  `stage-quality-audits/<stage-run-id>.md`, `stage-audits/<stage-run-id>.*`, and
  `target-workspace-evidence.*`; do not classify it as infra/provider failure.
- Missing clean execution despite zero exit codes: inspect `verdict.md` and `grader.json` for pass-guard failures caused by missing `stage-result.md` or `validator-report.md`.
