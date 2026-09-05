# Repair prompt for `implement`

You are rerunning the `implement` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving task alignment,
scope safety, verification truthfulness, and cross-document status consistency.

## Read order (do not skip)

Read `stage-brief.md`, the current `implementation-report.md`, and its
`contracts/documents/implementation-report.md` contract before applying the findings.
1. `validator-report.md` (latest findings, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/implement.md`
4. `contracts/documents/questions.md` and `contracts/documents/answers.md`
5. stage input bundle for this attempt, especially provided optional context such as
   `context/acceptance-criteria.md` and `context/verification-output.md`

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

## Interview context

Read `contracts/documents/questions.md` and `contracts/documents/answers.md` when available.
Use stable QIDs and canonical `- Q1 [blocking] ...` or `- Q1 [non-blocking] ...` question
candidates through the controlled interview path. AIDD merges raw candidates and may normalize
safe presentation differences without changing meaning. Preserve unresolved blocking questions.
Operator answers use the same QID, for example `- Q1 [resolved] ...`; do not create or edit
`answers.md`, invent `A1`/`A2` answer ids, or create `[resolved]` answers yourself. Missing
answers remain an operator checkpoint. Render assumptions as non-bullet continuation prose.

## Authoring boundary

Write only `implementation-report.md` and other runtime-content targets explicitly listed in `stage-brief.md`.
Do not write `stage-result.md` or `validator-report.md`; AIDD owns validation, attempt history,
terminal status, repair references, and downstream next actions. Read those records as evidence.
`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it.
Keep any repair summary and remaining content blockers in `implementation-report.md` using its existing sections.
If a finding concerns an AIDD-owned record, report the inconsistency without editing that record.

Read the repair budget in `repair-brief.md`. On `repair-budget-final-attempt` or
`Rerun allowed after this attempt: no`, still repair the content; do not fail solely because no
later rerun is available. AIDD may record `succeeded` only after canonical validation passes;
`repair-budget-exhausted` with unresolved findings remains `failed`. Do not reset budget or
attempt history. Keep evidence and unresolved questions consistent with the repaired content.

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
5. re-check `git status --short --untracked-files=all`; top-level `workitems/...`, stray
   stage/control documents, or unrelated scratch files must be cleaned up or reported as a
   not-clean implementation state.
6. Do not delete, move, reclone, or recreate the prepared repository checkout or setup-owned
   paths listed in `context/workspace-baseline.md`. If the
   prepared checkout, configured stage runner command, or packaged contracts disappear, report the repair
   attempt as `blocked` or `failed` with the exact missing path instead of running `git clone` or
   rebuilding the setup workspace.
7. If the setup-owned workspace ran any test, type, lint, docs, or build command, re-check ignored
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
- `incomplete summary`: rewrite change summary so it maps selected task id -> edits -> outcomes;
- `invalid no-op`: add evidence-backed justification and actionable next step, or convert run from
  no-op to real scoped edits;

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.

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
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Do not create top-level `workitems/...`; canonical stage artifacts are under `.aidd/workitems/...`
    from the repository root.
8. Do not delete, move, reclone, or recreate the prepared repository checkout or setup-owned
    workspace paths; missing checkout/runner/contract paths are blockers, not repair work.

Keep repair bounded: if verification still fails after one focused fix attempt, record the
exact failing command/output in `implementation-report.md` and stop instead of continuing
ad hoc debugging until timeout. AIDD records the resulting failed validation and stage state.

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

AIDD owns downstream-order drift correction: the immediate next stage after `implement` is
`review`. Preserve content needed for that handoff; do not bypass the planning or
implementation gates by naming a later stage. AIDD never hands off directly to `qa`.
