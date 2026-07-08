# Live End-to-End Catalog

This catalog defines the authored public-repository scenarios used for manual live E2E audits.

## Purpose

Live E2E now has two roles:

- `small` `flow-regression` lanes answer whether the installed black-box flow still
  reaches `qa` and preserves execution evidence.
- `medium`, `large`, and `xlarge` `product-evaluation` lanes answer whether AIDD can
  carry a real product request through `idea -> qa` with stage-by-stage quality review
  by the launching agent.

That makes live E2E different from the deterministic lanes:

- adapter conformance proves adapter contract behavior;
- deterministic stage and workflow scenarios prove repo-local invariants quickly;
- manual live E2E proves installed-CLI full-flow behavior on a pinned public repository;
- product-evaluation live E2E adds manual per-stage and final code/product quality
  audits without turning those quality decisions into runner-owned verdicts.

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
7. Change into the target repository root for setup, stage, verify, and teardown.
8. Select the first authored task from the scenario's `authored-task-pool`.
9. Run installed `aidd` from that repository root with explicit workflow bounds `idea -> qa`.
   The manifest `limits.timeout_minutes` value is the budget for each public
   `aidd stage run` command in the stepwise black-box loop, not a global flow
   timeout and not a deliverable quality signal.
10. Keep target `.aidd/` rooted inside the target repository.
11. Preserve install, setup, run, verify, and teardown evidence in the eval bundle.
12. Write `stage-audits/<stage-run-id>.json` and `.md` after each stage run.
13. Preserve `stage-timing.json`, `stage-timing.md`, `self-repair-matrix.json`, and
    `self-repair-matrix.md` so operators can audit step duration, per-attempt runtime windows,
    deterministic repair-probe coverage, terminal document consistency, per-stage command
    timeout budgets, and repair behavior.
14. In live manifests, AIDD self-check verification commands must call the installed
    `aidd` binary from `PATH` directly, for example `aidd stage questions ...`.
    Do not use `uv run aidd ...` for these checks inside the target repository:
    package-manager invocation can create target-repo lockfiles after QA and pollute
    the final workspace evidence. Target-project verification commands may still use
    the target repository's package manager when that is the repo's normal test surface.
15. For `product-evaluation` runs, after every successful stage run the runner writes
    `stage-audits/<stage-run-id>.*`, stops with `awaiting-quality-review`, and requires the
    launching agent to write the exact
    `stage-quality-audits/<stage-run-id>.md` path named in `flow-state.json` before
    resuming the same `--run-id`.
    The `implement` runner audit separates tracked files, new untracked product files,
    known harness/config untracked files, and setup-baseline untracked files so manual
    code review can inspect the complete deliverable workspace. If it records
    `product_untracked_files`, final `code-quality-report.md` and `quality-report.md`
    must name those files and explain how they were reviewed before counted-clean.
16. For `product-evaluation`, normal review/QA defects may use `request-remediation`
    in the manual audit for a `review` or `qa` stage run. The evaluator then uses the
    existing operator remediation flow to create the durable request, run a new
    `implement`, mark downstream `review` and `qa` stale, and rerun stale downstream
    stages one at a time with another quality checkpoint after each stage run.
17. Terminal product-evaluation execution pass requires a fresh terminal `qa`, no stale
    downstream stages, and passing manifest verification. The runner still does not score
    subjective product quality.
18. For manual local runs, the launching agent is the operator-agent and quality
    auditor: it answers blocking questions, records answer reasoning, reviews each
    `product-evaluation` stage before resume, and writes final
    `flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md`
    when a product-quality decision is needed.
19. After at least one completed stage in a manual checkpoint run, the operator may
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
Authenticated native-runtime UI proof is tracked separately in
[`Real-Provider UI E2E Lane`](./real-provider-ui-e2e.md). That lane is manual,
Codex-first, and starts from clean `aidd ui` onboarding with explicit runtime selection.

## Product Scope Boundary

