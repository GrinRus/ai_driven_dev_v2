---
name: aidd-eval
description: Run harness and eval scenarios for ai_driven_dev_v2, validate document-first stage outputs, preserve runtime logs, analyze failures, and produce durable audit artifacts for deterministic and manual-live lanes.
---

# aidd-eval

## Use when

- You need to run a harness scenario against one of the maintained runtimes.
- You need to validate stage outputs against Markdown document contracts.
- You need to check self-repair behavior after validator failures.
- You need to capture runtime logs, normalized events, and log-analysis artifacts.
- You need to audit generated artifacts and generated code after execution.

For **local live-run operator guidance**, prefer `live-e2e`.
Use `aidd-eval` when the main task is generic eval execution, artifact analysis,
validation discipline, grading, and failure classification across deterministic
and manual-live lanes.

## Required reading

1. `docs/architecture/eval-harness-integration.md`
2. `docs/architecture/document-contracts.md`
3. `docs/architecture/adapter-protocol.md`
4. `docs/architecture/runtime-matrix.md`
5. `docs/e2e/scenario-matrix.md`
6. `docs/e2e/live-quality-rubric.md` for live scenarios
7. the selected scenario under `harness/scenarios/`
8. `.agents/skills/aidd-eval/references/e2e-flow-audit.md`

## Lane split

- Deterministic scenarios use `feature_source.mode: fixture-seed` and may run in `ci` or `manual`.
- Live scenarios use `feature_source.mode: authored-task-pool`, must live under `harness/scenarios/live/`, and are manual-only.

## Hard rules

1. Never hand-edit runtime-generated stage output documents during an eval run.
2. Always probe the adapter first.
3. Always preserve raw runtime logs.
4. Always validate output Markdown documents against their contracts.
5. Always allow the stage self-repair loop to run if the scenario expects repairable failures.
6. Always keep question/answer events as durable artifacts.
7. Always generate log-analysis output.
8. Keep infrastructure failures separate from model or document failures.
9. For live scenarios, preserve install evidence, feature-selection evidence, and execution artifacts.
10. Never mutate roadmap or backlog files as part of live manual quality reporting.
11. For manual live lanes, the launching agent is the operator-agent: answer blocking
    questions in `answers.md` with exact lines such as
    `- Q1 [resolved] answer text`, write `answer-analysis.md`, and write
    `quality-report.md` as the manual post-run report when a deliverable quality
    decision is needed.
12. Do not hand-edit runtime-generated stage output documents while adding
    operator-authored answers or the manual quality report.

## Default procedure

1. Load the scenario and confirm the requested runtime is allowed.
2. Probe the adapter and record capability information.
3. Prepare or reset the fixture workspace or target repository.
4. Run the requested stage or flow through the harness.
   For live scenarios, select the first authored task, build/install the artifact
   under test from the temp source snapshot, clone the target repository under the
   temp work root, and run AIDD from the target repository root.
5. Capture:
   - install transcript and artifact identity for live scenarios,
   - feature-selection evidence for live scenarios,
   - fixture-seed metadata for deterministic scenarios,
   - raw runtime logs,
   - structured runtime logs when available,
   - normalized events,
   - question/answer events,
   - validator outcomes,
   - repair attempts.
6. Validate all required output documents.
7. Run graders and log analysis.
8. Write the final execution audit artifacts.
9. Report the final execution verdict explicitly.
10. For terminal live runs, write manual `quality-report.md` only after inspecting
    the execution bundle and any additional manual checks.

## Canonical output locations

- `.aidd/reports/evals/<run_id>/runtime.log`
- `.aidd/reports/evals/<run_id>/runtime.jsonl` when supported
- `.aidd/reports/evals/<run_id>/events.jsonl` when supported
- `.aidd/reports/evals/<run_id>/install-transcript.json`
- `.aidd/reports/evals/<run_id>/feature-selection.json`
- `.aidd/reports/evals/<run_id>/validator-report.md`
- `.aidd/reports/evals/<run_id>/repair-history.md`
- `.aidd/reports/evals/<run_id>/log-analysis.md`
- `.aidd/reports/evals/<run_id>/grader.json`
- `.aidd/reports/evals/<run_id>/verdict.md`
- `.aidd/reports/evals/<run_id>/stage-audits/<stage>.json`
- `.aidd/reports/evals/<run_id>/stage-audits/<stage>.md`
- `.aidd/reports/evals/<run_id>/answer-analysis.md` when the launching
  operator-agent answered blocking questions
- `.aidd/reports/evals/<run_id>/quality-report.md` only when the launching SWE
  agent writes the manual post-run quality report

Manual live mutable execution is outside the source checkout by default:
`${TMPDIR:-/tmp}/aidd-live-e2e/<run_id>/source/aidd`,
`${TMPDIR:-/tmp}/aidd-live-e2e/<run_id>/build/dist`,
`${TMPDIR:-/tmp}/aidd-live-e2e/<run_id>/install-home`,
`${TMPDIR:-/tmp}/aidd-live-e2e/<run_id>/uv-cache`, and
`${TMPDIR:-/tmp}/aidd-live-e2e/<run_id>/target/<repo-slug>`.

## Execution verdict taxonomy

For eval harness runs, preserve the stable execution verdict taxonomy:

- `pass`
- `fail`
- `blocked`
- `infra-fail`

Live deliverable quality is not an eval runner verdict. For terminal live runs,
record it only in the manual post-run `quality-report.md`; the runner must not
parse that report or use it to change the execution verdict.

## Example command shape

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-yielded-rows-interview.yaml --runtime opencode --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals
```
