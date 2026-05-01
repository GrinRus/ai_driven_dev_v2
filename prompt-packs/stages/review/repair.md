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
5. current outputs:
   - `review-report.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md`.

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

Use concrete repair actions:

- unsupported finding: remove claim or rewrite with explicit evidence from implement artifacts or
  acceptance-criteria mismatch;
- missing severity: assign explicit severity (`critical`, `high`, `medium`, `low`) per finding;
- missing disposition: assign explicit disposition (`must-fix`, `follow-up`, `accepted-risk`,
  `invalid`);
- approval mismatch: align approval status with unresolved `must-fix` findings and required-change
  summary;
- status drift: align validator verdict, stage status, blockers, and next actions.

## Repair rules

1. Preserve valid evidence-backed findings; avoid rewriting unaffected sections.
2. Keep finding ids stable where possible.
3. Do not mark stage `succeeded` while unresolved `must-fix` findings remain.
4. Keep blocking ambiguity explicit via `[blocking]` questions when required baseline is missing.
5. Keep `stage-result.md` attempt status truthful for the current repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-exhausted` or `Rerun allowed after this attempt: no`, `stage-result.md` status must be `failed`; do not claim `succeeded`.
9. Do not claim success unless required headings, validator verdict, stage-result status, approval status, and unresolved findings are mutually consistent.

## Repair exit checks

- every remaining finding has stable id, severity, disposition, and rationale,
- no unsupported or evidence-free finding remains active,
- approval status is coherent with unresolved `must-fix` findings,
- required changes are explicit for non-approved outcomes,
- repair-budget exhaustion cannot coexist with `stage-result.md` status `succeeded`,
- no conflict remains between `review-report.md`, `validator-report.md`, and `stage-result.md`.
