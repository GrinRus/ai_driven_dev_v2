# Run prompt for `tasklist`

## Stage objective

Produce a `tasklist` package that is executable in dependency order, reviewable task by task,
and consistent with upstream `plan` and `review-spec` decisions.

The stage is complete only when each task has a single dominant deliverable, explicit dependency
notes, and a concrete verification signal.

## Inputs to read first

- required:
  - `../plan/output/plan.md`
  - `../plan/output/stage-result.md`
  - `../review-spec/output/review-spec-report.md`
  - `../review-spec/output/stage-result.md`
  - `../review-spec/output/validator-report.md`
- optional context when available:
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/previous-decisions.md`
- contract of record:
  - `contracts/stages/tasklist.md`

## Required outputs (always write)

- `tasklist.md`
- `stage-result.md`
- `validator-report.md`

## Decomposition discipline

1. Use stable task ids and imperative task titles.
2. Keep one dominant output artifact per task so each item can be implemented and reviewed in one pass.
3. Record explicit dependencies for every task (`none` or concrete task/upstream ids).
4. Keep task ordering executable in dependency order, not only grouped by topic.
5. Add at least one concrete verification note per task (test/check/scenario).
6. Do not mark stage `succeeded` when upstream `review-spec` readiness/sign-off has unresolved
   blocking conditions.

## Execution instructions

1. Read all required inputs and `contracts/stages/tasklist.md` before drafting outputs.
2. Build `tasklist.md` with sections required by contract (`Task summary`, `Ordered tasks`,
   `Dependencies`, `Verification notes`).
3. Ensure dependency references are resolvable and avoid hidden prerequisites.
4. Keep task scope bounded; split bundled work into separate ordered tasks.
5. Update `stage-result.md` and `validator-report.md` so readiness, blockers, and next actions are
   consistent with tasklist content.
6. If required inputs are missing or sequencing/ownership assumptions are unresolved, raise
   questions with stable ids and `[blocking]` / `[non-blocking]` markers instead of inventing
   decisions.

## Completion checklist

- tasklist decomposition is ordered and dependency-executable,
- each task has one dominant deliverable and explicit dependency note,
- verification notes are concrete and task-specific,
- unresolved blocking ambiguity is represented as explicit questions,
- `stage-result.md` and `validator-report.md` match tasklist readiness and blockers.
