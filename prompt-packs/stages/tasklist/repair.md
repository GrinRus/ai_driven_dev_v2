# Repair prompt for `tasklist`

You are rerunning the `tasklist` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Diagnose the failure class before editing (task independence, ordering clarity, reviewability, or question-handling drift).
3. Correct only missing or incorrect parts while preserving valid task entries and dependency links.
4. Rework dependencies and ordering together when any prerequisite mapping changes.
5. Ensure each task keeps one dominant output artifact and at least one concrete verification note.
6. If ambiguity remains unresolved, write targeted `[blocking]` or `[non-blocking]` questions instead of inventing assumptions.
7. Update `stage-result.md` and `validator-report.md` so repaired attempt status is truthful.

## Repair exit checks

- no task bundles unrelated outcomes or relies on hidden prerequisites,
- dependency order is executable and references resolvable task ids,
- every task has concrete verification guidance,
- question markers and stage status are consistent (`[blocking]` unresolved => no `succeeded`).
