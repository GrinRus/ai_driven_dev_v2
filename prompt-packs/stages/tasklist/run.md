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
  - `stage-brief.md` required output skeletons
  - `contracts/stages/tasklist.md` only when it is present in the current checkout

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

## Interview document syntax

- `questions.md` bullets must be exactly `- Q1 [blocking] text` or
  `- Q1 [non-blocking] text`.
- `answers.md` bullets must be exactly `- Q1 [resolved] text`,
  `- Q1 [partial] text`, or `- Q1 [deferred] text`.
- Do not put punctuation immediately after the marker: `- Q1 [resolved]: text` and
  `- Q1: [resolved] text` are invalid.
- Do not invent `A1`/`A2` answer ids; answer bullets always reuse question ids.
- If no operator answer is present, write `# Answers\n\n- none\n`; do not create
  `[resolved]` answers yourself.

## Installed package workspace discipline

- Repository-local `contracts/...` files may be absent in installed package runs. Do not spend the turn
  searching broadly for missing contracts or scanning all of `.aidd`; use `stage-brief.md` as the
  embedded contract skeleton and proceed.
- Limit pre-write inspection to the required inputs, the optional context files needed for task
  decomposition, and `stage-brief.md`. Avoid broad commands such as `rg --files .aidd` before the
  required outputs exist.
- After reading the required inputs, make the first file-changing action create or replace all
  required stage documents: `tasklist.md`, `stage-result.md`, `validator-report.md`, `questions.md`,
  and `answers.md`. Do not end the turn after analysis-only reads.

## Decomposition discipline

1. Use stable task ids and imperative task titles. Use one id style consistently, such as
   `T1`, `T2`, ... or `TL-1`, `TL-2`, ....
2. Keep one dominant output artifact per task so each item can be implemented and reviewed in one pass.
   Render each item as `### <task-id> — <imperative title>` followed by non-empty
   `Outcome`, `Dominant deliverable`, and `In scope` bullets. Add an `Acceptance criteria`
   bullet with one or more nested criteria using the exact `<task-id>-AC<n>` shape,
   for example `<task-id>-AC1` and `<task-id>-AC2`. Acceptance ids must be unique
   across the document.
   `In scope` must name at least one backticked repository-relative file or directory prefix.
   Do not use absolute paths, `..` traversal, or glob syntax. Explanatory prose does not replace
   concrete path prefixes.
3. Record explicit dependencies for every task (`none` or concrete task/upstream ids).
4. Map every task to at least one existing plan milestone by writing the exact `M<n>` id in the
   task's `Outcome`, optional `Context`, a nested acceptance criterion, or the task's dedicated
   `Verification notes` entry. Cover every plan milestone. Do not add `Milestone` or
   `Plan milestone`: those fields are outside the canonical rich-task grammar and are ignored.
5. Keep task ordering executable in dependency order, not only grouped by topic.
   Dependencies may reference only earlier task cards. Reject self-dependencies, unknown task ids,
   forward references, and dependency cycles rather than hiding them in prose or expecting AIDD to
   reorder the cards.
6. Add at least one concrete verification note per task (test/check/scenario). The dedicated
   `Verification notes` section must contain a bullet or list item for every task id declared in
   `Ordered tasks`, including command-only or verification-only tasks. Do not rely on checks
   embedded only inside `Ordered tasks`; those checks must be repeated or summarized under the
   matching task id in `Verification notes`.
7. Do not mark stage `succeeded` when upstream `review-spec` readiness/sign-off has unresolved
   blocking conditions.
8. When `context/verification-output.md` names authored verification commands, copy those commands
   exactly and preserve those commands exactly when citing them in task verification notes.
   Preserve flags, path lists, environment variables, and coverage/cache-disabling options such as
   `--coverage.enabled=false`; do not rewrite them as `npx`, package-manager aliases, or broader
   suite commands.
9. Optional broad checks outside the authored verification boundary may be listed only as
   optional/non-blocking exploratory checks. Do not turn them into required task completion or final
   pass criteria unless the authored task or review-spec explicitly requires them.
10. In JavaScript or TypeScript packages, do not plan a concrete helper/module path as private or
   internal-only until you inspect `package.json` `exports`, wildcard subpath exports such as
   `./utils/*`, generated declaration outputs, and existing public import conventions. If the
   proposed path can be imported through the package boundary, either choose a non-exported
   location or record the public API risk and required compatibility evidence in the tasklist.

## Execution instructions

1. Read all required inputs and `stage-brief.md` before drafting outputs. Read
   `contracts/stages/tasklist.md` only if it is already present; absence of repository-local
   contracts is not a blocker because `stage-brief.md` carries the required skeletons.
2. Build `tasklist.md` with sections required by contract (`Task summary`, `Ordered tasks`,
   `Dependencies`, `Verification notes`).
   In `Verification notes`, create one entry for each task id from `Ordered tasks`; command-only
   verification tasks still need their own entry even if their task title already names the
   command.
3. Ensure dependency references are resolvable and avoid hidden prerequisites.
4. Keep task scope bounded; split bundled work into separate ordered tasks.
   Compact bullet-only tasks are invalid; use the complete H3 task-card shape for every id.
5. Use `context/verification-output.md` as the verification boundary when present; if you need to
   mention an authored command, quote it exactly rather than paraphrasing executable details.
6. When naming JS/TS helper or module paths, include export-map/public-surface evidence in the
   task notes before calling the path private or internal-only.
7. Update `stage-result.md` and `validator-report.md` so readiness, blockers, and next actions are
   consistent with tasklist content.
   When tasklist and validation evidence support success, `stage-result.md` `Next actions` must
   name the exact immediate canonical downstream stage id: `implement`. Do not write only generic
   wording such as `implementation` or `implementation stage`.
8. If required inputs are missing or sequencing/ownership assumptions are unresolved, raise
   questions with stable ids and `[blocking]` / `[non-blocking]` markers instead of inventing
   decisions.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Replace the entire bootstrap placeholder when writing `stage-result.md`; do not leave
  `# Stage result` / `Stage not run yet.` above the real `# Stage Result` document.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- tasklist decomposition is ordered and dependency-executable,
- each task has one dominant deliverable and explicit dependency note,
- each task card has an outcome, in-scope boundary, and task-local acceptance criteria,
- every task cites an existing plan `M<n>` id in `Outcome`, `Context`, an acceptance criterion,
  or its dedicated `Verification notes` entry, and every plan milestone is covered,
- no task relies on an unsupported `Milestone` or `Plan milestone` field,
- every in-scope boundary contains safe backticked repository-relative path prefixes,
- verification notes are concrete, task-specific, and include every declared task id,
- command-only or verification-only task ids are present in the dedicated `Verification notes`
  section, not only in `Ordered tasks`,
- authored verification commands from `context/verification-output.md` are preserved exactly, or
  referenced generically without changing command flags or broadening scope,
- optional broader checks are not promoted to required pass criteria outside the authored boundary,
- JavaScript/TypeScript helper or module paths include export-map evidence before any
  private/internal-only claim,
- unresolved blocking ambiguity is represented as explicit questions,
- successful `stage-result.md` next-action copy names the exact immediate next stage id `implement`,
- `stage-result.md` and `validator-report.md` match tasklist readiness and blockers.
