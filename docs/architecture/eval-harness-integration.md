# Eval and Harness Integration

## 1. Purpose

This document defines how harness and eval capabilities are embedded into AIDD and how
they relate to deterministic CI checks and manual external audits.

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
- install preparation for manual external audit lanes;
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

### 4.4 Manual external operator-audit layer

This layer answers: can an operator manually install AIDD, enter a real repository,
select a reproducible authored task, run the governed flow from `idea` through `qa`,
preserve execution evidence, and write any deliverable-quality decision manually
after the terminal run?

Its contract is:

- the target repository is a pinned public repository from the external eval catalog;
- the artifact under test is an installed AIDD CLI, not a source-checkout shortcut;
- the selected task comes from the scenario's authored task pool;
- workflow bounds are explicit and fixed to the scenario policy;
- AIDD runs only through public installed CLI surfaces;
- install, setup, run, verify, and teardown evidence is preserved;
- automation for this lane is manual-only and must not be treated as a CI or release gate.
  Detailed runbooks and artifact inventories live in `docs/e2e/`.

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
- manual answer policy and interview expectations;
- grading rules;
- timeout and patch-budget limits.

Manual external scenarios additionally imply installed-artifact identity, authored-task
selection, public operator-surface execution, manual quality decisions, and durable
audit-bundle evidence. The exact command, environment, and artifact contract belongs to
`docs/e2e/live-e2e-catalog.md` and `docs/e2e/live-quality-rubric.md`.

Deterministic scenarios additionally imply:

- `feature_source.mode: fixture-seed`;
- repo-local or fixture-local execution expectations;
- CI eligibility only when `automation_lane: ci`.

## 6. Eval run lifecycle

1. Load the scenario and validate runtime eligibility.
2. Probe the requested adapter and record capabilities.
3. For manual external audits, prepare the installed artifact and pinned target
   repository according to the scenario policy in `docs/e2e/`.
4. Resolve and persist the scenario feature seed:
   - fixture-owned seed metadata for deterministic scenarios;
   - the first authored task for manual external scenarios.
5. Prepare the AIDD artifact under test when the scenario uses the manual external lane.
6. Run setup commands in the target repository root with a non-interactive harness
   environment (`CI=1`, Corepack download prompts disabled, and package-manager
   audit/fund prompts disabled) so setup cannot wait on hidden terminal input.
7. For manual external audits, execute through public installed-AIDD surfaces, inspect
   evidence, classify the step, and decide whether to continue, request answers, await
   manual quality review, stop, or finish.
8. Capture raw runtime logs and emitted structured logs when supported.
9. Capture emitted normalized events and include them in first-failure boundary analysis.
10. Capture question and answer artifacts whenever a manual external or deterministic run uses them.
11. Capture validator outcomes and repair attempts.
12. Write runner-owned per-stage-run audits after every manual external stage attempt.
13. For product-evaluation scenarios, stop after successful stage runs until manual
    quality evidence is supplied. `blocked` remains reserved for unresolved questions
    or runtime approvals. A manual remediation decision uses the existing operator
    remediation flow instead of a runner-owned product-quality shortcut.
14. Run scenario verification commands.
15. Run log analysis.
16. Write execution-only grader data, verdict, summary, and durable bundle metadata,
    including install provenance when applicable.
17. After the terminal run, the launching SWE agent may write manual
    `flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`;
    the runner does not create, parse, or score those quality decisions.

## 7. Mandatory output artifacts

Manual external eval runs should write durable execution evidence, timing evidence,
log-analysis evidence, validator/repair evidence, and final summary/verdict artifacts
under the eval report root. Product-evaluation quality reports are manual artifacts:
they are not runner-scored and must not mutate the execution verdict. The exact bundle
inventory and workspace-evidence contract live in `docs/e2e/`.

Manifest authors must keep installed-AIDD self-checks on the installed CLI surface,
for example `aidd stage questions ...`, instead of source-checkout commands.
Repository-native test commands may still use that repository's normal package manager.

`self-repair-matrix.json` and `.md` include the deterministic repair-probe catalog for
all stages from `idea` to `qa`. Each probe row records the observed initial verdict,
repair success, attempts used, final failure code, and terminal document consistency
from the run artifacts when that stage was reached.
Repair attempts also persist per-attempt `repair-context.md` under the run attempt
directory so timing reports can attribute the repair reason to the exact retry rather
than the final `repair-brief.md` state.
Manual external runs should additionally preserve install provenance in harness metadata:
install channel, artifact source, artifact identity, repository cwd, workspace root, and
packaged-resource source.

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
- local manual operator audits: external audits against curated public repositories;
- release: build, publish, and PyPI installability verification only.

## 11. Summary

Harness and eval make runtime agnosticism, deterministic regression coverage, and manual
installed-operator audits measurable rather than aspirational.
