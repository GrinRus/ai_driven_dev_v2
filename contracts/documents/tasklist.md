# Document Contract: `tasklist.md`

## Purpose

Break the plan into reviewable implementation tasks with sequencing and verification notes.

## Required sections

- `Task summary`
- `Ordered tasks`
- `Dependencies`
- `Verification notes`

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- task references use stable ids consistently, for example `T1`, `T2` or `TL-1`, `TL-2`,
- `Verification notes` uses bullet items that reference every task id from `Ordered tasks`,
  including command-only or verification-only tasks,
- checks embedded only inside `Ordered tasks` do not replace the dedicated per-task
  `Verification notes` entries,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
