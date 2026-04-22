# Live End-to-End Catalog

This catalog defines the first curated set of public GitHub repositories and scenario types for live E2E runs.

## Why these repositories

We want repositories that are:

- public and stable,
- active enough to matter,
- runnable without proprietary services,
- bounded enough for repeated eval work,
- diverse across Python and TypeScript runtime ecosystems.

## Selection policy

Every live E2E run must:

- clone a public GitHub repository,
- resolve and record the exact commit SHA at run start,
- store the diff, runtime log, and verification output,
- use a task that fits within a bounded patch budget,
- preserve any user questions raised during the run.

## Primary repository set

### 1. `fastapi/typer`

Why it is in the set:

- Python CLI framework,
- active open-source maintenance,
- tests, typing, and docs all matter,
- good fit for CLI- and document-oriented tasks.

Default setup lane:

- Python 3.12+
- `uv sync --group tests` or equivalent project install
- verify with `uv run pytest`

Initial scenarios:

- **AIDD-LIVE-001 — styled help alignment bugfix**  
  Based on issue `#1159`. Fix help-line width calculation when styled help text is present. Add a regression test and preserve existing help rendering behavior.
  First reference run on April 22, 2026 used runtime `generic-cli`, pinned revision
  `9ce8e30383ef419c490431caab5a515eca669b1b`, and produced status `harness_fail`
  because setup command `uv run pytest -q || pytest -q` exited with status `2`.
- **AIDD-LIVE-002 — boolean option help rendering**  
  Based on issue `#678`. Improve `--help` rendering for boolean options so type/default details remain clear. Add regression coverage.

### 2. `encode/httpx`

Why it is in the set:

- mature Python networking library,
- integrated CLI,
- strong test culture,
- useful for error-message and transport-facing scenarios.

Default setup lane:

- Python 3.12+
- project environment with test dependencies
- verify with `pytest`

Initial scenarios:

- **AIDD-LIVE-003 — invalid header error message**  
  Based on issue `#3400`. Improve the invalid-header encoding error so the failing header name is visible in the resulting exception or wrapper message. Add regression coverage.
  First reference run on April 22, 2026 used runtime `generic-cli`, pinned revision
  `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`, and produced status `harness_fail`
  because verification command `uv run pytest -q || pytest -q` exited with status `4`.
- **AIDD-LIVE-004 — CLI docs sync**  
  A controlled docs-and-tests scenario around the integrated CLI. The task is to update docs/examples after a small CLI behavior change and prove that docs, examples, and verification still align.

### 3. `simonw/sqlite-utils`

Why it is in the set:

- Python CLI utility and library,
- active public issue tracker,
- real command-line workflows with data fixtures,
- good for bugfix and interview-driven feature scenarios.

Default setup lane:

- Python 3.12+
- project environment with test dependencies
- verify with `pytest`

Initial scenarios:

- **AIDD-LIVE-005 — header-only CSV bugfix**  
  Based on issue `#705`. Prevent a crash when `--detect-types` is used on a CSV file that contains only a header row. Add a regression test.
  First reference run on April 22, 2026 used runtime `generic-cli`, pinned revision
  `8d74ffc93292c604d5827e2b44fffedca0c28c19`, and produced status `harness_pass`
  with all setup, run, and verification commands succeeding.
  Codex parity reference run on April 22, 2026 used runtime `codex`, pinned revision
  `8d74ffc93292c604d5827e2b44fffedca0c28c19`, and produced status `harness_pass`
  with all setup, run, and verification commands succeeding.
- **AIDD-LIVE-006 — yielded rows feature with interview**  
  Based on issue `#694`. Add a CLI path for passing Python code or a Python file that yields rows to insert. This is explicitly an interview scenario: the system must ask the user about execution trust boundaries, accepted input form, and documentation expectations before implementation.
  First reference run on April 22, 2026 used runtime `generic-cli`, pinned revision
  `8d74ffc93292c604d5827e2b44fffedca0c28c19`, and produced status `harness_fail`
  because the verify-stage check for `answers.md` exited with status `1`.
  Codex parity reference run on April 22, 2026 used runtime `codex`, pinned revision
  `8d74ffc93292c604d5827e2b44fffedca0c28c19`, and produced status `harness_fail`
  because the verify-stage check for `answers.md` exited with status `1`.

