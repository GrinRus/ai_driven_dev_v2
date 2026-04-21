# Run prompt for `implement`

## Goal

Apply the selected task to the repository, explain the change, and record verification evidence.

## Inputs to read first

- `../tasklist/output/tasklist.md`
- `../tasklist/output/stage-result.md`
- `../tasklist/output/validator-report.md`
- `context/repository-state.md`
- `context/task-selection.md`
- `context/allowed-write-scope.md`
- optional context when available: constraints, previous decisions, runtime capabilities
- stage contract: `contracts/stages/implement.md`

## Required outputs

- `implementation-report.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed
- `repair-brief.md` only when validation fails and repair is required

## Instructions

1. Read all required upstream artifacts before writing outputs.
2. Confirm selected task id exists in `tasklist.md` before applying changes.
3. Treat `context/allowed-write-scope.md` as a hard constraint for touched files.
4. Write `implementation-report.md` with selected task id, explicit change summary, touched-files list, and verification notes.
5. Ensure each touched-files entry includes path plus short change intent and stays inside allowed write scope.
6. Include verification outcomes for the primary checks actually run; do not claim checks that were not executed.
7. Write or update `stage-result.md` and `validator-report.md` so readiness and verification outcomes are consistent.
8. If required inputs are missing or write-scope/task-selection constraints are unclear, raise a question instead of inventing assumptions.
9. Keep the output useful for the next stage rather than merely well-formatted.

## Completion checklist

- implementation report references the selected task id directly,
- change summary is specific and aligned with produced edits,
- touched-files list is explicit and within allowed write scope,
- verification notes name concrete checks and observed outcomes,
- stage result and validator report agree with implementation outcomes.
