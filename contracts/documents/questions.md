# Document Contract: `questions.md`

## Purpose

Store user-facing clarification questions raised during a stage.

## Required sections

- `Questions`

## Field notes

- `Questions`
  - Must be a bullet list where each bullet is one atomic question.
  - Each question entry must be a top-level bullet; nested or indented bullets under a
    question entry are invalid because they are parsed as additional question entries.
  - Each question must include a marker: `[blocking]` or `[non-blocking]`.
  - Each question must include a stable question id token (for example, `Q1`, `Q2`).
  - Canonical question syntax is `- Q1 [blocking] question text` or
    `- Q1 [non-blocking] question text`.
  - Blocking questions must describe why progression cannot continue without an answer.
  - Use `- none` only when the stage has no clarification needs.

## Blocking-question markers

- `[blocking]` means the stage cannot progress to terminal success without an answer.
- `[non-blocking]` means the stage may continue with explicit assumptions.
- Marker text is case-sensitive and must appear immediately after the question id token.
- The marker must be followed by a space and question text, not punctuation. Forms such as
  `- Q1 [blocking]: question text` or `- Q1: [blocking] question text` are invalid.

## Authoring rules

- Keep question wording direct, answerable, and scoped to one decision.
- Do not merge multiple decisions into one question bullet.
- Do not fabricate answers inside this document; answers belong in `answers.md`.
- When assumptions are acceptable, still record the question with `[non-blocking]`.
- Preserve question ids across revisions to keep durable cross-references stable.
- Treat `questions.md` as a merged stage interview ledger. When a later runtime attempt
  asks a question with an existing id, update that question in place; when it asks a new
  id, append it; do not silently remove unresolved questions that were omitted from the
  later attempt output.
- Preserve every existing question that is still referenced by `answers.md`, including
  resolved questions. A later runtime attempt must not replace the ledger with `- none`
  when durable answers still refer to an earlier question id.
- To stop blocking on a question, either provide a matching `[resolved]` answer in
  `answers.md` or re-emit the same question id as `[non-blocking]` while recording the
  bounded assumption in the stage output artifact.
- Put alternatives, examples, or rationale in the question sentence itself, or in plain
  continuation prose that does not start with `-`.
- Only bullets inside the `Questions` section are interpreted as question entries;
  use noncanonical sections only for non-authoritative prose metadata.
- Do not use answer ids such as `A1` or `A2` in `questions.md`; durable interview
  cross-references always use `Q`-prefixed question ids.

## Runtime candidate and ledger semantics

`questions.md` is the AIDD-owned canonical ledger. A runtime attempt may provide a
question candidate as structured data or Markdown, but the candidate is not canonical
until the interview merge boundary accepts it. The merge boundary follows these rules:

- Match questions by the exact stable `QID`; never match or replace an entry because its
  prose looks similar.
- Replace a matching question in its existing position, and append a new `QID` after the
  existing ledger in candidate order. The ledger's order is otherwise stable.
- Preserve omitted questions, including unresolved questions and questions referenced by
  `answers.md`. A candidate containing `- none` means that the candidate raised no new
  questions; it is not permission to erase the durable ledger.
- Treat equivalent presentation as safe to normalize only when meaning is unchanged:
  `-`/`*` list markers, optional marker-adjacent punctuation, and indented continuation
  prose may normalize to the canonical bullet form. Rewording, merging decisions,
  inferring a missing policy marker, or converting a table into questions is not safe
  normalization.

The raw candidate remains attempt evidence even when it is rejected. A duplicate `QID`
within one candidate, contradictory entries for one `QID`, or any other semantically
ambiguous candidate is retained with an explicit `operator-attention` disposition. Such
a candidate must not mutate the canonical ledger, overwrite an operator answer, or
consume repair budget. The operator must confirm, edit, or reject the candidate before a
later attempt can use it.

## Validation cues

- the required heading set is present exactly once,
- each listed question has a stable id and a valid blocking marker,
- marker usage is consistent with blocker semantics,
- `- none` appears only when no open questions exist.
- A later attempt that omits an earlier question must not cause a matching answer to become
  orphaned; cross-document validation must continue to resolve the same question id.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
