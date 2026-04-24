---
name: aidd-eval
description: Run harness and eval scenarios for ai_driven_dev_v2, validate document-first stage outputs, preserve runtime logs, analyze failures, and produce durable audit artifacts.
---

# aidd-eval

## Use when

- You need to run a harness scenario against one of the maintained adapters.
- You need to validate stage outputs against Markdown document contracts.
- You need to check self-repair behavior after validator failures.
- You need to capture runtime logs, normalized events, and log-analysis artifacts.
- You need to audit quality of generated artifacts and generated code after execution.
- You need to convert a real failure into a regression case.

## Do not use when

- The task is ordinary feature implementation without scenario execution.
- The task is architecture writing only.
- The task is manual document review without runtime execution.

## Required reading

1. `docs/architecture/eval-harness-integration.md`
2. `docs/architecture/document-contracts.md`
3. `docs/architecture/adapter-protocol.md`
4. `docs/architecture/runtime-matrix.md`
5. `docs/e2e/live-quality-rubric.md` for live scenarios
6. the selected scenario under `harness/scenarios/`
7. `.agents/skills/aidd-eval/references/e2e-flow-audit.md`

## Inputs

- adapter id
- scenario id or scenario file
- fixture workspace
- work item id
- interactive mode
- timeout / budget policy

## Hard rules

1. Never hand-edit runtime-generated stage output documents during an eval run.
2. Always probe the adapter first.
3. Always preserve raw runtime logs.
4. Always validate output Markdown documents against their contracts.
5. Always allow the stage self-repair loop to run if the scenario expects repairable failures.
6. Always keep question/answer events as durable artifacts.
7. Always generate log-analysis output.
8. Keep infrastructure failures separate from model or document failures.
9. For live scenarios, preserve install evidence for the AIDD artifact under test.
10. For live scenarios, preserve issue-selection evidence and quality artifacts.

## Default procedure

1. Load the scenario.
2. Probe the adapter and record capability information.
3. Prepare or reset the fixture workspace.
4. Run the requested stage or flow through the harness.
   For live scenarios, select the seeded issue, install the artifact under test first, and run AIDD from the target repository root.
5. Capture:
   - install transcript and artifact identity for live scenarios,
   - issue-selection evidence for live scenarios,
   - raw runtime logs,
   - structured runtime logs when available,
   - normalized events,
   - question/answer events,
   - validator outcomes,
    - repair attempts.
6. Validate all required output documents.
7. Run live quality commands and score the resulting artifact/code quality when the scenario requires it.
8. Run graders.
9. Run log analysis.
10. Write the final audit artifacts.
11. Report the final execution verdict and quality conclusion explicitly.

## Canonical output locations

- `.aidd/reports/evals/<run_id>/runtime.log`
- `.aidd/reports/evals/<run_id>/runtime.jsonl` when supported
- `.aidd/reports/evals/<run_id>/events.jsonl` when supported
- `.aidd/reports/evals/<run_id>/install-transcript.json`
- `.aidd/reports/evals/<run_id>/issue-selection.json`
- `.aidd/reports/evals/<run_id>/validator-report.md`
- `.aidd/reports/evals/<run_id>/repair-history.md`
- `.aidd/reports/evals/<run_id>/log-analysis.md`
- `.aidd/reports/evals/<run_id>/grader.json`
- `.aidd/reports/evals/<run_id>/verdict.md`
- `.aidd/reports/evals/<run_id>/quality-report.md`
- `.aidd/reports/evals/<run_id>/quality-transcript.json`

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
aidd eval run harness/scenarios/example-smoke.yaml --runtime claude-code
```

## Final response format

Status: <pass|fail|blocked|infra-fail>
Scenario: <scenario id>
Runtime: <runtime id>
Adapter: <adapter id>
Contracts: <validated documents>
Repair: <none|attempt count>
Questions: <none|count>
Quality gate: <pass|warn|fail|none>
Log analysis: <path>
Artifacts updated: <paths>
Failures: <none or concise list>
Next actions: <one short list>
