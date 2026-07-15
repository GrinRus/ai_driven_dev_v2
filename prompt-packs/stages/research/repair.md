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

1. identify the root cause in source content (`Sources`, `Findings`, `Evidence trace`,
   `Trade-offs`, `Open questions`);
2. patch the smallest section that resolves the issue;
3. re-check citation consistency across `Sources`, `Findings`, and `Evidence trace`;
4. re-check blocker status in `stage-result.md` against unresolved `[blocking]` questions.
5. remove or account for any temporary research scripts or probes left directly under `.aidd/`;
   cite evidence in canonical Markdown instead of preserving scratch files.
6. re-check that any local repro/probe cited by research is bounded by construction. Do not
   preserve evidence from an open-ended server, infinite stream, watcher, or command that
   only stopped because the external per-stage timeout fired or the run was interrupted. Add
   a finite iteration count, an in-script timeout such as `anyio.fail_after(...)`, or
   `subprocess.run(..., timeout=...)`; otherwise downgrade the probe to `not-run: <reason>`.
7. re-check ignored verification residue from research commands with
   `git status --ignored --short --untracked-files=all` or equivalent evidence; `.pytest_cache/`,
   `.ruff_cache/`, `coverage/`, `.coverage*`, `__pycache__/`, build, dist, or dependency-cache artifacts must be
   absent, cleaned, or explicitly kept as active workspace pollution findings. Do not claim cleanup
   passed from a narrower check.

Use concrete repair actions:

- unsupported claim: add supporting citations or downgrade claim to explicit assumption;
- missing or broken citation link: add/fix citation id in `Sources` and update references;
- weak freshness handling: add access date or stale-risk note with follow-up action;
- unresolved research ambiguity: keep or add blocking question instead of inventing facts.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.
- If `stage-result.md` retained the bootstrap placeholder, replace the whole file content; do not
  keep `# Stage result` / `Stage not run yet.` above the repaired `# Stage Result` document.

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
12. When `Status` is `succeeded`, `stage-result.md` `Next actions` must name `plan` as the
    exact immediate canonical downstream stage; generic `planning` wording is not enough.
13. Do not create top-level `workitems/...`; canonical stage artifacts are under `.aidd/workitems/...`
    from the repository root.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- material findings are citation-backed or explicitly marked as assumptions,
- stale-sensitive findings include freshness context and follow-up action,
- no stray research scratch files remain directly under `.aidd/`,
- no ignored verification residue from research commands remains unexplained or hidden behind a
  succeeded status,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- successful `stage-result.md` next-action copy names the exact immediate next stage id `plan`,
- unresolved `[blocking]` questions still prevent `succeeded`.
