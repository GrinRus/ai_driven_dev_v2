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
4. Use roadmap-style reasoning: order milestones by dependency and risk, and justify major sequencing choices.
5. Ensure each major risk has mitigation intent plus at least one verification note.
6. Ensure scope boundaries, trade-offs, and acceptance signals are explicit enough for user approval review.
7. Write or update `stage-result.md` and `validator-report.md` in Markdown.
8. If required upstream context is missing or contradictory, raise a question instead of inventing assumptions.
9. Keep the output useful for downstream execution rather than merely well-formatted.

## Completion checklist

- milestone ordering is coherent and dependency-aware,
- risks are specific and linked to mitigation intent,
- verification notes map to milestones, risks, or both,
- scope boundaries and acceptance signals are explicit,
- stage status and validator summary are consistent.
