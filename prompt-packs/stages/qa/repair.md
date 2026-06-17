# Repair prompt for `qa`

You are rerunning the `qa` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving evidence traceability,
verdict/recommendation coherence, and truthful stage status.

## Read order (do not skip)

1. `validator-report.md` (latest findings, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/qa.md`
4. `contracts/documents/qa-report.md`,
   `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. `contracts/documents/questions.md` and `contracts/documents/answers.md`
6. stage input bundle for this attempt, especially provided optional context such as
   `context/selected-task.md`, `context/verification-output.md`, and
   `context/verification-artifacts.md`, plus upstream `../tasklist/output/tasklist.md`
   and `../plan/output/plan.md` when present
7. current outputs:
   - `qa-report.md`
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

1. identify root cause class:
   - unsupported or evidence-free verdict/recommendation claim,
   - missing evidence references for material QA claims,
   - missing or bundled acceptance coverage bullets for `AC-N` criteria,
   - verdict/recommendation mismatch with unresolved findings or missing critical checks,
   - residual-risk incompleteness (severity/mitigation/ownership gaps),
   - cross-document status drift (`qa-report.md` vs `stage-result.md` vs `validator-report.md`);
2. patch only the smallest section needed in `qa-report.md`;
3. re-check verdict, recommendation, and risk summary for consistency;
4. re-check `stage-result.md` and `validator-report.md` so blockers and terminal status match.
5. re-check repository evidence, preferably `git status --short --untracked-files=all`; top-level
   `workitems/...`, unexplained untracked non-`.aidd` files, or stray `.aidd/` scratch files must
   keep QA `not-ready` / `hold` unless they were cleaned up before the repaired output.
6. re-check ignored verification residue with `git status --ignored --short --untracked-files=all`
   or equivalent evidence; `.pytest_cache/`, `.ruff_cache/`, `coverage/`, `.coverage*`,
   `__pycache__/`, build, dist, or dependency-cache artifacts must be absent, cleaned, or explicitly keep QA
   `not-ready` / `hold`. Do not claim cleanup passed from a narrower check.

Use concrete repair actions:

- unsupported claim: remove claim or rewrite with explicit verification evidence reference;
- overstated execution surface: remove names such as `TestClient`, direct ASGI invocation,
  browser UI, CLI, fixture, or generated output unless the cited evidence explicitly shows
  that exact surface; if acceptance criteria give alternatives such as `ASGI/TestClient`,
  preserve only the alternative that the evidence actually exercised;
- missing evidence: add direct references to available verification output, verification artifacts,
  or upstream evidence for each material QA claim, using `EV-1`, `EV-2`, ... evidence ids and/or
  backticked artifact paths;
- missing acceptance coverage: when `context/acceptance-criteria.md` exists, add one top-level
  checklist bullet per criterion using the shape
  ``- AC-1: confirmed. Evidence: EV-1, `context/verification-output.md`. <criterion-specific sentence>.``;
  each bullet must name exactly one `AC-N` id and cite same-bullet evidence. Replace range claims
  such as `AC-1 through AC-4` with separate criterion bullets;
- verdict mismatch: align verdict and release recommendation with unresolved findings and
  critical-check availability;
- missed tasklist/plan requirement: when upstream tasklist or plan artifacts name a nontrivial
  implementation detail, risk mitigation, named mechanism, or verification promise that is absent
  from the diff, tests, or implementation evidence, do not keep `QA verdict: ready`; use
  `not-ready` and `hold` unless the upstream artifact explicitly supersedes that requirement.
  Named mechanisms include concrete APIs/library calls, named synchronization primitives,
  language-appropriate exception cause/chaining mechanisms, and required regression assertions;
- risk gaps: add residual risk entries with severity plus mitigation/ownership; keep
  `Known issues: none.` only as an empty known-defect marker, not as a residual risk item;
  do not pair `QA verdict: ready` with residual risk bullets. Use `ready-with-risks` and
  `proceed-with-conditions` for real remaining risks, or move satisfied selected-boundary
  tradeoff notes out of `Known issues`;
- optional-check overreach: if authored verification, acceptance criteria, and review are clean,
  do not turn a non-required broader check into `ready-with-risks` or
  `proceed-with-conditions` unless it reveals a concrete defect. If the broader check failed only
  in unrelated files or environment-sensitive surfaces outside the selected scope, keep it as a
  non-blocking optional-check note rather than a residual risk;
- status drift: align validator verdict, stage status, blockers, and next actions.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Preserve valid evidence-backed conclusions; avoid rewriting unaffected sections.
2. Do not escalate to `ready`/`proceed` while critical evidence is missing or contradictory.
3. Use only allowed recommendation values: `proceed`, `proceed-with-conditions`, `hold`.
   Put the selected value in a dedicated `## Release recommendation` section.
4. Keep blocking uncertainty explicit via `[blocking]` questions and `hold` recommendation.
5. Keep optional broader-check limitations as non-blocking notes when authored verification,
   review, and acceptance criteria are clean. Do not preserve `ready-with-risks` solely for isolated
   optional broad-suite failures in unrelated environment-sensitive tests.
6. Do not preserve `ready-with-risks` only because the task intentionally selected a hazardous or
   limited behavior, such as trusted local code execution, when the implementation matches the
   resolved boundary and includes required confirmation, documentation, tests, and evidence.
   Keep `ready-with-risks` only for a remaining risk beyond the authored boundary, missing
   mitigation/evidence, broadened scope, or contradictory artifacts.
7. Keep `stage-result.md` attempt status truthful for the current repair attempt.
8. Use exact required headings from document contracts; do not rename or qualify headings.
9. Read the repair budget section in `repair-brief.md` before declaring terminal status.
10. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
11. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
12. Do not claim success unless required headings, validator verdict, stage-result status, QA verdict, and verification evidence are mutually consistent.
13. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.
14. Do not create top-level `workitems/...`; canonical stage artifacts are under `.aidd/workitems/...`
    from the repository root.

## Repair exit checks

- quality verdict is evidence-backed and explicitly stated,
- release recommendation is actionable and coherent with verdict/risk profile,
- residual risks include severity plus mitigation/ownership where needed,
- `QA verdict: ready` has no residual risk bullets; remaining real risks use
  `ready-with-risks` and `proceed-with-conditions`,
- empty known-issue markers such as `Known issues: none.` are not the only risk evidence when
  the report also declares residual risk,
- optional checks outside the authored verification boundary are not treated as release
  conditions unless they expose a concrete defect,
- isolated optional broad-suite failures in unrelated environment-sensitive tests remain
  non-blocking notes when selected-task evidence is clean,
- intentional selected design constraints are not treated as residual risks when required
  mitigations and evidence are complete,
- available tasklist/plan task details and risk mitigations were cross-checked before declaring
  `ready` or `proceed`,
- named plan/tasklist mechanisms were either found in code/tests or explicitly superseded before
  declaring `ready` or `proceed`,
- no evidence-free material claim remains,
- every `AC-N` from acceptance context has its own same-bullet evidence reference when acceptance
  criteria are provided,
- top-level `workitems/...` duplicates and stray scratch artifacts are absent or keep QA `not-ready`,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- no conflict remains between `qa-report.md`, `validator-report.md`, and `stage-result.md`.
