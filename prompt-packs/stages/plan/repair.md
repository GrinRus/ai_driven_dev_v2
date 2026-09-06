# Repair prompt for `plan`

You are rerunning the `plan` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving milestone ordering
logic, dependency clarity, and review readiness.

## Runtime write authority

Write only `plan.md` and other runtime-content targets explicitly listed in `stage-brief.md`.
Do not write `stage-result.md` or `validator-report.md`; AIDD owns their canonical
status, validation, history, and publication. Never create, edit, delete, or replace either record.
If a finding names one, expose the needed correction in `plan.md` for AIDD reconciliation.
`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it.
Keep any repair summary and remaining content blockers in `plan.md` using its existing sections.
AIDD owns terminal status, repair references, and downstream next actions. Read workflow records
and their contracts as evidence.

## Read order (do not skip)

Read `stage-brief.md`, the current `plan.md`, and its
`contracts/documents/plan.md` contract before applying the findings.

1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/plan.md`
4. `contracts/documents/questions.md` and `contracts/documents/answers.md`
5. `context/allowed-write-scope.md` when present

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

1. identify the root cause in the source section (`Milestones`, `Risks`, `Dependencies`,
   `Verification approach`, `Verification notes`, scope boundaries);
2. patch the smallest section that resolves the issue code;
3. re-check sequencing consistency across milestones and dependency links;
4. keep readiness and blocker claims in `plan.md` consistent with unresolved `[blocking]`
   questions and substantive repair evidence; AIDD derives stage status.

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
  Treat `SEM-PLAN-SCOPE-MISMATCH` as fail-closed evidence and correct every named proposed write
  before claiming the Plan is ready.
- downstream-order drift: keep plan recommendations flow-aware: `review-spec` is the immediate
  canonical downstream stage, before task decomposition, implementation, review, or QA.
  AIDD writes workflow next actions.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy only the `plan.md` skeleton headings from `stage-brief.md` or its document contract
  when substantive output is malformed. AIDD repairs generated workflow records.

## Repair rules

1. Preserve valid plan sections; do not rewrite unaffected content.
2. Keep milestone and question ids stable where possible.
3. Keep unresolved `[blocking]` questions explicit under blockers and next actions.
4. Use exact required headings from document contracts; do not rename or qualify headings.
5. Before declaring success, verify every proposed repository write path against
    `context/allowed-write-scope.md` when present; read-only evidence paths and commands do not
    expand that implementation boundary.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- milestone sequencing and dependency constraints are coherent and explicit,
- every milestone has a stable `M<N>` id and verification notes reference those ids,
- risk mitigation and verification expectations are linked for highest-risk work,
- no milestone or strategy proposes a helper, module, test, configuration, generated artifact, or
  other repository write outside canonical `context/allowed-write-scope.md` when it exists,

AIDD owns downstream-order drift correction: the immediate next stage after `plan` is
`review-spec`. Preserve content needed for that handoff; do not bypass the planning or
implementation gates by naming a later stage.
