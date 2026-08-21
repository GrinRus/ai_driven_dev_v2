# Document Contract: `tasklist.md`

## Purpose

Break the plan into reviewable implementation tasks with sequencing and verification notes.

## Required sections

- `Task summary`
- `Ordered tasks`
- `Dependencies`
- `Verification notes`

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- task references use stable ids consistently, for example `T1`, `T2` or `TL-1`, `TL-2`,
- every entry in `Ordered tasks` is an H3 task card whose heading starts with its stable id
  and an imperative title,
- every task card contains exactly one non-empty `Outcome`, `Dominant deliverable`, and
  `In scope` field,
- a task that intentionally produces command/check evidence without a task-local repository diff
  declares `Execution mode: verification-only`; omitted mode means `repository-change`,
- `In scope` contains at least one backticked repository-relative file or directory prefix;
  absolute paths, `..` traversal, and glob syntax are invalid,
- when the work item has `context/allowed-write-scope.md`, every `In scope` prefix is equal to an
  allowed prefix or is its descendant on a path-component boundary,
- every task card contains at least one task-local acceptance criterion whose stable id
  matches `<task-id>-AC<n>`,
- acceptance criterion ids are unique across the document,
- `Dependencies` has one entry per task id, starts with `none` or known earlier task ids, and
  contains no self-reference, forward reference, or cycle; optional rationale after the
  machine-readable value is ignored for graph construction,
- `Verification notes` uses bullet items that reference every task id from `Ordered tasks`,
  including command-only or verification-only tasks,
- checks embedded only inside `Ordered tasks` do not replace the dedicated per-task
  `Verification notes` entries,
- every task cites at least one exact existing plan milestone id such as `M1` in its `Outcome`,
  optional `Context`, a nested acceptance criterion, or its dedicated `Verification notes` entry,
- every plan milestone is covered by at least one task; ad hoc `Milestone` or `Plan milestone`
  fields are not part of the canonical task-card grammar and do not count,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.

Canonical task-card shape:

```md
### TL-1 — Add the bounded behavior

- Outcome: The requested behavior is observable at the supported boundary.
- Dominant deliverable: `src/example.py` contains the bounded implementation.
- In scope: `src/example.py` and focused regression coverage under `tests/`.
- Acceptance criteria:
  - TL-1-AC1: Milestone M1 supported input produces the expected output.
```

Optional task-card fields are `Context`, `Implementation constraints`, and `Out of scope`.
`Execution mode` is also optional for repository-change tasks and defaults to
`repository-change`; the only explicit alternate value is `verification-only`. A
verification-only card still requires bounded `In scope`, acceptance criteria, dependencies, and
dedicated verification notes. It is not an unsupported no-op: its dominant deliverable and
acceptance criteria must be executable evidence rather than repository edits.
Plan milestone ids may appear in `Outcome`, `Context`, acceptance-criterion text, or the task's
dedicated `Verification notes` entry. Do not add a separate `Milestone` or `Plan milestone` field.
Backticked task-scope paths use exact-file or directory-prefix semantics. They are enforced even
when no global allowed-write scope exists; when global scope exists, the effective boundary is the
intersection of task-local and global scope, and Tasklist validation rejects an empty or
out-of-bound intersection before implementation begins.

## Required semantics versus Markdown presentation

The executable meaning of a task card is independent of harmless Markdown presentation. The
following semantic obligations must remain explicit and machine-checkable:

- an H3 card with one stable task id and an imperative title;
- one `Outcome`, one `Dominant deliverable`, and bounded `In scope` paths;
- task-local acceptance criteria with stable ids;
- an explicit dependency entry in executable order; and
- one dedicated verification entry for every task.

presentation-only changes may include equivalent emphasis around a field label or task id
(for example `**Outcome**` or `` `TL-1` ``) and equivalent unordered-list punctuation (`-` or
`*`). They must not change words, paths, ids, ordering, or the presence of any required field.
These variants are normalization candidates for the tolerant parser; until that parser support is
installed, the canonical card shape above remains the safe authoring form.

Compact one-line task bullets, pipe tables, prose that requires inferred fields, missing H3 cards,
ambiguous ids, inferred dependencies, and omitted acceptance or verification evidence remain
invalid. A renderer or parser must fail closed rather than inventing executable task semantics from
layout, punctuation, or nearby prose.