Public GitHub repositories are live E2E targets and support/reporting evidence sources.
They are not the supported local operator intake path. The product does not expose
`aidd init --github-issue <url>` because that command is out of product scope; local
operators initialize work items from the target project root with
`aidd init --work-item <id> --root .aidd`.

## Manual-Only Local Audit Policy

- `automation_lane` for every live scenario is `manual`.
- `live_matrix_role: flow-regression` is valid only for `feature_size: small`.
- `live_matrix_role: product-evaluation` is required for `feature_size: medium`,
  `large`, and `xlarge`.
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
- Resume from `awaiting-quality-review` requires the exact audit file named in
  `flow-state.json`, for example `stage-quality-audits/stage-0007-review.md`. If that file is
  missing, the runner refuses the resume instead of advancing the stage loop.
- `blocked` is reserved for unresolved model questions or runtime approvals. It is
  distinct from `awaiting-quality-review`.
- Malformed interview documents in `questions.md` or `answers.md`, including bullets such as
  `- Q1 [resolved]: ...`, are AIDD stage-output/document-contract failures. They are
  not `provider-no-progress`, not `manual-quality-stop`, not a product-quality verdict,
  and not a runner-scored counted-clean decision.
- Unsupported `review-spec` claims, such as high-severity issues without direct evidence or
  contradictions with upstream `research`/`plan` without `Reconciliation`, are AIDD
  stage-output/document-contract failures. They are not `provider-no-progress`, not
  `manual-quality-stop`, not a product-quality verdict, and not a runner-scored
  counted-clean decision.
- `Flow decision: request-remediation` is valid only for `review` and `qa` stage-run
  audits and must include source stage, source ids, and operator note. It starts the
  existing AIDD remediation flow; it is not a new core stage and does not replace
  `operator-intervention`.
- If a stage quality audit records `Flow decision: stop-not-counted`, the next resume
  ends the run as `manual-quality-stop`; it is not an infra/provider failure and not a
  `blocked` run. The runner writes `manual-quality-stop.json`,
  `manual-quality-stop.md`, and stop-point `target-workspace-evidence.*`; it does not
  write `verdict.md` or `grader.json` for that manual terminal state.
- If the evaluator is interrupted, it records `interrupted-resumable` state,
  attempts to terminate live runtime subprocesses, and requires explicit
  `--run-id` before continuing.
- `limits.timeout_minutes` is the per-stage hard command timeout. Separately,
  `limits.no_progress_timeout_minutes` is an idle-progress budget for public
  `aidd stage run` commands; its default for live manifests is `30` minutes.
  If the provider process stays alive but stdout/stderr and watched stage artifacts
  stop changing past that budget, the evaluator stops the process group and records
  terminal `infra-fail` with reason `provider-no-progress before completed stage
  artifact`. This is not `blocked`, not `manual-quality-stop`, not product-quality
  failure, and not a product-quality defect.
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
  CLI, UI, and UI/API surfaces during observed running-stage wait states and after each stage.
- Manual checkpoint notes should include an operator-intervention checkpoint when
  the run uses `aidd stage interact` or the UI `Request change` panel.

## Manual Evidence Rotation Policy

When refreshing live E2E evidence, operators should prefer rotating across different
products, repositories, feature families, and scenario sizes instead of repeatedly choosing
the same product and feature shape. Diversity is part of the success analysis: it helps
separate AIDD workflow quality from one repository's setup quirks, one runtime's behavior
on a familiar task, or one narrow class of changes.

Repeating a scenario is still appropriate when the goal is a targeted rerun: confirming a
fixed blocker, comparing runtimes on the same manifest, validating a repin, or preserving a
canonical smoke proof. Otherwise, manual refresh batches should choose a different product
or feature family from the most recent manually accepted run whenever provider readiness
and local environment constraints allow it.

## Next-Flow Terminal Checkpoint Policy

After a public-repository live run reaches terminal `qa`, the launching operator must
inspect the completed-run handoff before writing any manual deliverable-quality decision:

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

### `encode/httpx`

- `AIDD-LIVE-004` - small `flow-regression` docs/config lane with docs-only execution verification

### `simonw/sqlite-utils`

