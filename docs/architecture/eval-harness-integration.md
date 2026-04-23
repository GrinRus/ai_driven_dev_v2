# Eval and Harness Integration

## 1. Purpose

This document explains how harness and eval capabilities are embedded into AIDD v2 from the beginning.

## 2. Why harness is part of product architecture

AIDD v2 supports multiple runtimes and document repair loops. That means the system can fail in ways that ordinary unit tests do not capture:

- runtime availability problems,
- permission or auth issues,
- document validation churn,
- self-repair loops,
- question/answer pauses,
- adapter-specific log behavior,
- drift between runtimes.

The harness is therefore a core subsystem, not an afterthought.

## 3. Harness responsibilities

The harness owns:

- fixture workspace setup,
- scenario loading,
- adapter probing,
- stage execution control,
- raw log capture,
- normalized event capture,
- validator and repair history capture,
- replay support,
- grader invocation,
- log analysis,
- final verdict assembly.

## 4. Eval layers

### 4.1 Unit validation layer

- document validators,
- parser behavior,
- cross-document rules,
- failure classification.

### 4.2 Adapter conformance layer

- probe,
- launch,
- raw log capture,
- question handling,
- timeout behavior,
- failure mapping.

### 4.3 Stage smoke layer

Run one stage with a controlled fixture and verify:
- output documents,
- validator behavior,
- repair behavior,
- logs.

### 4.4 Full e2e workflow layer

Run the complete workflow or a large subset across a realistic repository fixture.

## 5. Scenario model

Harness scenarios should be defined in YAML and describe:

- scenario id,
- runtime(s),
- fixture repo,
- stage scope,
- prompt pack versions,
- validation expectations,
- whether user questions are expected,
- grading rules,
- timeout and budget limits.

Determinism rules:

- live scenarios must pin `repo.revision` to an immutable commit sha;
- harness metadata must record scenario-manifest hash and resolved execution revision;
- replay of a prior run must reuse the same scenario manifest and revision pin.

## 6. Eval run lifecycle

1. Probe the requested adapter.
2. Materialize or reset the fixture workspace.
3. Start the requested stage or flow.
4. Capture raw runtime logs.
5. Capture normalized events.
6. Record question/answer events.
7. Record validator outcomes.
8. Record repair attempts.
9. Run graders.
10. Run log analysis.
11. Write final verdict artifacts.

Grader output must include three explicit lanes:

- contract compliance,
- process compliance,
- task outcome.

## 7. Mandatory output artifacts

Every eval run should aim to write:

- `.aidd/reports/evals/<run_id>/runtime.log`
- `.aidd/reports/evals/<run_id>/runtime.jsonl` when supported
- `.aidd/reports/evals/<run_id>/events.jsonl`
- `.aidd/reports/evals/<run_id>/validator-report.md`
- `.aidd/reports/evals/<run_id>/repair-history.md`
- `.aidd/reports/evals/<run_id>/log-analysis.md`
- `.aidd/reports/evals/<run_id>/grader.json`
- `.aidd/reports/evals/<run_id>/verdict.md`
- `.aidd/reports/evals/<run_id>/harness-metadata.json` including scenario hash and execution pin.

## 8. Log analysis requirements

Log analysis is mandatory for eval runs because logs often reveal adapter and runtime problems before graders do.

The analysis should detect at least:

- repeated identical failure loops,
- repeated validator failures across repair attempts,
- permission denials,
- auth problems,
- no-op runs,
- missing file writes,
- suspiciously short runs,
- timeout drift,
- excessive question churn.

Output should exist in both:
- human-readable Markdown,
- machine-friendly structured form if needed later.

## 9. Converting failures into regression cases

Every real-world failure that matters should be convertible into:

- a fixture,
- a scenario,
- a grader,
- and an expected result.

This is how the project accumulates reliability over time.

## 10. CI integration

Recommended CI layers:

- pull request: lint, typecheck, unit tests, one smoke scenario,
- main branch: wider smoke matrix,
- nightly: adapter conformance + selected e2e evals,
- release: full maintained runtime matrix.

## 11. Summary

Harness and eval are required to make runtime agnosticism measurable rather than aspirational.
