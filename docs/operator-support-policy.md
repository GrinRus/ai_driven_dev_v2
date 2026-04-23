# Operator Support Policy

## 1. Purpose

This document defines:

- what operator support AIDD currently provides;
- what information is required for actionable issue reports;
- how maintainers triage incoming operator issues.

As of April 23, 2026, AIDD exposes executable `run`, `stage run`, and `eval run` surfaces.

## 2. Support Scope

### 2.1 Supported operator surfaces

Maintainers currently provide best-effort support for:

- installation and environment bootstrap (`uv sync --extra dev`);
- runtime discovery and probe diagnostics (`uv run aidd doctor`);
- workspace initialization (`uv run aidd init --work-item <id>`);
- workflow and stage orchestration behavior (`aidd run`, `aidd stage run`);
- harness/eval execution behavior (`aidd eval run`, `aidd eval summary`);
- run-inspection commands (`aidd run show`, `aidd run logs`, `aidd run artifacts`);
- stage summaries and question routing (`aidd stage summary`, `aidd stage questions`).

### 2.2 Out-of-scope requests (current phase)

The following are not treated as defects unless roadmap status changes:

- defects in third-party runtime binaries themselves (outside adapter behavior);
- failures caused by missing runtime auth/session state outside AIDD control;
- network/provider outages for live repository or package infrastructure;
- custom local scenario scripts that are not reproducible from committed manifests.

## 3. Issue Types and Triage Intent

Use one primary issue type:

- `installation`: dependency, Python, or `uv` setup blockers;
- `runtime-probe`: runtime detection/version/capability mismatches in `aidd doctor`;
- `run-inspection`: `run show/logs/artifacts` metadata lookup, path resolution, or log retrieval failures;
- `validator-state`: stage summary, validator counts, report linkage, or blocking-question handling;
- `harness-eval`: scenario loading, eval execution, verdict generation, or grader/log-analysis drift;
- `documentation`: operator docs are missing, stale, or contradictory.

## 4. Issue Reporting Instructions

Open a GitHub issue in this repository and include all required sections below.

### 4.1 Required report content

1. Problem statement:
   - one-sentence failure summary;
   - expected behavior;
   - actual behavior.

2. Reproduction steps:
   - exact commands (copy/paste ready);
   - exact scenario path or work item id;
   - exact runtime id.

3. Environment:
   - OS and version;
   - Python version;
   - `uv` version;
   - repository commit SHA.

4. Diagnostics:
   - full `uv run aidd doctor` output;
   - relevant command output with exit code;
   - artifact paths from `uv run aidd run artifacts ...` when available;
   - runtime log tail from `uv run aidd run logs ... --tail --lines 80` when available.

5. Documents (if validator or stage state is involved):
   - `validator-report.md`;
   - `repair-brief.md` (if present);
   - `questions.md` and `answers.md` (if present).

### 4.2 Minimal issue template

```md
## Summary
- Expected:
- Actual:

## Reproduction
1.
2.
3.

## Environment
- OS:
- Python:
- uv:
- Commit SHA:

## Diagnostics
- aidd doctor output:
  <paste full output>
- failing command output:
  <paste full output including error text and exit code>

## Artifacts
- Work item:
- Runtime:
- Stage:
- Paths:
```

## 5. Maintainer Triage Policy

Issues are handled in this order:

1. reproducibility and missing-information check;
2. scope check against current roadmap state;
3. classification into defect, expected behavior, docs gap, or follow-up roadmap work.

Maintainers may close issues as:

- `resolved` (fix landed);
- `needs-info` (missing required diagnostics);
- `expected-current-behavior` (matches documented behavior and support scope);
- `not-reproducible` (cannot reproduce with provided data);
- `duplicate` (covered by an existing issue).

There is no guaranteed response-time SLA in the current phase.

## 6. Data Handling Expectations

- Do not post secrets, tokens, private repository URLs, or credentials.
- Redact sensitive paths and identifiers where needed.
- Keep enough unredacted diagnostics to preserve reproducibility.

## 7. Related References

- [Operator Handbook](./operator-handbook.md)
- [Operator Troubleshooting Guide](./operator-troubleshooting.md)
- [Roadmap](./backlog/roadmap.md)
