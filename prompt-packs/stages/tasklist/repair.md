# Repair prompt for `tasklist`

You are rerunning the `tasklist` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving task id stability,
dependency clarity, and reviewability of each task item.

## Read order (do not skip)

1. `validator-report.md` (latest finding codes, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `stage-brief.md` (embedded required skeletons for installed package runs)
4. `contracts/stages/tasklist.md` when present
5. `contracts/documents/tasklist.md`, `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
6. `contracts/documents/questions.md` and `contracts/documents/answers.md`
7. current outputs:
   - `tasklist.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md` and reference `repair-brief.md` by path for traceability.

Repository-local `contracts/...` files may be absent in installed package checkouts. Do not
search broadly for missing contracts or fail because they are absent; use `stage-brief.md` as the
authoritative skeleton source and repair the required outputs immediately. After reading
`validator-report.md`, `repair-brief.md`, and `stage-brief.md`, the first file-changing action must
create or replace `tasklist.md`, `stage-result.md`, `validator-report.md`, `questions.md`, and
`answers.md` as needed. Do not end the turn after analysis-only reads.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

Interview document format is strict. `questions.md` bullets use `- Q1 [blocking|non-blocking] ...`;
`answers.md` bullets must reuse the same question id with `[resolved|partial|deferred]`, for example
`- Q1 [resolved] ...`. Do not put a colon after the marker; `- Q1 [resolved]: ...` is invalid.
Do not use `- Q1: [resolved] ...`; it is invalid. Do not invent `A1`/`A2` answer ids.
If no operator answer is present, write `# Answers\n\n- none\n`; do not create `[resolved]`
answers yourself. Render assumptions or metadata as non-bullet continuation prose.

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

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Preserve valid tasks; do not rewrite unaffected sections.
2. Keep task ids stable where possible; add new ids only when splitting is required.
   Accepted stable id styles include `T1`, `T2`, ... and `TL-1`, `TL-2`, ...; keep one style
   consistent across ordered tasks, dependencies, and verification notes.
3. Do not mark `succeeded` while unresolved `[blocking]` questions remain.
4. Keep dependency references resolvable to listed task ids or explicit upstream artifacts.
5. Keep `stage-result.md` attempt status truthful for the current repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
10. Do not claim success unless required headings, validator verdict, stage-result status, and task dependencies are mutually consistent.
11. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.

## Repair exit checks

- no task bundles unrelated outcomes or hides prerequisites,
- dependencies are explicit and ordering is executable,
- every task has at least one concrete verification note,
- unresolved blocking ambiguity is represented in questions/blockers,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- `tasklist.md`, `validator-report.md`, and `stage-result.md` are status-consistent.
