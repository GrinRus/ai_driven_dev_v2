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
  - `context/acceptance-criteria.md`
  - `context/verification-output.md`
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

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## Conditional outputs

- `questions.md` and `answers.md` when blocking clarification is required

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Implementation discipline

1. Selected task id from `context/task-selection.md` must be explicit in the implementation
   report. If upstream `tasklist.md` decomposes that selected task into local ids such as `T1` or
   `TL-1`, use those local ids to structure touched-file and verification evidence where practical.
2. `context/allowed-write-scope.md` is a hard boundary for touched files.
3. `context/acceptance-criteria.md` and `context/verification-output.md` define the
   authored live acceptance and verification baseline for the implementation.
4. Change summary must describe what changed, why it changed, and how it maps to the selected task id.
5. Touched-files list must include concrete path + short intent per entry and never claim unobserved edits.
6. Verification notes must list actual checks run (or explicitly not run) with observed outcomes.
7. No-op outcomes require explicit evidence-based justification plus next action; otherwise no-op is invalid.
8. Stage/validator status must match observed implementation and verification evidence.

## Execution instructions

1. Read all required inputs and `contracts/stages/implement.md` before drafting outputs.
2. Confirm selected task id, acceptance criteria, scope limits, verification commands, and
   repository baseline before editing outputs.
3. Produce `implementation-report.md` with selected task id, scoped change summary, touched-files list,
   verification notes, and residual risk/deferred notes when applicable.
4. Keep touched-files entries bounded to allowed scope and aligned with observable repository changes.
   Use top-level bullets for each file, with a backticked path plus short intent (`path` - intent,
   `path`: intent, or `path` -> intent). Put line-level details under that file entry.
5. Record verification using concrete commands/checks and outcomes; include observed results such as
   `-> pass`, `exit 0`, `exit code 0`, or the captured tool summary. Do not imply execution that did
   not happen.
   When `context/verification-output.md` lists authored or scenario verification commands, run those
   commands after the implementation or explicitly mark each skipped command as not-run with a reason.
6. If required inputs are missing or scope/task constraints conflict, raise a `[blocking]` question
   instead of inventing assumptions.
7. Update `validator-report.md` and `stage-result.md` so readiness, blockers, and next actions remain
   consistent with implementation evidence.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- selected task id is explicit and traced to implementation summary,
- edits stay within allowed write scope,
- touched-files list is concrete and evidence-backed,
- verification notes are factual and command-specific,
- no-op handling (if any) includes justification, evidence, and next action,
- `implementation-report.md`, `validator-report.md`, and `stage-result.md` are consistent.
