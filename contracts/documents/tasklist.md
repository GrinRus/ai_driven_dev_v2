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
- `In scope` contains at least one backticked repository-relative file or directory prefix;
  absolute paths, `..` traversal, and glob syntax are invalid,
- every task card contains at least one task-local acceptance criterion whose stable id
  matches `<task-id>-AC<n>`,
- acceptance criterion ids are unique across the document,
- `Dependencies` has one entry per task id, uses `none` or known earlier task ids, and contains
  no self-reference, forward reference, or cycle,
- `Verification notes` uses bullet items that reference every task id from `Ordered tasks`,
  including command-only or verification-only tasks,
- checks embedded only inside `Ordered tasks` do not replace the dedicated per-task
  `Verification notes` entries,
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
  - TL-1-AC1: The supported input produces the expected output.
```

Optional task-card fields are `Context`, `Implementation constraints`, and `Out of scope`.
Backticked task-scope paths use exact-file or directory-prefix semantics. They are enforced even
when no global allowed-write scope exists; when global scope exists, the effective boundary is the
intersection of task-local and global scope.
