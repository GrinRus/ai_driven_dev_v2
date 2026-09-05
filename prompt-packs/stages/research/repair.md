# Repair prompt for `research`

You are rerunning the `research` stage because validation failed.

Your job is to resolve research-validator findings with minimal edits while preserving evidence
traceability and question-state consistency.

## Read order (do not skip)

Read `stage-brief.md`, the current `research-notes.md`, and its
`contracts/documents/research-notes.md` contract before applying the findings.
1. `validator-report.md` (latest issue list and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/research.md`
4. `contracts/documents/questions.md` and `contracts/documents/answers.md`

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

## Interview context

Read `contracts/documents/questions.md` and `contracts/documents/answers.md` when available.
Use stable QIDs and canonical `- Q1 [blocking] ...` or `- Q1 [non-blocking] ...` question
candidates through the controlled interview path. AIDD merges raw candidates and may normalize
safe presentation differences without changing meaning. Preserve unresolved blocking questions.
Operator answers use the same QID, for example `- Q1 [resolved] ...`; do not create or edit
`answers.md`, invent `A1`/`A2` answer ids, or create `[resolved]` answers yourself. Missing
answers remain an operator checkpoint. Render assumptions as non-bullet continuation prose.

## Authoring boundary

Write only `research-notes.md` and other runtime-content targets explicitly listed in `stage-brief.md`.
Do not write `stage-result.md` or `validator-report.md`; AIDD owns validation, attempt history,
terminal status, repair references, and downstream next actions. Read those records as evidence.
`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it.
Keep any repair summary and remaining content blockers in `research-notes.md` using its existing sections.
If a finding concerns an AIDD-owned record, report the inconsistency without editing that record.

Read the repair budget in `repair-brief.md`. On `repair-budget-final-attempt` or
`Rerun allowed after this attempt: no`, still repair the content; do not fail solely because no
later rerun is available. AIDD may record `succeeded` only after canonical validation passes;
`repair-budget-exhausted` with unresolved findings remains `failed`. Do not reset budget or
attempt history. Keep evidence and unresolved questions consistent with the repaired content.

## Finding-to-fix mapping

For each finding:

1. identify the root cause in source content (`Sources`, `Findings`, `Evidence trace`,
   `Trade-offs`, `Open questions`);
2. patch the smallest section that resolves the issue;
3. re-check citation consistency across `Sources`, `Findings`, and `Evidence trace`;
4. remove or account for any temporary research scripts or probes left directly under `.aidd/`;
   cite evidence in canonical Markdown instead of preserving scratch files.
5. re-check that any local repro/probe cited by research is bounded by construction. Do not
   preserve evidence from an open-ended server, infinite stream, watcher, or command that
   only stopped because the external per-stage timeout fired or the run was interrupted. Add
   a finite iteration count, an in-script timeout such as `anyio.fail_after(...)`, or
   `subprocess.run(..., timeout=...)`; otherwise downgrade the probe to `not-run: <reason>`.
6. re-check ignored verification residue from research commands with
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

## Repair rules

1. Keep citation ids and question ids stable where possible.
2. Preserve valid evidence mappings; do not rewrite unaffected sections.
3. Keep unresolved `[blocking]` questions explicit under `Blockers` and `Open questions`.
4. Use exact required headings from document contracts; do not rename or qualify headings.
5. Do not create top-level `workitems/...`; canonical stage artifacts are under `.aidd/workitems/...`
    from the repository root.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- material findings are citation-backed or explicitly marked as assumptions,
- stale-sensitive findings include freshness context and follow-up action,
- no stray research scratch files remain directly under `.aidd/`,
- no ignored verification residue from research commands remains unexplained or hidden behind a
  succeeded status,
- unresolved `[blocking]` questions still prevent `succeeded`.

AIDD owns downstream-order drift correction: the immediate next stage after `research` is
`plan`. Preserve content needed for that handoff; do not bypass the planning or
implementation gates by naming a later stage.
