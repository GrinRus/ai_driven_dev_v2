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
  - `context/acceptance-criteria.md`
  - `context/verification-output.md`
  - `context/verification-artifacts.md`
  - `context/constraints.md`
  - `context/previous-decisions.md`
- contract of record:
  - `contracts/stages/tasklist.md`

## Required outputs (always write)

- `tasklist.md`
- `stage-result.md`
- `validator-report.md`

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Decomposition discipline

1. Use stable task ids and imperative task titles. Use one id style consistently, such as
   `T1`, `T2`, ... or `TL-1`, `TL-2`, ....
2. Keep one dominant output artifact per task so each item can be implemented and reviewed in one pass.
3. Record explicit dependencies for every task (`none` or concrete task/upstream ids).
4. Keep task ordering executable in dependency order, not only grouped by topic.
5. Add at least one concrete verification note per task (test/check/scenario).
6. Do not mark stage `succeeded` when upstream `review-spec` readiness/sign-off has unresolved
   blocking conditions.
7. When `context/verification-output.md` names authored verification commands, copy those commands
   exactly and preserve those commands exactly when citing them in task verification notes.
   Preserve flags, path lists, environment variables, and coverage/cache-disabling options such as
   `--coverage.enabled=false`; do not rewrite them as `npx`, package-manager aliases, or broader
   suite commands.
8. Optional broad checks outside the authored verification boundary may be listed only as
   optional/non-blocking exploratory checks. Do not turn them into required task completion or final
   pass criteria unless the authored task or review-spec explicitly requires them.

## Execution instructions

1. Read all required inputs and `contracts/stages/tasklist.md` before drafting outputs.
2. Build `tasklist.md` with sections required by contract (`Task summary`, `Ordered tasks`,
   `Dependencies`, `Verification notes`).
3. Ensure dependency references are resolvable and avoid hidden prerequisites.
4. Keep task scope bounded; split bundled work into separate ordered tasks.
5. Use `context/verification-output.md` as the verification boundary when present; if you need to
   mention an authored command, quote it exactly rather than paraphrasing executable details.
6. Update `stage-result.md` and `validator-report.md` so readiness, blockers, and next actions are
   consistent with tasklist content.
7. If required inputs are missing or sequencing/ownership assumptions are unresolved, raise
   questions with stable ids and `[blocking]` / `[non-blocking]` markers instead of inventing
   decisions.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- tasklist decomposition is ordered and dependency-executable,
- each task has one dominant deliverable and explicit dependency note,
- verification notes are concrete and task-specific,
- authored verification commands from `context/verification-output.md` are preserved exactly, or
  referenced generically without changing command flags or broadening scope,
- optional broader checks are not promoted to required pass criteria outside the authored boundary,
- unresolved blocking ambiguity is represented as explicit questions,
- `stage-result.md` and `validator-report.md` match tasklist readiness and blockers.
