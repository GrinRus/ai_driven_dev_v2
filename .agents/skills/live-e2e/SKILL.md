---
name: live-e2e
description: Prepare, run, resume, or audit a manual installed AIDD workflow against a pinned public repository; use for local live E2E, not deterministic checks or package publishing.
---

# live-e2e

Use this skill for a scenario in `harness/scenarios/live/`. For deterministic
execution or an existing generic eval bundle, use [aidd-eval](../aidd-eval/SKILL.md).
Live E2E remains local manual operator evidence, outside GitHub Actions, CI/CD,
and release gates.

## Select the requested operation

- **Prepare:** inspect the manifest and prerequisites; stop with a concrete launch command.
- **Run/resume:** execute the selected manifest/runtime and handle its operator checkpoints.
- **Audit:** inspect retained evidence and write the requested analysis; do not start a run.
- **Stabilize:** only when fixes and repeated runs are in scope, use the iteration loop below.

Preserve the user's chosen scenario, provider, scope, and existing authorization.
Do not turn one run into an unbounded provider matrix. Provider authentication and
credential changes need their own authorization; this skill does **not** provision
runtime authentication, wrapper scripts, or provider setup.

## Prepare a run

Use a prepared local **source checkout**. Read the selected manifest, its entry in
[the live catalog](../../../docs/e2e/live-e2e-catalog.md), and relevant coverage in
[the scenario matrix](../../../docs/e2e/scenario-matrix.md). Consult
[the operator handbook](../../../docs/operator-handbook.md) for an unfamiliar operator action.

Confirm `automation_lane: manual`, `stage_scope: idea -> qa`, the requested runtime
in `runtime_targets`, a resolved repository pin, and the first listed authored task.
Tracked AIDD source must be clean: the harness builds a wheel from a snapshot of
tracked AIDD `HEAD`, not uncommitted edits or the published PyPI package.

```bash
uv sync --locked --extra dev
uv run aidd doctor
uv run aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex
```

Inspect doctor output, including execution readiness; a zero exit alone is not proof
of provider readiness. Native Codex preflight checks `codex login status` in the
operator environment inherited by execution.

Native provider CLI commands are the default. The live Codex profile in
`src/aidd/harness/live_runtime_config.py` currently generates:

```toml
[runtime.codex]
model = "gpt-5.6-luna"
reasoning_effort = "high"
```

This profile is specific to manual live evaluation. Native Codex startup ignores
unrelated user configuration/plugins; other providers retain native model defaults.
When intentionally supplying an AIDD-compatible wrapper command, use the matching
`AIDD_EVAL_CODEX_COMMAND`, `AIDD_EVAL_CLAUDE_CODE_COMMAND`,
`AIDD_EVAL_OPENCODE_COMMAND`, or `AIDD_EVAL_QWEN_COMMAND`. An override selects
`adapter-flags` mode and must accept AIDD's adapter flags; a raw provider command
is not automatically a compatible wrapper.

## Launch and resume

From the AIDD source root, this starts a **new** run:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals
```

The defaults are `--work-root ${TMPDIR:-/tmp}/aidd-live-e2e` and
`--report-root .aidd/reports/evals`. Use explicit roots when stable audit paths matter.
Mutable source/build/install/target state lives under the work root; durable bundles
live under the report root. The harness clones the target, seeds its `.aidd/`, writes
`aidd.example.toml`, then runs the installed binary from the target repository root.
Installation has an isolated home/cache; stage execution inherits operator auth
without copying credentials. Keep `.aidd` inside the target for installed live runs.

Record the returned run ID and `flow-state.json`. **Every resume needs explicit
`--run-id <id>` plus the original manifest, runtime, work root, and report root.**
Omitting `--run-id` always creates a fresh run, even after answering questions.
Replace `RUN_ID_FROM_FLOW_STATE` with the recorded ID:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals --run-id RUN_ID_FROM_FLOW_STATE
```

## Handle operator checkpoints

For manual live runs, the launching agent is the operator-agent. Resolve authored
task choices within the agreed scenario; a credential, destructive operation, or
out-of-scope product decision is not answered by inventing permission.

| Checkpoint or decision | Required action before explicit resume |
| --- | --- |
| `blocked` by questions | Read `operator-action-request.md` and referenced `questions.md`; write standard `[resolved]` answers in its `answers.md` and explain choices in bundle `answer-analysis.md`. |
| `awaiting-quality-review` | Read `quality_review_required_stage_run_id` and exact required path in `flow-state.json`; inspect stage artifacts, runtime logs, `stage-audits/<stage-run-id>.*`, target diff and task evidence; write the required stage audit. |
| `operator-intervention` | Preserve evidence and resolve the identified external decision within existing authorization; do not substitute a fabricated answer. |
| Terminal execution or `manual-quality-stop` | Audit the retained outcome; do not resume as a new execution or overwrite reports to improve the verdict. |

Use exact answer lines such as `- Q1 [resolved] answer text`, with no colon after
`[resolved]`. Never hand-edit runtime-generated stage outputs while adding answers.
Stage audits may choose `continue`, `continue-with-risk`, `request-remediation`
only for `review` or `qa`, `operator-intervention`, or `stop-not-counted`.
Normal remediation uses the existing operator remediation surface, preserves
`completed_stage_runs`, and reruns stale downstream stages through fresh checkpoints.

Read [quality report templates](references/quality-reports.md) for a quality checkpoint
or terminal product-evaluation decision. Read
[evidence and verdicts](../aidd-eval/references/evidence-and-verdicts.md) to classify
failures, inspect task-aware checkpoints, or judge bundle completeness and workspace
hygiene. The runner reports execution; the launching agent writes
`flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md` after
inspecting evidence. A passing execution is not an automatic deliverable-quality pass.

## Bounded stabilization

When stabilization is requested, plan step, execute through public operator surfaces,
inspect artifacts/UI/API/logs, classify the first decisive signal, and decide the next step.
Fix the smallest accepted local task, run its focused checks, and preserve the old bundle.
Live reruns require a clean tracked revision; commit only when that is within the
accepted task. Rerun the same manifest/runtime until it is clean **within the agreed
run/time budget**; stop on budget exhaustion, repeated unchanged external blockers,
or a decision requiring new scope. Change scenario/provider only when coverage expansion
is part of that scope. Record fixes, pinned variables, execution and manual quality results,
evidence locations, and remaining gaps. Do not mutate roadmap/backlog as part of manual
quality reporting; planning changes are separate accepted work.
