# Run prompt for `qa`

## Stage objective

Produce a defensible `qa` package that states:

- quality verdict (`ready`, `ready-with-risks`, or `not-ready`),
- residual risk profile with mitigation and ownership notes,
- release recommendation (`proceed`, `proceed-with-conditions`, or `hold`),
- evidence links that justify material claims.

The stage is complete only when verdict, recommendation, and evidence are coherent across
`qa-report.md`, `stage-result.md`, and `validator-report.md`.

## Inputs to read first

- required:
  - `../implement/output/implementation-report.md`
  - `../implement/output/stage-result.md`
  - `../implement/output/validator-report.md`
  - `../review/output/review-report.md`
  - `../review/output/stage-result.md`
  - `../review/output/validator-report.md`
- optional context when available:
  - `../tasklist/output/tasklist.md`
  - `../plan/output/plan.md`
  - `context/selected-task.md`
  - `context/diff-summary.md`
  - `context/verification-output.md`
  - `context/verification-artifacts.md`
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/release-policy.md`
- contract of record:
  - `contracts/stages/qa.md`

## Required outputs (always write)

- `qa-report.md`
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

## Interview document syntax

- `questions.md` bullets must be exactly `- Q1 [blocking] text` or
  `- Q1 [non-blocking] text`.
- `answers.md` bullets must be exactly `- Q1 [resolved] text`,
  `- Q1 [partial] text`, or `- Q1 [deferred] text`.
- Do not put punctuation immediately after the marker: `- Q1 [resolved]: text` and
  `- Q1: [resolved] text` are invalid.
- Do not invent `A1`/`A2` answer ids; answer bullets always reuse question ids.
- If no operator answer is present, write `# Answers\n\n- none\n`; do not create
  `[resolved]` answers yourself.

## QA discipline

1. Do not declare `succeeded`, `ready`, or `proceed` when upstream `review` is unresolved or
   explicitly `rejected`.
2. Do not pass QA when verification output/artifacts are missing for material claims.
3. Every material verdict/recommendation claim must point to concrete verification evidence.
   Do not name a specific execution surface, test harness, or API path such as `TestClient`,
   direct ASGI invocation, browser UI, CLI, fixture, or generated output unless the cited
   evidence explicitly shows that surface. If acceptance criteria name alternatives such as
   `ASGI/TestClient`, state the exact surface that was actually exercised.
4. Residual risks must include severity and explicit mitigation/ownership notes.
5. Blocking uncertainty must become a `[blocking]` question with release recommendation `hold`.
6. When present, the selected task and `context/verification-output.md` define the authored
   verification boundary. Do not downgrade to `ready-with-risks` or `proceed-with-conditions` only because
   optional broader checks outside that boundary were not run or were blocked by local sandbox
   policy, unless they reveal a concrete defect or contradict acceptance criteria/review evidence.
   If an optional broader check was run and failed only in unrelated files or environment-sensitive
   surfaces outside the selected scope, while authored verification, acceptance criteria, and review
   evidence are clean, record it as a non-blocking optional-check note instead of a residual risk,
   `ready-with-risks`, or `proceed-with-conditions`. Downgrade only when the failure touches changed
   files, selected public surfaces, acceptance criteria, plan/tasklist promises, review findings, or
   cannot be isolated from the deliverable.
7. Intentional design constraints selected by the authored task or resolved interview answers are
   not residual release risks by themselves. For example, trusted local code execution is `ready`
   when explicit confirmation, documentation, tests, and scope boundaries required by the selected
   task are complete. Downgrade only for missing mitigation/evidence, broadened scope, contradictory
   review/verification artifacts, or a concrete defect beyond the selected boundary.
8. When `context/diff-summary.md`, `context/repository-state.md`, or upstream implementation/review
   evidence shows lockfile, dependency manifest, generated resolver output, or project config
   changes outside the selected task scope, set `QA verdict: not-ready` and release recommendation
   `hold`.
9. When upstream tasklist or plan artifacts are available, cross-check nontrivial task details,
   required mitigations, and explicit risk-verification promises against the diff, tests, and
   implementation evidence. Do not declare `QA verdict: ready` solely because review approved:
   if a planned behavior or named mechanism is missing, such as an error-cause or
   diagnostic-context preservation promise, a required named synchronization primitive, a concrete
   API/library call, or a required regression assertion that has no code or test evidence, set
   `QA verdict: not-ready` and release recommendation `hold` unless upstream artifacts explicitly
   supersede that requirement.
