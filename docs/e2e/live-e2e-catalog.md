# Live End-to-End Catalog

This catalog defines the authored public-repository scenarios used for manual live E2E audits.

## Purpose

Live E2E exists to answer one question:

> Can an operator manually run installed AIDD against a pinned public repository, follow the full governed flow from `idea` through `qa`, and preserve durable execution plus quality evidence?

That makes live E2E different from the deterministic lanes:

- adapter conformance proves adapter contract behavior;
- deterministic stage and workflow scenarios prove repo-local invariants quickly;
- manual live E2E proves installed-CLI full-flow behavior on a pinned public repository.

Live E2E is no longer part of CI or release automation. It is a manual external-audit lane only.

## Canonical Execution Model

Every live E2E run must follow the installed full-flow operator model:

1. Select a maintained manifest from `harness/scenarios/live/`.
2. Resolve and record the pinned target repository commit.
3. Prepare a working copy of that repository.
4. Install the AIDD artifact under test with `uv tool`.
5. Change into the target repository root.
6. Select the first authored task from the scenario's `authored-task-pool`.
7. Run installed `aidd` from that repository root with explicit workflow bounds `idea -> qa`.
8. Keep `.aidd/` rooted inside the target repository.
9. Preserve install, setup, run, verify, quality, and teardown evidence in the eval bundle.
10. Preserve `stage-timing.json`, `stage-timing.md`, `self-repair-matrix.json`, and
    `self-repair-matrix.md` so operators can audit step duration, per-attempt runtime windows,
    deterministic repair-probe coverage, terminal document consistency, and repair behavior.

Live E2E is not defined by source-checkout execution from the AIDD repository itself, and it is not a merge gate.
Local-wheel live evals build from the source checkout containing the scenario manifest. To
test an already published package, set `AIDD_EVAL_PUBLISHED_PACKAGE_SPEC` to the exact
package spec, for example `ai-driven-dev-v2==0.1.0a2`; published-package mode must not
require a source checkout root.

The local operator UI has a separate E2E evidence lane in
[`Operator UI Local-Project E2E Lane`](./operator-ui-local-project.md). That lane uses
local fixture projects and service-level UI tests, not public-repository live manifests.

## Product Scope Boundary

Public GitHub repositories are live E2E targets and support/reporting evidence sources.
They are not the supported local operator intake path. The product does not expose
`aidd init --github-issue <url>` because that command is out of product scope; local
operators initialize work items from the target project root with
`aidd init --work-item <id> --root .aidd`.

## Manual-Only Automation Policy

- `automation_lane` for every live scenario is `manual`.
- The only supported automation entrypoint is `.github/workflows/manual-live-e2e.yml`,
  which invokes the black-box evaluator module instead of a product CLI command.
- That workflow supports optional GitHub secret overrides for custom wrapper
  commands:
  - `AIDD_EVAL_CLAUDE_CODE_COMMAND` for `claude-code`
  - `AIDD_EVAL_CODEX_COMMAND` for `codex`
  - `AIDD_EVAL_OPENCODE_COMMAND` for `opencode`
- When no override is set, the evaluator validates the default native provider
  command on the runner before cloning or installing artifacts.
- Secret override values must point to runner-available wrapper commands that
  accept the AIDD adapter contract flags.
- CI must not reference `harness/scenarios/live/`.
- Release automation must not run live scenarios or require live-eval artifacts.
- Live manifests must declare `live_flow.driver: stepwise-black-box`,
  `live_flow.checkpoint_policy: after-each-step`, and
  `live_flow.frontend_checkpoints: true` so every live run inspects the public
  CLI, UI, and UI/API surfaces after each stage.

## Maintained Repository Set

### `fastapi/typer`

- `AIDD-LIVE-001` - authored styled help alignment bugfix (`setup-blocked`; not a canonical README smoke until repinned or fixed)
- `AIDD-LIVE-002` - authored boolean option help rendering task

### `encode/httpx`

- `AIDD-LIVE-003` - authored invalid header error message task
- `AIDD-LIVE-004` - authored CLI docs sync task