- `AIDD-LIVE-005` - small `flow-regression` header-only CSV bugfix lane
- `AIDD-LIVE-006` - xlarge `product-evaluation` yielded rows feature with security/trust interview

### `honojs/hono`

- `AIDD-LIVE-007` - medium `product-evaluation` non-Error throw handling task
- `AIDD-LIVE-008` - xlarge `product-evaluation` router parity with `/**` syntax interview

### `openapi-ts/openapi-typescript`

- `AIDD-LIVE-010` - large `product-evaluation` discriminator composition codegen task with interview

### `pytest-dev/pytest`

- `AIDD-LIVE-011` - xlarge `product-evaluation` collection error summary task with interview

### `Kludex/starlette`

- `AIDD-LIVE-012` - large `product-evaluation` streaming error and disconnect boundary task

## Candidate Repository Drafts

Candidate drafts are not maintained coverage. They are setup-proofed lanes that
may be promoted only after a separate proof run and planning update. See
[`Live E2E Candidate Setup Audits`](./live-e2e-candidate-setup-audits.md) for
the Pydantic, FastAPI, Rich, and Ruff audit table.

### `Textualize/rich`

- `AIDD-LIVE-013` - medium candidate-only `product-evaluation` lane for literal
  bracketed markup rendering across console and table output

## Matrix Source Of Truth

Use [`Scenario Matrix`](./scenario-matrix.md) as the source of truth for:

- `scenario_class`
- `feature_size`
- `automation_lane`
- `canonical_runtime`
- provider rollout coverage

For live scenarios in this wave:

- `codex` is the primary canonical runtime for maintained small regression, medium
  product-evaluation, and selected large non-interview live lanes;
- `qwen` is experimental and may be used for the small docs-only live lane and
  the Hono medium lane when `aidd eval doctor` confirms local provider readiness;
- `opencode` covers at least one live lane and remains the canonical runtime for the
  maintained live interview expansion lanes;
- `claude-code` keeps `AIDD-LIVE-005` as a small regression lane and uses
  `AIDD-LIVE-007` plus `AIDD-LIVE-012` as maintained medium and large
  coverage candidates when
  `aidd eval doctor` confirms provider/auth readiness; generated live runtime
  config extends long-running `research`, `plan`, `review-spec`, `tasklist`,
  `implement`, `review`, and `qa` stage attempts;
- `generic-cli` remains a deterministic baseline provider and is not a maintained live provider in this wave.
- Public-repository live E2E now records frontend/API checkpoint evidence as raw
  run-integrity evidence, but brokered approval proof and full UI/UX audit evidence
  remain in the operator UI/local-project lane or the manual `quality-report.md`.

Representative matrix coverage for the live lane:

| Scenario class | Feature size | Live role | Maintained provider | Representative scenarios |
| --- | --- | --- | --- | --- |
| `live-full-flow` | `small` | `flow-regression` | `codex`, `qwen` experimental | `AIDD-LIVE-004` |
| `live-full-flow` | `small` | `flow-regression` | `codex`, `opencode`, `claude-code` | `AIDD-LIVE-005` |
| `live-full-flow` | `medium` | `product-evaluation` | `codex`, `claude-code` planned, `qwen` experimental | `AIDD-LIVE-007` |
| `live-full-flow` | `large` | `product-evaluation` | `codex`, `claude-code` planned | `AIDD-LIVE-012` |
| `live-full-flow-interview` | `large` | `product-evaluation` | `opencode` | `AIDD-LIVE-010` |
| `live-full-flow-interview` | `xlarge` | `product-evaluation` | `opencode` | `AIDD-LIVE-006`, `AIDD-LIVE-008`, `AIDD-LIVE-011` |

`AIDD-LIVE-001` is retired from maintained coverage because it is setup-blocked before
the runtime boundary. The maintained small lanes are regression-smoke only and must not
be used as counted-clean product-quality evidence.

