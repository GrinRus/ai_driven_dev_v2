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
5. current outputs:
   - `qa-report.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

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
  `verification-artifacts.md` for each material QA claim;
- verdict mismatch: align verdict and release recommendation with unresolved findings and
  critical-check availability;
- risk gaps: add residual risk entries with severity plus mitigation/ownership;
- status drift: align validator verdict, stage status, blockers, and next actions.

## Repair rules

1. Preserve valid evidence-backed conclusions; avoid rewriting unaffected sections.
2. Do not escalate to `ready`/`proceed` while critical evidence is missing or contradictory.
3. Use only allowed recommendation values: `proceed`, `proceed-with-conditions`, `hold`.
4. Keep blocking uncertainty explicit via `[blocking]` questions and `hold` recommendation.
5. Keep `stage-result.md` attempt status truthful for the current repair attempt.

## Repair exit checks

- quality verdict is evidence-backed and explicitly stated,
- release recommendation is actionable and coherent with verdict/risk profile,
- residual risks include severity plus mitigation/ownership where needed,
- no evidence-free material claim remains,
- no conflict remains between `qa-report.md`, `validator-report.md`, and `stage-result.md`.
