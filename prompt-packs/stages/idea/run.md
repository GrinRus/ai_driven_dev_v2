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
  - `context/selected-task.md`
  - `context/acceptance-criteria.md`
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
    - `Constraints` as Markdown bullet items, or exactly `- none`
    - `Open questions` as Markdown bullet items, or exactly `- none`
- `validator-report.md`
  - include structural, semantic, and cross-document findings;
  - end with terminal verdict (`pass` or `fail`).
- `stage-result.md`
  - include attempt summary, status, produced outputs, validation summary, blockers, and next actions.

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## Conditional outputs

- `questions.md` when clarification is required.
- `answers.md` only when user answers are provided for recorded questions.

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Execution instructions

1. Read all required inputs and `contracts/stages/idea.md` before drafting outputs.
2. Write `idea-brief.md` using only supportable statements from inputs plus explicit assumptions.
   In `Problem statement`, describe the user-visible problem and affected scope from the request
   and context. Do not assert source-code root causes, line-level symptoms, shared failure modes,
   or proof of current behavior unless those facts are already present in the inputs; leave source
   diagnosis to `research`.
   In `Desired outcome`, avoid unsupported absolute claims such as guaranteed compatibility,
   complete elimination of risk, or proof that all downstream behavior is preserved unless the
   provided inputs already contain that evidence. Phrase outcomes as target goals and explicitly
   tie them to the selected request, constraints, and acceptance context.
   In `Constraints` and `Open questions`, prose-only text is invalid; write one
   top-level bullet per item, and when there are no items write exactly `- none`.
3. Replace ambiguity with durable questions in `questions.md` using stable ids and
   `[blocking]` / `[non-blocking]` markers. Write one top-level bullet per question id;
   do not put indented or nested bullets under a question. Put alternatives or examples
   in the question sentence or non-bullet continuation prose.
   When `context/selected-task.md`, `context/acceptance-criteria.md`, or the incoming request
   explicitly says blocking answers, interview answers, or operator policy decisions are required
   before downstream planning or implementation, including before task decomposition, review, or
   release, those questions are `[blocking]`. Do not downgrade that obligation to `[non-blocking]`
   just because repository conventions could support a plausible default policy.
4. Treat unresolved `[blocking]` questions as stage blockers; do not mark the stage as `succeeded`.
5. Write `validator-report.md` so its findings and verdict match the actual artifact state.
6. Write `stage-result.md` so status and blockers are consistent with both `validator-report.md`
   and question/answer artifacts.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- required output documents exist and are Markdown,
- `idea-brief.md` required sections are complete and contain no placeholders,
- unresolved `[blocking]` questions prevent `succeeded`,
- `stage-result.md` and `validator-report.md` agree on verdict and blockers.
