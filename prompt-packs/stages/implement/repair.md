# Repair prompt for `implement`

You are rerunning the `implement` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving task alignment,
scope safety, verification truthfulness, and cross-document status consistency.

## Read order (do not skip)

1. `validator-report.md` (latest findings, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/implement.md`
4. `contracts/documents/implementation-report.md`,
   `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. `contracts/documents/questions.md` and `contracts/documents/answers.md`
6. stage input bundle for this attempt, especially provided optional context such as
   `context/acceptance-criteria.md` and `context/verification-output.md`
7. current outputs:
   - `implementation-report.md`
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

1. identify the root cause class:
   - `missing diffs`,
   - `unverifiable claims`,
   - `incomplete summary`,
   - `invalid no-op rationale`,
   - cross-document status drift;
2. patch only the smallest affected section(s) of `implementation-report.md`;
3. re-check touched-files entries against observable repository changes and allowed write scope;
   each top-level entry needs a backticked file path plus short intent, while nested bullets may hold
   line-level details;
4. re-check verification entries for concrete command/check evidence plus observed outcome
   (`-> pass`, `exit 0`, `exit code 0`, or captured tool summary);
   any pass/fail/success outcome claim without executable/check evidence in the same bullet is still
   invalid. Manual or `CliRunner` checks must cite the executed command/snippet, artifact path, or
   captured assertion result; replace unevidenced `manual inspection -> pass` claims with concrete
   evidence or `not-run: <reason>`. Use one bullet per command/check with this exact shape:
   ``- `command goes here` -> pass (observed summary)`` or
   ``- `command goes here` -> fail (exit code N; observed summary)``.
5. keep repair bounded: if verification still fails after one focused fix attempt, record the exact
   failing command/output and terminal status instead of continuing ad hoc debugging until timeout.
6. re-check `stage-result.md` and `validator-report.md` for status/blocker consistency.
7. re-check `git status --short --untracked-files=all`; top-level `workitems/...`, stray
   stage/control documents, or unrelated scratch files must be cleaned up or reported as a
   not-clean implementation state.
8. Do not delete, move, reclone, or recreate the prepared repository checkout or any live harness
   run directory such as `source/`, `build/`, `install-home/`, `uv-cache/`, or `target/`. If the
   prepared checkout, installed `aidd` command, or packaged contracts disappear, report the repair
   attempt as `blocked` or `failed` with the exact missing path instead of running `git clone` or
   rebuilding the harness workspace.
9. When feasible, re-check ignored local artifacts with
   `git status --ignored --short --untracked-files=all`; newly created `.venv/`, `.pytest_cache/`,
   `.ruff_cache/`, `.pdm-build/`, `coverage/`, `.coverage*`, build, dist, or dependency-cache directories are
   workspace pollution unless they are required by the selected deliverable or removed before
   terminal output. Do not claim cleanup passed or mark cleanup resolved unless the cited evidence
   explicitly checks `.pytest_cache/`, `.ruff_cache/`, `coverage/`, `.coverage*`, `__pycache__/`,
   build, dist, and dependency-cache residue.

Use concrete repair actions:

- `missing diffs`: remove unsupported touched-files claims or add missing concrete entries that match
  observed edits;
- `incomplete touched-files intent`: rewrite each top-level touched-files bullet in the exact shape
  ``- `path/to/file.ext` - changed <short intent>`` so the path, separator, and intent are on the
  same line;
- `unverifiable claims`: replace vague assertions with concrete command/check outcomes, or mark as
  `not-run: <reason>` explicitly;
- unresolved failing verification: keep the failure visible in `implementation-report.md`,
  `stage-result.md`, and `validator-report.md`; do not claim success while debugging is incomplete;
- `incomplete summary`: rewrite change summary so it maps selected task id -> edits -> outcomes;
- `invalid no-op`: add evidence-backed justification and actionable next step, or convert run from
  no-op to real scoped edits;
- status drift: align validator verdict, stage status, blockers, and next actions.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Preserve valid evidence-backed sections; do not rewrite unaffected parts.
2. Keep any selected task id from `context/task-selection.md`, any local tasklist ids used for
   verification, and provided scope constraints explicit after every edit.
3. Rework touched-files list and verification notes together whenever implementation claims change.
4. Do not claim commands/checks that were not executed in this attempt; if
   `context/verification-output.md` lists authored or scenario verification commands, record each
   command as executed with outcome or explicitly not-run with a reason.
5. If no-op is retained, include justification, evidence, and next action; otherwise no-op is invalid.
6. Keep `stage-result.md` attempt status truthful for the current repair attempt.
7. Use exact required headings from document contracts; do not rename or qualify headings.
8. Read the repair budget section in `repair-brief.md` before declaring terminal status.
9. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
10. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
11. Do not claim success unless required headings, validator verdict, stage-result status, touched files, and verification evidence are mutually consistent.
12. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.
13. Do not create top-level `workitems/...`; canonical stage artifacts are under `.aidd/workitems/...`
    from the repository root.
14. Do not delete, move, reclone, or recreate the prepared repository checkout or live harness run
    directories; missing checkout/install/contract paths are blockers, not repair work.

## Repair exit checks

- no edit or verification claim remains without observable evidence,
- every verification bullet with a pass/fail/success claim has the command/check and observed
  outcome on the same bullet,
- unresolved failed verification is explicit instead of hidden by open-ended debugging,
- selected task id, change summary, touched-files list, and verification notes are mutually consistent,
- touched-files entries stay within allowed write scope, match observed edits, and include same-line
  path + intent for every top-level file entry,
- no top-level `workitems/...` artifacts or unrelated scratch files remain in the deliverable workspace,
- no live harness checkout/install directories were deleted or recreated, and no ignored local
  environment, cache, coverage, build, or dist artifacts are left as unexplained workspace
  pollution; cleanup evidence explicitly covers `.pytest_cache/`, `.ruff_cache/`, `coverage/`,
  `.coverage*`, `__pycache__/`, build, dist, and dependency-cache residue,
- no-op outcomes (if any) include evidence-backed rationale and actionable next step,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- no status drift remains between `implementation-report.md`, `validator-report.md`, and `stage-result.md`.
