# Document Contract: `review-report.md`

## Purpose

Capture implementation review findings and readiness judgment.

## Required sections

- `Verdict`
- `Findings`
- `Risks`
- `Required follow-up`
- `Task acceptance evidence` when the upstream tasklist uses rich task cards

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- upstream references are present when the stage requires them.
- findings may be top-level bullets or `### RV-*` / `### REV-*` subsections,
- if no review findings remain, the `Findings` section may instead contain an explicit
  no-findings declaration such as `- none` or `No review findings were identified.`,
- nested finding metadata bullets still belong to the enclosing finding and must include
  severity, disposition, rationale, and evidence.
- `Task acceptance evidence` contains exactly one top-level entry per task acceptance criterion:
  `- Task: \`TL-1\`; Acceptance: \`TL-1-AC1\`; Status: \`pass\`; Evidence: \`path\`; Notes: ...`,
- supported task-acceptance statuses are `pass`, `fail`, and `not-verified`; `fail` or
  `not-verified` cannot accompany an approved review verdict.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
