# Document Contract: `research-notes.md`

## Purpose

Capture relevant sources, findings, trade-offs, and unresolved items.

## Required sections

- `Scope`
- `Sources`
- `Findings`
- `Trade-offs`
- `Evidence trace`
- `Open questions`

## Field notes

- `Sources`
  - Each source entry must include a stable citation id (for example `[S1]`).
  - Each source entry must include enough locator detail to revisit the evidence (URL, file path, or document reference).
  - Time-sensitive sources should include an access date or freshness note.
- `Findings`
  - Findings that influence scope, feasibility, architecture, or risk must reference one or more source citation ids.
  - Findings without supporting evidence must be marked as assumptions, not facts.
- `Evidence trace`
  - Must map major findings or recommendations to supporting citation ids.
  - Must make missing evidence explicit when any finding has only partial support.
- `Open questions`
  - Should capture unresolved evidence uncertainty and stale-data follow-up needs when they affect progression risk.

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
