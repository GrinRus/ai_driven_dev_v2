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
- when `context/acceptance-criteria.md` exists, acceptance coverage is explicit: one top-level
  bullet per `AC-N`, each naming exactly one criterion id and citing same-bullet evidence,
- `Known issues` may include an empty marker such as `- Known issues: none.`;
  residual risk entries are separate items and must include severity plus mitigation or ownership,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
