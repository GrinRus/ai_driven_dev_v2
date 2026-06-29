# Scenario Matrix

This document is the source of truth for the maintained scenario matrix in
`ai_driven_dev_v2`.

## Axes

Every maintained scenario is classified by:

- `scenario_class`
- `feature_size`
- `automation_lane`
- `canonical_runtime`
- `runtime_targets`
- `feature_source.mode`
- `live_matrix_role` for live scenarios

The supported classes are:

- `deterministic-stage`
- `deterministic-workflow`
- `live-full-flow`
- `live-full-flow-interview`

All live classes use `live_flow.answer_policy: agent-decides`: any live scenario
may block on unresolved questions and resume after the launching operator-agent
writes resolved answers. `live-full-flow-interview` is the coverage class for
scenarios where that blocking interview path is expected by the manifest.

The supported feature sizes are:

- `tiny` - docs/config-only, 1-2 files, no runtime behavior change.
- `small` - live flow-regression only, used to prove that the live flow still runs.
- `medium` - product-evaluation task across 2-3 subsystems, with manual stage audits.
- `large` - cross-module, API, or runtime behavior product-evaluation task.
- `xlarge` - interview, security, API-sensitive, or multi-subsystem product-evaluation task.

Live scenarios add `live_matrix_role`:

- `flow-regression` is allowed only with `feature_size: small`. These lanes prove flow
  health and do not count as product-delivery evaluation.
- `product-evaluation` is required for `medium`, `large`, and `xlarge`. These lanes
  black-box evaluate whether AIDD can carry a real product change through `idea -> qa`.
  They use a stage-run ledger, so repeated remediation loops such as
  `implement -> review -> implement -> review -> qa` preserve distinct runner and manual
  audits for every stage run.

The supported automation lanes are:

- `ci`
- `manual`

## Representative Buckets

The maintained set must cover these buckets without turning the matrix into a full cross-product:

| Bucket | Required coverage | Maintained scenarios |
| --- | --- | --- |
| deterministic stage | `small + ci` | `AIDD-SMOKE-001` |
| deterministic workflow | `medium + ci` | `AIDD-DETERMINISTIC-001`, `AIDD-DETERMINISTIC-003` |
| deterministic workflow | `large + manual` | `AIDD-DETERMINISTIC-002` |
| live full flow regression | `small + manual + flow-regression` | `AIDD-LIVE-004`, `AIDD-LIVE-005` |
| live full flow product evaluation | `medium + manual + product-evaluation` | `AIDD-LIVE-007` |
| live full flow product evaluation | `large + manual + product-evaluation` | `AIDD-LIVE-012` |
| live full flow interview product evaluation | `large + manual + product-evaluation` | `AIDD-LIVE-010` |
| live full flow interview product evaluation | `xlarge + manual + product-evaluation` | `AIDD-LIVE-006`, `AIDD-LIVE-008`, `AIDD-LIVE-011` |

`AIDD-LIVE-001` is retired from maintained coverage because it is setup-blocked before
the runtime boundary. The maintained small lanes are regression-smoke only:
`AIDD-LIVE-004` for docs/config flow health and `AIDD-LIVE-005` for code-change flow
health.

`AIDD-LIVE-004` is intentionally docs-only. Its maintained execution gate checks the
selected documentation acceptance criteria instead of the whole upstream HTTPX suite:
tracked diff remains limited to `README.md` and `docs/index.md`, both docs surfaces carry
the concrete `https://httpbin.org/json` CLI example, added docs lines do not introduce
placeholder runnable URLs, verification does not call the public endpoint, and QA artifacts
are published.

## Operator UI Local-Project Lane

Operator UI evidence is tracked separately from the scenario-class matrix because it is a
local product UI lane, not a provider/runtime eval manifest. The lane is documented in
[`Operator UI Local-Project E2E Lane`](./operator-ui-local-project.md) and is covered by
deterministic `OperatorUiService` and CLI tests rather than a new harness scenario class.

The lane proves local-project behavior: page load, workflow-run request delegation,
blocking answer persistence, runtime logs, artifact and validation visibility,
repair-history links, and declared project-set root visibility. Public GitHub
repositories remain live E2E inputs only.

The installed/source local-project smoke path is tracked as
`AIDD-INSTALLED-LOCAL-001` in
`harness/scenarios/smoke/installed-local-project-fixture.yaml`. It remains a
manual fixture smoke and does not use public GitHub task intake.

Real-provider UI E2E is a manual local-project lane, not a new scenario class. Its
acceptance matrix lives in [`Real-Provider UI E2E Lane`](./real-provider-ui-e2e.md).
Provider priority is Codex first, then Claude Code, OpenCode, and optional experimental
Qwen when local auth is ready.

## Provider Rollout Policy

- `generic-cli` is the deterministic baseline provider.
- `codex` is the primary canonical runtime for maintained small regression, medium
  product-evaluation, and selected large non-interview live lanes.
- `qwen` is experimental and may be used for the small docs-only live lane and
  the Hono medium lane when `aidd eval doctor` confirms local provider readiness.
