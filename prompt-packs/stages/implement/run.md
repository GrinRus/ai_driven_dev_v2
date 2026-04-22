# Run prompt for `implement`

## Stage objective

Execute the selected `tasklist` item inside the allowed write scope, produce a truthful
implementation summary, and capture verification evidence that is auditable.

The stage is complete only when reported edits, verification outcomes, and stage status are
consistent across `implementation-report.md`, `validator-report.md`, and `stage-result.md`.

## Inputs to read first

- required:
  - `../tasklist/output/tasklist.md`
  - `../tasklist/output/stage-result.md`
  - `../tasklist/output/validator-report.md`
  - `context/repository-state.md`
  - `context/task-selection.md`
  - `context/allowed-write-scope.md`
- optional context when available:
  - `context/constraints.md`
  - `context/previous-decisions.md`
  - `context/runtime-capabilities.md`
- contract of record:
  - `contracts/stages/implement.md`

## Required outputs (always write)

- `implementation-report.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when blocking clarification is required
- `repair-brief.md` only after validation failure

## Implementation discipline

1. Selected task id from `context/task-selection.md` must exist in upstream `tasklist.md`.
2. `context/allowed-write-scope.md` is a hard boundary for touched files.
3. Change summary must describe what changed, why it changed, and how it maps to selected task id.
4. Touched-files list must include concrete path + short intent per entry and never claim unobserved edits.
5. Verification notes must list actual checks run (or explicitly not run) with observed outcomes.
6. No-op outcomes require explicit evidence-based justification plus next action; otherwise no-op is invalid.
7. Stage/validator status must match observed implementation and verification evidence.

## Execution instructions

1. Read all required inputs and `contracts/stages/implement.md` before drafting outputs.
2. Confirm selected task id, scope limits, and repository baseline before editing outputs.
3. Produce `implementation-report.md` with selected task id, scoped change summary, touched-files list,
   verification notes, and residual risk/deferred notes when applicable.
4. Keep touched-files entries bounded to allowed scope and aligned with observable repository changes.
5. Record verification using concrete commands/checks and outcomes; do not imply execution that did not happen.
6. If required inputs are missing or scope/task constraints conflict, raise a `[blocking]` question
   instead of inventing assumptions.
7. Update `validator-report.md` and `stage-result.md` so readiness, blockers, and next actions remain
   consistent with implementation evidence.

## Completion checklist

- selected task id is explicit and traced to implementation summary,
- edits stay within allowed write scope,
- touched-files list is concrete and evidence-backed,
- verification notes are factual and command-specific,
- no-op handling (if any) includes justification, evidence, and next action,
- `implementation-report.md`, `validator-report.md`, and `stage-result.md` are consistent.
