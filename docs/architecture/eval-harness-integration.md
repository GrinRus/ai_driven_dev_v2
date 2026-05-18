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

This layer answers: can an operator manually install AIDD, enter a real repository, select a reproducible authored task, run the governed flow from `idea` through `qa`, and prove both execution and quality?

Its contract is:

- the target repository is a pinned public repository from the live catalog;
- the artifact under test is an installed AIDD CLI, not a source-checkout shortcut;
- the selected task comes from the scenario's authored task pool;
- live workflow bounds are explicit and fixed to `idea -> qa`;
- AIDD runs from the target repository root;
- `.aidd/` is rooted inside that repository;
- the harness seeds a target-repository `aidd.example.toml` for the installed run;
- install, setup, run, verify, quality, and teardown evidence is preserved;
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
- quality gate policy;
- interview expectations;
- grading rules;
- timeout and patch-budget limits.

Live scenarios additionally imply:

- install channel;
- artifact source and identity;
- deterministic authored task selection from the manifest task pool;
- target repository cwd as the operator execution root;
- `.aidd` workspace rooted inside that target repository.
- a live runtime config written into the prepared working copy, with optional command overrides from `AIDD_EVAL_<RUNTIME>_COMMAND`.
- one post-verification quality phase that writes quality artifacts without mutating roadmap or backlog files.

Deterministic scenarios additionally imply:

- `feature_source.mode: fixture-seed`;
- repo-local or fixture-local execution expectations;
- CI eligibility only when `automation_lane: ci`.

## 6. Eval run lifecycle

1. Load the scenario and validate runtime eligibility.
2. Probe the requested adapter and record capabilities.
3. Prepare or reset the pinned target repository working copy.
4. Resolve and persist the scenario feature seed:
   - fixture-owned seed metadata for deterministic scenarios;
   - the first authored task for live scenarios.
5. Prepare the AIDD artifact under test when the scenario uses the installed-live lane.
6. Run setup commands in the target repository root.
7. For live E2E, plan the next step, execute through public installed-AIDD surfaces
   (`aidd stage run` plus inspection commands), inspect evidence, classify the step,
   and decide whether to continue, request answers, stop, or finish.
8. Capture raw runtime logs and emitted structured logs when supported.
9. Capture emitted normalized events and include them in first-failure boundary analysis.
10. Capture question and answer artifacts when used.
11. Capture validator outcomes and repair attempts.
12. Run scenario verification commands.
13. Run scenario quality commands.
14. Run graders and quality scoring.
15. Run log analysis.
16. Write verdict and durable bundle metadata, including install provenance when applicable.

## 7. Mandatory output artifacts

Every black-box live E2E run should aim to write:

- `.aidd/reports/evals/<run_id>/flow-state.json`
- `.aidd/reports/evals/<run_id>/flow-steps.json`
- `.aidd/reports/evals/<run_id>/flow-report.md`
- `.aidd/reports/evals/<run_id>/operator-actions.jsonl`
- `.aidd/reports/evals/<run_id>/frontend-checkpoints.json`
- `.aidd/reports/evals/<run_id>/frontend-checkpoints.md`
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
- `.aidd/reports/evals/<run_id>/quality-report.md`
- `.aidd/reports/evals/<run_id>/summary.md`
- `.aidd/reports/evals/<run_id>/feature-selection.json`
- `.aidd/reports/evals/<run_id>/setup-transcript.json`
- `.aidd/reports/evals/<run_id>/run-transcript.json`
- `.aidd/reports/evals/<run_id>/verify-transcript.json`
- `.aidd/reports/evals/<run_id>/quality-transcript.json`

`self-repair-matrix.json` and `.md` include the deterministic repair-probe catalog for
all stages from `idea` to `qa`. Each probe row records the observed initial verdict,
repair success, attempts used, final failure code, and terminal document consistency
from the run artifacts when that stage was reached.
Repair attempts also persist per-attempt `repair-context.md` under the run attempt
directory so timing reports can attribute the repair reason to the exact retry rather
than the final `repair-brief.md` state.
- `.aidd/reports/evals/<run_id>/teardown-transcript.json`

Installed live runs should additionally preserve install provenance in harness metadata:

- install channel;
- artifact source;
- artifact identity;
- target repository cwd;
- workspace root;
- packaged-resource source.

The machine-readable grader payload must preserve separate execution and quality sections so execution verdict taxonomy remains stable while the quality gate can still downgrade or fail a run.

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

Quality analysis is also mandatory for live E2E because a technically completed run can still produce weak artifacts or weak code. The quality layer should score:

- `flow_fidelity`
- `artifact_quality`
- `code_quality`

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
- manual workflow dispatch: installed live external audits against curated public repositories;
- release: build, publish, and PyPI installability verification only.

## 11. Summary

Harness and eval make runtime agnosticism, deterministic regression coverage, and manual installed-operator audits measurable rather than aspirational.
