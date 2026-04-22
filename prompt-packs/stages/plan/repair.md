# Repair prompt for `plan`

You are rerunning the `plan` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving milestone ordering
logic, dependency clarity, and review readiness.

## Read order (do not skip)

1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/plan.md`
4. `contracts/documents/plan.md`, `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. current outputs:
   - `plan.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

## Finding-to-fix mapping

For each finding:

1. identify the root cause in the source section (`Milestones`, `Risks`, `Dependencies`,
   `Verification approach`, `Verification notes`, scope boundaries);
2. patch the smallest section that resolves the issue code;
3. re-check sequencing consistency across milestones and dependency links;
4. re-check stage status and blockers in `stage-result.md` against validator verdict and unresolved
   `[blocking]` questions.

Use concrete repair actions:

- vague sequencing: rewrite milestone order so dependencies are explicit and executable;
- missing dependency logic: add explicit `depends on` / ordering constraints in `Dependencies`;
- weak risk handling: add concrete risk statement with mitigation intent;
- verification mismatch: map verification notes to specific milestones/risks, including highest-risk
  work;
- unclear approval readiness: clarify `Out of scope`, trade-offs, and acceptance signals;
- unresolved ambiguity: keep or add a blocking question instead of inventing assumptions.

## Repair rules

1. Preserve valid plan sections; do not rewrite unaffected content.
2. Keep milestone and question ids stable where possible.
3. Do not mark `succeeded` while validator verdict is `fail`.
4. Keep unresolved `[blocking]` questions explicit under blockers and next actions.
5. Keep `stage-result.md` attempt history and terminal status truthful for this repair attempt.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- milestone sequencing and dependency constraints are coherent and explicit,
- risk mitigation and verification expectations are linked for highest-risk work,
- `stage-result.md` and `validator-report.md` remain consistent on verdict and blocker state.
