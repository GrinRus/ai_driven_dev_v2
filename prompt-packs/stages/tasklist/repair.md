# Repair prompt for `tasklist`

You are rerunning the `tasklist` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving task id stability,
dependency clarity, and reviewability of each task item.

## Runtime write authority

Write only `tasklist.md` as the substantive repair output. Do not write `stage-result.md` or
`validator-report.md`; AIDD owns their canonical status, validation, history, and publication.
Read existing workflow records as evidence. Use the controlled interview path for questions
and operator answers; do not invent answers.

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
any repair summary in `tasklist.md` and reference `repair-brief.md` by path for traceability.

Repository-local `contracts/...` files may be absent in installed package checkouts. Do not
search broadly for missing contracts or fail because they are absent; use `stage-brief.md` as the
authoritative skeleton source and repair the required outputs immediately. After reading
`validator-report.md`, `repair-brief.md`, and `stage-brief.md`, the first file-changing action must
create or replace `tasklist.md`; use the controlled interview path for `questions.md` and
`answers.md` when needed. Do not end the turn after analysis-only reads.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

## Validator-report protocol v1

Read `validator-report.md` as AIDD-owned finding evidence; do not rewrite it:

- interpret the canonical fields `Total issues`, `Blocking issues`, `Affected documents`,
  `Dominant failure categories`, optional `Finding occurrences`, `Verdict`, and
  `Repair required for progression`;
- when citing a finding, copy only finding codes declared by
  `contracts/documents/validator-report.md`; do not invent, rename, or generalize a code;
- recognize `Validator verdict` and `Repair required` as read-only legacy field aliases;
  AIDD writers emit the canonical labels;
- recognize `STRUCT-MISSING-DOCUMENT`, `STRUCT-MISSING-HEADING`,
  `STRUCT-EMPTY-SECTION`, and `CROSS-REFERENCE-MISMATCH` as read-only legacy codes.

Any other field alias or finding code is invalid protocol vocabulary. Report unknown input
vocabulary in substantive runtime content instead of changing the validator report. If it or any
other blocker prevents completion, submit a `[blocking]` question through the controlled
interview path; substantive blocker prose alone does not pause AIDD.

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
   - missing task-card outcome, deliverable, scope, or acceptance criteria,
   - malformed or duplicate task/acceptance ids, unsafe scope paths, forward dependencies, and
     dependency cycles,
   - task-local scope paths outside canonical `context/allowed-write-scope.md`,
   - missing or unknown task-to-plan milestone mappings,
   - cross-document status drift;
2. patch the smallest affected section in `tasklist.md`;
3. re-check dependency references and task ordering after every dependency edit;
4. read `stage-result.md` and `validator-report.md` as prior evidence and expose current blockers
   in substantive runtime content for AIDD reconciliation.

Use concrete repair actions:

- bundled task scope: split into smaller ordered tasks with one dominant deliverable each;
- coupled behavior/regression scope: keep the production correction and its regression coverage in
  one bounded card, or add an explicit earlier dependency-ready production card; do not broaden a
  tests-only card beyond its authored `In scope` and do not weaken fail-closed scope validation;
- incomplete task card: preserve its id and add concrete `Outcome`, `Dominant deliverable`,
  `In scope`, and an `Acceptance criteria` field with unique `<task-id>-AC<n>` entries; make
  `In scope` include safe backticked repository-relative file or directory prefixes;
- task scope outside the authored global boundary: replace or split the affected card so every
  backticked `In scope` prefix is equal to or beneath a prefix in
  `context/allowed-write-scope.md`; do not edit, broaden, or reinterpret that context document,
  and use a blocking question if the approved plan has no implementable path inside it;
- hidden or unclear prerequisites: add explicit dependency ids or `none`, then reorder tasks so
  every dependency references an earlier card. If an entry has rationale after the machine-readable
  value, keep that rationale after the leading `none` or task ids; milestone/review ids in rationale
  are not dependencies;
- missing or unknown plan milestone mapping: cite an exact existing `M<n>` id in the task's
  `Outcome`, optional `Context`, a nested acceptance criterion, or its dedicated
  `Verification notes` entry. Cover every plan milestone. Do not add or preserve an ad hoc
  `Milestone` or `Plan milestone` field because the canonical rich-task grammar ignores it;
- weak verification guidance: add concrete primary checks per task (test/check/scenario), with
  one dedicated `Verification notes` entry for every task id declared in `Ordered tasks`,
  including command-only or verification-only tasks. Put the concrete check/result on the same
  top-level mapping bullet, for example - TL-1: `uv run pytest -q tests/test_example.py -> pass`;
  never leave `- TL-1:` empty with the only commands in nested bullets, which the canonical
  parser treats as missing verification;
- unclassified evidence-only task: add `Execution mode: verification-only` only when the task's
  dominant deliverable and acceptance criteria require command/check evidence without a
  task-local repository edit; otherwise keep the repository-change default,
- unresolved upstream blocking conditions: keep/add `[blocking]` questions instead of forcing
  `succeeded`;
- stage/validator drift: correct tasklist readiness and blocker evidence; AIDD derives
  terminal status and next actions from post-runtime validation.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy only the `tasklist.md` skeleton headings from `stage-brief.md` or its document contract
  when substantive output is malformed. AIDD repairs generated workflow records.
- Replace bootstrap placeholders in `tasklist.md` completely; AIDD owns placeholder removal
  in generated workflow records.

## Repair rules

1. Preserve valid tasks; do not rewrite unaffected sections.
2. Keep task ids stable where possible; add new ids only when splitting is required.
   Accepted stable id styles include `T1`, `T2`, ... and `TL-1`, `TL-2`, ...; keep one style
   consistent across ordered tasks, dependencies, and verification notes.
3. Do not mark `succeeded` while unresolved `[blocking]` questions remain.
4. Keep dependency references resolvable to listed task ids or explicit upstream artifacts.
5. Keep `tasklist.md` evidence truthful for the current repair attempt; AIDD owns attempt status.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before reporting the repair outcome.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed substantive findings; AIDD derives terminal status from post-runtime validation; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, AIDD sets terminal status to `failed`.
10. Do not claim the repair is complete unless required headings and task dependencies are mutually consistent.
11. If all listed findings are resolved and no blockers remain, record the repaired evidence in `tasklist.md`; AIDD determines `succeeded` after validation. Do not treat the previous failed validator report as a new result.
12. AIDD writes successful `stage-result.md` `Next actions` to name `implement` as
    the exact immediate canonical downstream stage; generic `implementation` wording is not enough.

## Repair exit checks

- no task bundles unrelated outcomes or hides prerequisites,
- every task uses the complete H3 task-card shape and has well-formed acceptance ids,
- dependencies are explicit and ordering is executable,
- every task has at least one concrete verification note in the dedicated `Verification notes`
  section,
- every task-local scope prefix is inside canonical `context/allowed-write-scope.md` when present,
- every task maps to an existing plan `M<n>` id through `Outcome`, `Context`, an acceptance
  criterion, or its dedicated `Verification notes` entry, and every plan milestone is covered,
- no repair relies on an unsupported `Milestone` or `Plan milestone` field,
- command-only or verification-only task ids are covered explicitly in `Verification notes`,
- every task intended to finish with an empty task-local diff explicitly declares
  `Execution mode: verification-only`,
- unresolved blocking ambiguity is represented in questions/blockers,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- successful `stage-result.md` next-action copy names the exact immediate next stage id `implement`,
- `tasklist.md`, `validator-report.md`, and `stage-result.md` are status-consistent.
