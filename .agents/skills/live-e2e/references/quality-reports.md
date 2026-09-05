# Manual Live Quality Reports

Read this reference when a product-evaluation run requests a stage quality audit or
when writing its final quality reports. Use the exact required path from `flow-state.json`;
retain earlier stage-run audits when remediation repeats a stage.

## Stage audit template

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

After any terminal product-evaluation run, the launching SWE agent must write
`flow-quality-report.md`, `code-quality-report.md`, and `quality-report.md` in the
eval bundle before deciding counted-clean product quality. The runner does not create,
parse, validate, or score these files. Use this final report outline:

Terminal product-evaluation bundles may include
`product-evaluation-bundle-summary.json` and
`product-evaluation-bundle-summary.md`. The summary is navigation evidence, not
runner-owned quality scoring. Use it to locate stage-quality audit decisions,
remediation source ids, repair counts, tracked/untracked product files, known
harness files, final report presence, and terminal flow-state/verdict consistency,
then read the primary evidence before making a decision. It does not change
`verdict.md`, `grader.json`, final manual reports, or any execution status, and it
does not compute `counted-clean`. Manual `quality-report.md` remains the only final counted-clean decision.

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
- Review/QA artifacts:
- Operator UI/API checkpoints, next-flow checkpoint, or manual screenshot/browser evidence:
- Extra manual checks run by SWE agent:

## Notes
- Follow-ups:
- Residual risks:
```

Keep `Run Integrity` separate from artifact, code, test, and UI/UX quality.
API probes in `frontend-checkpoints.*` are raw surface evidence, not a UI/UX audit.
Observed running stages add a `running-stage` checkpoint phase for the disabled
`wait-for-stage` next action, active running-stage visibility, and runtime-log affordance,
including the honest pending-log state before `runtime.log` exists; completed stages keep
the `post-stage` phase for stage API and artifact reachability.
`frontend-checkpoints.md` includes a manual visual review checklist for visible next
action, active stage, desktop/mobile topbar readability, failure-appropriate recovery
primary action, reachable logs/artifacts/questions/answers, next-flow handoff visibility,
and long-path/log/action-copy overflow.
Screenshots and browser notes are optional manual evidence, not runner-generated artifacts.
When the operator passes `--manual-frontend-evidence <path>`, the runner copies that
operator-supplied file or directory into `manual-frontend-evidence/` and references it
from `frontend-checkpoints.*` as non-gating evidence for the manual `quality-report.md`.
The `Operator UI/UX decision` is a manual AIDD operator-UI sub-decision only; it
does not change `verdict.md`, `grader.json`, or any execution status. Inspect
terminal flow visibility, stage list navigation, artifact/log views, questions and
answers, repair evidence, next-flow handoff, state clarity, readability, keyboard
path, focus visibility, responsive behavior, and any manually captured screenshots
or browser notes. Treat the checklist as a prompt, not as proof; record actual
browser evidence or explicitly mark surfaces `not inspected`. Mark generated
product UI as `not-applicable` unless you explicitly performed a separate
product-UI review.

## Next-flow terminal checkpoint

After terminal `qa`, inspect the completed-run handoff before writing the final
operator decision:

1. Open the loopback UI or recorded UI/API checkpoint evidence.
2. Confirm **Flow Complete** is visible for the terminal run.
3. Record final QA status, blockers, final artifacts, approval counts, repair counts,
   answered-question counts, and recommended next-flow actions.
4. Record the operator next-flow decision as `no-follow-up`, `follow-up-draft`,
   `clone-draft`, `eval-batch`, `archive`, or `blocked`.
5. If a draft/eval/archive decision is recorded, preserve source-run references and
   selected source artifact links as evidence.

Do not launch a second public-repository flow by default. Child-flow proof is a
separate manual-only option when the evaluator explicitly supports it; it must stay
outside CI/CD and release automation and must write separate lineage evidence instead
of mutating the completed source run.

The evaluator option `--enable-next-flow-follow-up-proof` is off by default. Use it
only for a deliberate manual maintained-scenario proof after terminal passing `qa`.
When enabled, the evaluator creates a follow-up draft from the terminal QA report and
writes `next-flow-lineage.json`; it still must not launch a child public-repository
flow.
