# Repair prompt for `review`

You are rerunning the `review` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving finding traceability,
severity/disposition coherence, and approval-decision correctness.

## Read order (do not skip)

1. `validator-report.md` (latest findings, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/review.md`
4. `contracts/documents/review-report.md`,
   `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. `contracts/documents/questions.md` and `contracts/documents/answers.md`
6. current outputs:
   - `review-report.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present
7. upstream task context when available:
   - `../tasklist/output/tasklist.md`
   - `../plan/output/plan.md`

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

1. identify root cause class:
   - unsupported/evidence-free finding,
   - missing or inconsistent severity,
   - missing or inconsistent disposition,
   - approval-status mismatch,
   - cross-document status drift;
2. patch only the smallest section needed in `review-report.md`;
3. re-check finding ids, severity labels, and dispositions for consistency;
4. re-check `stage-result.md` and `validator-report.md` so blockers and terminal status match.

Findings may be top-level bullets or `### RV-*` / `### REV-*` subsections. When a finding uses a
subsection, keep nested severity/disposition/rationale/evidence bullets inside that subsection; do
not split those metadata bullets into standalone findings.

Use concrete repair actions:

- unsupported finding: remove claim or rewrite with explicit evidence from implement artifacts or
  acceptance-criteria mismatch; add an explicit `Evidence:` line that cites
  `implementation-report.md`, a changed file path, or an acceptance-criteria id such as `AC-1`;
  if no such evidence exists, mark the finding `invalid` or remove it;
- incomplete task acceptance evidence: rebuild `Task acceptance evidence` with exactly one
  structured bullet per `<task-id>-AC<n>` pair, one pair per bullet, a `pass`, `fail`, or
  `not-verified` status, and an `EV-N` id or backticked artifact path; use
  `Review status: rejected` while any entry is non-pass;
- no active findings: write exactly `- none` or `No review findings were identified.` in the
  `Findings` section instead of creating placeholder finding metadata;
- missing severity: assign explicit severity (`critical`, `high`, `medium`, `low`) per finding;
- missing disposition: assign explicit disposition (`must-fix`, `follow-up`, `accepted-risk`,
  `invalid`);
- approval mismatch: align approval status with unresolved `must-fix` findings and required-change
  summary;
- workspace hygiene contradiction: re-check ignored residue after all review commands, including
  `.pytest_cache/`, `.ruff_cache/`, `.pdm-build/`, `coverage/`, `.coverage*`, `__pycache__/`,
  build, dist, and dependency-cache artifacts. If residue still exists, remove it and cite
  post-cleanup evidence, or add an active `RV-*` finding with direct residue evidence. Do not write
  `Findings: none` while residue exists.
- missed tasklist/plan requirement: if available tasklist or plan artifacts name a nontrivial
  implementation detail, risk mitigation, named mechanism, or verification promise that is absent
  from the diff, tests, or implementation evidence, add or keep a `must-fix` finding unless the
  upstream artifact explicitly supersedes that requirement. Named mechanisms include concrete
  APIs/library calls, named synchronization primitives, language-appropriate exception
  cause/chaining mechanisms, and required regression assertions;
- status drift: align validator verdict, stage status, blockers, and next actions.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Preserve valid evidence-backed findings; avoid rewriting unaffected sections.
2. Keep finding ids stable where possible.
3. Do not mark stage `succeeded` while unresolved `must-fix` findings remain.
4. Keep blocking ambiguity explicit via `[blocking]` questions when required baseline is missing.
5. Keep `stage-result.md` attempt status truthful for the current repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
10. Do not claim success unless required headings, validator verdict, stage-result status, approval status, and unresolved findings are mutually consistent.
11. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.

## Repair exit checks

- every remaining finding has stable id, severity, disposition, and rationale,
- or the `Findings` section contains an explicit no-findings declaration and no active finding
  entries,
- every remaining finding has explicit `Evidence:` metadata or equivalent inline evidence tied to
  implementation output or acceptance criteria,
- no unsupported or evidence-free finding remains active,
- approval status is coherent with unresolved `must-fix` findings,
- available tasklist/plan task details and risk mitigations were cross-checked against the diff,
  tests, and implementation evidence,
- named plan/tasklist mechanisms were either found in code/tests or explicitly superseded,
- ignored residue was checked after all review commands; residue was removed with evidence or
  recorded as an active finding,
- required changes are explicit for non-approved outcomes,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- no conflict remains between `review-report.md`, `validator-report.md`, and `stage-result.md`.
