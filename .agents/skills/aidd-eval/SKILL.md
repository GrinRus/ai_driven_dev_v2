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
9. For live scenarios, preserve install evidence, feature-selection evidence, and quality artifacts.
10. Never mutate roadmap or backlog files as part of live quality auditing.
11. For manual live lanes, the launching agent is the operator-agent: answer blocking
    questions in `answers.md` with exact lines such as
    `- Q1 [resolved] answer text`, write `answer-analysis.md`, and write
    `operator-quality-analysis.md` as operator-authored eval bundle evidence.
12. Do not hand-edit runtime-generated stage output documents while adding
    operator-authored answer or quality evidence.

## Default procedure

1. Load the scenario and confirm the requested runtime is allowed.
2. Probe the adapter and record capability information.
3. Prepare or reset the fixture workspace or target repository.
4. Run the requested stage or flow through the harness.
   For live scenarios, select the first authored task, install the artifact under test first, and run AIDD from the target repository root.
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
7. Run live quality commands and score artifact/code quality when the scenario requires it.
8. Run graders.
9. Run log analysis.
10. Write the final audit artifacts.
11. Report the final execution verdict and quality conclusion explicitly.

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
- `.aidd/reports/evals/<run_id>/quality-report.md`
- `.aidd/reports/evals/<run_id>/quality-transcript.json`
- `.aidd/reports/evals/<run_id>/answer-analysis.md` when the launching
  operator-agent answered blocking questions
- `.aidd/reports/evals/<run_id>/operator-quality-analysis.md` for counted manual
  live clean-pass decisions

## Execution verdict taxonomy

For eval harness runs, preserve the stable execution verdict taxonomy:

- `pass`
- `fail`
- `blocked`
- `infra-fail`

Quality remains additive and must be reported separately as:

- `pass`
- `warn`
- `fail`
- `none`

## Example command shape

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime opencode
```
