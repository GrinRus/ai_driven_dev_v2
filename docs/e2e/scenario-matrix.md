# Scenario Matrix

This document is the source of truth for the maintained scenario matrix in `ai_driven_dev_v2`.

## Axes

Every maintained scenario is classified by:

- `scenario_class`
- `feature_size`
- `automation_lane`
- `canonical_runtime`
- `runtime_targets`
- `feature_source.mode`

The supported classes are:

- `deterministic-stage`
- `deterministic-workflow`
- `live-full-flow`
- `live-full-flow-interview`

The supported feature sizes are:

- `small`
- `medium`
- `large`

The supported automation lanes are:

- `ci`
- `manual`

## Representative buckets

The maintained set must cover these buckets without turning the matrix into a full cross-product:

| Bucket | Required coverage | Maintained scenarios |
| --- | --- | --- |
| deterministic stage | `small + ci` | `AIDD-SMOKE-001` |
| deterministic workflow | `medium + ci` | `AIDD-DETERMINISTIC-001` |
| deterministic workflow | `large + manual` | `AIDD-DETERMINISTIC-002` |
| live full flow | `small + manual` | `AIDD-LIVE-001`, `AIDD-LIVE-003`, `AIDD-LIVE-005` |
| live full flow | `medium + manual` | `AIDD-LIVE-002`, `AIDD-LIVE-004`, `AIDD-LIVE-007` |
| live full flow interview | `large + manual` | `AIDD-LIVE-006`, `AIDD-LIVE-008` |

## Provider rollout policy

- `generic-cli` is the deterministic baseline provider.
- `codex` is the primary canonical runtime for maintained small and medium live lanes.
- `opencode` must cover at least one live lane and one deterministic workflow lane.
- `claude-code` remains deterministic by default and is enabled only for the `AIDD-LIVE-005` small smoke lane.
- Live manifests must not be scheduled in `ci` or release automation.

## Maintained scenario set

| Scenario | Path | Class | Size | Lane | Canonical runtime | Runtime targets | Feature source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AIDD-SMOKE-001` | `harness/scenarios/smoke/plan-stage-minimal-fixture.yaml` | `deterministic-stage` | `small` | `ci` | `generic-cli` | `generic-cli` | `fixture-seed` |
| `AIDD-STAGEPACK-PLAN-SMOKE-001` | `harness/scenarios/smoke/plan-stagepack-smoke.yaml` | `deterministic-stage` | `medium` | `ci` | `opencode` | `generic-cli`, `claude-code`, `codex`, `opencode` | `fixture-seed` |
| `AIDD-DETERMINISTIC-001` | `harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml` | `deterministic-workflow` | `medium` | `ci` | `opencode` | `generic-cli`, `claude-code`, `opencode` | `fixture-seed` |
| `AIDD-DETERMINISTIC-002` | `harness/scenarios/deterministic/minimal-python-full-workflow.yaml` | `deterministic-workflow` | `large` | `manual` | `generic-cli` | `generic-cli`, `claude-code` | `fixture-seed` |
| `AIDD-LIVE-001` | `harness/scenarios/live/typer-styled-help-alignment.yaml` | `live-full-flow` | `small` | `manual` | `codex` | `codex` | `curated-issue-pool` |
| `AIDD-LIVE-002` | `harness/scenarios/live/typer-boolean-help-rendering.yaml` | `live-full-flow` | `medium` | `manual` | `codex` | `codex` | `curated-issue-pool` |
| `AIDD-LIVE-003` | `harness/scenarios/live/httpx-invalid-header-message.yaml` | `live-full-flow` | `small` | `manual` | `codex` | `codex` | `curated-issue-pool` |
| `AIDD-LIVE-004` | `harness/scenarios/live/httpx-cli-docs-sync.yaml` | `live-full-flow` | `medium` | `manual` | `codex` | `codex` | `curated-issue-pool` |
| `AIDD-LIVE-005` | `harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml` | `live-full-flow` | `small` | `manual` | `codex` | `codex`, `opencode`, `claude-code` | `curated-issue-pool` |
| `AIDD-LIVE-006` | `harness/scenarios/live/sqlite-utils-yielded-rows-interview.yaml` | `live-full-flow-interview` | `large` | `manual` | `opencode` | `codex`, `opencode` | `curated-issue-pool` |
| `AIDD-LIVE-007` | `harness/scenarios/live/hono-non-error-throw-handling.yaml` | `live-full-flow` | `medium` | `manual` | `codex` | `codex` | `curated-issue-pool` |
| `AIDD-LIVE-008` | `harness/scenarios/live/hono-router-double-star-parity.yaml` | `live-full-flow-interview` | `large` | `manual` | `opencode` | `opencode` | `curated-issue-pool` |

## Feature selection policy

- Deterministic scenarios always use `feature_source.mode: fixture-seed`.
- Live scenarios always use `feature_source.mode: curated-issue-pool`.
- Live execution selects the first listed issue from the curated pool.
- Deterministic execution keeps feature selection inside the fixture-owned seed bundle.
