# Run prompt for `review`

## Stage objective

Produce a defensible `review` package that classifies implementation findings by severity and
disposition, then makes an explicit approval decision (`approved`, `approved-with-conditions`,
or `rejected`).

The stage is complete only when every finding is evidence-backed, severity/disposition labels are
coherent, and approval status matches unresolved `must-fix` items. If there are no review
findings, the `Findings` section must say exactly `- none` or
`No review findings were identified.`

## Inputs to read first

- required:
  - `../implement/output/implementation-report.md`
  - `../implement/output/stage-result.md`
  - `../implement/output/validator-report.md`
- optional context when available:
  - `../tasklist/output/tasklist.md`
  - `../plan/output/plan.md`
  - `context/diff-summary.md`
  - `context/acceptance-criteria.md`
  - `context/verification-output.md`
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/review-baseline.md`
- contract of record:
  - `contracts/stages/review.md`

## Required outputs (always write)

- `review-report.md`
- `stage-result.md`
- `validator-report.md`

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Review discipline

1. Findings must have stable ids, explicit severity, explicit disposition, and rationale tied to
   implementation evidence or acceptance-criteria mismatch.
   Use either top-level bullet findings or `### RV-*` / `### REV-*` finding subsections; when using
   subsections, keep severity, disposition, rationale, and evidence as nested metadata under that
   finding.
   Every finding must include an explicit `Evidence:` metadata item or equivalent inline evidence
   text that cites `implementation-report.md`, a changed file path, or an acceptance-criteria id
   such as `AC-1`. A plausible rationale without this evidence reference is invalid.
   If there are no active findings, do not invent a finding id; write a single explicit
   no-findings declaration instead.
2. Severity and disposition labels must stay consistent between detailed findings and summary
   sections.
3. `must-fix` findings block `approved` status until resolved.
4. Required changes must map to concrete finding ids when status is conditional or rejected.
5. Missing or contradictory baseline context needed for a defensible decision must become explicit
   questions, not silent assumptions.
6. When present, selected task evidence, acceptance criteria, and `context/verification-output.md`
   define the authored verification boundary. Do not convert optional broader checks outside that boundary
   into `approved-with-conditions` unless they reveal a concrete defect, contradict acceptance
   criteria, are required by review baseline or release policy, or leave required selected-task
   verification inconclusive.
7. Review the complete local workspace change set. Newly created untracked source files under the
   allowed write scope are part of the AIDD deliverable when repository evidence shows they exist.
   Do not reject solely because such a file is absent from `git diff --stat`; inspect it and treat
   it as a changed file unless it is missing, outside scope, undocumented by implementation
   evidence, or an explicit release policy requires a tracked-only patch artifact.
   Inspect or cite `git status --short --untracked-files=all`, not only `git diff --name-only`,
   before declaring the workspace clean. Project-local provider state such as `.qwen/...`,
   `.claude/...`, `.codex/...`, `.opencode/...`, and unexpected lockfiles such as `uv.lock` are
   not AIDD workspace artifacts. If they appear as new target-repository files and are not known
   setup-baseline files required by the task, record a `must-fix` finding instead of treating them
   as harmless runtime noise.
   If `context/diff-summary.md`, `context/repository-state.md`, or implementation evidence shows
   lockfile, dependency manifest, generated resolver output, or project config changes that are not
   required by the selected task, record a `must-fix` finding and do not approve the change cleanly.
8. Intentional design constraints selected by the authored task or resolved interview answers are
   acceptance context, not findings by themselves. For example, do not write an `accepted-risk`
   finding solely because the task intentionally executes trusted local Python when the
   implementation requires explicit confirmation, documents the trust boundary, and stays within
   the selected scope. Write a finding only for missing mitigation/evidence, broadened scope,
   contradictory artifacts, or a concrete defect.
9. When `../tasklist/output/tasklist.md` or `../plan/output/plan.md` is available, audit the
   implementation against task-level details and planned risk mitigations, not only acceptance
   criteria. For each nontrivial task detail or mitigation in those upstream artifacts, verify it is
   present in the diff, tests, or implementation evidence. Treat named mechanisms as requirements
   when the plan/tasklist made them concrete: examples include a specific API/library call,
   named synchronization primitive, language-appropriate exception cause/chaining mechanism,
   or a required regression assertion. If the implementation omits it, such as missing a promised
   error-cause or diagnostic-context preservation check, record a `must-fix` finding unless the
   upstream artifact explicitly supersedes that requirement.
10. In `review-report.md`, write the approval decision as a machine-readable line:
   `- Review status: approved` (or `approved-with-conditions` / `rejected`) under
   `Approval status` or `Verdict`, then add rationale separately.

## Execution instructions

1. Read required `implement` artifacts, upstream tasklist/plan artifacts when present, existing
   optional context such as diff summary, acceptance criteria, `context/verification-output.md`,
   and `contracts/stages/review.md` before drafting outputs.
2. Do not mark stage `succeeded` when `implement` status is unresolved or validator verdict is
   `fail`.
3. Draft `review-report.md` with sections for findings, approval decision, and required changes.
   Put the approval decision on its own line using `- Review status: approved` (or
   `approved-with-conditions` / `rejected`) before explanatory rationale.
4. Keep every finding tied to observable evidence from `implementation-report.md` and/or explicit
   acceptance-criteria mismatch. For subsection findings, use this metadata shape:
   - `Severity: low|medium|high|critical|info|none`
   - `Disposition: must-fix|follow-up|accepted-risk|invalid`
   - `Evidence: implementation-report.md ...`, changed file path, or `AC-*`
   - `Rationale: ...`
5. Use allowed dispositions (`must-fix`, `follow-up`, `accepted-risk`, `invalid`) and keep wording
   unambiguous for downstream QA.
6. If contradictions in baseline prevent defensible decision, ask a `[blocking]` question instead
   of forcing approval.
7. Keep out-of-boundary exploratory check limitations as non-blocking notes when authored
   verification and acceptance criteria are clean.
8. Update `validator-report.md` and `stage-result.md` so verdict, blockers, and next actions match
   the final review decision.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- If no clarification is needed and you create `questions.md` or `answers.md`, write exactly
  `# Questions\n\n- none\n` or `# Answers\n\n- none\n`; do not write prose such as
  `No questions required.` as a bullet.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- findings are uniquely identified with severity and disposition labels,
- each finding has explicit `Evidence:` metadata or inline evidence tied to implementation output
  or acceptance-criteria mismatch,
- approval status is explicit and consistent with unresolved `must-fix` findings,
- required changes map to concrete findings for non-approved outcomes,
- optional checks outside the authored verification boundary are not treated as approval
  conditions unless they expose a concrete defect or selected-task evidence gap,
- intentional selected design constraints are not emitted as `accepted-risk` findings when their
  required mitigations and evidence are complete,
- available tasklist/plan task details and risk mitigations were cross-checked against the diff,
  tests, and implementation evidence,
- named plan/tasklist mechanisms were either found in code/tests or explicitly superseded,
- blocking ambiguity is surfaced via explicit questions,
- `review-report.md`, `validator-report.md`, and `stage-result.md` are outcome-consistent.
