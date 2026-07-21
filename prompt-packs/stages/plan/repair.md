# Repair prompt for `plan`

You are rerunning the `plan` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving milestone ordering
logic, dependency clarity, and review readiness.

## Read order (do not skip)

1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/plan.md`
4. `contracts/documents/plan.md`, `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. `contracts/documents/questions.md` and `contracts/documents/answers.md`
6. current outputs:
   - `plan.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present
7. `context/allowed-write-scope.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md` and reference `repair-brief.md` by path for traceability.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

## Validator-report protocol v1

When repairing a draft `validator-report.md`:

- write only the canonical fields `Total issues`, `Blocking issues`, `Affected documents`,
  `Dominant failure categories`, optional `Finding occurrences`, `Verdict`, and
  `Repair required for progression`;
- copy only finding codes declared by `contracts/documents/validator-report.md`; do not
  invent, rename, or generalize a code;
- treat `Validator verdict` and `Repair required` as read-only legacy field aliases and
  rewrite them to their canonical labels;
- treat `STRUCT-MISSING-DOCUMENT`, `STRUCT-MISSING-HEADING`,
  `STRUCT-EMPTY-SECTION`, and `CROSS-REFERENCE-MISMATCH` as read-only legacy codes;
  never author them in repaired output.

Canonical output is mandatory even when the input used a declared legacy alias. Any other field
alias or finding code is invalid protocol vocabulary; do not preserve it.

Interview document format is strict. `questions.md` bullets use `- Q1 [blocking|non-blocking] ...`;
`answers.md` bullets must reuse the same question id with `[resolved|partial|deferred]`, for example
`- Q1 [resolved] ...`. Do not put a colon after the marker; `- Q1 [resolved]: ...` is invalid.
Do not use `- Q1: [resolved] ...`; it is invalid. Do not invent `A1`/`A2` answer ids.
If no operator answer is present, write `# Answers\n\n- none\n`; do not create `[resolved]`
answers yourself. Render assumptions or metadata as non-bullet continuation prose.

## Finding-to-fix mapping

For each finding:

1. identify the root cause in the source section (`Milestones`, `Risks`, `Dependencies`,
   `Verification approach`, `Verification notes`, scope boundaries);
2. patch the smallest section that resolves the issue code;
3. re-check sequencing consistency across milestones and dependency links;
4. re-check stage status and blockers in `stage-result.md` against validator verdict and unresolved
   `[blocking]` questions.

Use concrete repair actions:

- vague sequencing: rewrite milestone order so dependencies are explicit and executable;
- missing milestone ids: give every milestone a stable `M<N>` id such as `M1` or `M2` and keep
  those ids consistent in dependencies and verification notes;
- missing dependency logic: add explicit `depends on` / ordering constraints in `Dependencies`;
- weak risk handling: add concrete risk statement with mitigation intent;
- verification mismatch: map verification notes to specific milestone ids and risks, including
  highest-risk work;
- unclear approval readiness: clarify `Out of scope`, trade-offs, and acceptance signals;
- unresolved ambiguity: keep or add a blocking question instead of inventing assumptions.
- out-of-scope implementation path: remove the proposed create/modify/move/delete path; keep a
  small private helper inside allowed files when safe or raise a blocking question. Treat
  `context/allowed-write-scope.md` as exhaustive and do not edit, broaden, or reinterpret it.
- downstream-order drift: if successful `stage-result.md` next actions skip `review-spec` and point
  to task decomposition, implementation, review, or QA, rewrite the next action to name
  `review-spec` as the immediate canonical downstream stage.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Preserve valid plan sections; do not rewrite unaffected content.
2. Keep milestone and question ids stable where possible.
3. Do not mark `succeeded` while validator verdict is `fail`.
4. Keep unresolved `[blocking]` questions explicit under blockers and next actions.
5. Keep `stage-result.md` attempt history and terminal status truthful for this repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
10. Do not claim success unless required headings, validator verdict, stage-result status, and milestone verification mapping are mutually consistent.
11. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.
12. When `stage-result.md` status is `succeeded`, its first downstream action must name
    `review-spec`, not a later canonical stage.
13. Before declaring success, verify every proposed repository write path against
    `context/allowed-write-scope.md` when present; read-only evidence paths and commands do not
    expand that implementation boundary.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- milestone sequencing and dependency constraints are coherent and explicit,
- every milestone has a stable `M<N>` id and verification notes reference those ids,
- risk mitigation and verification expectations are linked for highest-risk work,
- no milestone or strategy proposes a helper, module, test, configuration, generated artifact, or
  other repository write outside canonical `context/allowed-write-scope.md` when it exists,
- successful `stage-result.md` next actions name `review-spec` as the immediate downstream stage,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- `stage-result.md` and `validator-report.md` remain consistent on verdict and blocker state.
