# Live End-to-End Catalog

This catalog defines the authored public-repository scenarios used for manual live E2E audits.

## Purpose

Live E2E exists to answer one question:

> Can an operator manually run installed AIDD against a pinned public repository, follow the full governed flow from `idea` through `qa`, and preserve durable execution plus quality evidence?

That makes live E2E different from the deterministic lanes:

- adapter conformance proves adapter contract behavior;
- deterministic stage and workflow scenarios prove repo-local invariants quickly;
- manual live E2E proves installed-CLI full-flow behavior on a pinned public repository.

Live E2E is manual local operator audit evidence only. It is not CI/CD, not a release
workflow, not GitHub Actions, and not a release gate.

## Canonical Execution Model

Every live E2E run must follow the installed full-flow operator model:

1. Select a maintained manifest from `harness/scenarios/live/`.
2. Create a temp work layout under `<work-root>/<run_id>/`.
3. Snapshot tracked AIDD `HEAD` into `<work-root>/<run_id>/source/aidd`; dirty tracked
   source is an infra/config blocker.
4. Build the local wheel into `<work-root>/<run_id>/build/dist`.
5. Install the artifact with isolated
   `HOME=<work-root>/<run_id>/install-home` and
   `UV_CACHE_DIR=<work-root>/<run_id>/uv-cache`.
6. Clone and pin the target repository directly under
   `<work-root>/<run_id>/target/<repo-slug>`.
7. Change into the target repository root for setup, stage, verify, and quality execution.
8. Select the first authored task from the scenario's `authored-task-pool`.
9. Run installed `aidd` from that repository root with explicit workflow bounds `idea -> qa`.
10. Keep target `.aidd/` rooted inside the target repository.
11. Preserve install, setup, run, verify, quality, and teardown evidence in the eval bundle.
12. Write `stage-audits/<stage>.json` and `.md` after each stage.
13. Preserve `stage-timing.json`, `stage-timing.md`, `self-repair-matrix.json`, and
    `self-repair-matrix.md` so operators can audit step duration, per-attempt runtime windows,
    deterministic repair-probe coverage, terminal document consistency, and repair behavior.
14. For manual local runs, the launching agent is the operator-agent: it answers
    blocking questions, records answer reasoning, and writes an operator-authored
    quality analysis before a run can be counted as clean.
15. After at least one completed stage in a manual checkpoint run, the operator may
    submit one stage-scoped intervention request through CLI or UI. If used, preserve
    `operator-requests/request-000N.md`, the resulting attempt log, validation result,
    and a short `operator-intervention-analysis.md` explaining why the request was
    needed and whether validation accepted the result.

Live E2E is not defined by mutable source-checkout execution from the AIDD repository
itself, and it is not a merge gate. The source checkout is read only during local-wheel
snapshot/build preparation, while durable evidence is written to
`<report-root>/<run_id>`; the default report root is `.aidd/reports/evals`.
Public-repository live E2E always builds and installs a local wheel from clean tracked
`HEAD`. Published-package install proof belongs to a separate release/install lane.

The local operator UI has a separate E2E evidence lane in
[`Operator UI Local-Project E2E Lane`](./operator-ui-local-project.md). That lane uses
local fixture projects and service-level UI tests, not public-repository live manifests.

## Product Scope Boundary

Public GitHub repositories are live E2E targets and support/reporting evidence sources.
They are not the supported local operator intake path. The product does not expose
`aidd init --github-issue <url>` because that command is out of product scope; local
operators initialize work items from the target project root with
`aidd init --work-item <id> --root .aidd`.

## Manual-Only Local Audit Policy

- `automation_lane` for every live scenario is `manual`.
- The only supported execution entrypoint is a local operator command that invokes the
  black-box evaluator module from a prepared source checkout, for example:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals
