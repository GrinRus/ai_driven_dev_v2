# Live E2E Manual Quality Report Guide

Live E2E has two separate decisions:

- the runner's execution verdict in `verdict.md`, `grader.json`, `summary.md`, and
  `harness-metadata.json`;
- the launching SWE agent's manual quality decision in
  `.aidd/reports/evals/<run_id>/quality-report.md`.

The runner does not create, parse, validate, or score `quality-report.md`. It also
does not compute counted-clean status. A missing manual quality report must not
change a passing execution verdict.

## Execution Bundle

The live runner owns execution evidence only. It records whether the installed
`idea -> qa` flow ran through public CLI/UI surfaces, whether verification passed,
whether questions blocked the run, and whether provider or harness failures occurred.

Runner-owned artifacts include:

- `flow-state.json`
- `flow-steps.json`
- `flow-report.md`
- `operator-actions.jsonl`
- `frontend-checkpoints.json`
- `frontend-checkpoints.md`
- `stage-audits/<stage>.json`
- `stage-audits/<stage>.md`
- `runtime.log`
- `runtime.jsonl` when attempts emitted structured JSONL
- `events.jsonl` when attempts emitted normalized JSONL
- `validator-report.md`
- `repair-history.md`
- `log-analysis.md`
- `stage-timing.json`
- `stage-timing.md`
- `grader.json`
- `verdict.md`
- `summary.md`
- `feature-selection.json`
- `install-transcript.json`
- `setup-transcript.json`
- `run-transcript.json`
- `verify-transcript.json`
- `teardown-transcript.json`
- `harness-metadata.json`
- `next-flow-checkpoint.json`
- `next-flow-checkpoint.md`

The runner no longer emits `quality-transcript.json`, `acceptance-coverage.*`,
`ui-ux-checkpoints.*`, `operator-quality-analysis.md`, or
`operator-quality-analysis-validation.json`.

`frontend-checkpoints.*` are raw run-integrity evidence for the public operator
surfaces. They are not a UI/UX audit, not screenshot evidence, and not a quality gate.

## Manual Report

After the terminal run, the launching SWE agent may write:

`.aidd/reports/evals/<run_id>/quality-report.md`

Use this exact structure:

```markdown
# Live E2E Quality Report

## Decision
- Run integrity decision: clean | defective | blocked-infra | blocked-provider | blocked-harness
- Deliverable quality decision: counted-clean | not-counted | blocked-model-quality | blocked-product-defect
- Overall decision: counted-clean | not-counted | blocked

## Run Integrity
- Execution verdict:
- Stages reached:
- Evidence completeness:
- Runtime/provider/log issues:
- Repair/interview behavior:
- Timeout policy/evidence:
- Run blockers:

## Artifact Quality
- Stage artifact completeness:
- Idea/research/plan/review-spec/tasklist quality:
- Cross-stage consistency:
- Stage-result/validator consistency:
- Validator report quality:
- Repair burden analysis:
- Artifact evidence links:

## Code Quality
- Diff scope, including tracked and untracked files:
- Acceptance criteria evidence:
- Architecture/maintainability/API compatibility:
- Edge cases/security/performance risks:
- Test quality and regression relevance:
- Baseline/before-after evidence:
- Code evidence links:

## UI/UX Quality
- User workflows inspected:
- Visual/readability/layout evidence:
- Accessibility/keyboard/focus notes:
- Responsive behavior notes:
- Empty/loading/error/blocking states:
- UX evidence links:

## Evidence Reviewed
- Flow evidence:
- Stage audits:
- Logs/transcripts:
- Target repo diff:
- Review/QA artifacts:
- UI/API or screenshot evidence:
- Extra manual checks run by SWE agent:

## Notes
- Follow-ups:
- Residual risks:
```

## Decision Boundaries

`Run Integrity` evaluates only the live run and evidence bundle: execution verdict,
stage reachability, log completeness, provider behavior, repair/interview flow, and
harness defects. Review `run-transcript.json`, `stage-timing.json`, and
`log-analysis.md` to confirm that timeout evidence distinguishes the per-stage
command timeout from the absence of a global flow timeout.

`Artifact Quality`, `Code Quality`, and `UI/UX Quality` evaluate the deliverable
produced by the full flow. These sections are manual review, not runner state.

The manual `counted-clean` phrase is only a human-authored deliverable-quality
decision inside `quality-report.md`. AIDD does not parse it.

## Required Manual Review Coverage

Artifact review should cover the content depth of all stage outputs, cross-stage
traceability, validator report usefulness, and repair burden cause. Classify repair
burden as format issue, prompt/context issue, validator/contract issue, model
quality issue, or product ambiguity. Also inspect `stage-audits/<stage>.*` for
non-gating consistency findings where a runtime-authored `stage-result.md` validator
claim differs from the canonical validator/audit verdict.

Code review should cover the full target repository diff, including untracked files.
It should address acceptance criteria evidence, architectural fit, maintainability,
API compatibility, edge cases, security, performance, test relevance, and any
baseline or before/after proof.

UI/UX review should inspect real operator/user workflows. API probes alone are not
UX evidence. Cite screenshots or browser evidence manually when available, and
record visual layout/readability, accessibility, keyboard/focus, responsive behavior,
and empty/loading/error/blocking states.