### `simonw/sqlite-utils`

- `AIDD-LIVE-005` - authored header-only CSV bugfix task
- `AIDD-LIVE-006` - authored yielded rows feature with interview

### `honojs/hono`

- `AIDD-LIVE-007` - authored non-Error throw handling task
- `AIDD-LIVE-008` - authored router parity with `/**` syntax interview

## Matrix Source Of Truth

Use [`Scenario Matrix`](./scenario-matrix.md) as the source of truth for:

- `scenario_class`
- `feature_size`
- `automation_lane`
- `canonical_runtime`
- provider rollout coverage

For live scenarios in this wave:

- `codex` is the primary canonical runtime for maintained tiny, small, and medium live lanes;
- `opencode` covers at least one live lane;
- `claude-code` is enabled only for the `AIDD-LIVE-005` small smoke lane, where the
  manual timeout budget is intentionally extended to 240 minutes because native
  Claude Code full-flow attempts can run materially longer than Codex/OpenCode
  attempts; its generated live runtime config also extends long-running
  `research`, `tasklist`, `implement`, `review`, and `qa` stage attempts;
- `generic-cli` remains a deterministic baseline provider and is not a maintained live provider in this wave.

Representative matrix coverage for the live lane:

| Scenario class | Feature size | Maintained provider | Representative scenarios |
| --- | --- | --- | --- |
| `live-full-flow` | `tiny` | `codex` | `AIDD-LIVE-004` |
| `live-full-flow` | `small` | `codex`, `claude-code` smoke | `AIDD-LIVE-003`, `AIDD-LIVE-005` |
| `live-full-flow` | `medium` | `codex` | `AIDD-LIVE-002`, `AIDD-LIVE-007` |
| `live-full-flow-interview` | `large` | `opencode` | `AIDD-LIVE-006` |
| `live-full-flow-interview` | `xlarge` | `opencode` | `AIDD-LIVE-008` |

`AIDD-LIVE-001` remains in the maintained set for historical evidence, but its current
Typer pin is setup-blocked before the runtime boundary. Use `AIDD-LIVE-005` as the
canonical installed live smoke until `AIDD-LIVE-001` is repinned or its setup baseline is
fixed.

## Live-Scenario Contract

Every maintained live scenario must:

- live under `harness/scenarios/live/`;
- declare `scenario_class` as `live-full-flow` or `live-full-flow-interview`;
- declare `feature_size`;
- declare `automation_lane: manual`;
- declare `canonical_runtime` that also appears in `runtime_targets`;
- use `feature_source.mode: authored-task-pool`;
- select the first listed authored task deterministically;
- define authored task `id`, `title`, `summary`, `intent`, `target_change`, `expected_scope`,
  `acceptance_criteria`, `verification`, `quality_bar`, and `size_rationale`;
- define authored task `interview` guidance only for `live-full-flow-interview` scenarios;
- force full-flow `idea -> qa`;
- run repo-local verification commands;
- run repo-local quality commands;
- preserve feature-selection, validator, log-analysis, verdict, and quality artifacts.

## Expected Artifacts

Every live eval bundle must aim to contain:

- `runtime.log`
- `validator-report.md`
- `repair-history.md`
- `log-analysis.md`
- `stage-timing.json`
- `stage-timing.md`
- `self-repair-matrix.json`
- `self-repair-matrix.md`
- `grader.json`
- `verdict.md`
- `quality-report.md`
- `feature-selection.json`
- `install-transcript.json`
- `setup-transcript.json`
- `run-transcript.json`
- `verify-transcript.json`
- `quality-transcript.json`
- `teardown-transcript.json`

## Interview Scenarios

The maintained interview scenarios are:

- `AIDD-LIVE-006`
- `AIDD-LIVE-008`

These scenarios must block when questions are unresolved and resume only after `answers.md`
is present in the expected target-repository workspace path.

## Related References

- [`Scenario Matrix`](./scenario-matrix.md)
- [`Live Quality Rubric`](./live-quality-rubric.md)
- [`Eval and Harness Integration`](../architecture/eval-harness-integration.md)