```

- Brokered approval proof is outside the public-repository live E2E lane. Keep it
  in the operator UI/local-project evidence lane so this evaluator stays focused
  on installed `aidd stage run`, CLI inspection, loopback UI/API checkpoints, and
  target-repository verification.
- When `--run-id` is omitted, the evaluator creates a fresh evidence bundle and
  does not resume prior state. Resume blocked or interrupted-resumable evidence
  only by passing that exact `--run-id`. If the generated run id already exists,
  the evaluator appends `-r2`, `-r3`, and so on instead of appending to the old
  bundle.
- If the evaluator is interrupted, it records `interrupted-resumable` state,
  attempts to terminate live runtime subprocesses, and requires explicit
  `--run-id` before continuing.
- Local runs may use optional environment variable overrides for custom wrapper commands:
  - `AIDD_EVAL_CLAUDE_CODE_COMMAND` for `claude-code`
  - `AIDD_EVAL_CODEX_COMMAND` for `codex`
  - `AIDD_EVAL_OPENCODE_COMMAND` for `opencode`
  - `AIDD_EVAL_QWEN_COMMAND` for experimental `qwen`
- When no override is set, the evaluator validates the default native provider command
  locally before cloning or installing artifacts.
- Override values must point to locally available wrapper commands that accept the AIDD
  adapter contract flags.
- GitHub Actions workflows must not reference `harness/scenarios/live/`.
- GitHub Actions workflows must not invoke `live_e2e_black_box`, require provider
  credentials, or use live-eval artifacts.
- CI/CD and release automation must not run live scenarios or require live-eval artifacts.
- Live manifests must declare `live_flow.driver: stepwise-black-box`,
  `live_flow.checkpoint_policy: after-each-step`, and
  `live_flow.frontend_checkpoints: true` so every live run inspects the public
  CLI, UI, and UI/API surfaces after each stage.
- Manual checkpoint notes should include an operator-intervention checkpoint when
  the run uses `aidd stage interact` or the UI `Request change` panel.

## Next-Flow Terminal Checkpoint Policy

After a public-repository live run reaches terminal `qa`, the launching operator must
inspect the completed-run handoff before deciding whether the run is counted:

- open the loopback UI or UI/API checkpoint evidence and confirm **Flow Complete** is
  visible for the terminal run;
- record the final QA status, visible blockers, final artifacts, approval counts,
  repair counts, answered-question counts, and recommended next-flow actions;
- record the operator next-flow decision as one of `no-follow-up`, `follow-up-draft`,
  `clone-draft`, `eval-batch`, `archive`, or `blocked`;
- if the operator records `follow-up-draft`, `clone-draft`, or `eval-batch`, preserve
  source-run references and selected source artifact links as evidence only;
- if the operator records `archive`, verify the completed run remains readable through
  dashboard/history/artifact inspection evidence.

Launching a second public-repository flow is **not** required for a clean live E2E run.
The default policy is to stop after the terminal checkpoint and operator-quality
analysis. Any child-flow proof must be explicitly enabled by a manual operator in a
separate future option, remain outside CI/CD and release automation, and record separate
lineage evidence instead of mutating the completed source run.

The optional evaluator flag `--enable-next-flow-follow-up-proof` is off by default.
When a manual operator explicitly enables it for a terminal passing run, the evaluator
creates a follow-up draft from the terminal QA report and writes `next-flow-lineage.json`
with source-run and child work item lineage. The flag must not launch a second public
repository flow and must remain manual-only.

## Maintained Repository Set

### `fastapi/typer`

- `AIDD-LIVE-001` - authored styled help alignment bugfix (`setup-blocked`; not a canonical README smoke until repinned or fixed)
- `AIDD-LIVE-002` - authored boolean option help rendering task

### `encode/httpx`

- `AIDD-LIVE-003` - authored invalid header error message task
- `AIDD-LIVE-004` - authored CLI docs sync task with docs-only counted verification

### `simonw/sqlite-utils`

- `AIDD-LIVE-005` - authored header-only CSV bugfix task
- `AIDD-LIVE-006` - authored yielded rows feature with interview
- `AIDD-LIVE-009` - less scripted CSV import resilience boundary task

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
- `qwen` is experimental and may be used for the tiny docs-only live lane and
  the Hono medium lane when `aidd eval doctor` confirms local provider readiness;
- `opencode` covers at least one live lane;
- `claude-code` keeps `AIDD-LIVE-005` as a small smoke lane and uses
  `AIDD-LIVE-007` as the planned maintained medium coverage candidate when
  `aidd eval doctor` confirms provider/auth readiness; generated live runtime
  config extends long-running `research`, `plan`, `review-spec`, `tasklist`,
  `implement`, `review`, and `qa` stage attempts;
- `generic-cli` remains a deterministic baseline provider and is not a maintained live provider in this wave.
- Public-repository live E2E now records UI/UX evidence artifacts, but brokered
  approval proof remains in the operator UI/local-project lane rather than this
  public-repository lane.

Representative matrix coverage for the live lane:

| Scenario class | Feature size | Maintained provider | Representative scenarios |
| --- | --- | --- | --- |
| `live-full-flow` | `tiny` | `codex`, `qwen` experimental | `AIDD-LIVE-004` |
| `live-full-flow` | `small` | `codex`, `claude-code` smoke | `AIDD-LIVE-003`, `AIDD-LIVE-005`, `AIDD-LIVE-009` |
| `live-full-flow` | `medium` | `codex`, `claude-code` planned, `qwen` experimental | `AIDD-LIVE-002`, `AIDD-LIVE-007` |
| `live-full-flow-interview` | `large` | `opencode` | `AIDD-LIVE-006` |
| `live-full-flow-interview` | `xlarge` | `opencode` | `AIDD-LIVE-008` |

`AIDD-LIVE-001` remains in the maintained set for historical evidence, but its current
Typer pin is setup-blocked before the runtime boundary. Use `AIDD-LIVE-005` as the
canonical installed live smoke until `AIDD-LIVE-001` is repinned or its setup baseline is
fixed.

`AIDD-LIVE-004` is the maintained tiny docs-only lane. Its counted gate is scoped to
documentation acceptance criteria: tracked product diff limited to the selected docs
files, consistent `https://httpbin.org/json` CLI example text, no placeholder runnable
URLs in added docs lines, no public endpoint call during verification, and QA artifact
publication. Full HTTPX pytest can still be run by an operator as exploratory
target-repository evidence, but it is not the clean-pass gate for this tiny documentation
scenario because unrelated async timeout tests can fail outside the selected docs change.

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
- declare `live_flow.answer_policy: agent-decides` so any stage can block on questions
  and resume after the launching operator-agent writes resolved answers;
