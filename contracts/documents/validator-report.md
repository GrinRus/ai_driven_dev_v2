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

Optional non-verdict evidence may use an `Advisory observations` section between
`Cross-document checks` and `Result`.

## Protocol version

This contract defines validator-report protocol v1. AIDD writers must emit the canonical
field labels and finding codes below. During the v1 compatibility window, readers may also
accept only the aliases declared under `Legacy read aliases`. Removing those aliases requires
a new major validator-report protocol version.

## Required skeleton

```md
# Validator Report

## Summary

- Total issues: `<number>`
- Blocking issues: `<yes|no>`
- Affected documents: `<workspace-relative paths or none>`
- Dominant failure categories: `<ordered categories or none>`
- Finding occurrences: `<raw finding count; include only when duplicates were collapsed>`

## Structural checks

- none

## Semantic checks

- none

## Cross-document checks

- none

## Advisory observations

- none

## Result

- Verdict: `<pass|fail>`
- Repair required for progression: `<yes|no>`
```

## Field notes

- `Summary`
  - Must state total issue count and whether blocking issues exist.
  - Must summarize affected documents and dominant failure categories.
  - `Total issues` counts unique displayed findings after exact duplicate findings are
    collapsed. When duplicates were collapsed, include `Finding occurrences` with the raw
    finding count.
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

## Progression semantics

- A canonical finding in a report with `Verdict: fail` is required for stage
  progression, regardless of its severity. A report must not describe a
  fail-causing finding as optional or set `Repair required for progression: no`.
- `Blocking issues` is a progression summary: it is `yes` when any canonical
  finding remains and `no` only when the report has no findings. Severity does
  not decide whether a finding blocks progression.
- Advisory observations are non-verdict evidence. They must be recorded outside
  the canonical validator finding sections, under `Advisory observations`, and
  must not turn a failing report into a passing report or consume repair budget.
- A report containing only advisory observations has no canonical findings,
  declares `Verdict: pass`, and does not request repair. Advisory observations
  remain visible in the repair brief without becoming correction actions.

## Canonical issue-code vocabulary

Every canonical finding code has one protocol-owned report section. AIDD writers must not
publish codes outside this list.

### Structural checks

- `INTERVIEW-MALFORMED-DOCUMENT`
- `STRUCT-DUPLICATE-REQUIRED-SECTION`
- `STRUCT-EMPTY-REQUIRED-SECTION`
- `STRUCT-MISSING-REQUIRED-DOCUMENT`
- `STRUCT-MISSING-REQUIRED-SECTION`
- `STRUCT-OUTPUT-PROMOTED`
- `STRUCT-STALE-STAGE-RESULT-PLACEHOLDER`

### Semantic checks

- `SEM-INCOMPLETE-EXECUTION-SUMMARY`
- `SEM-INCOMPLETE-SECTION`
- `SEM-MISSING-DIFF-EVIDENCE`
- `SEM-MISSING-EVIDENCE-LINK`
- `SEM-MISSING-EVIDENCE-REF`
- `SEM-PLAN-SCOPE-MISMATCH`
- `SEM-PLACEHOLDER-CONTENT`
- `SEM-RISK-UNDERREPORT`
- `SEM-TASK-DIFF-MISMATCH`
- `SEM-TASK-SCOPE-MISMATCH`
- `SEM-UNSUPPORTED-CLAIM`
- `SEM-UNSUPPORTED-VERDICT`
- `SEM-UNVERIFIABLE-CHECK-CLAIM`

### Cross-document checks

- `CROSS-ANSWER-WITHOUT-QUESTION`
- `CROSS-BLOCKING-UNANSWERED`
- `CROSS-DUPLICATE-ANSWER-ID`
- `CROSS-DUPLICATE-QUESTION-ID`
- `CROSS-IMPLEMENTATION-FINALIZATION`
- `CROSS-PROJECT-SET-EVIDENCE-MISSING`
- `CROSS-QA-REVIEW-RISK`
- `CROSS-QA-UPSTREAM-EVIDENCE`
- `CROSS-QA-UPSTREAM-VERDICT`
- `CROSS-REPAIR-BRIEF-NOT-REFERENCED`
- `CROSS-REPAIR-BUDGET-EXHAUSTED`
- `CROSS-REPAIR-MENTION-WITHOUT-BRIEF`
- `CROSS-REVIEW-IMPLEMENT-EVIDENCE`
- `CROSS-REVIEW-IMPLEMENT-FINDING`
- `CROSS-REVIEW-IMPLEMENT-PATH`
- `CROSS-TASKLIST-PLAN-DEPENDENCY`
- `CROSS-TASKLIST-PLAN-MILESTONE`
- `CROSS-TASKLIST-PLAN-VERIFICATION`

## Legacy read aliases

Protocol v1 readers accept these historical forms, but writers must never emit them:

- field `Validator verdict` resolves to canonical field `Verdict`;
- field `Repair required` resolves to canonical field `Repair required for progression`;
- code `STRUCT-MISSING-DOCUMENT` resolves to `STRUCT-MISSING-REQUIRED-DOCUMENT`;
- code `STRUCT-MISSING-HEADING` resolves to `STRUCT-MISSING-REQUIRED-SECTION`;
- code `STRUCT-EMPTY-SECTION` resolves to `STRUCT-EMPTY-REQUIRED-SECTION`;
- code `CROSS-REFERENCE-MISMATCH` remains readable as a legacy cross-document code but
  has no canonical replacement because its historical meaning is ambiguous.

## Severity rules

- Severity describes impact and repair priority; it is not a progression
  disposition. Every canonical finding in a failing report remains required for
  progression.
- `critical`
  - Must be used for the highest-impact issues where stage output is unsafe or
    impossible without repair.
  - Examples: missing required output document, unresolved blocking question.
- `high`
  - Must be used for major contract violations that likely invalidate stage
    output quality.
- `medium`
  - Must be used for material quality gaps that require repair before
    progression, but have lower impact than critical/high findings.
- `low`
  - Must be used for minor quality issues that still violate a canonical
    contract and therefore remain required while the report verdict is `fail`.
- Advisory observations are not validator findings and must not be represented
  by lowering a finding's severity to `low`.

## Authoring rules

- Keep each finding as one atomic issue with one issue code and one severity.
- Render each finding as
  `- \`CODE\` (\`severity\`) in \`workspace-relative/path\`: actionable message`.
- Include workspace-relative document paths in backticks for every finding.
- Collapse exact duplicate findings with the same issue code, severity, location, and
  message into one bullet with an occurrence count instead of repeating identical bullets.
- Do not omit severity for any listed issue.
- Do not classify a canonical finding as optional based on its severity.
- Do not report `pass` when any `critical` issue remains unresolved.
- Do not report `pass` when any canonical AIDD validator finding remains unresolved.
- Do not report `Verdict: fail` with `Repair required for progression: no`.
- Keep wording diagnostic and actionable; avoid generic statements such as `bad output`.
- Advisory observations use the same evidence-rich finding syntax but are not
  included in `Total issues`, `Blocking issues`, or the terminal verdict.
- Semantic content findings should identify the concrete offending token or rule input and
  its source line whenever the validator can determine it, so a bounded repair can patch the
  named content without regenerating unrelated sections.

## Validation cues

- the required heading set is present exactly once,
- each finding includes issue code, severity, and source reference,
- issue codes conform to the documented vocabulary format,
- severity labels follow the defined rule set,
- the final result is consistent with listed severities.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