`AIDD-LIVE-004` is the maintained small docs-only regression lane. Its execution verification is
scoped to documentation acceptance criteria: tracked product diff limited to the
selected docs files, consistent `https://httpbin.org/json` CLI example text, no
placeholder runnable URLs in added docs lines, no public endpoint call during
verification, and QA artifact publication. Full HTTPX pytest can still be run by an
operator as exploratory target-repository evidence, but it is not required
execution evidence for this documentation scenario because unrelated async
timeout tests can fail outside the selected docs change.

## Live-Scenario Contract

Every maintained live scenario must:

- live under `harness/scenarios/live/`;
- declare `scenario_class` as `live-full-flow` or `live-full-flow-interview`;
- declare `feature_size`;
- declare `live_matrix_role`;
- use `live_matrix_role: flow-regression` only with `feature_size: small`;
- use `live_matrix_role: product-evaluation` for `medium`, `large`, and `xlarge`;
- declare `automation_lane: manual`;
- declare `canonical_runtime` that also appears in `runtime_targets`;
- declare `repo.revision`;
- use `feature_source.mode: authored-task-pool`;
- select the first listed authored task deterministically;
- define authored task `id`, `title`, `summary`, `intent`, `target_change`, `expected_scope`,
  `acceptance_criteria`, `verification`, `quality_bar`, and `size_rationale`;
  `quality_bar` is authored task metadata only and must not be treated as an automatic
  live quality gate;
- for `product-evaluation`, define task `visible_request`, `audit_rubric`, and
  `complexity_axes`; only `visible_request` is runtime-facing product request context,
  while `audit_rubric` is for the launching agent's manual review;
- declare `live_flow.answer_policy: agent-decides` so any stage can block on questions
  and resume after the launching operator-agent writes resolved answers;
- define authored task `interview` guidance when the scenario is
  `live-full-flow-interview`; other live scenarios may include it as optional context;
- document manual operator-intervention guidance when the run is expected to exercise
  a stage-scoped correction after a completed or blocked stage;
- force full-flow `idea -> qa`;
- run repo-local verification commands;
- omit `quality:` blocks; post-run quality review is a manual SWE-agent report;
- preserve feature-selection, validator, log-analysis, verdict, and execution artifacts.

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
- `summary.md`
- `feature-selection.json`
- `install-transcript.json`
- `harness-metadata.json`
- `flow-state.json`
- `setup-transcript.json`
- `run-transcript.json`
- `verify-transcript.json`
- `teardown-transcript.json`
- `stage-audits/<stage-run-id>.json`
- `stage-audits/<stage-run-id>.md`
- `stage-quality-audits/<stage-run-id>.md` for each completed `product-evaluation` stage run,
  written manually by the launching agent before resume
- `target-workspace-evidence.json`
- `target-workspace-evidence.md`
- `product-evaluation-bundle-summary.json` for terminal `product-evaluation` bundles
- `product-evaluation-bundle-summary.md` for terminal `product-evaluation` bundles
- `frontend-checkpoints.json`
- `frontend-checkpoints.md`
- `next-flow-checkpoint.json`
- `next-flow-checkpoint.md`

`frontend-checkpoints.md` starts with a manual visual review checklist for the launching
agent. It names the browser checks that API probes cannot prove: visible next action and
active stage, readable desktop/mobile topbar labels, failure-appropriate recovery primary
action, reachable logs/artifacts/questions/answers, next-flow handoff visibility, and no
horizontal overflow for long paths, log labels, or action copy. The checklist is operator
guidance only; it is not runner-generated screenshot evidence and not a UI/UX quality gate.
When a public stage exposes `preparing`, `executing`, or `validating` metadata while the
stage command is still alive, `frontend-checkpoints.*` also records a `running-stage`
phase: disabled `wait-for-stage` next action, active running stage visibility, and runtime
log affordance, including the pending-log state before `runtime.log` exists. The normal
`post-stage` phase still records completed stage API and artifact reachability.

The runner does not create `flow-quality-report.md`, `code-quality-report.md`,
`quality-report.md`, `quality-transcript.json`, `acceptance-coverage.*`,
`ui-ux-checkpoints.*`, `operator-quality-analysis.md`, or
`operator-quality-analysis-validation.json`.

