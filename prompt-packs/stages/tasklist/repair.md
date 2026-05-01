# Repair prompt for `tasklist`

You are rerunning the `tasklist` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving task id stability,
dependency clarity, and reviewability of each task item.

## Read order (do not skip)

1. `validator-report.md` (latest finding codes, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/tasklist.md`
4. `contracts/documents/tasklist.md`, `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. current outputs:
   - `tasklist.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md`.

## Finding-to-fix mapping

For each finding:

1. identify the root cause in one of these areas:
   - task independence,
   - ordering/dependency clarity,
   - reviewability/verification notes,
   - cross-document status drift;
2. patch the smallest affected section in `tasklist.md`;
3. re-check dependency references and task ordering after every dependency edit;
4. re-check `stage-result.md` and `validator-report.md` for status/blocker consistency.

Use concrete repair actions:

- bundled task scope: split into smaller ordered tasks with one dominant deliverable each;
- hidden or unclear prerequisites: add explicit dependency ids or `none`, then reorder tasks;
- weak verification guidance: add concrete primary checks per task (test/check/scenario);
- unresolved upstream blocking conditions: keep/add `[blocking]` questions instead of forcing
  `succeeded`;
- stage/validator drift: align blocker list, terminal status, and next actions with validator
  outcome.

## Repair rules

1. Preserve valid tasks; do not rewrite unaffected sections.
2. Keep task ids stable where possible; add new ids only when splitting is required.
3. Do not mark `succeeded` while unresolved `[blocking]` questions remain.
4. Keep dependency references resolvable to listed task ids or explicit upstream artifacts.
5. Keep `stage-result.md` attempt status truthful for the current repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-exhausted` or `Rerun allowed after this attempt: no`, `stage-result.md` status must be `failed`; do not claim `succeeded`.
9. Do not claim success unless required headings, validator verdict, stage-result status, and task dependencies are mutually consistent.

## Repair exit checks

- no task bundles unrelated outcomes or hides prerequisites,
- dependencies are explicit and ordering is executable,
- every task has at least one concrete verification note,
- unresolved blocking ambiguity is represented in questions/blockers,
- repair-budget exhaustion cannot coexist with `stage-result.md` status `succeeded`,
- `tasklist.md`, `validator-report.md`, and `stage-result.md` are status-consistent.
