# Safe task-card presentation fixture

This fixture records presentation changes that preserve executable meaning. It is intentionally
kept outside the runtime-success example directory until tolerant parser support is installed.

## Meaning that must remain present

- `### TL-1 —` remains an H3 card with the same stable id and order.
- `**Outcome**` and `` `Outcome` `` still name the same non-empty outcome field.
- `-` and `*` list markers are interchangeable when they do not add or remove a field.
- `Dominant deliverable`, bounded backticked `In scope` paths, task-local acceptance ids,
  dependencies, and dedicated verification remain explicit.

No wording, path, id, dependency, acceptance criterion, or verification result may be inferred or
silently rewritten while applying these presentation changes.
