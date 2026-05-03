# Document Contract: `review-spec-report.md`

## Purpose

Record whether the plan is coherent and ready for task decomposition.

## Required sections

- `Readiness state`
- `Issue list`
- `Strengths`
- `Recommendation summary`
- `Required changes`
- `Decision`

## Field notes

- `Readiness state`
  - Must declare one explicit state: `ready`, `ready-with-conditions`, or `not-ready`.
  - Must align with the decision and issue severity.
- `Issue list`
  - Must enumerate concrete issues as top-level bullet items or `###` issue subsections.
  - Each issue item/subsection must include explicit severity (`critical`, `high`, `medium`,
    `low`, or `info`) and rationale.
  - If no material issue exists, may use an explicit no-issue marker such as `No material issues
    identified.` or a no-defect item with `Severity: none`.
  - Must prioritize issues that block safe task decomposition.
- `Recommendation summary`
  - Must summarize actionable review recommendations as prioritized Markdown list items in priority
    order; either ordered or unordered lists are valid.
  - Must map recommendations to listed issues when applicable.
- `Decision`
  - Must declare explicit sign-off status using one of: `approved`, `approved-with-conditions`, `rejected`.
  - Must align with `Readiness state` and issue severity.

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