10. If repository evidence shows top-level `workitems/...` duplicates, unexplained non-`.aidd`
    untracked files, or direct `.aidd/*.py`-style scratch files, set `QA verdict: not-ready` and
    release recommendation `hold` unless upstream implementation cleaned them up before QA output.
    Project-local provider state such as `.qwen/...`, `.claude/...`, `.codex/...`, `.opencode/...`,
    and unexpected lockfiles such as `uv.lock` are non-`.aidd` target-repository files, not AIDD
    workspace artifacts. Do not call them harmless runtime artifacts unless repository baseline
    evidence proves they existed after setup and before stage execution.
    When `context/workspace-baseline.md` is provided, use it as setup-owned workspace baseline
    evidence: files listed as setup-owned or setup-baseline files do not make QA `not-ready`
    solely because they are still visible in `git status`. They become blockers only if
    implementation changed them, cites them as deliverable evidence, contradicts the selected task,
    or new untracked files appear outside that baseline.
    If implementation evidence says the prepared checkout disappeared, was recloned, or setup-owned
    workspace paths were deleted, moved, or recreated, set `QA verdict: not-ready` and release
    recommendation `hold`. Setup workspace recovery is an execution blocker, not product evidence.
    If `context/workspace-baseline.md`, `git status --ignored --short --untracked-files=all`, or
    equivalent evidence shows new ignored local artifacts such as `.venv/`, `.pytest_cache/`,
    `.ruff_cache/`, `.pdm-build/`, `coverage/`, `.coverage*`, build, dist, or dependency-cache directories, treat
    them as workspace pollution unless they are selected deliverable outputs or were removed before
    the final QA report. Do not rely only on a clean review report when current repository evidence
    shows ignored residue. Do not write "cleanup passed" or equivalent wording, and do not set
    `QA verdict: ready`, unless the cited command explicitly checks `.pytest_cache/`,
    `.ruff_cache/`, `coverage/`, `.coverage*`, `__pycache__/`, build, dist, and dependency-cache
    residue after all QA commands have run.
11. If the diff changes a shared public-surface mechanism such as a CLI decorator,
    parser/helper, router/error boundary, schema transform helper, or public API adapter, require
    evidence for affected sibling commands, routes, generated outputs, or documented public surfaces.
    Missing help/usage, docs consistency, API compatibility, or generated-output blast-radius
    evidence is a QA blocker unless upstream review explicitly accepted it as out of scope with
    a concrete mitigation.
    For JavaScript or TypeScript packages, treat `package.json` `exports`, wildcard subpath
    exports such as `./utils/*`, generated declarations, and existing public import conventions
    as readiness evidence. If a new helper/module is package-importable but implementation/review
    calls it internal-only, set `QA verdict: not-ready` unless that public API impact is tested or
    explicitly accepted with mitigation.

## Execution instructions

1. Read all required upstream artifacts, existing optional context, and `contracts/stages/qa.md`
   before drafting outputs.
2. Verify upstream `review` outcome is not `rejected` and is consistent with implementation status.
   When `context/selected-task.md` is provided, use its expected scope, quality bar, and acceptance
   context to separate required scenario evidence from optional exploratory checks.
   When repository change evidence is provided, inspect every changed tracked or untracked
   deliverable file, excluding AIDD workspace/config artifacts, before deciding readiness.
   If no repository change evidence is provided, run or cite `git status --short --untracked-files=all`
   or equivalent project-native evidence before deciding readiness.
   Exclude only `.aidd/...` workspace state and known harness config such as `aidd.example.toml`;
   do not exclude provider-local directories such as `.qwen/skills/...` from repository-state
   readiness accounting.
   Do not cite `git diff -- <untracked-file>` as complete evidence for a newly created untracked
   file: plain `git diff` does not show untracked file contents. Cite `git status --short
   --untracked-files=all` plus direct file inspection, or an explicit untracked-file diff method
   such as `git diff --no-index /dev/null <untracked-file>`.
   For setup-owned or setup-baseline files listed in `context/workspace-baseline.md`, cite that
   context and keep them out of deliverable blockers unless the current stage changed or depended
   on them.
3. Build `qa-report.md` with these exact H2 sections:
   `Quality verdict`, `Verification summary`, `Release recommendation`, `Evidence`,
   `Known issues`, and `Readiness`.
   In `Quality verdict`, put the quality decision on its own machine-readable line near the
   top, for example `- QA verdict: ready` (or `ready-with-risks` / `not-ready`), then add
   rationale separately.
4. In `Release recommendation`, put exactly one supported state on its own bullet:
   `proceed`, `proceed-with-conditions`, or `hold`.
