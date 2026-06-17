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

## Required outputs (always write)

- `implementation-report.md`
- `stage-result.md`
- `validator-report.md`

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## Conditional outputs

- `questions.md` and `answers.md` when blocking clarification is required

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Implementation discipline

1. When `context/task-selection.md` is provided, the selected task id must be explicit in the implementation
   report. If upstream `tasklist.md` decomposes that selected task into local ids such as `T1` or
   `TL-1`, use those local ids to structure touched-file and verification evidence where practical.
2. When `context/allowed-write-scope.md` is provided, it is a hard boundary for touched files.
3. When provided, `context/acceptance-criteria.md` and `context/verification-output.md` define the
   authored live acceptance and verification baseline for the implementation.
4. Change summary must describe what changed, why it changed, and how it maps to the selected task id.
5. Touched-files list must include concrete path + short intent per entry and never claim unobserved edits.
   Treat newly created untracked source files under the allowed write scope as observed workspace
   edits. Include them in the touched-files list alongside tracked diffs; the deliverable is the
   local workspace state, not a tracked-only patch.
6. Verification notes must list actual checks run (or explicitly not run) with observed outcomes.
7. No-op outcomes require explicit evidence-based justification plus next action; otherwise no-op is invalid.
8. Stage/validator status must match observed implementation and verification evidence.
9. Do not use `git stash`, `git reset`, `git checkout --`, or `git restore` in the deliverable
   workspace to run negative checks or revert files. Use a disposable copy for destructive
   experiments, or mark the check `not-run: <reason>`.
   Do not delete, move, reclone, or recreate the prepared repository checkout or any live harness
   run directory such as `source/`, `build/`, `install-home/`, `uv-cache/`, or `target/`.
   If the prepared checkout, installed `aidd` command, or packaged contracts disappear, stop and
   report the stage as `blocked` or `failed` with the exact missing path; do not try to recover by
   running `git clone` or rebuilding the harness workspace inside the stage.
10. Do not leave lockfiles, dependency manifests, generated resolver output, or project config
   changed unless the selected task explicitly requires dependency/config updates. If such files
   change incidentally, stop and report the out-of-scope change instead of silently treating it as
   part of the implementation.
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
    Also inspect ignored local artifacts when feasible, for example with
    `git status --ignored --short --untracked-files=all`; newly created `.venv/`, `.pytest_cache/`,
    `.ruff_cache/`, `.pdm-build/`, `coverage/`, `.coverage*`, build, dist, or dependency-cache directories are
    workspace pollution unless they are part of the selected deliverable or are removed before
    terminal output. After running verification that can create cache or coverage residue, either
    remove those files or report the implementation as not clean; do not claim cleanup passed unless
    the cited command actually checks `.pytest_cache/`, `.ruff_cache/`, `coverage/`, `.coverage*`,
    `__pycache__/`, build, dist, and dependency-cache residue.
13. When the implementation changes a shared public-surface mechanism such as a CLI decorator,
    parser/helper, router/error boundary, schema transform helper, or public API adapter, inspect
    the sibling commands, routes, generated outputs, or documented public surfaces that reuse that
    mechanism. Record focused blast-radius evidence for help/usage text, API compatibility, and
    docs consistency, or explicitly mark the unchecked sibling surface as a residual risk.

## Execution instructions

1. Read all required inputs, existing optional context, and `contracts/stages/implement.md` before drafting outputs.
2. Confirm selected task id, acceptance criteria, scope limits, verification commands, and
   repository baseline when those inputs are provided before editing outputs.
3. Produce `implementation-report.md` with selected task id, scoped change summary, touched-files list,
   verification notes, and residual risk/deferred notes when applicable.
4. Before and after editing, inspect the repository change set with `git status --short --untracked-files=all` and
   `git diff --name-only` or an equivalent project-native command when Git is unavailable.
   List every tracked or untracked changed deliverable file in `implementation-report.md`, excluding
   AIDD workspace/config artifacts. If a changed file is harness-owned or generated by setup,
   explain why it is excluded.
5. Keep touched-files entries bounded to allowed scope and aligned with observable repository changes.
   Use top-level bullets for each file, with a backticked path plus short intent on the same line;
   copy this exact shape for every file: ``- `path/to/file.ext` - changed <short intent>``.
   Do not write a top-level bullet that only names
   a path, and do not rely on nested bullets to supply the file-level intent. Put line-level
   details under that file entry.
   If `git status --short` or equivalent repository evidence shows untracked files created for the
   task, list and describe those files rather than relying only on `git diff --name-only`.
   Before declaring `succeeded`, self-check the `Touched files` section: every top-level file
   bullet must have a backticked path, a separator (`-`, `:`, or `->`), and a short intent on the
   same line.
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
   Manual or `CliRunner` checks must cite the executed command/snippet, artifact path, or captured
   assertion result; do not write `manual inspection -> pass` without evidence.
   When `context/verification-output.md` lists authored or scenario verification commands, run those
   commands after the implementation or explicitly mark each skipped command as not-run with a reason.
   For skipped checks, write `not-run: <reason>` in the verification note.
7. Write or update `implementation-report.md`, `stage-result.md`, and `validator-report.md` before
   optional broad-suite verification or exploratory debugging. A truthful failed verification report
   is better than timing out without stage artifacts.
8. If required inputs are missing or provided scope/task constraints conflict, raise a `[blocking]`
   question instead of inventing assumptions.
9. Update `validator-report.md` and `stage-result.md` so readiness, blockers, and next actions remain
   consistent with implementation evidence.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- selected task id is explicit and traced to implementation summary when provided,
- edits stay within allowed write scope when provided,
- touched-files list is concrete and evidence-backed, with path + same-line intent for every
  top-level file entry,
- verification notes are factual and command-specific,
- every verification bullet with a pass/fail/success claim has the command/check and observed
  outcome on the same bullet,
- failed verification is reported promptly instead of hidden behind open-ended debugging,
- shared public-surface helper changes include focused blast-radius evidence for sibling
  commands/routes/generated outputs or explicit residual risk,
- no-op handling (if any) includes justification, evidence, and next action,
- no top-level `workitems/...` artifacts, stray stage/control documents, or scratch files are left
  in the deliverable workspace,
- no live harness checkout/install directories were deleted or recreated, and no ignored local
  environment, cache, coverage, build, or dist artifacts are left as unexplained workspace
  pollution; a cleanup claim is valid only when its evidence explicitly covers `.pytest_cache/`,
  `.ruff_cache/`, `coverage/`, `.coverage*`, `__pycache__/`, build, dist, and dependency-cache residue,
- `implementation-report.md`, `validator-report.md`, and `stage-result.md` are consistent.
