# Repair prompt for `research`

You are rerunning the `research` stage because validation failed.

Your job is to resolve research-validator findings with minimal edits while preserving evidence
traceability and question-state consistency.

## Read order (do not skip)

1. `validator-report.md` (latest issue list and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/research.md`
4. `contracts/documents/research-notes.md`, `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. `contracts/documents/questions.md` and `contracts/documents/answers.md`
6. current outputs:
   - `research-notes.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md` and reference `repair-brief.md` by path for traceability.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

Interview document format is strict. `questions.md` bullets use `- Q1 [blocking|non-blocking] ...`;
`answers.md` bullets must reuse the same question id with `[resolved|partial|deferred]`, for example
`- Q1 [resolved] ...`. Do not put a colon after the marker; `- Q1 [resolved]: ...` is invalid.
Do not invent `A1`/`A2` answer ids. Render assumptions or metadata as non-bullet continuation prose.

## Finding-to-fix mapping

For each finding:

1. identify the root cause in source content (`Sources`, `Findings`, `Evidence trace`,
   `Trade-offs`, `Open questions`);
2. patch the smallest section that resolves the issue;
3. re-check citation consistency across `Sources`, `Findings`, and `Evidence trace`;
4. re-check blocker status in `stage-result.md` against unresolved `[blocking]` questions.

Use concrete repair actions:

- unsupported claim: add supporting citations or downgrade claim to explicit assumption;
- missing or broken citation link: add/fix citation id in `Sources` and update references;
- weak freshness handling: add access date or stale-risk note with follow-up action;
- unresolved research ambiguity: keep or add blocking question instead of inventing facts.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Keep citation ids and question ids stable where possible.
2. Preserve valid evidence mappings; do not rewrite unaffected sections.
3. Do not mark `succeeded` while validator verdict is `fail`.
4. Keep unresolved `[blocking]` questions explicit under `Blockers` and `Open questions`.
5. Keep `stage-result.md` attempt history and terminal status truthful for this repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
10. Do not claim success unless required headings, validator verdict, stage-result status, and evidence-backed findings are mutually consistent.
11. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- material findings are citation-backed or explicitly marked as assumptions,
- stale-sensitive findings include freshness context and follow-up action,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- unresolved `[blocking]` questions still prevent `succeeded`.
