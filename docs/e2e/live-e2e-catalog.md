# Live End-to-End Catalog

This catalog defines the curated public-repository scenarios used for installed live E2E runs.

## Purpose

Live E2E exists to prove the operator experience, not just harness mechanics.

A live run answers this question:

> Can an operator install AIDD, enter a real repository, run a governed workflow there, and preserve durable evidence of what happened?

That makes live E2E different from other evaluation layers:

- adapter conformance proves adapter contract behavior;
- smoke scenarios prove bounded workflow or stage invariants quickly;
- runtime parity compares maintained runtimes on shared fixtures;
- live E2E proves installed-CLI behavior on a pinned public repository.

## Canonical execution model

Every live E2E run must follow the installed operator model:

1. Select a scenario from `harness/scenarios/live/`.
2. Prepare a pinned working copy of the target public repository.
3. Install the AIDD artifact under test:
   - local wheel via `uv tool` in development and CI;
   - published package via `uv tool` in release verification.
4. Change into the target repository root.
5. Run installed `aidd` from that repository root.
6. Keep `.aidd/` rooted inside the target repository.
7. Preserve install evidence, raw runtime logs, verification output, validator output, and final verdict.

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
- use a task that fits within a bounded patch budget;
- install and identify the AIDD artifact under test;
- launch installed `aidd` from the target repository root;
- root the `.aidd` workspace in that target repository;
- preserve setup, install, run, verify, and teardown transcripts;
- preserve user questions and answers when the scenario requires interview flow;
- fail or block explicitly when verification, validation, installability, or interview evidence is missing.

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
  Based on issue `#1159`. Fix help-line width calculation when styled help text is present. Add a regression test and preserve existing help rendering behavior.
- **AIDD-LIVE-002 — boolean option help rendering**  
  Based on issue `#678`. Improve `--help` rendering for boolean options so type/default details remain clear. Add regression coverage.

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
  Based on issue `#3400`. Improve the invalid-header encoding error so the failing header name is visible in the resulting exception or wrapper message. Add regression coverage.
- **AIDD-LIVE-004 — CLI docs sync**  
  A controlled docs-and-tests scenario around the integrated CLI. Update docs/examples after a small CLI behavior change and prove that docs, examples, and verification still align.

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
  Based on issue `#705`. Prevent a crash when `--detect-types` is used on a CSV file that contains only a header row. Add a regression test.
  This is the first canonical installed live workflow proof.
  Tagged-release published-package verification uses this scenario with `generic-cli` as a deterministic release-proof runtime.
  Historical April 22, 2026 reference bundles for `codex` and `opencode` are still archived, but they no longer define the live lane contract by themselves.
- **AIDD-LIVE-006 — yielded rows feature with interview**  
  Based on issue `#694`. Add a CLI path for passing Python code or a Python file that yields rows to insert.
  This is explicitly an interview scenario: the system must ask the user about execution trust boundaries, accepted input form, and documentation expectations before implementation.

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
  Based on issue `#4708`. Ensure thrown non-`Error` values from middleware still flow through `onError` instead of causing an unhandled rejection. Add a regression test.
- **AIDD-LIVE-008 — router parity with `/**` syntax**  
  Based on issue `#4633`. Align router behavior or document the intended divergence. This may require an interview if the compatibility risk is unclear.

## Scenario lanes

### Installed operator proof lane

Use this lane to prove that installed AIDD can execute a real workflow from the target repository root:

- `AIDD-LIVE-005` (primary canonical scenario)

### Published Artifact Release-Proof Lane

Use this lane to prove that the published package can execute one pinned live scenario from the
target repository root during tagged-release verification:

- `AIDD-LIVE-005` on `generic-cli`

### Interview lane

Use these scenarios to validate blocking question handling in the installed operator model:

- `AIDD-LIVE-006`
- `AIDD-LIVE-008`

### Docs-and-alignment lane

Use these scenarios to validate that code, examples, docs, and validation still align under live execution:

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

Historical parity context retained from April 22, 2026:

- Codex smoke baseline: `AIDD-LIVE-005` -> `eval-live-005-codex-reference-20260422T123518Z`
- Codex interview baseline: `AIDD-LIVE-006` -> `eval-live-006-codex-reference-20260422T123937Z`
- OpenCode smoke baseline: `AIDD-LIVE-005` -> `eval-live-005-opencode-20260422T142733Z`
- OpenCode interview baseline: `AIDD-LIVE-006` -> `eval-live-006-opencode-20260422T142812Z`

Those archived bundles remain useful for comparison, but they do not change the installed-operator contract for new live runs.

Tagged-release published-package verification intentionally uses `generic-cli` for deterministic
CI execution. Maintained-runtime task-completion evidence remains a separate signal.

## What a live E2E report must record

Every live report must include:

- scenario id;
- repository URL;
- resolved target repository commit SHA;
- runtime id and adapter id;
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
- final verdict.

## Runnable manifests

The live manifest set lives in `harness/scenarios/live/`.
