# Document Contract: `qa-report.md`

## Purpose

Summarize verification evidence, remaining risks, and release readiness.

## Required sections

- `Verification summary`
- `Release recommendation`
- `Evidence`
- `Known issues`
- `Readiness`

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- `Release recommendation` declares exactly one supported state:
  `proceed`, `proceed-with-conditions`, or `hold`,
- material evidence entries use stable `EV-N` ids and/or backticked artifact paths,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
