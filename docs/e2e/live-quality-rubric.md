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
- `target-workspace-evidence.json`
- `target-workspace-evidence.md`
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
Screenshots and browser notes are optional manual evidence, not runner-generated artifacts.

`target-workspace-evidence.*` records the target repository snapshot after setup and
after the terminal/stop state. It classifies tracked diff, setup-baseline untracked
files, known harness config such as `aidd.example.toml`, new untracked files, top-level
`workitems/...` pollution, unexpected `.aidd/` scratch files, and new ignored local
artifacts such as `.venv/`, `.pytest_cache/`, `.pdm-build/`, `coverage/`, build,
dist, or dependency-cache files. New ignored files under an ignored root that already
existed at setup, for example `.venv/.../__pycache__`, are recorded as `setup-baseline ignored churn`
rather than pollution findings. These findings are non-gating execution
evidence for manual review; they do not alter `verdict.md` or `grader.json`.

## Manual Report

After the terminal run, the launching SWE agent may write:

`.aidd/reports/evals/<run_id>/quality-report.md`

Use this exact structure:

```markdown
# Live E2E Quality Report

## Decision
- Run integrity decision: clean | defective | blocked-infra | blocked-provider | blocked-harness
- Deliverable quality decision: counted-clean | not-counted | blocked-model-quality | blocked-product-defect
- Operator UI/UX decision: acceptable | acceptable-with-risks | not-acceptable | not-applicable
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
- Operator UI workflows inspected:
- Terminal flow visibility:
- Navigation and discoverability:
- State clarity:
- Readability/layout:
- Accessibility/keyboard/focus notes:
- Responsive behavior notes:
- Generated product UI applicability:
- Operator UI/UX evidence links:

## Evidence Reviewed
- Flow evidence:
- Stage audits:
- Logs/transcripts:
- Target repo diff:
- Target workspace evidence:
- Review/QA artifacts:
- Operator UI/API checkpoints, next-flow checkpoint, or manual screenshot/browser evidence:
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
`Operator UI/UX decision` is a human-authored sub-decision about the AIDD operator
UI only. It does not alter `verdict.md`, `grader.json`, or any runner execution
status.

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
Inspect `target-workspace-evidence.*` and, when needed, run or cite
`git status --short --untracked-files=all` plus
`git status --ignored --short --untracked-files=all`. Treat top-level
`workitems/...` duplicate stage artifacts as severe deliverable pollution and
normally `not-counted`; this is the top-level `workitems/...` duplicate case.
Treat `aidd.example.toml` as harness/operator config, not product diff. Treat
direct `.aidd/*.py`-style scratch files as artifact hygiene findings that must be
explained or cleaned before a clean deliverable decision.
If artifacts or implementation notes show that the prepared checkout disappeared,
was recloned, or that live harness directories such as `install-home/`, `source/`,
`build/`, or `target/` were deleted/recreated, classify the deliverable as
`not-counted`: harness workspace recovery is run integrity evidence, not product
implementation work.

Operator UI/UX review should inspect real AIDD operator workflows: terminal flow
visibility, stage list navigation, artifact inspection, log inspection,
questions/answers, repair evidence, and next-flow handoff. API probes alone are not
UX evidence. Cite screenshots or browser evidence manually when available, and
record visual hierarchy, density, labels, truncation for long paths/logs, keyboard
path, focus visibility, labels or landmarks where manually inspectable,
desktop/tablet/mobile responsive behavior or explicitly `not inspected`, and
empty/loading/error/blocking, interview, and repair states. Generated product UI is
outside this operator-UI review unless the manual report explicitly marks it
`not-applicable`.
