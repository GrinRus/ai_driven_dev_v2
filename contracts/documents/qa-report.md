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
- ready/proceed-style reports that cite test/type/lint/docs/build commands also cite
  ignored residue evidence from `git status --ignored --short --untracked-files=all`
  collected after all QA commands, or equivalent post-command workspace hygiene evidence,
- when `context/acceptance-criteria.md` exists, acceptance coverage is explicit: one top-level
  bullet per `AC-N`, each naming exactly one criterion id and citing same-bullet evidence,
- `Known issues` may include an empty marker such as `- Known issues: none.`;
  residual risk entries are separate items and must include severity plus mitigation or ownership,
- `QA verdict: ready` must not include residual risk entries; use `ready-with-risks`
  and `proceed-with-conditions` for real remaining risks, or move satisfied
  selected-boundary tradeoff notes out of residual-risk bullets,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
