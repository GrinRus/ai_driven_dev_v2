# Eval and Harness Integration

## 1. Purpose

This document defines how harness and eval capabilities are embedded into AIDD and how they relate to deterministic CI checks and manual live E2E audits.

## 2. Why harness is part of product architecture

AIDD supports multiple runtimes, repair loops, and interview pauses. Ordinary unit tests do not capture failures such as:

- runtime availability problems;
- installability drift between source and packaged CLI paths;
- permission or auth issues;
- document validation churn;
- self-repair loops;
- question and answer pauses;
- adapter-specific log behavior;
- drift between maintained runtimes;
- divergence between contributor checkout behavior and operator-installed behavior.

The harness is therefore product code, not an afterthought.

## 3. Harness responsibilities

The harness owns:

- scenario loading;
- adapter probing;
- repository preparation and pinning;
- install preparation for installed-live lanes;
- stage or workflow execution control;
- raw log capture;
- normalized event capture;
- validator and repair history capture;
- question and answer artifact capture;
- replay support;
- grader invocation;
- log analysis;
- final verdict assembly;
- durable result-bundle writing.

## 4. Eval layers

### 4.1 Unit validation layer

- document validators;
- parser behavior;
- cross-document rules;
- failure classification.

### 4.2 Adapter conformance layer

This layer answers: does an adapter honor the maintained runtime contract?

It covers:

- probe behavior;
- capability declaration;
- launch semantics;
- raw log capture;
- question handling;
- timeout behavior;
- failure mapping;
- workspace targeting.

### 4.3 Stage smoke layer

This layer runs one stage or one bounded workflow subset and verifies:

- required output documents;
- validator behavior;
- repair behavior;
- log capture;
- verdict correctness.

### 4.4 Manual installed live operator layer

This layer answers: can an operator manually install AIDD, enter a real repository,
select a reproducible authored task, run the governed flow from `idea` through `qa`,
preserve execution evidence, and write any deliverable-quality decision manually
after the terminal run?

Its contract is:

- the target repository is a pinned public repository from the live catalog;
- the artifact under test is an installed AIDD CLI, not a source-checkout shortcut;
- the selected task comes from the scenario's authored task pool;
- live workflow bounds are explicit and fixed to `idea -> qa`;
- AIDD runs from the target repository root;
- `.aidd/` is rooted inside that repository;
- the harness seeds a target-repository `aidd.example.toml` for the installed run;
- live manifest `limits.timeout_minutes` is a per-stage public `aidd stage run`
  command budget in the stepwise black-box loop, while provider adapter timeout
  profiles come from the generated target-repository `aidd.example.toml`;
- install, setup, run, verify, and teardown evidence is preserved;
- automation for this lane is manual-only and must not be treated as a CI or release gate.

## 5. Scenario model

Harness scenarios are defined in YAML and describe:

- scenario id;
- scenario class;
- feature size;
- automation lane;
- canonical runtime;
- target repository and optional pin;
- stage scope;
- runtime targets;
- setup and verify commands;
- feature source policy;
- live answer policy and interview expectations;
- grading rules;
- timeout and patch-budget limits.

Live scenarios additionally imply:

- install channel;
- artifact source and identity;
- deterministic authored task selection from the manifest task pool;
- target repository cwd as the operator execution root;
- `.aidd` workspace rooted inside that target repository.
- a live runtime config written into the prepared working copy, with optional command overrides from `AIDD_EVAL_<RUNTIME>_COMMAND`.
- `agent-decides` answer handling for any live scenario that blocks on questions.
- an execution-only bundle lifecycle that stops after verification and teardown;
  any deliverable quality review is a manual post-run `quality-report.md` written
  by the launching SWE agent, not by the runner.

Deterministic scenarios additionally imply:

- `feature_source.mode: fixture-seed`;
- repo-local or fixture-local execution expectations;
- CI eligibility only when `automation_lane: ci`.

## 6. Eval run lifecycle

1. Load the scenario and validate runtime eligibility.
2. Probe the requested adapter and record capabilities.
3. For black-box live E2E, create a temp work layout, snapshot tracked AIDD `HEAD`,
   build/install from that snapshot, and clone the pinned target repository under
   `<work-root>/<run_id>/target/<repo-slug>`.
