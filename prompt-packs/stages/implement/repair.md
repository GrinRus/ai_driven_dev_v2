# Repair prompt for `implement`

You are rerunning the `implement` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving task alignment,
scope safety, verification truthfulness, and cross-document status consistency.

## Runtime write authority

Write only `implementation-report.md` as the substantive repair output. Do not write `stage-result.md` or
`validator-report.md`; AIDD owns their canonical status, validation, history, and publication.
Read existing workflow records as evidence. Use the controlled interview path for questions
and operator answers; do not invent answers.

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
any repair summary in `implementation-report.md` and reference `repair-brief.md` by path for traceability.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

## Validator-report protocol v1

Read `validator-report.md` as AIDD-owned finding evidence; do not rewrite it:

- interpret the canonical fields `Total issues`, `Blocking issues`, `Affected documents`,
  `Dominant failure categories`, optional `Finding occurrences`, `Verdict`, and
  `Repair required for progression`;
- when citing a finding, copy only finding codes declared by
  `contracts/documents/validator-report.md`; do not invent, rename, or generalize a code;
- recognize `Validator verdict` and `Repair required` as read-only legacy field aliases;
  AIDD writers emit the canonical labels;
- recognize `STRUCT-MISSING-DOCUMENT`, `STRUCT-MISSING-HEADING`,
  `STRUCT-EMPTY-SECTION`, and `CROSS-REFERENCE-MISMATCH` as read-only legacy codes.

Any other field alias or finding code is invalid protocol vocabulary. Report unknown input
vocabulary in substantive runtime content instead of changing the validator report. If it or any
other blocker prevents completion, submit a `[blocking]` question through the controlled
interview path; substantive blocker prose alone does not pause AIDD.

Interview document format is strict. `questions.md` bullets use `- Q1 [blocking|non-blocking] ...`;
`answers.md` bullets must reuse the same question id with `[resolved|partial|deferred]`, for example
`- Q1 [resolved] ...`. Do not put a colon after the marker; `- Q1 [resolved]: ...` is invalid.
Do not use `- Q1: [resolved] ...`; it is invalid. Do not invent `A1`/`A2` answer ids.
If no operator answer is present, write `# Answers\n\n- none\n`; do not create `[resolved]`
answers yourself. Render assumptions or metadata as non-bullet continuation prose.

## Finding-to-fix mapping

For each finding:

1. identify the root cause class:
   - `missing diffs`,
   - `unverifiable claims`,
   - `incomplete summary`,
   - `invalid no-op rationale`,
   - cross-document status drift;
2. patch only the smallest affected section(s) of `implementation-report.md`;
   when a finding says an acceptance criterion is missing, add or repair the dedicated
   `## Acceptance evidence` section and copy every missing acceptance id verbatim. Keep one
   top-level bullet per id; descriptive paraphrases do not satisfy the finding.
3. re-check touched-files entries against observable repository changes and allowed write scope;
   each top-level entry needs a backticked file path plus short intent, while nested bullets may hold
   line-level details. For a rich task attempt, compare against the current task-local baseline/final
   diff rather than the cumulative workspace: remove prerequisite-only claims unless the current
   task changed those paths again, and do not revert successful prior-task changes;
4. re-check verification entries for concrete command/check evidence plus observed outcome
   (`-> pass`, `exit 0`, `exit code 0`, or captured tool summary);
   any pass/fail/success outcome claim without executable/check evidence in the same bullet is still
   invalid. Manual or `CliRunner` checks must cite the executed command/snippet, artifact path, or
   captured assertion result; replace unevidenced `manual inspection -> pass` claims with concrete
   evidence or `not-run: <reason>`. Use one bullet per command/check with this exact shape:
   ``- `command goes here` -> pass (observed summary)`` or
   ``- `command goes here` -> fail (exit code N; observed summary)``.
   Do not preserve mutation-only cleanup bullets such as `rm -rf ... -> pass` as verification
   evidence; keep cleanup prose brief and cite a separate check command such as `find ...`,
   `git status --ignored ...`, or `test ! -e ...` that proves residue is absent.
5. keep repair bounded: if verification still fails after one focused fix attempt, record the exact
   failing command/output and terminal status instead of continuing ad hoc debugging until timeout.
6. read `stage-result.md` and `validator-report.md` as prior evidence and expose current blockers
   in substantive runtime content for AIDD reconciliation.
7. re-check `git status --short --untracked-files=all`; top-level `workitems/...`, stray
   stage/control documents, or unrelated scratch files must be cleaned up or reported as a
   not-clean implementation state.
8. Do not delete, move, reclone, or recreate the prepared repository checkout or setup-owned
   paths listed in `context/workspace-baseline.md`. If the
   prepared checkout, configured stage runner command, or packaged contracts disappear, report the repair
   attempt as `blocked` or `failed` with the exact missing path instead of running `git clone` or
   rebuilding the setup workspace.