`run-transcript.json` records the aggregate black-box stage loop. Its aggregate
`timeout_seconds` stays `null` unless the runner gains a true global flow timeout.
The same file carries a `timeout_policy` object that identifies the per-stage command
budget, currently `scope: "per-stage-command"`. `stage-timing.json` and
`stage-timing.md` show the actual timeout recorded for each `run-stage` command.
`verify-transcript.json` may include `workspace_cleanup` when successful manifest
verification created known ignored byproducts after QA. That cleanup is limited to
new verification residue and is execution hygiene before final workspace evidence.

`target-workspace-evidence.*` compares the target repository snapshot after setup with
the final workspace state. It is non-gating evidence for manual quality review:
`aidd.example.toml` is harness config, setup-created untracked files remain visible,
top-level `workitems/...` duplicates are severe deliverable pollution, and direct
`.aidd/*.py` scratch files are artifact hygiene findings. It also surfaces new
ignored local artifacts such as `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pdm-build/`,
`coverage/`, build, dist, or dependency-cache files. New files inside a setup-baseline
ignored root, such as `.venv/.../__pycache__`, are recorded as `setup-baseline ignored churn`
rather than pollution findings. Evidence that a runtime
deleted/recreated the prepared checkout or live harness run directories is a run
integrity and deliverable-quality blocker for manual review. The runner does not
turn these findings into a quality gate.

For terminal `product-evaluation` bundles, `product-evaluation-bundle-summary.*`
is generated as a read-only index over existing evidence: stage-quality audit
presence and decisions, remediation source ids, repair counts, tracked and
untracked product files, known harness files, final report presence, and terminal
flow-state/verdict consistency. The summary is navigation evidence, not
runner-owned quality scoring. It does not update `verdict.md`, `grader.json`,
`flow-quality-report.md`, `code-quality-report.md`, or `quality-report.md`, and it
does not compute `counted-clean`. Manual `quality-report.md` remains the only final counted-clean decision.

After a terminal run, the launching SWE agent may add manual post-run evidence:

- `flow-quality-report.md` with stage-by-stage flow quality and operator experience notes
- `code-quality-report.md` with final target-repository code review, diff, and verification assessment
- `quality-report.md` with run-integrity, stage summary, product delivery, code quality,
  test/verification, manual AIDD operator UI/UX decisions, and final
  counted/not-counted decision
- `answer-analysis.md` when the launching operator-agent answered blocking questions
- `operator-intervention-analysis.md` when the launching operator-agent submitted an
  operator intervention request
- `next-flow-lineage.json` only when the manual operator explicitly enabled
  `--enable-next-flow-follow-up-proof`

The manual operator UI/UX decision must inspect AIDD operator workflows rather than
reinterpret `frontend-checkpoints.*` HTTP/API and operator-surface semantic checks as
UX proof. Use the `frontend-checkpoints.md` manual visual checklist as a prompt, then
record actual browser evidence or explicitly mark surfaces `not inspected`.
At minimum, review terminal flow
visibility, stage list navigation, artifact/log views, questions and answers,
repair evidence, next-flow handoff, state clarity, readability, keyboard/focus
behavior where manually inspectable, responsive behavior or `not inspected`, and
any manually captured screenshots or browser notes. Generated product UI is outside this live E2E operator-UI review unless the report marks it `not-applicable`.

For `product-evaluation`, counted-clean is possible only when every completed stage run has
a corresponding `stage-quality-audits/<stage-run-id>.md`, the final code review exists in
`code-quality-report.md`, and the final `quality-report.md` records
`counted-clean` with `Iteration History`, every remediation request, source id,
operator note, stale downstream rerun, and fresh terminal QA state. If implement-stage evidence contains `product_untracked_files`, those
files must be explicitly covered in the final code and quality reports. A runner
execution `pass` without those manual artifacts is only an execution pass, not
counted-clean product-quality evidence.

## Interview Scenarios

The maintained interview scenarios are:

- `AIDD-LIVE-006`
- `AIDD-LIVE-008`
- `AIDD-LIVE-010`
- `AIDD-LIVE-011`

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
