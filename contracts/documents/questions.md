# Document Contract: `questions.md`

## Purpose

Store user-facing clarification questions raised during a stage.

## Required sections

- `Questions`

## Field notes

- `Questions`
  - Must be a bullet list where each bullet is one atomic question.
  - Each question must include a marker: `[blocking]` or `[non-blocking]`.
  - Each question must include a stable question id token (for example, `Q1`, `Q2`).
  - Blocking questions must describe why progression cannot continue without an answer.
  - Use `- none` only when the stage has no clarification needs.

## Blocking-question markers

- `[blocking]` means the stage cannot progress to terminal success without an answer.
- `[non-blocking]` means the stage may continue with explicit assumptions.
- Marker text is case-sensitive and must appear immediately after the question id token.

## Authoring rules

- Keep question wording direct, answerable, and scoped to one decision.
- Do not merge multiple decisions into one question bullet.
- Do not fabricate answers inside this document; answers belong in `answers.md`.
- When assumptions are acceptable, still record the question with `[non-blocking]`.
- Preserve question ids across revisions to keep durable cross-references stable.

## Validation cues

- the required heading set is present exactly once,
- each listed question has a stable id and a valid blocking marker,
- marker usage is consistent with blocker semantics,
- `- none` appears only when no open questions exist.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
