# Run prompt for `implement`

## Stage objective

Execute the selected `tasklist` item inside the allowed write scope, produce a truthful
implementation summary, and capture verification evidence that is auditable.

The stage is complete only when reported edits, verification outcomes, and stage status are
consistent across `implementation-report.md`, `validator-report.md`, and `stage-result.md`.

## Inputs to read first

- required:
  - `../tasklist/output/tasklist.md`
  - `../tasklist/output/stage-result.md`
  - `../tasklist/output/validator-report.md`
  - `context/repository-state.md`
- optional context when available:
  - `context/task-selection.md`
  - `context/allowed-write-scope.md`
  - `context/acceptance-criteria.md`
  - `context/verification-output.md`
  - `context/constraints.md`
  - `context/previous-decisions.md`
  - `context/runtime-capabilities.md`
- contract of record:
  - `contracts/stages/implement.md`

## Runtime-authored outputs (always write)

- `implementation-report.md`
## AIDD-generated records (do not write)

- `validator-report.md` is written canonically by AIDD after structural, semantic, and
  cross-document validation.
- `stage-result.md` is written canonically by AIDD from lifecycle state and validation outcome.
- Runtime content must expose implementation evidence for reconciliation but must not create or edit
  either terminal record as a completion target.

## Conditional outputs

- `questions.md` and `answers.md` when blocking clarification is required

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

## Implementation discipline

1. When `context/task-selection.md` is provided, the selected task id must be explicit in the implementation
   report. If upstream `tasklist.md` decomposes that selected task into local ids such as `T1` or
   `TL-1`, use those local ids to structure touched-file and verification evidence where practical.
   Treat the selected task card's `Outcome`, `In scope`, and every `<task-id>-AC<n>` item
   as hard implementation boundaries. Cite every acceptance id in the implementation report
   with implementation or verification evidence. Before declaring the task complete, add a
   dedicated `## Acceptance evidence` section with exactly one top-level bullet per acceptance
   criterion, copying each id verbatim (for example `- T4-AC1: ...`). A descriptive claim without
   the exact authored id is incomplete, even when the command passed.
2. When `context/allowed-write-scope.md` is provided, it is a hard boundary for touched files.
3. When provided, `context/acceptance-criteria.md` and `context/verification-output.md` define the
   authored acceptance and verification baseline for the implementation.
4. Execute exactly the selected task card from `context/task-selection.md` as one bounded
   implementation unit, then stop. Do not implement, edit tests for, or otherwise modify files
   owned only by a later task card, even when those paths are present in the global allowed write
   scope. Later cards must run in their own attempts. If a later card's existing test is useful,
   run it read-only when possible; never pre-implement its deliverable or advance to the next
   dependency-ready card in the same attempt.
5. Change summary must describe what changed, why it changed, and how it maps to the selected task id.
6. Touched-files list must include concrete path + short intent per entry and never claim unobserved edits.
   For a rich task attempt, report only the current task-local repository diff between that task's
   baseline and final snapshot. Exclude prerequisite changes unless the current task changes them again.
   Do not use the cumulative workspace or cumulative `git diff`
   as the touched-files list. You may mention prerequisite state in `Summary` or `Risks`; aggregate
   finalization owns cumulative touched-file evidence across successful tasks. Include
   newly created untracked source files from the current task under the allowed write scope as observed
   task-local edits and include them alongside that task's tracked diffs: the deliverable is the
   current task-local workspace state, not a tracked-only patch.
   For explicit `verification-only` selection, instead require exactly `- none` and stop with a
   failure if the task changed any repository file.
