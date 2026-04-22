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
5. current outputs:
   - `research-notes.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

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

## Repair rules

1. Keep citation ids and question ids stable where possible.
2. Preserve valid evidence mappings; do not rewrite unaffected sections.
3. Do not mark `succeeded` while validator verdict is `fail`.
4. Keep unresolved `[blocking]` questions explicit under `Blockers` and `Open questions`.
5. Keep `stage-result.md` attempt history and terminal status truthful for this repair attempt.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- material findings are citation-backed or explicitly marked as assumptions,
- stale-sensitive findings include freshness context and follow-up action,
- unresolved `[blocking]` questions still prevent `succeeded`.
