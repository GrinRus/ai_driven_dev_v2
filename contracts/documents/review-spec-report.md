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
    `low`, `info`, or `none`), evidence, and rationale.
  - `Evidence` must reference a concrete upstream artifact, research/source id, target file path,
    probe/check result, or other durable reviewed evidence.
  - `critical` and `high` issues must cite direct evidence, such as a backticked artifact/file
    path, source id, research finding id, milestone id, acceptance id, or command/check result.
  - If an issue contradicts upstream `research` or `plan` evidence, it must include
    `Reconciliation` that names the stronger evidence and explains why the contradiction is valid.
  - Unsupported phrases such as `source inspection shows` are invalid unless the same issue names
    the concrete source artifact or check result being inspected.
  - If no material issue exists, must use a no-defect item/subsection with `Severity: none` and
    evidence and rationale. Bare no-issue prose such as `No material issues identified.` is invalid.
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
