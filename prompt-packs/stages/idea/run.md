# Run prompt for `idea`

## Stage objective

Convert the incoming request into an actionable and auditable `idea` package that downstream
`research` and `plan` stages can trust without guessing.

The stage is complete only when the problem framing is explicit, constraints are concrete, and
question state is visible.

## Inputs to read first

- required:
  - `context/intake.md`
  - `context/user-request.md`
- optional context when present:
  - `context/business-context.md`
  - `context/constraints.md`
  - `context/repository-state.md`
  - `context/previous-decisions.md`
- contract of record:
  - `contracts/stages/idea.md`

## Required outputs (always write)

- `idea-brief.md`
  - include complete sections:
    - `Problem statement`
    - `Desired outcome`
    - `Constraints`
    - `Open questions`
- `validator-report.md`
  - include structural, semantic, and cross-document findings;
  - end with terminal verdict (`pass` or `fail`).
- `stage-result.md`
  - include attempt summary, status, produced outputs, validation summary, blockers, and next actions.

## Conditional outputs

- `questions.md` when clarification is required.
- `answers.md` only when user answers are provided for recorded questions.

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Execution instructions

1. Read all required inputs and `contracts/stages/idea.md` before drafting outputs.
2. Write `idea-brief.md` using only supportable statements from inputs plus explicit assumptions.
3. Replace ambiguity with durable questions in `questions.md` using stable ids and
   `[blocking]` / `[non-blocking]` markers.
4. Treat unresolved `[blocking]` questions as stage blockers; do not mark the stage as `succeeded`.
5. Write `validator-report.md` so its findings and verdict match the actual artifact state.
6. Write `stage-result.md` so status and blockers are consistent with both `validator-report.md`
   and question/answer artifacts.

## Completion checklist

- required output documents exist and are Markdown,
- `idea-brief.md` required sections are complete and contain no placeholders,
- unresolved `[blocking]` questions prevent `succeeded`,
- `stage-result.md` and `validator-report.md` agree on verdict and blockers.