6. Verification notes must list actual checks run (or explicitly not run) with observed outcomes.
   Every executable command bullet must include a terminal outcome on the same line. Prefer the
   literal markers `-> pass`, `-> fail`, or `-> not-run: <reason>`; an explicit negative/clean
   result such as `-> no task-local cache or coverage residue` is also valid when it directly
   describes the command's observed result. Do not use vague outcome prose such as `looks good`
   or `completed successfully` without a concrete marker or exit code.
   When an authored verification source already includes the command and its terminal outcome,
   preserve that complete text byte-for-byte inside one Markdown code span, including the outcome
   marker (for example, `` `uv run --frozen pytest -q tests/test_responses.py -> pass` ``). Do not
   split it into `` `command` -> pass ``, move the marker outside the code span, normalize flags or
   paths, or replace the authored command with a count-only summary. Additional observed detail may
   follow the closed span, but the exact authored command/result text must remain intact.
   Treat `Verification` as a command ledger, not a narrative status log: every top-level or nested
   bullet that says a check `passed`, `failed`, `succeeded`, `errored`, or otherwise reports an
   outcome must include that check's executable command, assertion, artifact path, or captured
   tool output on the same bullet. Do not add standalone caveats such as `neither command failed`
   or `warnings did not fail` to `Verification`; put resolver/tool warnings and other explanatory
   context under `Risks` or `Follow-up`, where they do not masquerade as a check result. If a caveat
   must remain in `Verification`, pair it with the exact command and its terminal marker on that
   same evidence item. A command-free outcome claim remains invalid even when another bullet nearby
   contains the command it refers to.
7. No-op outcomes require explicit evidence-based justification plus next action; otherwise no-op is invalid.
   The sole exception is a rich task whose system-owned selection explicitly says
   `Execution mode: verification-only`: execute and preserve its required checks, report
   `- none` in `Touched files`, and do not make repository edits. This is not a no-op.
8. Stage/validator status must match observed implementation and verification evidence.
9. Do not use `git stash`, `git reset`, `git checkout --`, or `git restore` in the deliverable
   workspace to run negative checks or revert files. Use a disposable copy for destructive
   experiments, or mark the check `not-run: <reason>`.
   Do not delete, move, reclone, or recreate the prepared repository checkout or setup-owned
   paths listed in `context/workspace-baseline.md`.
   If the prepared checkout, configured stage runner command, or packaged contracts disappear, stop and
   report the stage as `blocked` or `failed` with the exact missing path; do not try to recover by
   running `git clone` or rebuilding the setup workspace inside the stage.
10. Do not leave lockfiles, dependency manifests, generated resolver output, or project config
   changed unless the selected task explicitly requires dependency/config updates. If such files
   change incidentally, stop and report the out-of-scope change instead of silently treating it as
   part of the implementation.
   Before handoff, inspect `git diff --name-only` and restore tool-generated `uv.lock` changes;
   dependency or lockfile updates are allowed only when the selected task explicitly puts them in
   scope and the report names that decision.
   Before removing or renaming a shared helper, symbol, or public function, search all tracked
   consumers (for example `rg -n 'symbol_name' .`) and either retain a compatibility symbol or
   migrate every consumer with focused coverage. A focused suite alone is insufficient: run the
   full target test collection, including unchanged consumers, for example
   `uv run pytest --collect-only -q`, and resolve any import or collection failure before handoff.
11. Keep debugging bounded. Prefer authored verification commands and existing regression tests.
    If a check fails, make at most one focused fix attempt for that failure class, then rerun the
    narrow check. If it still fails or the root cause is unclear, stop editing and write the
    required output documents with the exact failing command/output and `stage-result.md` status
    `failed` or `blocked` as appropriate. Do not create an open-ended series of ad hoc debug
    scripts, and do not spend the stage trying to make optional broad checks pass before recording
    the required implementation report.
12. Do not create top-level `workitems/...`. Canonical stage/control artifacts are under
    `.aidd/workitems/...` from the repository root. If `git status --short --untracked-files=all`
    shows top-level `workitems/...`, stray stage documents, or scratch files unrelated to the
    selected task, clean them up or report the implementation as not clean.
    If this setup-owned workspace runs any test, type, lint, docs, or build command, verification
    notes must include the exact command
    `git status --ignored --short --untracked-files=all` with an observed outcome.
    `git status --short --untracked-files=all` is insufficient because it hides ignored residue.
    Newly created `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pdm-build/`, `coverage/`,
    `.coverage*`, build, dist, or dependency-cache directories are workspace pollution unless
    they are part of the selected deliverable or are removed before terminal output. After running
    verification that can create cache or coverage residue, either remove those files or report
    the implementation as not clean; do not claim cleanup passed unless the cited command actually
    checks `.pytest_cache/`, `.ruff_cache/`, `coverage/`, `.coverage*`, `__pycache__/`, build, dist,
    and dependency-cache residue.