4. Resolve and persist the scenario feature seed:
   - fixture-owned seed metadata for deterministic scenarios;
   - the first authored task for live scenarios.
5. Prepare the AIDD artifact under test when the scenario uses the installed-live lane.
6. Run setup commands in the target repository root with a non-interactive harness
   environment (`CI=1`, Corepack download prompts disabled, and package-manager
   audit/fund prompts disabled) so setup cannot wait on hidden terminal input.
7. For live E2E, plan the next step, execute through public installed-AIDD surfaces
   (`aidd stage run` plus inspection commands), inspect evidence, classify the step,
   and decide whether to continue, request answers, await manual quality review,
   stop, or finish.
8. Capture raw runtime logs and emitted structured logs when supported.
9. Capture emitted normalized events and include them in first-failure boundary analysis.
10. Capture question and answer artifacts whenever a live or deterministic run uses them.
11. Capture validator outcomes and repair attempts.
12. Write runner-owned per-stage audits after every live stage.
13. For `product-evaluation`, stop after each successful stage with
    `awaiting-quality-review` until the launching agent writes
    `stage-quality-audits/<stage>.md`; `blocked` remains reserved for unresolved
    questions or runtime approvals.
14. Run scenario verification commands.
15. Run log analysis.
16. Write execution-only grader data, verdict, summary, and durable bundle metadata,
    including install provenance when applicable.
17. After the terminal run, the launching SWE agent may write manual
    `flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`;
    the runner does not create, parse, or score those quality decisions.

## 7. Mandatory output artifacts

Every black-box live E2E run should aim to write:

- `.aidd/reports/evals/<run_id>/flow-state.json`
- `.aidd/reports/evals/<run_id>/flow-steps.json`
- `.aidd/reports/evals/<run_id>/flow-report.md`
- `.aidd/reports/evals/<run_id>/operator-actions.jsonl`
- `.aidd/reports/evals/<run_id>/frontend-checkpoints.json`
- `.aidd/reports/evals/<run_id>/frontend-checkpoints.md`
- `.aidd/reports/evals/<run_id>/stage-audits/<stage>.json`
- `.aidd/reports/evals/<run_id>/stage-audits/<stage>.md`
- `.aidd/reports/evals/<run_id>/stage-quality-audits/<stage>.md` for
  product-evaluation stages, written manually before resume
- `.aidd/reports/evals/<run_id>/target-workspace-evidence.json`
- `.aidd/reports/evals/<run_id>/target-workspace-evidence.md`
- `.aidd/reports/evals/<run_id>/runtime.log`
- `.aidd/reports/evals/<run_id>/runtime.jsonl` when attempts emitted structured JSONL
- `.aidd/reports/evals/<run_id>/events.jsonl` when attempts emitted normalized JSONL
- `.aidd/reports/evals/<run_id>/validator-report.md`
- `.aidd/reports/evals/<run_id>/repair-history.md`
- `.aidd/reports/evals/<run_id>/log-analysis.md`
- `.aidd/reports/evals/<run_id>/stage-timing.json`
- `.aidd/reports/evals/<run_id>/stage-timing.md`
- `.aidd/reports/evals/<run_id>/self-repair-matrix.json`
- `.aidd/reports/evals/<run_id>/self-repair-matrix.md`
- `.aidd/reports/evals/<run_id>/grader.json`
- `.aidd/reports/evals/<run_id>/verdict.md`
- `.aidd/reports/evals/<run_id>/summary.md`
- `.aidd/reports/evals/<run_id>/feature-selection.json`
- `.aidd/reports/evals/<run_id>/setup-transcript.json`
- `.aidd/reports/evals/<run_id>/run-transcript.json`
- `.aidd/reports/evals/<run_id>/verify-transcript.json`
- `.aidd/reports/evals/<run_id>/teardown-transcript.json`

`.aidd/reports/evals/<run_id>/flow-quality-report.md`,
`.aidd/reports/evals/<run_id>/code-quality-report.md`, and
`.aidd/reports/evals/<run_id>/quality-report.md` are manual SWE-agent artifacts.
They are not part of execution bundle completeness and must not affect `verdict.md`
or `grader.json`. Product-evaluation counted-clean evidence requires those final
reports plus every `stage-quality-audits/<stage>.md`. When a UI/UX decision is
needed, the report records a human-authored AIDD operator UI/UX decision; the runner
does not derive that decision from `frontend-checkpoints.*`.

