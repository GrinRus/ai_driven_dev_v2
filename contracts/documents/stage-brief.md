# Document Contract: `stage-brief.md`

## Purpose

Provide one runtime-facing Markdown brief that defines the current stage, target outcome,
document IO expectations, and constraints before execution starts.

## Required sections

The authored document must include these top-level headings exactly:

- `Stage`
- `Goal`
- `Inputs`
- `Outputs`
- `Constraints`
- `Open questions`

## Field notes

- `Stage`
  - Must contain exactly one canonical stage name from the active stage chain.
  - Must use the lowercase stage id (for example, `plan`).
- `Goal`
  - Must describe the stage outcome in 1-3 sentences.
  - Must stay scoped to the current stage and avoid downstream commitments.
- `Inputs`
  - Must list the expected input documents as workspace-relative paths.
  - Each item must be one document path per bullet.
- `Outputs`
  - Must list the required output documents as workspace-relative paths.
  - Must include `stage-result.md` when the stage contract requires it.
- `Constraints`
  - Must list hard requirements the runtime must respect for this run.
  - Must include format constraints when relevant (for example, Markdown-only output).
- `Open questions`
  - Must list unresolved questions that may block completion.
  - Must be explicit when there are no unresolved items (for example, `- none`).

## Authoring rules

- Use the required heading names exactly; do not rename or merge headings.
- Keep all document paths in backticks and workspace-relative form.
- Do not invent user answers or hidden assumptions; unresolved items belong in `Open questions`.
- Keep wording specific and actionable; avoid placeholder text such as `TBD`, `N/A`, or `...`.
- Do not embed JSON schemas or machine-only payloads in place of narrative Markdown content.

## Validation cues

- the required heading set is present exactly once,
- the stage name is canonical and stage-specific,
- input and output paths are explicit and workspace-relative,
- unresolved clarifications are surfaced in `Open questions`,
- the brief does not invent missing user answers.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
