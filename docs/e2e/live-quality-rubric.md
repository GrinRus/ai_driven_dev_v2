# Live E2E Manual Quality Report Guide

Live E2E has two separate decisions:

- the runner's execution verdict in `verdict.md`, `grader.json`, `summary.md`, and
  `harness-metadata.json` for terminal execution states `pass`, `fail`, `blocked`, and
  `infra-fail`;
- the launching SWE agent's manual quality decision in
  `.aidd/reports/evals/<run_id>/quality-report.md`.

The runner does not create, parse, validate, or score `quality-report.md`. It also
does not compute counted-clean status. A missing manual quality report must not
change a passing execution verdict.

For `product-evaluation` scenarios, the launching SWE agent must also review every
completed stage run before the runner may continue. The runner stops with
`awaiting-quality-review` after a successful stage run and names the exact required
`stage-quality-audits/<stage-run-id>.md` file. Resume with the same `--run-id` is
allowed only after that file exists. Repeated development loops such as
`implement -> review -> implement -> review -> qa` therefore create multiple stage-run
audits without overwriting earlier evidence.

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
- `stage-audits/<stage-run-id>.json`
- `stage-audits/<stage-run-id>.md`
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
- `manual-quality-stop.json` and `manual-quality-stop.md` only when a manual stage
  audit chooses `stop-not-counted`

The runner no longer emits `quality-transcript.json`, `acceptance-coverage.*`,
`ui-ux-checkpoints.*`, `operator-quality-analysis.md`, or
`operator-quality-analysis-validation.json`.

`frontend-checkpoints.*` are raw run-integrity evidence for the public operator
surfaces, including HTTP/API probes and operator-surface semantic checks for run,
stage, next-action, log, and artifact signals.
They are not a UI/UX audit, not screenshot evidence, and not a quality gate.
`frontend-checkpoints.md` includes a manual visual review checklist for the launching
agent: visible next action and active stage, readable desktop/mobile topbar labels,
failure-appropriate recovery primary action, reachable logs/artifacts/questions/answers,
and no horizontal overflow for long paths, log labels, or action copy.
Screenshots and browser notes are optional manual evidence, not runner-generated artifacts.

The `stage-audits/<implement-stage-run-id>.*` implement audit separates tracked changed files, new untracked product
files, known harness/config untracked files, and setup-baseline untracked files. New
untracked product files are non-gating execution evidence, but the manual code review
must inspect them before any counted-clean decision. This is especially important for
JavaScript/TypeScript packages where a new source helper may be public when
`package.json` `exports` uses wildcard subpaths such as `./utils/*`.
When `stage-audits/<implement-stage-run-id>.*` records `product_untracked_files`, the manual
`code-quality-report.md` and `quality-report.md` must name those files and state how
they were reviewed before recording `counted-clean`.

`target-workspace-evidence.*` records the target repository snapshot after setup and
after the terminal/stop state. It classifies tracked diff, setup-baseline untracked
files, known harness config such as `aidd.example.toml`, new untracked files, top-level
`workitems/...` pollution, unexpected `.aidd/` scratch files, and new ignored local
artifacts such as `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pdm-build/`, `coverage/`,
build, dist, or dependency-cache files. New ignored files under an ignored root that already
existed at setup, for example `.venv/.../__pycache__`, are recorded as `setup-baseline ignored churn`
rather than pollution findings. These findings are non-gating execution
evidence for manual review; they do not alter `verdict.md` or `grader.json`.

When manifest `verify.commands` pass but create local ignored byproducts after QA
has finished, the runner may remove only newly-created known verification residue
such as `.pytest_cache/`, `.ruff_cache/`, `coverage/`, `__pycache__/`, `.coverage*`, build, or dist
before final `target-workspace-evidence.*` is captured. That cleanup is recorded in
`verify-transcript.json.workspace_cleanup` and the `verify` step details. It is
runner-owned execution hygiene, not a deliverable quality gate.

