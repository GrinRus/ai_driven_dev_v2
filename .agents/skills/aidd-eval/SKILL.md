---
name: aidd-eval
description: Execute deterministic AIDD scenarios or audit existing eval bundles, validation, repair, and runtime evidence; use live-e2e for new or resumed live provider runs.
---

# aidd-eval

Choose execution or analysis from the request. An audit uses retained artifacts;
it does not authorize resetting fixtures, rerunning providers, or repairing product code.
For **local live-run operator guidance**, prefer [live-e2e](../live-e2e/SKILL.md).

## Deterministic execution

Read the chosen manifest and its coverage in
[the scenario matrix](../../../docs/e2e/scenario-matrix.md). For harness changes, read
the owning section of [eval integration](../../../docs/architecture/eval-harness-integration.md).
The `aidd eval execute` surface accepts local `fixture-seed` scenarios with the
`generic-cli` fixture runtime; it does not launch a chosen live provider.

```bash
uv run aidd eval doctor harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml --runtime generic-cli
uv run aidd eval execute harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml --root .aidd/eval-audit
uv run aidd eval summary --root .aidd/eval-audit
```

Use a dedicated root and inspect the printed evidence bundle, `verdict.md`,
`grader.json`, `validator-report.md`, `repair-history.md`, and `log-analysis.md`.
The scenario supplies setup, invocation, verification, and teardown; inspect those
commands before execution. Do not substitute a different fixture or hand-edit generated
outputs to make verification pass. Probe readiness, preserve available raw logs, let
expected bounded repair/interview paths run, then report the observed verdict.

For an accepted broader deterministic lane, use `scripts/run_ci_scenarios.py` and
the check routing in [agent development](../../../docs/agent-development.md).
That lane is distinct from a single-scenario eval.

## Audit an existing bundle

1. Establish scenario/fixture or repository pin, runtime, run/stage/attempt IDs, and
   recorded prompt/config identity. Use the actual bundle root, not a presumed default.
2. Follow [evidence and verdicts](references/evidence-and-verdicts.md) for the relevant
   lane. Inspect logs, substantive outputs, canonical validator/lifecycle reports,
   repair/interview history, and selected-task evidence when present.
3. Identify the first decisive signal; separate infrastructure/provider, adapter,
   orchestration, contract/validator, prompt, and artifact-quality causes. Use
   [runtime-log-triage](../runtime-log-triage/SKILL.md) for a focused diagnosis.
4. Write the requested analysis separately from runner-owned evidence, following
   [the audit outline](references/e2e-flow-audit.md). Name observed facts, inference,
   execution verdict, evidence paths, uninspected surfaces, and bounded follow-ups.

For live product-evaluation analysis, the launching agent is the operator-agent;
the [manual quality templates](../live-e2e/references/quality-reports.md) define stage
and final reports. Preserve the runner's execution verdict even when manual quality
is unacceptable. Never mutate roadmap or backlog files as part of live manual quality
reporting. Do not overwrite runtime outputs, logs, or existing runner reports.