### 4. `honojs/hono`

Why it is in the set:

- TypeScript multi-runtime framework,
- adapter-agnostic by nature,
- good stress test for non-Python repos,
- strong fit for middleware and runtime-behavior scenarios.

Default setup lane:

- Bun or compatible Node toolchain
- `bun install`
- verify with `tsc --noEmit && vitest --run`

Initial scenarios:

- **AIDD-LIVE-007 — non-Error throw handling**  
  Based on issue `#4708`. Ensure thrown non-`Error` values from middleware still flow through `onError` instead of causing an unhandled rejection. Add a regression test.
  First reference run on April 22, 2026 used runtime `generic-cli`, pinned revision
  `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`, and produced status `harness_fail`
  because verification command `bun test` exited with status `1`.
- **AIDD-LIVE-008 — router parity with `/**` syntax**  
  Based on issue `#4633`. Align router behavior or document the intended divergence. This may require an interview if the compatibility risk is unclear.
  First reference run on April 22, 2026 used runtime `generic-cli`, pinned revision
  `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`, and produced status `harness_fail`
  because verification command `test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/idea/answers.md`
  exited with status `1`.

## Scenario lanes

### Smoke lane

Use these for frequent cross-runtime checks:

- AIDD-LIVE-001
- AIDD-LIVE-003
- AIDD-LIVE-005
- AIDD-LIVE-007

### Interview lane

Use these to validate user-question handling:

- AIDD-LIVE-006
- AIDD-LIVE-008

### Docs-and-alignment lane

Use these to validate that code, examples, docs, and validation all stay coherent:

- AIDD-LIVE-002
- AIDD-LIVE-004

## Codex Minimum Parity Scenario Set

This matrix defines the minimum Codex parity set for `W7-E1-S3`.
The goal is to establish one stable smoke baseline, one interview baseline,
and one docs/alignment comparator before expanding lane coverage.

| Lane | Scenario ID | Selection rationale | Planned task |
| --- | --- | --- | --- |
| smoke | `AIDD-LIVE-005` | Stable Python-only setup with an existing harness-pass baseline and bounded patch scope. | `W7-E1-S3-T2` |
| interview | `AIDD-LIVE-006` | Exercises blocking question flow, answer persistence, and resume behavior. | `W7-E1-S3-T3` |
| docs-alignment | `AIDD-LIVE-004` | Validates docs/examples coherence after runtime-specific execution differences. | `W7-E1-S3-T4` |

Out-of-scope for the minimum set:

- `AIDD-LIVE-007` and `AIDD-LIVE-008` (Bun/TypeScript lane), deferred until the first Codex parity baseline is archived.

## Codex Parity Snapshot (April 22, 2026)

Completed reference runs from the minimum set:

- Smoke lane (`AIDD-LIVE-005`): `eval-live-005-codex-reference-20260422T123518Z` -> `harness_pass`.
- Interview lane (`AIDD-LIVE-006`): `eval-live-006-codex-reference-20260422T123937Z` -> `harness_fail`.

Known parity gaps and adapter-specific limitations:

- The `aidd run` command remains a roadmap placeholder for all runtimes, so current Codex parity is infrastructure-level (setup/run/verify contract) rather than full stage-execution parity.
- Interview flow parity is incomplete: `AIDD-LIVE-006` fails because `.aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/idea/answers.md` is not produced before the verify gate.
- Current Codex probe capability report is limited to `raw-log` and `env-injection`; no validated support is declared for structured logs, native question events, resume, non-interactive mode, working-directory control, or subagents.
- Docs-alignment lane (`AIDD-LIVE-004`) remains the next comparator for code/docs/example coherence after runtime-specific behavior differences.

## What a live E2E report must record

Every report must include:

- repository URL,
- resolved commit SHA,
- scenario id,
- runtime id,
- adapter id,
- raw runtime log,
- normalized event log,
- question and answer artifacts when used,
- validator report,
- verification command output,
- final verdict.

## Runnable manifests

The first manifest set lives in `harness/scenarios/live/`.
