# Document Contract: `implementation-report.md`

## Purpose

Explain what changed, which files were touched, and what verification was run.

## Required sections

- `Summary`
- `Touched files`
- `Verification`
- `Risks`
- `Follow-up`

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- touched file entries include a backticked file path plus same-line change intent,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.

For a rich task attempt, `Touched files` describes only the current task-local repository diff:
files changed between that task attempt's repository baseline and final snapshot. Files changed by
an already successful prerequisite task are excluded unless the current task changes them again.
Prerequisite or cumulative workspace state may be explained in `Summary` or `Risks`, but it must
not be claimed as a current-task touch. Aggregate finalization owns the cumulative touched-file
evidence across successful tasks. A generic one-shot implementation report without a rich task
ledger continues to describe the observed deliverable workspace state.
