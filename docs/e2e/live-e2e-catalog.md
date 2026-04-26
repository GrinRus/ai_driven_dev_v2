# Live End-to-End Catalog

This catalog defines the curated public-repository scenarios used for manual live E2E audits.

## Purpose

Live E2E exists to answer one question:

> Can an operator manually run installed AIDD against a pinned public repository, follow the full governed flow from `idea` through `qa`, and preserve durable execution plus quality evidence?

That makes live E2E different from the deterministic lanes:

- adapter conformance proves adapter contract behavior;
- deterministic stage and workflow scenarios prove repo-local invariants quickly;
- manual live E2E proves installed-CLI full-flow behavior on a pinned public repository.

Live E2E is no longer part of CI or release automation. It is a manual external-audit lane only.

## Canonical execution model

Every live E2E run must follow the installed full-flow operator model:

1. Select a maintained manifest from `harness/scenarios/live/`.
2. Resolve and record the pinned target repository commit.
3. Prepare a working copy of that repository.
4. Install the AIDD artifact under test with `uv tool`.
5. Change into the target repository root.
6. Select the first issue from the scenario's curated issue pool.
7. Run installed `aidd` from that repository root with explicit workflow bounds `idea -> qa`.
8. Keep `.aidd/` rooted inside the target repository.
9. Preserve install, setup, run, verify, quality, and teardown evidence in the eval bundle.

Live E2E is not defined by source-checkout execution from the AIDD repository itself, and it is not a merge gate.

## Manual-only automation policy

- `automation_lane` for every live scenario is `manual`.
- The only supported automation entrypoint is `.github/workflows/manual-live-e2e.yml`.
- That workflow supports optional GitHub secret overrides for custom wrapper
  commands:
  - `AIDD_EVAL_CODEX_COMMAND` for `codex`
  - `AIDD_EVAL_OPENCODE_COMMAND` for `opencode`
- When no override is set, the harness validates the default native provider
  command on the runner before cloning or installing artifacts.
- Secret override values must point to runner-available wrapper commands that
  accept the AIDD adapter contract flags.
- CI must not reference `harness/scenarios/live/`.
- Release automation must not run live scenarios or require live-eval artifacts.

## Maintained repository set

### `fastapi/typer`

- `AIDD-LIVE-001` — styled help alignment bugfix
- `AIDD-LIVE-002` — boolean option help rendering

### `encode/httpx`

- `AIDD-LIVE-003` — invalid header error message
- `AIDD-LIVE-004` — CLI docs sync

### `simonw/sqlite-utils`

- `AIDD-LIVE-005` — header-only CSV bugfix
- `AIDD-LIVE-006` — yielded rows feature with interview

### `honojs/hono`

- `AIDD-LIVE-007` — non-Error throw handling
- `AIDD-LIVE-008` — router parity with `/**` syntax interview

## Matrix source of truth

Use [`Scenario Matrix`](./scenario-matrix.md) as the source of truth for:

- `scenario_class`
- `feature_size`
- `automation_lane`
- `canonical_runtime`
- provider rollout coverage

For live scenarios in this wave:

- `codex` is the primary canonical runtime for maintained small and medium live lanes;
- `opencode` covers at least one live lane;
- `claude-code` is not yet rolled out for live lanes;
- `generic-cli` remains a deterministic baseline provider and is not a maintained live provider in this wave.

Representative matrix coverage for the live lane:

| Scenario class | Feature size | Maintained provider | Representative scenarios |
| --- | --- | --- | --- |
| `live-full-flow` | `small` | `codex` | `AIDD-LIVE-001`, `AIDD-LIVE-003`, `AIDD-LIVE-005` |
| `live-full-flow` | `medium` | `codex` | `AIDD-LIVE-002`, `AIDD-LIVE-004`, `AIDD-LIVE-007` |
| `live-full-flow-interview` | `large` | `opencode` | `AIDD-LIVE-006`, `AIDD-LIVE-008` |

## Live-scenario contract

Every maintained live scenario must:

- live under `harness/scenarios/live/`;
- declare `scenario_class` as `live-full-flow` or `live-full-flow-interview`;
- declare `feature_size`;
- declare `automation_lane: manual`;
- declare `canonical_runtime` that also appears in `runtime_targets`;
- use `feature_source.mode: curated-issue-pool`;
- select the first listed issue deterministically;
- force full-flow `idea -> qa`;
- run repo-local verification commands;
- run repo-local quality commands;
- preserve issue-selection, validator, log-analysis, verdict, and quality artifacts.

## Expected artifacts

Every live eval bundle must aim to contain:

- `runtime.log`
- `validator-report.md`
- `repair-history.md`
- `log-analysis.md`
- `grader.json`
- `verdict.md`
- `quality-report.md`
- `issue-selection.json`
- `install-transcript.json`
- `setup-transcript.json`
- `run-transcript.json`
- `verify-transcript.json`
- `quality-transcript.json`
- `teardown-transcript.json`

## Interview scenarios

The maintained interview scenarios are:

- `AIDD-LIVE-006`
- `AIDD-LIVE-008`

These scenarios must block when questions are unresolved and resume only after `answers.md` is present in the expected target-repository workspace path.

## Related references

- [`Scenario Matrix`](./scenario-matrix.md)
- [`Live Quality Rubric`](./live-quality-rubric.md)
- [`Eval and Harness Integration`](../architecture/eval-harness-integration.md)
