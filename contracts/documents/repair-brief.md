# Document Contract: `repair-brief.md`

## Purpose

Describe what failed validation and what the repair attempt must correct.

`repair-brief.md` is AIDD-owned repair control evidence. Runtime adapters and model
providers may read it as input, but must not rewrite it. Model-authored repair summaries
belong in `stage-result.md` or a future `repair-notes.md`, not in this control artifact.

## Required sections

- `Failed checks`
- `Required corrections`
- `Relevant upstream docs`

## Field notes

- `Failed checks`
  - Must list failed validator issues from the latest attempt with issue code and severity.
  - Must include workspace-relative source document references for each failed check.
- `Required corrections`
  - Must define concrete corrections mapped to the listed failed checks.
  - Must separate mandatory fixes from optional quality improvements.
- `Relevant upstream docs`
  - Must list upstream artifacts required to perform the repair safely.
  - Must include `questions.md` or `answers.md` when clarification state affects the fix.

## Rerun-budget notes

- Must include current attempt index and remaining repair attempts.
- Must state whether another rerun is allowed after this repair attempt.
- Must declare `repair-budget-exhausted` when no attempts remain.
- `repair-budget-exhausted` means the repaired stage terminal status must be `failed`.
- Must not instruct indefinite retries.

## Fix-plan rules

- Each required correction must map to one or more failed check codes.
- Fix actions must be actionable and scoped to document-level edits.
- If a failed check cannot be repaired automatically, mark it as `needs-human-input` with reason.
- Do not add new scope beyond resolving listed failed checks unless explicitly required.

## Authoring rules

- Only AIDD core writes this document; runtime/model attempts treat it as read-only input.
- Keep remediation steps deterministic and stage-scoped.
- Use backticked workspace-relative paths for all document references.
- Keep one correction item per bullet to preserve auditability.
- Avoid generic instructions such as `improve quality` without concrete expected changes.
- Do not omit budget state; missing budget context invalidates repair control.

## Validation cues

- the required heading set is present exactly once,
- failed checks include code, severity, and source references,
- rerun-budget state is explicit and internally consistent,
- required corrections map back to failed checks,
- fix-plan items stay within repair scope.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