5. In `Evidence`, label material evidence entries as `EV-1`, `EV-2`, ... and include command
   outcomes or artifact paths in backticks.
   If the final verdict/recommendation is `ready`/`proceed` or
   `ready-with-risks`/`proceed-with-conditions` and you cite any test, type, lint, docs, or build
   command, include a post-QA ignored-residue evidence entry for
   `git status --ignored --short --untracked-files=all` or an equivalent command. Cite that same
   `EV-N` entry from `Verification summary` or `Readiness`, and state whether ignored residue is
   absent, cleaned before QA output, selected deliverable output, or setup-baseline residue outside
   the deliverable. A clean review report or a pre-QA status command is not enough.
6. When `context/acceptance-criteria.md` exists, add an acceptance coverage checklist under
   `Evidence` or `Readiness` with one top-level bullet per criterion. Copy this shape:
   ``- AC-1: confirmed. Evidence: EV-1, `context/verification-output.md`. <criterion-specific sentence>.``
   Each bullet must name exactly one `AC-N` id and cite same-bullet evidence using an `EV-N` id
   and/or a backticked artifact path. Do not use range claims such as `AC-1 through AC-4`, and do
   not rely on a generic sentence such as `all acceptance criteria passed`.
7. Tie verdict and recommendation claims to `verification-output.md` and/or
   `verification-artifacts.md` references when those documents are provided, and otherwise cite
   concrete upstream evidence.
8. In `Known issues`, use `- Known issues: none.` only as an empty known-defect marker.
   Put residual risks in separate bullets such as
   `- Residual risk RR-1: Severity: low. ... Mitigation/ownership: ...`.
   Do not pair `QA verdict: ready` with residual risk bullets. If a real residual risk
   remains, use `ready-with-risks` and `proceed-with-conditions`; if the note is an
   intentional selected-boundary tradeoff already covered by evidence, keep it out of
   `Known issues` and summarize it under `Readiness` instead.
10. Use only supported recommendation values (`proceed`, `proceed-with-conditions`, `hold`).
11. If critical checks are missing, contradictory, or inconclusive, ask a `[blocking]` question
   instead of inventing assumptions.
12. Keep optional broader-check limitations as non-blocking notes when authored verification,
   review, and acceptance criteria are clean. Isolated optional broad-suite failures in unrelated
   environment-sensitive tests are not residual risks for the selected task.
13. Keep `stage-result.md` and `validator-report.md` aligned with the final QA conclusion.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- If no clarification is needed and you create `questions.md` or `answers.md`, write exactly
  `# Questions\n\n- none\n` or `# Answers\n\n- none\n`; do not write prose such as
  `No questions required.` as a bullet.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- quality verdict is explicit and evidence-backed,
- residual risks include severity plus mitigation/ownership,
- `QA verdict: ready` has no residual risk bullets; remaining real risks use
  `ready-with-risks` and `proceed-with-conditions`,
- release recommendation is actionable and consistent with verdict,
- material claims reference concrete verification evidence,
- ready/proceed-style conclusions that cite test/type/lint/docs/build commands also cite
  post-QA ignored residue evidence with `git status --ignored --short --untracked-files=all`
  or an equivalent command,
- named execution surfaces match the cited evidence exactly rather than broadening an
  `A/B` acceptance alternative into an unsupported concrete claim,
- each `AC-N` from acceptance context has its own evidence-backed checklist bullet when acceptance
  criteria are provided,
- unresolved critical uncertainty is surfaced as blocking question with `hold`,
- optional checks outside the authored verification boundary are not treated as release
  conditions unless they expose a concrete defect,
- isolated optional broad-suite failures in unrelated environment-sensitive tests remain
  non-blocking notes when selected-task evidence is clean,
- intentional selected design constraints are not treated as residual risks when their required
  mitigations and evidence are complete,
- available tasklist/plan task details and risk mitigations were cross-checked before declaring
  `ready` or `proceed`,
- named plan/tasklist mechanisms were either found in code/tests or explicitly superseded before
  declaring `ready` or `proceed`,
- `qa-report.md`, `stage-result.md`, and `validator-report.md` are outcome-consistent.
- top-level `workitems/...` duplicates, unexplained untracked files, and stray `.aidd/` scratch files
  are absent or explicitly make QA `not-ready`.
- ignored verification residue such as `.pytest_cache/`, `.ruff_cache/`, `coverage/`, `.coverage*`,
  `__pycache__/`, build, dist, and dependency-cache artifacts is absent, cleaned before QA, or explicitly keeps QA
  `not-ready`; do not claim cleanup passed from a narrower check or from review alone.
- shared public-surface helper changes have blast-radius evidence for affected sibling
  commands/routes/generated outputs and help/docs/API compatibility.
