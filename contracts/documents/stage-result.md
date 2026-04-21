# Document Contract: `stage-result.md`

## Purpose

Summarize a completed or halted stage attempt with durable status, output evidence,
validation state, blockers, and next actions.

## Required sections

- `Stage`
- `Attempt history`
- `Status`
- `Produced outputs`
- `Validation summary`
- `Blockers`
- `Next actions`
- `Terminal state notes`

## Field notes

- `Stage`
  - Must contain exactly one canonical stage id for the result.
  - Must match the stage that produced this file.
- `Attempt history`
  - Must list attempts in chronological order.
  - Each attempt must include at minimum: attempt number, trigger (`initial` or `repair`), and outcome.
  - Failed attempts must reference validator or runtime evidence when available.
- `Status`
  - Must contain one terminal stage status for this run (`succeeded`, `failed`, `blocked`, or `needs-input`).
  - Must not use ambiguous states such as `done-ish` or `in progress`.
- `Produced outputs`
  - Must list output documents produced in the final attempt as workspace-relative paths.
  - Must explicitly note missing required outputs when status is not `succeeded`.
- `Validation summary`
  - Must summarize whether validation passed, failed, or was not reached.
  - Must reference `validator-report.md` when validation produced findings.
- `Blockers`
  - Must list concrete blockers that prevented clean completion, or `- none`.
  - Blocking questions must be cross-referenced when present.
- `Next actions`
  - Must define actionable follow-up steps for operators or the next stage.
  - Must distinguish retry actions from downstream stage progression.
- `Terminal state notes`
  - Must explain why the stage ended in the declared terminal status.
  - Must include repair-budget outcome when repair logic was used.

## Authoring rules

- Use required heading names exactly; do not collapse `Attempt history` into `Status`.
- Keep document paths and artifact references workspace-relative and wrapped in backticks.
- Keep attempt numbering monotonic and contiguous within the document.
- Do not claim success when required outputs or validation evidence are missing.
- Use explicit `- none` markers instead of leaving required sections empty.

## Validation cues

- the required heading set is present exactly once,
- terminal status is from the allowed vocabulary,
- attempt history is ordered and references attempt outcomes,
- produced outputs and validation state agree with each other,
- terminal state notes justify why the run stopped.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
