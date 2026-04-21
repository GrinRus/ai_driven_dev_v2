# Document Contract: `answers.md`

## Purpose

Store durable answers to the questions raised during a stage.

## Required sections

- `Answers`

## Field notes

- `Answers`
  - Must be a bullet list where each bullet maps to one question id from `questions.md`.
  - Each answer must include a marker: `[resolved]`, `[partial]`, or `[deferred]`.
  - Each answer must include the question id token (for example, `Q1`, `Q2`) for durable linking.
  - `[resolved]` answers must contain actionable content, not placeholders.
  - `[partial]` and `[deferred]` answers must state what is still missing.
  - Use `- none` only when no answers were provided yet.

## Answer-resolution markers

- `[resolved]` means the question is fully answered for the current stage progression.
- `[partial]` means some answer exists but follow-up is required before safe completion.
- `[deferred]` means the answer is intentionally postponed to a later stage or decision point.
- Marker text is case-sensitive and must appear immediately after the question id token.

## Authoring rules

- Do not answer questions that are not present in `questions.md`.
- Preserve question ids exactly as written in `questions.md`; do not renumber in `answers.md`.
- Keep answers specific and auditable; avoid placeholders such as `TBD` or `decide later` without context.
- When an answer changes, append the updated answer in place and keep the latest marker truthful.
- Keep one decision per bullet to avoid mixing unrelated outcomes.

## Validation cues

- the required heading set is present exactly once,
- each answer bullet has a question id and a valid resolution marker,
- marker usage is consistent with progression state,
- `- none` appears only when there are no answer entries.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
