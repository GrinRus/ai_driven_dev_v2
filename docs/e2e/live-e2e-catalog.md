# Live End-to-End Catalog

This catalog defines the curated public-repository scenarios used for installed live E2E runs.

## Purpose

Live E2E exists to prove the full installed operator flow, not just harness mechanics.

A live run answers this question:

> Can an operator install AIDD, enter a real repository, select a bounded issue seed, run the governed flow from `idea` through `qa`, and preserve durable evidence of both execution and quality?

That makes live E2E different from other evaluation layers:

- adapter conformance proves adapter contract behavior;
- smoke scenarios prove bounded workflow or stage invariants quickly;
- runtime parity compares maintained runtimes on shared fixtures;
- live E2E proves installed-CLI full-flow behavior on a pinned public repository.

## Canonical execution model

Every live E2E run must follow the installed full-flow operator model:

1. Select a scenario from `harness/scenarios/live/`.
2. Prepare a pinned working copy of the target public repository.
3. Install the AIDD artifact under test:
   - local wheel via `uv tool` in development and CI;
   - published package via `uv tool` in release verification.
4. Change into the target repository root.
5. Select one issue seed from the scenario's curated issue pool.
6. Run installed `aidd` from that repository root with explicit workflow bounds `idea -> qa`.
7. Keep `.aidd/` rooted inside the target repository.
8. Preserve install evidence, raw runtime logs, full-flow stage artifacts, verification output, quality artifacts, and final execution/quality conclusions.

Live E2E is not defined by a source-checkout invocation such as
`python -m aidd.cli.main` from the AIDD repository itself. That path can still be
useful for development, but it is not the canonical live lane.

## Why these repositories

We want repositories that are:

- public and stable;
- active enough to matter;
- runnable without proprietary services;
- bounded enough for repeated operator-proof runs;
- diverse across Python and TypeScript ecosystems.

## Selection policy

Every live E2E scenario must:

- target a repository listed in this catalog;
- resolve and record the exact target repository commit SHA at run start;
- use a bounded curated issue pool for reproducible issue selection;
- force full-flow execution from `idea` through `qa`;
- install and identify the AIDD artifact under test;
- launch installed `aidd` from the target repository root;
- root the `.aidd` workspace in that target repository;
- preserve setup, install, run, verify, quality, and teardown transcripts;
- preserve user questions and answers when the scenario requires interview flow;
- fail or block explicitly when verification, validation, installability, issue-selection, or interview evidence is missing;
- run repo-local quality checks after verification and write a quality report to the eval bundle.

## Primary repository set

### 1. `fastapi/typer`

Why it is in the set:

- Python CLI framework;
- active open-source maintenance;
- tests, typing, and docs all matter;
- good fit for CLI- and document-oriented tasks.

Default setup lane:

- Python 3.12+
- `uv sync --group tests` or equivalent project install
- verify with `uv run pytest`

Initial scenarios:

- **AIDD-LIVE-001 — styled help alignment bugfix**
- **AIDD-LIVE-002 — boolean option help rendering**

### 2. `encode/httpx`

Why it is in the set:

- mature Python networking library;
- integrated CLI;
- strong test culture;
- useful for error-message and transport-facing scenarios.

Default setup lane:

- Python 3.12+
- project environment with test dependencies
- verify with `pytest`

Initial scenarios:

- **AIDD-LIVE-003 — invalid header error message**
- **AIDD-LIVE-004 — CLI docs sync**

### 3. `simonw/sqlite-utils`

Why it is in the set:

- Python CLI utility and library;
- active public issue tracker;
- real command-line workflows with data fixtures;
- good for bugfix and interview-driven feature scenarios.

Default setup lane:

- Python 3.12+
- project environment with test dependencies
- verify with `pytest`

Initial scenarios:

- **AIDD-LIVE-005 — header-only CSV bugfix**
  This remains the primary canonical full-flow live workflow proof and the tagged-release published-package proof.
- **AIDD-LIVE-006 — yielded rows feature with interview**
  This remains an explicit interview scenario: the system must ask the user about execution trust boundaries, accepted input form, and documentation expectations before implementation.

### 4. `honojs/hono`

Why it is in the set:

- TypeScript multi-runtime framework;
- adapter-agnostic by nature;
- good stress test for non-Python repos;
- strong fit for middleware and runtime-behavior scenarios.

Default setup lane:

- Bun or compatible Node toolchain
- `bun install`
- verify with `tsc --noEmit && vitest --run`

Initial scenarios:

- **AIDD-LIVE-007 — non-Error throw handling**
- **AIDD-LIVE-008 — router parity with `/**` syntax**

## Scenario lanes

### Full-flow operator audit lane

Use this lane to prove that installed AIDD can execute a governed workflow from `idea` through `qa` in a real repository:

- `AIDD-LIVE-005` (primary canonical scenario)

### Published artifact release-proof lane

Use this lane to prove that the published package can execute one pinned full-flow live scenario from the
target repository root during tagged-release verification:

- `AIDD-LIVE-005` on `generic-cli`

### Interview lane

Use these scenarios to validate blocking question handling inside the full-flow installed operator model:

- `AIDD-LIVE-006`
- `AIDD-LIVE-008`

### Docs-and-alignment lane

Use these scenarios to validate that code, examples, docs, and validation still align under full-flow live execution:

- `AIDD-LIVE-002`
- `AIDD-LIVE-004`

### Candidate smoke reuse lane

These scenarios may still be reused by smoke or parity work, but those lanes are governed elsewhere:

- `AIDD-LIVE-001`
- `AIDD-LIVE-003`
- `AIDD-LIVE-005`
- `AIDD-LIVE-007`

## Runtime parity notes

Runtime parity still matters, but it is no longer the defining purpose of the live lane.

Use these sources for parity-first work:

- `docs/architecture/adapter-conformance-matrix.md`
- maintained smoke scenarios under `harness/scenarios/smoke/`
- archived reference bundles under `.aidd/reports/evals/`

Tagged-release published-package verification intentionally uses `generic-cli` for deterministic
CI execution. Maintained-runtime task-completion evidence remains a separate development and nightly signal.

## Quality rubric

Live E2E now carries a second layer in addition to execution verdict: a quality gate.

The canonical rubric is defined in `docs/e2e/live-quality-rubric.md` and scores:

- `flow_fidelity`
- `artifact_quality`
- `code_quality`

The eval bundle records:

- execution verdict in `verdict.md`;
- quality gate and quality findings in `quality-report.md`;
- combined machine-readable execution and quality metadata in `grader.json`.

## What a live E2E report must record

Every live report must include:

- scenario id;
- repository URL;
- resolved target repository commit SHA;
- runtime id and adapter id;
- selected issue snapshot from the curated issue pool;
- install channel, such as `uv-tool`;
- artifact source, such as `local-wheel` or `published-package`;
- artifact identity, such as wheel filename or published package spec;
- target repository cwd used for the run;
- workspace root used for the run;
- raw runtime log;
- normalized event log when supported;
- question and answer artifacts when used;
- validator report;
- verification command output;
- quality command output;
- execution verdict;
- quality gate and quality verdict.

## Runnable manifests

The live manifest set lives in `harness/scenarios/live/`.