13. When the implementation changes a shared public-surface mechanism such as a CLI decorator,
    parser/helper, router/error boundary, schema transform helper, or public API adapter, inspect
    the sibling commands, routes, generated outputs, or documented public surfaces that reuse that
    mechanism. Record focused blast-radius evidence for help/usage text, API compatibility, and
    docs consistency, or explicitly mark the unchecked sibling surface as a residual risk.
14. In JavaScript or TypeScript packages, do not claim a new helper/module is internal solely
    because it is under `src/` or has no direct documentation. Inspect `package.json` `exports`,
    wildcard subpath exports such as `./utils/*`, generated declaration outputs, and existing
    public import conventions. If the new path can be imported through the package boundary,
    treat it as public API surface and record compatibility/test evidence or choose a private
    location that is not exported.

15. Async test resource cleanup
   - When a regression test interrupts an async generator or iterator because a disconnect,
     cancellation, or send error stops iteration, close it explicitly with `aclosing` or an
     equivalent deterministic close protocol before returning or raising.
   - Run the authored regression test on every configured AnyIO backend, including asyncio and
     Trio. Treat `ResourceWarning`, `PytestUnraisableExceptionWarning`, or an unclosed async
     resource as verification failures; do not suppress the warning or report a green test.
   - Accept an interrupted-generator fixture only when its implementation report names the
     explicit cleanup mechanism and records clean backend results. Reject or flag the exact
     unclosed-generator pattern even when the assertion itself passes.
   - Keep direct-ASGI coverage rationale and hard-disconnect limitations explicit, and keep the
     cleanup change bounded to the regression test rather than weakening production behavior.

## Execution instructions

1. Read all required inputs, existing optional context, and `contracts/stages/implement.md` before drafting outputs.
2. Confirm selected task id, acceptance criteria, scope limits, verification commands, and
   repository baseline when those inputs are provided before editing outputs.
3. Produce `implementation-report.md` with selected task id, scoped change summary, touched-files list,
   verification notes, an `Acceptance evidence` entry for every authored acceptance id, and residual
   risk/deferred notes when applicable.
4. Before and after editing, inspect the repository change set with `git status --short --untracked-files=all` and
   `git diff --name-only` or an equivalent project-native command when Git is unavailable.
   For a rich task attempt, use these commands for situational awareness but list only paths changed
   since the current task's own baseline. Do not claim prerequisite-only changes merely because
   they remain visible in the cumulative workspace. For a generic one-shot implementation without
   a rich task ledger, list every tracked or untracked changed deliverable file, excluding AIDD
   workspace/config artifacts. If a changed file is harness-owned or generated by setup, explain
   why it is excluded.
5. Keep touched-files entries bounded to allowed scope and aligned with observable repository changes.
   Use top-level bullets for each file, with a backticked path plus short intent on the same line;
   copy this exact shape for every file: ``- `path/to/file.ext` - changed <short intent>``.
   Do not write a top-level bullet that only names
   a path, and do not rely on nested bullets to supply the file-level intent. Put line-level
   details under that file entry.
   If `git status --short` or equivalent repository evidence shows untracked files created for the
   current task, list and describe those files rather than relying only on `git diff --name-only`.
   Before declaring `succeeded`, self-check the `Touched files` section: every top-level file
   bullet must have a backticked path, a separator (`-`, `:`, or `->`), and a short intent on the
   same line.
   For explicit `verification-only` selection, self-check instead that the section is exactly
   `- none` and that repository evidence shows no task-local change.
