# Run prompt for `idea`

## Goal

Turn the incoming request into a clearer problem statement, desired outcome, constraints, and open questions.

## Inputs to read first

- required: `context/intake.md`, `context/user-request.md`
- optional context when available: business context, constraints, repository state, previous decisions
- stage contract: `contracts/stages/idea.md`

## Required outputs

- `idea-brief.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed
- `repair-brief.md` only when validation fails and repair is required

## Instructions

1. Read all available inputs and the `idea` stage contract before writing outputs.
2. Write `idea-brief.md` with complete `Problem statement`, `Desired outcome`, `Constraints`, and `Open questions` sections.
3. Keep required sections non-placeholder and grounded in provided inputs; record explicit assumptions when unavoidable.
4. If ambiguity remains, write `questions.md` entries with stable ids and `[blocking]` / `[non-blocking]` markers instead of guessing.
5. Write `validator-report.md` with structural, semantic, and cross-document findings plus a terminal verdict (`pass` or `fail`).
6. Write `stage-result.md` so status and validation summary match validator and question outcomes.

## Completion checklist

- all required outputs exist and are Markdown,
- required `idea-brief.md` sections are complete and non-placeholder,
- unresolved `[blocking]` questions prevent `succeeded` status,
- `stage-result.md` is consistent with `validator-report.md` and produced artifacts.
