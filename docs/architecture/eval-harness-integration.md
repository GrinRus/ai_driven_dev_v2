# Eval and Harness Integration

## 1. Purpose

This document defines how harness and eval capabilities are embedded into AIDD and how they relate to installed live E2E execution.

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

### 4.4 Installed live operator layer

This layer answers: can an operator install AIDD, enter a real repository, select a reproducible issue seed, run the governed flow from `idea` through `qa`, and prove both execution and quality?

Its contract is:

- the target repository is a pinned public repository from the live catalog;
- the artifact under test is an installed AIDD CLI, not a source-checkout shortcut;
- the selected issue comes from the scenario's curated issue pool;
- live workflow bounds are explicit and fixed to `idea -> qa`;
- AIDD runs from the target repository root;
- `.aidd/` is rooted inside that repository;
- the harness seeds a target-repository `aidd.example.toml` for the installed run;
- install, setup, run, verify, quality, and teardown evidence is preserved.

Development and CI should usually exercise this lane through a local wheel installed by `uv tool`.

### 4.5 Published artifact release proof layer

This layer answers: can the published release artifact complete at least one pinned live workflow scenario?

It extends installability checks beyond `aidd --version` and `aidd doctor` to one real live workflow proof.

## 5. Scenario model

Harness scenarios are defined in YAML and describe:

- scenario id;
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
- deterministic issue selection from a curated issue pool;
- target repository cwd as the operator execution root;
- `.aidd` workspace rooted inside that target repository.
- a live runtime config written into the prepared working copy, with optional command overrides from `AIDD_EVAL_<RUNTIME>_COMMAND`.
- one post-verification quality phase that writes quality artifacts without mutating roadmap or backlog files.

## 6. Eval run lifecycle

1. Load the scenario and validate runtime eligibility.
2. Probe the requested adapter and record capabilities.
3. Prepare or reset the pinned target repository working copy.
4. Select and persist one issue seed from the scenario's curated issue pool.
5. Prepare the AIDD artifact under test when the scenario uses the installed-live lane.
6. Run setup commands in the target repository root.
7. Launch AIDD from the target repository root with explicit workflow bounds.
8. Capture raw runtime logs and structured logs when supported.
9. Capture normalized events.
10. Capture question and answer artifacts when used.
11. Capture validator outcomes and repair attempts.
12. Run scenario verification commands.
13. Run scenario quality commands.
14. Run graders and quality scoring.
15. Run log analysis.
16. Write verdict and durable bundle metadata, including install provenance when applicable.

## 7. Mandatory output artifacts

Every eval run should aim to write:

- `.aidd/reports/evals/<run_id>/runtime.log`
- `.aidd/reports/evals/<run_id>/runtime.jsonl` when supported
- `.aidd/reports/evals/<run_id>/events.jsonl` when supported
- `.aidd/reports/evals/<run_id>/validator-report.md`
- `.aidd/reports/evals/<run_id>/repair-history.md`
- `.aidd/reports/evals/<run_id>/log-analysis.md`
- `.aidd/reports/evals/<run_id>/grader.json`
- `.aidd/reports/evals/<run_id>/verdict.md`
- `.aidd/reports/evals/<run_id>/quality-report.md`
- `.aidd/reports/evals/<run_id>/summary.md`
- `.aidd/reports/evals/<run_id>/issue-selection.json`
- `.aidd/reports/evals/<run_id>/setup-transcript.json`
- `.aidd/reports/evals/<run_id>/run-transcript.json`
- `.aidd/reports/evals/<run_id>/verify-transcript.json`
- `.aidd/reports/evals/<run_id>/quality-transcript.json`
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

- pull request: lint, typecheck, unit tests, and one smoke or packaging regression;
- main branch: wider smoke matrix and packaging/resource regressions;
- nightly: adapter conformance and selected installed live runs;
- release: installability checks plus one published-artifact live workflow proof.

## 11. Summary

Harness and eval make runtime agnosticism, installed-operator behavior, and release readiness measurable rather than aspirational.
