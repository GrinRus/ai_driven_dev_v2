# Document Contract: `stage-result.md`

## Purpose

Summarize a completed or halted stage attempt with durable status, output evidence,
validation state, blockers, and next actions.

The runtime writes this Markdown summary as a draft stage output. AIDD treats it as the
workflow-facing summary only after post-runtime validation, and may normalize terminal status
or validation wording when the canonical validator report proves the draft inconsistent.

## Required sections

- `Stage`
- `Attempt history`
- `Status`
- `Produced outputs`
- `Validation summary`
- `Blockers`
- `Next actions`
- `Terminal state notes`

## Required skeleton

```md
# Stage Result

## Stage

- Stage: `<canonical-stage-id>`

## Attempt history

- Attempt 1 (`initial`): <outcome and evidence>

## Status

- Status: `<succeeded|failed|blocked|needs-input>`

## Produced outputs

- `<AIDD-workspace-relative-path, for example workitems/<id>/stages/<stage>/output/<document.md>>`

## Validation summary

- Validator verdict: `<pass|fail|not-run>`
- Validator report: `workitems/<id>/stages/<stage>/validator-report.md`
  (repository-root path `.aidd/workitems/<id>/stages/<stage>/validator-report.md`)

## Blockers

- none

## Next actions

- <operator or downstream action>

## Terminal state notes

- <why the stage ended in the declared status>
```

## Field notes

- `Stage`
  - Must contain exactly one canonical stage id for the result.
  - Must match the stage that produced this file.
- `Attempt history`
  - Must list attempts in chronological order.
  - Each attempt must include at minimum: attempt number, trigger (`initial` or `repair`), and outcome.
  - Failed attempts must reference validator or runtime evidence when available.
  - Repair attempts must reference `repair-brief.md` by workspace-relative path when it exists.
- `Status`
  - Must contain one terminal stage status for this run (`succeeded`, `failed`, `blocked`, or `needs-input`).
  - Must not use ambiguous states such as `done-ish` or `in progress`.
- `Produced outputs`
  - Must list output documents produced in the final attempt as AIDD workspace-relative paths.
  - Must explicitly note missing required outputs when status is not `succeeded`.
  - When AIDD rewrites `stage-result.md` to preserve repair history after a validation pass,
    it must preserve any existing declared primary output documents in this section before
    listing common outputs such as `stage-result.md`, `validator-report.md`, or
    `repair-brief.md`.
- `Validation summary`
  - Must summarize whether validation passed, failed, or was not reached.
  - Must reference `validator-report.md` when validation produced findings.
- `Blockers`
  - Must list concrete blockers that prevented clean completion, or `- none`.
  - Blocking questions must be cross-referenced when present.
- `Next actions`
  - Must define actionable follow-up steps for operators or the next stage.
  - Must distinguish retry actions from downstream stage progression.
  - Downstream stage progression must follow canonical stage order
    (`idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`).
    For example, a successful `implement` result must point operators to `review`, not
    directly to `qa`; `qa` is only an appropriate downstream action after `review`
    has completed successfully.
- `Terminal state notes`
  - Must explain why the stage ended in the declared terminal status.
  - Must include repair-budget outcome when repair logic was used.
  - If AIDD normalizes stale runtime status/verdict text after canonical validation
    passes, terminal notes must not retain runtime-authored claims that the stage
    ended as `failed`, `blocked`, or `needs-input`.
  - If `repair-brief.md` declares `repair-budget-final-attempt`, status must reflect the actual validation outcome of that attempt, not fail solely because no later rerun is available.
  - If AIDD records `repair-budget-exhausted` after a failed final attempt, status must be `failed`.
- `Project-set evidence` (conditional)
  - Required only when the work item has `workitems/<id>/context/project-set.md`.
  - Must cite that project-set context path.
  - Must cite every declared project id and repository-relative root from the context document.
  - Must state how the stage evidence preserves per-project ownership, or explicitly mark a
    project as unaffected for this stage.

## Authoring rules

- Use required heading names exactly; do not collapse `Attempt history` into `Status`.
- Keep document paths and artifact references workspace-relative and wrapped in backticks.
- Treat `workitems/...` as relative to the configured `.aidd/` workspace root.
  From the repository root, canonical stage artifacts live under `.aidd/workitems/...`;
  do not create top-level `workitems/...`.
- When `repair-brief.md` exists, include a backticked workspace-relative reference to it in
  `Attempt history`, `Validation summary`, or `Terminal state notes`.
- When project-set context exists, include a `Project-set evidence` section before
  `Terminal state notes` and keep project ids and roots backticked exactly as declared in
  `project-set.md`.
- Keep attempt numbering monotonic and contiguous within the document.
- Do not claim success when required outputs or validation evidence are missing.
- Do not claim `Validator verdict: pass` when the canonical AIDD validator report lists
  findings.
- Do not skip canonical downstream stages in `Next actions`. The next-action copy is
  operator guidance, so it must name the immediate retry, repair, question-answering,
  or next-stage step rather than a later desired terminal state.
- If canonical AIDD validation passes, runtime exit succeeded, and no unresolved blocking
  questions remain, AIDD may normalize a stale draft `Status: failed|blocked` or
  `Validator verdict: fail` to `succeeded` / `pass` before publication and record that
  normalization in `Terminal state notes`. It must remove or replace stale
  terminal-status notes that contradict the normalized status, while preserving
  product-quality decisions in the primary stage report such as review rejection or QA
  readiness.
- Use explicit `- none` markers instead of leaving required sections empty.

## Validation cues

- the required heading set is present exactly once,
- terminal status is from the allowed vocabulary,
- attempt history is ordered and references attempt outcomes,
- produced outputs and validation state agree with each other,
- terminal state notes justify why the run stopped.
- when project-set context exists, `stage-result.md` has `Project-set evidence` that references
  every declared project id and root.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