9. If the setup-owned workspace ran any test, type, lint, docs, or build command, re-check ignored
   local artifacts with the exact command `git status --ignored --short --untracked-files=all`
   and include that command as its own verification bullet. `git status --short --untracked-files=all`
   is insufficient because it hides ignored residue. Newly created `.venv/`, `.pytest_cache/`,
   `.ruff_cache/`, `.pdm-build/`, `coverage/`, `.coverage*`, build, dist, or dependency-cache
   directories are workspace pollution unless they are required by the selected deliverable or
   removed before terminal output. Do not claim cleanup passed or mark cleanup resolved unless the
   cited evidence explicitly checks `.pytest_cache/`, `.ruff_cache/`, `coverage/`, `.coverage*`,
   `__pycache__/`, build, dist, and dependency-cache residue.

Use concrete repair actions:

- `missing diffs`: remove unsupported touched-files claims or add missing concrete entries that match
  observed current task-local edits; for `SEM-TASK-DIFF-MISMATCH`, exclude prerequisite-only paths
  without reverting prior task results, while aggregate finalization retains ownership of cumulative
  touched-file evidence;
- `incomplete touched-files intent`: rewrite each top-level touched-files bullet in the exact shape
  ``- `path/to/file.ext` - changed <short intent>`` so the path, separator, and intent are on the
  same line;
- `unverifiable claims`: replace vague assertions with concrete command/check outcomes, or mark as
  `not-run: <reason>` explicitly;
- unresolved failing verification: keep the failure visible in `implementation-report.md`
  for AIDD reconciliation; do not claim success while debugging is incomplete;
- `incomplete summary`: rewrite change summary so it maps selected task id -> edits -> outcomes;
- `invalid no-op`: add evidence-backed justification and actionable next step, or convert run from
  no-op to real scoped edits;
- status drift: correct conflicting claims in substantive runtime content and expose blockers
  and next-action evidence; AIDD reconciles validator verdict and stage status.
- downstream-order drift: keep implementation recommendations flow-aware: `review` follows
  `implement`, not directly `qa`; QA is only downstream after a successful review stage.
  AIDD writes workflow next actions.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy only the `implementation-report.md` skeleton headings from `stage-brief.md` or its document contract
  when substantive output is malformed. AIDD repairs generated workflow records.

## Repair rules

1. Preserve valid evidence-backed sections; do not rewrite unaffected parts.
2. Keep any selected task id from `context/task-selection.md`, any local tasklist ids used for
   verification, and provided scope constraints explicit after every edit.
3. Rework touched-files list and verification notes together whenever implementation claims change.
4. Do not claim commands/checks that were not executed in this attempt; if
   `context/verification-output.md` lists authored or scenario verification commands, record each
   command as executed with outcome or explicitly not-run with a reason.
   If a listed command depends on downstream review or QA artifacts that cannot exist until a later
   stage, record it as `not-run: future-stage artifact` instead of running it as an expected failure.
5. If no-op is retained, include justification, evidence, and next action; otherwise no-op is invalid.
   Do not apply no-op rationale to an explicitly selected `verification-only` task: preserve the
   required command outcomes, keep `Touched files` as `- none`, and remove or fail on any
   task-local repository edit.
6. Keep `implementation-report.md` evidence truthful for the current repair attempt; AIDD owns attempt status.
   When the repaired implementation succeeds, keep the next action flow-aware: hand off to
   `review`, not directly to `qa`.
7. Use exact required headings from document contracts; do not rename or qualify headings.
8. Read the repair budget section in `repair-brief.md` before reporting the repair outcome.
9. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed substantive findings; AIDD derives terminal status from post-runtime validation; do not fail solely because no later rerun is available.
10. If AIDD later records `repair-budget-exhausted` after validation, AIDD sets terminal status to `failed`.
11. Do not claim the repair is complete unless required headings, touched files, and verification evidence are mutually consistent.
12. If all listed findings are resolved and no blockers remain, record the repaired evidence in `implementation-report.md`; AIDD determines `succeeded` after validation. Do not treat the previous failed validator report as a new result.
13. Do not create top-level `workitems/...`; canonical stage artifacts are under `.aidd/workitems/...`
    from the repository root.
14. Do not delete, move, reclone, or recreate the prepared repository checkout or setup-owned
    workspace paths; missing checkout/runner/contract paths are blockers, not repair work.

## Repair exit checks

- no edit or verification claim remains without observable evidence,
- every verification bullet with a pass/fail/success claim has the command/check and observed
  outcome on the same bullet,
- unresolved failed verification is explicit instead of hidden by open-ended debugging,
- selected task id, change summary, touched-files list, and verification notes are mutually consistent,
- touched-files entries stay within allowed write scope, match observed edits, and include same-line
  path + intent for every top-level file entry,
- rich task touched-files entries match the current task-local diff, exclude prerequisite-only
  paths, and leave cumulative touched-file evidence to aggregate finalization,
- no top-level `workitems/...` artifacts or unrelated scratch files remain in the deliverable workspace,
- no setup-owned workspace paths were deleted or recreated, and no ignored local
  environment, cache, coverage, build, or dist artifacts are left as unexplained workspace
  pollution; cleanup evidence explicitly covers `.pytest_cache/`, `.ruff_cache/`, `coverage/`,
  `.coverage*`, `__pycache__/`, build, dist, and dependency-cache residue,
- no-op outcomes (if any) include evidence-backed rationale and actionable next step,
- explicit `verification-only` attempts have complete required command evidence, `Touched files`
  equal to `- none`, and no observed task-local repository change,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- no status drift remains between `implementation-report.md`, `validator-report.md`, and `stage-result.md`.
