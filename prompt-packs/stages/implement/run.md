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
4. Write or update required output documents in Markdown.
5. If required inputs are missing or write-scope/task-selection constraints are unclear, raise a question instead of inventing assumptions.
6. Keep the output useful for the next stage rather than merely well-formatted.