6. Record verification using concrete commands/checks and outcomes; include observed results such as
   `-> pass`, `exit code 0`, or the captured tool summary on the same bullet. Do not imply execution that did
   not happen.
   Use one bullet per command/check and copy this shape for executed checks:
   ``- `command goes here` -> pass (observed summary)`` or
   ``- `command goes here` -> fail (exit code N; observed summary)``.
   Do not write grouped verification prose where the command appears in one sentence and the
   outcome appears only in another bullet or paragraph.
   A verification note with any pass/fail/success outcome claim is invalid unless the same bullet
   includes executable/check evidence: a shell command in backticks, a test or code snippet path, an
   artifact path, or a captured assertion/tool summary.
   Complete shell compound checks such as ``if <check>; then exit 1; else exit 0; fi`` are allowed
   when the backticked command contains the concrete check and the same bullet records its outcome.
   A command-substitution assignment may precede that check, for example
   ``found=$(find ...); if test -n "$found"; then exit 1; fi``; a concrete trailing check may
   follow the closed compound in the same backticked command list.
   Manual or `CliRunner` checks must cite the executed command/snippet, artifact path, or captured
   assertion result; do not write `manual inspection -> pass` without evidence.
   Do not list mutation-only cleanup commands such as `rm -rf ...` as verification bullets with
   `-> pass`; if cleanup is needed, describe the cleanup briefly and add a separate check command
   such as `find ...`, `git status --ignored ...`, or `test ! -e ...` proving residue is absent.
   When `context/verification-output.md` lists authored or scenario verification commands, run those
   commands after the implementation or explicitly mark each skipped command as not-run with a reason.
   If an authored verification command depends on downstream review or QA artifacts that cannot exist
   until a later stage, record it as `not-run: future-stage artifact` during `implement` rather than
   executing it as an expected failure.
   For skipped checks, write `not-run: <reason>` in the verification note.
7. Write or update `implementation-report.md` and expose its evidence before optional broad-suite
   verification or exploratory debugging. A truthful failed verification report is better than
   timing out without stage artifacts; AIDD owns the canonical terminal records.
8. If required inputs are missing or provided scope/task constraints conflict, raise a `[blocking]`
   question instead of inventing assumptions.
9. Leave canonical `validator-report.md` and `stage-result.md` generation to AIDD; keep
   implementation evidence, blockers, and next-action recommendations truthful for reconciliation.
   When implementation and validation evidence support success, `stage-result.md` `Next actions`
   must point to `review` as the immediate downstream stage. Do not tell the operator to proceed
   directly to `qa`; QA can only run after the canonical `review` stage has completed successfully.

## Common output skeleton discipline

- Do not write `stage-result.md` or `validator-report.md`; AIDD owns their canonical skeletons and
  post-runtime publication.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep implementation evidence, questions, and blockers truthful; AIDD reconciles status, verdict,
  and next actions into canonical records.
- Keep `stage-result.md` next-action copy flow-aware: `implement` hands off to `review`, never
  directly to `qa`.

## Completion checklist

- selected task id is explicit and traced to implementation summary when provided,
- `Acceptance evidence` contains one top-level entry for every authored acceptance id, with each id
  copied verbatim and paired with observable implementation or verification evidence,
- edits stay within allowed write scope when provided,
- touched-files list is concrete and evidence-backed, with path + same-line intent for every
  top-level file entry,
- for a rich task attempt, touched-files entries match only the current task-local diff, exclude
  prerequisite-only paths, and leave cumulative touched-file evidence to aggregate finalization,
- verification notes are factual and command-specific,
- every verification bullet with a pass/fail/success claim has the command/check and observed
  outcome on the same bullet,
- failed verification is reported promptly instead of hidden behind open-ended debugging,
- shared public-surface helper changes include focused blast-radius evidence for sibling
  commands/routes/generated outputs or explicit residual risk,
- JavaScript/TypeScript helper additions that may sit under package `exports` include export-map
  evidence before they are described as internal,
- no-op handling (if any) includes justification, evidence, and next action,
- no top-level `workitems/...` artifacts, stray stage/control documents, or scratch files are left
  in the deliverable workspace,
- no setup-owned workspace paths were deleted or recreated, and no ignored local
  environment, cache, coverage, build, or dist artifacts are left as unexplained workspace
  pollution; a cleanup claim is valid only when its evidence explicitly covers `.pytest_cache/`,
  `.ruff_cache/`, `coverage/`, `.coverage*`, `__pycache__/`, build, dist, and dependency-cache residue,
- `implementation-report.md`, `validator-report.md`, and `stage-result.md` are consistent.
