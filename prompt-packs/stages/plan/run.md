# Run prompt for `plan`

## Goal

Describe the intended solution, boundaries, risks, rollout, and verification approach.

## Inputs to read first

- `../idea/output/idea-brief.md`
- `../idea/output/stage-result.md`
- `../research/output/research-notes.md`
- `../research/output/stage-result.md`
- `../research/output/validator-report.md`
- optional context when available: repository state, constraints, previous decisions
- stage contract: `contracts/stages/plan.md`

## Required outputs

- `plan.md`
- `stage-result.md`
- `validator-report.md`

## Instructions

1. Read all required upstream artifacts and the `plan` stage contract before writing outputs.
2. Build `plan.md` from grounded `idea` and `research` artifacts; do not bypass unresolved upstream failures.
3. Write `plan.md` with explicit `Milestones`, `Risks`, `Dependencies`, `Verification approach`, and `Verification notes`.
4. Ensure milestone order, risk coverage, and verification notes are consistent with the proposed implementation strategy.
5. Ensure scope boundaries and trade-offs are explicit enough for user approval review.
6. Write or update `stage-result.md` and `validator-report.md` in Markdown.
7. If required upstream context is missing or contradictory, raise a question instead of inventing assumptions.
8. Keep the output useful for downstream execution rather than merely well-formatted.
