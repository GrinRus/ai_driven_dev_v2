# Document Contract: `validator-report.md`

## Purpose

Describe structural, semantic, and cross-document validation findings.

The canonical report is written by AIDD after post-runtime validation. Any
model-authored `validator-report.md` content produced during runtime execution is treated
as draft evidence and may be replaced by the canonical AIDD validator report.

## Required sections

- `Summary`
- `Structural checks`
- `Semantic checks`
- `Cross-document checks`
- `Result`

## Field notes

- `Summary`
  - Must state total issue count and whether blocking issues exist.
  - Must summarize affected documents and dominant failure categories.
- `Structural checks`
  - Must list findings tied to file presence, headings, and basic shape checks.
  - Each finding must include issue code, severity, and source document path.
- `Semantic checks`
  - Must list findings tied to content quality, completeness, and unsupported claims.
  - Must explain why each semantic issue violates the contract intent.
- `Cross-document checks`
  - Must list consistency findings across linked artifacts (for example, questions vs answers).
  - Must include explicit upstream/downstream references for each finding.
- `Result`
  - Must declare one terminal validator verdict: `pass` or `fail`.
  - Must list whether repair is required for stage progression.

## Issue-code vocabulary

Use stable, uppercase codes with subsystem prefixes:

- `STRUCT-MISSING-DOCUMENT` for missing required files.
- `STRUCT-MISSING-HEADING` for missing required sections.
- `STRUCT-EMPTY-SECTION` for required sections with no meaningful content.
- `SEM-PLACEHOLDER-CONTENT` for unresolved placeholder text in required fields.
- `SEM-UNSUPPORTED-CLAIM` for assertions without evidence required by the contract.
- `CROSS-REFERENCE-MISMATCH` for broken or contradictory document references.
- `CROSS-BLOCKING-UNANSWERED` for unresolved blocking questions that prevent progression.
- `CROSS-REPAIR-BUDGET-EXHAUSTED` for terminal repair-budget exhaustion that stops progression.

## Severity rules

- `critical`
  - Must be used when stage progression is unsafe or impossible without repair.
  - Examples: missing required output document, unresolved blocking question.
- `high`
  - Must be used for major contract violations that likely invalidate stage output quality.
- `medium`
  - Must be used for non-blocking but material quality gaps that should be repaired.
- `low`
  - Must be used for minor quality issues that do not block progression on their own.

## Authoring rules

- Keep each finding as one atomic issue with one issue code and one severity.
- Include workspace-relative document paths in backticks for every finding.
- Do not omit severity for any listed issue.
- Do not report `pass` when any `critical` issue remains unresolved.
- Do not report `pass` when any canonical AIDD validator finding remains unresolved.
- Keep wording diagnostic and actionable; avoid generic statements such as `bad output`.

## Validation cues

- the required heading set is present exactly once,
- each finding includes issue code, severity, and source reference,
- issue codes conform to the documented vocabulary format,
- severity labels follow the defined rule set,
- the final result is consistent with listed severities.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
