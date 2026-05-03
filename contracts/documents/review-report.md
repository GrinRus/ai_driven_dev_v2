# Document Contract: `review-report.md`

## Purpose

Capture implementation review findings and readiness judgment.

## Required sections

- `Verdict`
- `Findings`
- `Risks`
- `Required follow-up`

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- upstream references are present when the stage requires them.
- findings may be top-level bullets or `### RV-*` / `### REV-*` subsections,
- nested finding metadata bullets still belong to the enclosing finding and must include
  severity, disposition, rationale, and evidence.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