Live manifests must not use `uv run aidd ...` for AIDD self-checks such as
`stage questions` or `stage run` inside the target repository. The installed live
runner already puts the built `aidd` artifact on `PATH`; using `uv run aidd ...`
can create target-repository lockfiles after QA and make final workspace evidence
not counted. Use `aidd stage questions ...` for AIDD self-checks, while keeping
target-project test commands on the package manager that belongs to that repository.

## Manual Report

For each product-evaluation stage, write this manual audit before resume:

```markdown
# Stage Quality Audit: <stage-run-id>

## Decision
- Stage run id: <stage-run-id>
- Stage: idea | research | plan | review-spec | tasklist | implement | review | qa
- Iteration: 1
- Stage quality: strong | acceptable | weak | failed
- Flow decision: continue | continue-with-risk | request-remediation | stop-not-counted | operator-intervention
- Reason:

## Remediation Request
- Source stage: review | qa
- Source ids: RV-1, EV-1
- Operator note:

## Checks
- Product alignment:
- Evidence quality:
- Repository understanding:
- Missing questions or assumptions:
- Cross-stage consistency:
- Risk handling:
- Specific defects:

## Evidence Reviewed
- Stage artifacts:
- Runtime logs:
- Runner stage audit:
- Previous stage-run evidence:
- Target repo evidence:
- Stale downstream state:

## Notes For Final Report
- AIDD quality signal:
- Residual risks:
```

Use `request-remediation` only for `review` and `qa` stage runs. The remediation
request section is required for that decision and must name the source stage, source
finding ids, and operator note. On resume, the runner uses the existing operator
remediation surface to create a durable remediation request, run a new `implement`,
mark downstream `review` and `qa` stale, and then rerun each stale downstream stage
one at a time with another quality checkpoint after each stage run. Use
`operator-intervention` only when a human must intervene manually; it does not start
the remediation loop.

If `Flow decision` is `stop-not-counted`, the next resume ends the run as
`manual-quality-stop`. This is not an execution failure, provider failure, infra failure,
or unresolved-question `blocked` state. The runner writes `manual-quality-stop.json`,
`manual-quality-stop.md`, `runtime.log`, `flow-report.md`, and
`target-workspace-evidence.*` for the stop point, but does not emit `verdict.md` or
`grader.json` because no execution verdict was assigned.

After the terminal run, the launching SWE agent may write:

- `.aidd/reports/evals/<run_id>/flow-quality-report.md`
- `.aidd/reports/evals/<run_id>/code-quality-report.md`
- `.aidd/reports/evals/<run_id>/quality-report.md`

Terminal `product-evaluation` bundles may also include generated
`product-evaluation-bundle-summary.json` and
`product-evaluation-bundle-summary.md`. The summary is navigation evidence, not
runner-owned quality scoring: use it to find stage-quality audit decisions,
remediation source ids, repair counts, tracked/untracked product files, known
harness files, final report presence, and terminal flow-state/verdict consistency.
It does not change `verdict.md`, `grader.json`, `flow-quality-report.md`,
`code-quality-report.md`, or `quality-report.md`, and it does not compute
`counted-clean`. Manual `quality-report.md` remains the only final counted-clean decision.

Use this exact structure:

