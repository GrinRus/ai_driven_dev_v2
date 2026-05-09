# Run prompt for `review`

## Stage objective

Produce a defensible `review` package that classifies implementation findings by severity and
disposition, then makes an explicit approval decision (`approved`, `approved-with-conditions`,
or `rejected`).

The stage is complete only when every finding is evidence-backed, severity/disposition labels are
coherent, and approval status matches unresolved `must-fix` items.

## Inputs to read first

- required:
  - `../implement/output/implementation-report.md`
  - `../implement/output/stage-result.md`
  - `../implement/output/validator-report.md`
  - `context/diff-summary.md`
  - `context/acceptance-criteria.md`
- optional context when available:
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/review-baseline.md`
- contract of record:
  - `contracts/stages/review.md`

## Required outputs (always write)

- `review-report.md`
- `stage-result.md`
- `validator-report.md`

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Review discipline

1. Findings must have stable ids, explicit severity, explicit disposition, and rationale tied to
   implementation evidence or acceptance-criteria mismatch.
   Use either top-level bullet findings or `### RV-*` / `### REV-*` finding subsections; when using
   subsections, keep severity, disposition, rationale, and evidence as nested metadata under that
   finding.
   Every finding must include an explicit `Evidence:` metadata item or equivalent inline evidence
   text that cites `implementation-report.md`, a changed file path, or an acceptance-criteria id
   such as `AC-1`. A plausible rationale without this evidence reference is invalid.
2. Severity and disposition labels must stay consistent between detailed findings and summary
   sections.
3. `must-fix` findings block `approved` status until resolved.
4. Required changes must map to concrete finding ids when status is conditional or rejected.
5. Missing/contradictory baseline context must become explicit questions, not silent assumptions.

## Execution instructions

1. Read required `implement` artifacts, diff summary, acceptance criteria, and
   `contracts/stages/review.md` before drafting outputs.
2. Do not mark stage `succeeded` when `implement` status is unresolved or validator verdict is
   `fail`.
3. Draft `review-report.md` with sections for findings, approval decision, and required changes.
4. Keep every finding tied to observable evidence from `implementation-report.md` and/or explicit
   acceptance-criteria mismatch. For subsection findings, use this metadata shape:
   - `Severity: low|medium|high|critical|info|none`
   - `Disposition: must-fix|follow-up|accepted-risk|invalid`
   - `Evidence: implementation-report.md ...`, changed file path, or `AC-*`
   - `Rationale: ...`
5. Use allowed dispositions (`must-fix`, `follow-up`, `accepted-risk`, `invalid`) and keep wording
   unambiguous for downstream QA.
6. If contradictions in baseline prevent defensible decision, ask a `[blocking]` question instead
   of forcing approval.
7. Update `validator-report.md` and `stage-result.md` so verdict, blockers, and next actions match
   the final review decision.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- findings are uniquely identified with severity and disposition labels,
- each finding has explicit `Evidence:` metadata or inline evidence tied to implementation output
  or acceptance-criteria mismatch,
- approval status is explicit and consistent with unresolved `must-fix` findings,
- required changes map to concrete findings for non-approved outcomes,
- blocking ambiguity is surfaced via explicit questions,
- `review-report.md`, `validator-report.md`, and `stage-result.md` are outcome-consistent.
