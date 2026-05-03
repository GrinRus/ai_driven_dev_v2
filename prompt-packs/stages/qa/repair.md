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
6. current outputs:
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
`- Q1 [resolved] ...`. Do not invent `A1`/`A2` answer ids. Render assumptions or metadata as
non-bullet continuation prose.

## Finding-to-fix mapping

For each finding:

1. identify root cause class:
   - unsupported or evidence-free verdict/recommendation claim,
   - missing evidence references for material QA claims,
   - verdict/recommendation mismatch with unresolved findings or missing critical checks,
   - residual-risk incompleteness (severity/mitigation/ownership gaps),
   - cross-document status drift (`qa-report.md` vs `stage-result.md` vs `validator-report.md`);
2. patch only the smallest section needed in `qa-report.md`;
3. re-check verdict, recommendation, and risk summary for consistency;
4. re-check `stage-result.md` and `validator-report.md` so blockers and terminal status match.

Use concrete repair actions:

- unsupported claim: remove claim or rewrite with explicit verification evidence reference;
- missing evidence: add direct references to `verification-output.md` or
  `verification-artifacts.md` for each material QA claim, using `EV-1`, `EV-2`, ...
  evidence ids and/or backticked artifact paths;
- verdict mismatch: align verdict and release recommendation with unresolved findings and
  critical-check availability;
- risk gaps: add residual risk entries with severity plus mitigation/ownership;
- status drift: align validator verdict, stage status, blockers, and next actions.

## Repair rules

1. Preserve valid evidence-backed conclusions; avoid rewriting unaffected sections.
2. Do not escalate to `ready`/`proceed` while critical evidence is missing or contradictory.
3. Use only allowed recommendation values: `proceed`, `proceed-with-conditions`, `hold`.
   Put the selected value in a dedicated `## Release recommendation` section.
4. Keep blocking uncertainty explicit via `[blocking]` questions and `hold` recommendation.
5. Keep `stage-result.md` attempt status truthful for the current repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
10. Do not claim success unless required headings, validator verdict, stage-result status, QA verdict, and verification evidence are mutually consistent.
11. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.

## Repair exit checks

- quality verdict is evidence-backed and explicitly stated,
- release recommendation is actionable and coherent with verdict/risk profile,
- residual risks include severity plus mitigation/ownership where needed,
- no evidence-free material claim remains,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- no conflict remains between `qa-report.md`, `validator-report.md`, and `stage-result.md`.