- define authored task `interview` guidance when the scenario is
  `live-full-flow-interview`; other live scenarios may include it as optional context;
- document manual operator-intervention guidance when the run is expected to exercise
  a stage-scoped correction after a completed or blocked stage;
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
- `harness-metadata.json`
- `flow-state.json`
- `setup-transcript.json`
- `run-transcript.json`
- `verify-transcript.json`
- `quality-transcript.json`
- `teardown-transcript.json`
- `stage-audits/<stage>.json`
- `stage-audits/<stage>.md`
- `acceptance-coverage.json`
- `acceptance-coverage.md`
- `operator-quality-analysis-validation.json`
- `ui-ux-checkpoints.json`
- `ui-ux-checkpoints.md`
- `next-flow-checkpoint.json`
- `next-flow-checkpoint.md`

For counted manual clean-pass decisions, the eval bundle must also include
operator-authored evidence:

- `operator-quality-analysis.md`
- `answer-analysis.md` when the launching operator-agent answered blocking questions
- `operator-intervention-analysis.md` when the launching operator-agent submitted an
  operator intervention request
- `next-flow-lineage.json` only when the manual operator explicitly enabled
  `--enable-next-flow-follow-up-proof`

## Interview Scenarios

The maintained interview scenarios are:

- `AIDD-LIVE-006`
- `AIDD-LIVE-008`

Any live scenario may block when questions are unresolved and resume only after
standard `answers.md` content is present in the target-repository workspace path.
Operator-authored answer lines use the exact form `- Q1 [resolved] answer text`
without a colon after `[resolved]`.
The interview scenarios above are the maintained coverage cases where the manifest
expects that blocking question path to happen.

## Related References

- [`Scenario Matrix`](./scenario-matrix.md)
- [`Live Quality Rubric`](./live-quality-rubric.md)
- [`Eval and Harness Integration`](../architecture/eval-harness-integration.md)
