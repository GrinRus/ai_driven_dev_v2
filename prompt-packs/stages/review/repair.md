# Repair prompt for `review`

You are rerunning the `review` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving finding traceability,
severity/disposition coherence, and approval-decision correctness.

## Runtime write authority

Write only `review-report.md` and other runtime-content targets explicitly listed in `stage-brief.md`.
Do not write `stage-result.md` or `validator-report.md`; AIDD owns their canonical
status, validation, history, and publication. Never create, edit, delete, or replace either record.
If a finding names one, expose the needed correction in `review-report.md` for AIDD reconciliation.
`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it.
Keep any repair summary and remaining content blockers in `review-report.md` using its existing sections.
AIDD owns terminal status, repair references, and downstream next actions. Read workflow records
and their contracts as evidence.

## Read order (do not skip)

Read `stage-brief.md`, the current `review-report.md`, and its
`contracts/documents/review-report.md` contract before applying the findings.

1. `validator-report.md` (latest findings, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/review.md`
4. `contracts/documents/questions.md` and `contracts/documents/answers.md`
5. upstream task context when available:
   - `../tasklist/output/tasklist.md`
   - `../plan/output/plan.md`

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

Read `contracts/documents/validator-report.md` and `contracts/documents/stage-result.md`
for canonical field labels and finding codes; do not invent or rename protocol vocabulary.
Report unknown input vocabulary in substantive content without modifying the workflow record.
If it or another blocker prevents completion, submit a `[blocking]` question through the
controlled interview path; substantive blocker prose alone does not pause AIDD.

## Interview context

Read `contracts/documents/questions.md` and `contracts/documents/answers.md` when available.
Use stable QIDs and canonical `- Q1 [blocking] ...` or `- Q1 [non-blocking] ...` question
candidates through the controlled interview path. AIDD merges raw candidates and may normalize
safe presentation differences without changing meaning. Preserve unresolved blocking questions.
Operator answers use the same QID, for example `- Q1 [resolved] ...`; do not create or edit
`answers.md`, invent `A1`/`A2` answer ids, or create `[resolved]` answers yourself. Missing
answers remain an operator checkpoint. Render assumptions as non-bullet continuation prose.

Read the repair budget in `repair-brief.md`. On `repair-budget-final-attempt` or
`Rerun allowed after this attempt: no`, still repair the content; do not fail solely because no
later rerun is available. AIDD determines `succeeded` after validation;
`repair-budget-exhausted` with unresolved findings remains `failed`. Do not reset budget or
attempt history. Keep evidence and unresolved questions consistent with the repaired content.
Do not treat the previous failed validator report as a new result.

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
4. read `stage-result.md` and `validator-report.md` as prior evidence and expose current blockers
   in substantive runtime content for AIDD reconciliation.

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
- status drift: correct conflicting claims in substantive runtime content and expose blockers
  and next-action evidence; AIDD reconciles validator verdict and stage status.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy only the `review-report.md` skeleton headings from `stage-brief.md` or its document contract
  when substantive output is malformed. AIDD repairs generated workflow records.

## Repair rules

1. Preserve valid evidence-backed findings; avoid rewriting unaffected sections.
2. Keep finding ids stable where possible.
3. Do not mark stage `succeeded` while unresolved `must-fix` findings remain.
4. Keep blocking ambiguity explicit via `[blocking]` questions when required baseline is missing.
5. Use exact required headings from document contracts; do not rename or qualify headings.

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