```markdown
# Live E2E Quality Report

## Decision
- Run integrity decision: clean | defective | blocked-infra | blocked-provider | blocked-harness
- Operator UI/UX decision: acceptable | acceptable-with-risks | not-acceptable | not-applicable
- Final decision: counted-clean | not-counted | blocked-model-quality | blocked-product-defect

## Stage-by-stage Quality Summary
- <stage-run-id> / <stage> / iteration <n>:

## Iteration History
- Initial pass:
- Remediation requests:
- Stale downstream reruns:
- Fresh terminal QA state:

## Product Delivery Assessment
- Product request fit:
- Acceptance criteria coverage:
- Requirement/interview handling:
- Cross-stage consistency:
- Residual product risks:

## Code Quality Assessment
- Diff scope, including tracked and untracked files:
- Architecture/maintainability/API compatibility:
- Edge cases/security/performance risks:
- Code review defects:
- Code evidence links:

## Test And Verification Assessment
- Commands run:
- Baseline/before-after evidence:
- Regression relevance:
- Not-run or deferred checks:
- Verification gaps:

## Run Integrity
- Execution verdict:
- Stages reached:
- Evidence completeness:
- Runtime/provider/log issues:
- Repair/interview behavior:
- Timeout policy/evidence:
- Awaiting-quality-review checkpoints:
- Manual quality stop:

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
- Runner stage audits:
- Stage quality audits:
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
command timeout, the live no-progress timeout, and the absence of a global flow
timeout.

Provider no-progress is an execution integrity blocker, not product quality. When
`log-analysis.md` reports `provider-no-progress before completed stage artifact`,
the public stage command was alive but stdout/stderr and watched stage artifacts
stopped changing until `limits.no_progress_timeout_minutes` elapsed. Treat that as
`blocked-provider`/`blocked-infra` evidence in the final matrix table; do not call
it counted-clean, manual-quality-stop, unresolved-question `blocked`, or an AIDD
code-quality defect.

Malformed interview documents are a separate AIDD stage-output/document-contract
failure. If `validator-report.md`, `repair-history.md`, or `log-analysis.md` names
`INTERVIEW-MALFORMED-DOCUMENT` for `questions.md` or `answers.md`, classify the run
as model/stage-output or prompt/repair quality evidence. Do not classify it as
provider no-progress, `manual-quality-stop`, unresolved-question `blocked`, or a
manual product-quality verdict.

Unsupported `review-spec` claims are also AIDD stage-output/document-contract
failures. If `review-spec-report.md` invents high-severity issues without direct
evidence, contradicts upstream `research` or `plan` without `Reconciliation`, or leaves
`stage-result.md` inconsistent with canonical validation, classify the run as
model/stage-output or prompt/validator quality evidence. Do not classify it as
provider no-progress, `manual-quality-stop`, unresolved-question `blocked`, or a
manual product-quality verdict.

`Artifact Quality`, `Code Quality`, and `UI/UX Quality` evaluate the deliverable
produced by the full flow. These sections are manual review, not runner state.
`Operator UI/UX decision` is a human-authored sub-decision about the AIDD operator
UI only. It does not alter `verdict.md`, `grader.json`, or any runner execution
status.

The manual `counted-clean` phrase is only a human-authored deliverable-quality
decision inside `quality-report.md`. AIDD does not parse it. For product-evaluation,
`counted-clean` also requires all stage-run quality audits, `code-quality-report.md`, and
`quality-report.md`; the final report must include `Iteration History` and name every
remediation request, source id, operator note, stale downstream rerun, and the final
fresh QA state. When implement-stage evidence contains `product_untracked_files`,
the final reports must explicitly cover those files. A runner execution `pass` alone is
not counted-clean.

## Required Manual Review Coverage

Artifact review should cover the content depth of all stage outputs, cross-stage
traceability, validator report usefulness, and repair burden cause. Classify repair
burden as format issue, prompt/context issue, validator/contract issue, model
quality issue, or product ambiguity. Also inspect `stage-audits/<stage-run-id>.*` for
non-gating consistency findings where a runtime-authored `stage-result.md` validator
claim differs from the canonical validator/audit verdict.

Code review should cover the full target repository diff, including untracked files.
It should address acceptance criteria evidence, architectural fit, maintainability,
API compatibility, edge cases, security, performance, test relevance, and any
baseline or before/after proof.
If the implement-stage audit reports `product_untracked_files`, list each such file in
the final code review and explain whether it is deliverable code, harness/config residue,
or a blocker for counted-clean quality.
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
UX evidence. Use the manual visual checklist in `frontend-checkpoints.md` as a prompt,
not as proof by itself. Cite screenshots or browser evidence manually when available, and
record visual hierarchy, density, labels, truncation for long paths/logs, keyboard
path, focus visibility, labels or landmarks where manually inspectable,
desktop/tablet/mobile responsive behavior or explicitly `not inspected`, and
empty/loading/error/blocking, interview, and repair states. Generated product UI is
outside this operator-UI review unless the manual report explicitly marks it
`not-applicable`.
