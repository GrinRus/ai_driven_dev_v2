# Run prompt for `review-spec`

## Stage objective

Produce a review-ready `review-spec` package that makes go/no-go decomposition decisions explicit,
defensible, and consistent across report, validator output, and stage status.

The stage is complete only when issue severity is concrete, recommendations are actionable, and
sign-off state is coherent with required changes.

## Inputs to read first

- required:
  - `../plan/output/plan.md`
  - `../plan/output/stage-result.md`
  - `../plan/output/validator-report.md`
  - `context/intake.md`
  - `context/user-request.md`
  - `context/repository-state.md`
- optional context when available:
  - `context/constraints.md`
  - `context/previous-decisions.md`
- contract of record:
  - `contracts/stages/review-spec.md`

## Required outputs (always write)

- `review-spec-report.md`
- `stage-result.md`
- `validator-report.md`

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

`review-spec-report.md` must use these exact top-level section headings:

- `## Readiness state`
- `## Issue list`
- `## Strengths`
- `## Recommendation summary`
- `## Required changes`
- `## Decision`

Write sign-off status under `## Decision`. Do not rename that section to aliases such as
`## Decision/sign-off`, `## Sign-off`, or `## Recommendation decision`; those headings are
structurally invalid even when the prose is semantically correct.

Under `## Readiness state`, write exactly one top-level bullet containing exactly one allowed token:
`ready`, `ready-with-conditions`, or `not-ready`. Do not use prose substitutes such as
`conditionally ready`; when conditions remain but decomposition can proceed, write a bullet
containing only `ready-with-conditions`.

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

## Review discipline

1. Every issue must be concrete, scoped, severity-tagged, evidence-backed, and rationale-backed.
2. Use either top-level bullets or `### I<N> - ...` subsections for the `Issue list`; each issue
   item/subsection must include explicit `Severity`, `Evidence`, and `Rationale` text.
   For bullet issues, use this shape on the same top-level bullet:
   `- I1: Severity: medium. Evidence: plan.md M2. Rationale: because ...`.
   For subsection issues, put these exact metadata bullets immediately under each heading:
   `- Severity: medium`, `- Evidence: plan.md M2`, and `- Rationale: because ...`.
   If no material issue exists, write a no-defect item with `Severity: none` and
   `Evidence: plan.md / research-notes.md` and `Rationale: because ...`; do not write bare prose such as `No material issues identified.`,
   and do not invent advisory issues just to satisfy format.
   `critical` and `high` issues must cite direct evidence: an upstream artifact path, research
   source id, research finding id, target file path, milestone id, acceptance id, or command/check
   result. Do not write unsupported claims such as `source inspection shows` unless the same issue
   names the concrete inspected artifact or check result.
   If an issue contradicts upstream `research-notes.md` or `plan.md`, include `Reconciliation:`
   naming the stronger direct evidence and explaining why the contradiction is valid.
3. Recommendation summary must use prioritized Markdown list items (ordered or unordered) and map
   remediation steps to identified issues where applicable.
4. Recommendations must be prioritized and explicit enough for downstream execution.
5. Sign-off decision must be explicit (`approved`, `approved-with-conditions`, or `rejected`) and
   consistent with readiness state and required changes.
   Use this exact mapping: `ready` -> `approved`, `ready-with-conditions` ->
   `approved-with-conditions`, and `not-ready` -> `rejected`.
6. Review readiness against the operator request, repository state, plan coherence, risk coverage,
   dependency clarity, acceptance and verification coverage, and readiness for task decomposition.
7. Blocking uncertainty must be turned into questions instead of implied assumptions.

## Execution instructions

1. Read required plan artifacts, intake/user request/repository context, optional context, and
   `contracts/stages/review-spec.md` before drafting outputs.
2. If required plan artifacts are missing or inconsistent, do not mark stage as `succeeded`.
3. Draft `review-spec-report.md` with the exact required headings: `Readiness state`,
   `Issue list`, `Strengths`, `Recommendation summary`, `Required changes`, and `Decision`.
4. Keep issue wording tied to observable plan gaps or risks, not generic quality statements.
   Do not expand implementation scope or convert speculative risk into a high-severity defect
   without direct durable evidence. If evidence is unclear, ask a question or record a low/info
   observation instead of inventing a blocker.
5. Map recommended actions to issue ids/severity where possible so remediation order is clear.
6. If contradictory constraints, missing decision authority, or missing acceptance policy block
   sign-off, raise a `[blocking]` question instead of forcing approval status.
7. Update `validator-report.md` and `stage-result.md` so verdict, blockers, and next actions remain
   consistent with report conclusions.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- issue list is concrete, severity-tagged, evidence-backed, and rationale-backed in either bullet or `### I<N>`
  subsection form; every subsection issue has immediate `Severity:`, `Evidence:`, and `Rationale:` bullets,
- recommendations are prioritized Markdown list items and mapped to identified issues,
- readiness state, required changes, and sign-off decision are coherent,
- unresolved blocking ambiguity is captured as explicit questions,
- stage status and validator verdict agree with report outcome.