- `opencode` must cover at least one live lane and one deterministic workflow lane; it is
  the canonical runtime for the maintained live interview expansion lanes.
- `claude-code` remains deterministic by default, keeps `AIDD-LIVE-005` as a
  small regression lane, and uses `AIDD-LIVE-007` plus `AIDD-LIVE-012` as planned
  maintained medium and large live coverage candidates when `aidd eval doctor`
  confirms provider/auth readiness; live config uses large native provider and
  stage budgets for every maintained `idea -> qa` stage.
- Live manifests must not be scheduled in `ci` or release automation.

## Maintained Scenario Set

| Scenario | Path | Class | Size | Live role | Lane | Canonical runtime | Runtime targets | Feature source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AIDD-SMOKE-001` | `harness/scenarios/smoke/plan-stage-minimal-fixture.yaml` | `deterministic-stage` | `small` | n/a | `ci` | `generic-cli` | `generic-cli` | `fixture-seed` |
| `AIDD-STAGEPACK-PLAN-SMOKE-001` | `harness/scenarios/smoke/plan-stagepack-smoke.yaml` | `deterministic-stage` | `medium` | n/a | `ci` | `opencode` | `generic-cli`, `claude-code`, `codex`, `opencode` | `fixture-seed` |
| `AIDD-INSTALLED-LOCAL-001` | `harness/scenarios/smoke/installed-local-project-fixture.yaml` | `deterministic-workflow` | `small` | n/a | `manual` | `generic-cli` | `generic-cli` | `fixture-seed` |
| `AIDD-DETERMINISTIC-001` | `harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml` | `deterministic-workflow` | `medium` | n/a | `ci` | `opencode` | `generic-cli`, `claude-code`, `opencode` | `fixture-seed` |
| `AIDD-DETERMINISTIC-002` | `harness/scenarios/deterministic/minimal-python-full-workflow.yaml` | `deterministic-workflow` | `large` | n/a | `manual` | `generic-cli` | `generic-cli`, `claude-code` | `fixture-seed` |
| `AIDD-DETERMINISTIC-003` | `harness/scenarios/deterministic/project-set-plan-context.yaml` | `deterministic-workflow` | `medium` | n/a | `ci` | `generic-cli` | `generic-cli` | `fixture-seed` |
| `AIDD-LIVE-004` | `harness/scenarios/live/httpx-cli-docs-sync.yaml` | `live-full-flow` | `small` | `flow-regression` | `manual` | `codex` | `codex`, `qwen` | `authored-task-pool` |
| `AIDD-LIVE-005` | `harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml` | `live-full-flow` | `small` | `flow-regression` | `manual` | `codex` | `codex`, `opencode`, `claude-code` | `authored-task-pool` |
| `AIDD-LIVE-006` | `harness/scenarios/live/sqlite-utils-yielded-rows-interview.yaml` | `live-full-flow-interview` | `xlarge` | `product-evaluation` | `manual` | `opencode` | `codex`, `opencode` | `authored-task-pool` |
| `AIDD-LIVE-007` | `harness/scenarios/live/hono-non-error-throw-handling.yaml` | `live-full-flow` | `medium` | `product-evaluation` | `manual` | `codex` | `codex`, `claude-code`, `qwen` | `authored-task-pool` |
| `AIDD-LIVE-008` | `harness/scenarios/live/hono-router-double-star-parity.yaml` | `live-full-flow-interview` | `xlarge` | `product-evaluation` | `manual` | `opencode` | `opencode` | `authored-task-pool` |
| `AIDD-LIVE-010` | `harness/scenarios/live/openapi-typescript-discriminator-composition.yaml` | `live-full-flow-interview` | `large` | `product-evaluation` | `manual` | `opencode` | `codex`, `opencode` | `authored-task-pool` |
| `AIDD-LIVE-011` | `harness/scenarios/live/pytest-collection-error-summary.yaml` | `live-full-flow-interview` | `xlarge` | `product-evaluation` | `manual` | `opencode` | `codex`, `opencode` | `authored-task-pool` |
| `AIDD-LIVE-012` | `harness/scenarios/live/starlette-streaming-error-boundary.yaml` | `live-full-flow` | `large` | `product-evaluation` | `manual` | `codex` | `codex`, `claude-code` | `authored-task-pool` |

## Feature Selection Policy

- Deterministic scenarios always use `feature_source.mode: fixture-seed`.
- Live scenarios always use `feature_source.mode: authored-task-pool`.
- Live execution selects the first listed authored task from the manifest.
- Product-evaluation live tasks must define `visible_request`, `audit_rubric`, and
  `complexity_axes`; only `visible_request` is runtime-facing task context.
- Live manifests using any other feature source mode are invalid.
- Deterministic execution keeps feature selection inside the fixture-owned seed bundle.
- Manual live refresh batches should rotate across products, repositories, feature
  families, and sizes where possible. Repeating a manifest is reserved for targeted blocker
  confirmation, runtime comparison, repin validation, or canonical smoke evidence.