`target-workspace-evidence.*` is runner-owned, non-gating evidence. It records the
target repository snapshot after setup and after terminal/stop state, including tracked
diff, baseline untracked files, `aidd.example.toml` as harness config, new untracked
files, top-level `workitems/...` pollution, unexpected `.aidd/` scratch files, and
new ignored local artifacts such as `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pdm-build/`,
`coverage/`, build, dist, or dependency-cache files. New ignored files under an
ignored root that already existed at setup are recorded as setup-baseline ignored
churn rather than pollution findings. Manual review must also treat
runtime attempts to delete/recreate the prepared checkout or live harness run
directories as run integrity evidence, not product implementation. These findings
support manual `quality-report.md` review and must not mutate the execution verdict.
If successful manifest verification creates ignored local byproducts after QA has
completed, `verify-transcript.json.workspace_cleanup` records runner cleanup of
newly-created known verification residue before final `target-workspace-evidence.*`
is captured. This cleanup is execution hygiene only.
Manifest authors must keep installed-live AIDD self-checks on the installed CLI
surface, for example `aidd stage questions ...`, instead of `uv run aidd ...`.
The latter can create target-repository lockfiles during post-QA verification and
turn an otherwise clean execution pass into a manual workspace-pollution finding.
Repository-native test commands may still use that repository's normal package manager.

`self-repair-matrix.json` and `.md` include the deterministic repair-probe catalog for
all stages from `idea` to `qa`. Each probe row records the observed initial verdict,
repair success, attempts used, final failure code, and terminal document consistency
from the run artifacts when that stage was reached.
Repair attempts also persist per-attempt `repair-context.md` under the run attempt
directory so timing reports can attribute the repair reason to the exact retry rather
than the final `repair-brief.md` state.
Installed live runs should additionally preserve install provenance in harness metadata:

- install channel;
- artifact source;
- artifact identity;
- work root;
- source snapshot path and revision when local-wheel mode is used;
- install home;
- uv cache path;
- target repository cwd;
- workspace root;
- packaged-resource source.

The machine-readable grader payload is execution-only. Manual deliverable quality
belongs in the optional post-run `quality-report.md` and must not downgrade or
mutate the execution verdict.

`run-transcript.json` records the aggregate black-box loop and includes a
`timeout_policy` object. Its aggregate `timeout_seconds` remains `null` unless the
runner uses a real global flow timeout; per-stage command budgets are visible in
`stage-timing.json`, `stage-timing.md`, and `log-analysis.md`.

## 8. Log analysis requirements

Log analysis is mandatory because logs often reveal adapter or install-path failures before graders do.

The analysis should detect at least:

- repeated identical failure loops;
- repeated validator failures across repair attempts;
- permission denials;
- auth problems;
- no-op runs;
- missing file writes;
- suspiciously short runs;
- timeout drift;
- excessive question churn;
- install-path mismatches between target cwd and artifact expectations.

Manual post-run quality review is still expected when the launching SWE agent needs a
deliverable-quality decision: a technically completed run can still produce weak
artifacts, weak code, weak tests, or poor operator UI/UX. That review belongs in
`quality-report.md` and is not a runner score. Operator UI/UX review should inspect
completed-flow visibility, stage/artifact/log/question navigation, repair and
next-flow handoff states, readability, keyboard/focus behavior, responsive behavior
or `not inspected`, and any manual screenshots or browser notes.

## 9. Converting failures into regression cases

Every real failure that matters should be convertible into:

- a fixture or public-repo scenario;
- a grader or explicit verify command;
- a reproducible expected result.

This is how the project accumulates reliability instead of anecdote.

## 10. CI and release integration

Recommended layers:

- pull request: lint, typecheck, unit tests, deterministic fixture regressions, and packaging checks;
- main branch: the same deterministic checks or a widened deterministic matrix;
- local manual operator audits: installed live external audits against curated public repositories;
- release: build, publish, and PyPI installability verification only.

## 11. Summary

Harness and eval make runtime agnosticism, deterministic regression coverage, and manual installed-operator audits measurable rather than aspirational.
