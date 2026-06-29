# Run prompt for `research`

## Stage objective

Build a reviewable `research` package that captures evidence-backed context for planning decisions,
while making uncertainty and follow-up risks explicit.

The stage is complete only when material findings are traceable to citations and unresolved
uncertainty is visible.

## Inputs to read first

- required:
  - `../idea/output/idea-brief.md`
  - `../idea/output/stage-result.md`
  - `context/repository-state.md`
- optional context when available:
  - `context/business-context.md`
  - `context/constraints.md`
  - `context/previous-decisions.md`
- contract of record:
  - `contracts/stages/research.md`

## Required outputs (always write)

- `research-notes.md`
  - include sections required by `contracts/documents/research-notes.md`:
    - `Scope`
    - `Sources`
    - `Findings`
    - `Trade-offs`
    - `Evidence trace`
    - `Open questions`
- `stage-result.md`
- `validator-report.md`

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

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

## Citation and uncertainty discipline

1. Every material claim in `Findings` must reference citation ids declared in `Sources`.
2. `Sources` entries must include enough locator detail to revisit evidence (URL/path/reference).
3. `Evidence trace` must map major findings or recommendations to supporting citation ids.
4. Uncertain or weakly supported points must be explicit in `Trade-offs` or `Open questions`.
5. Time-sensitive evidence must include freshness context (access date or stale-risk note).

## Scratch artifact discipline

- Keep every local probe bounded by construction. Do not run open-ended servers,
  infinite streaming generators, watchers, or repro scripts that can only stop via the
  external per-stage timeout. Use a finite iteration count, an in-script timeout
  such as `anyio.fail_after(...)`, or `subprocess.run(..., timeout=...)`; if the
  behavior cannot be bounded safely, record the probe as `not-run: <reason>` and cite
  static evidence instead.
- If you run temporary reproduction scripts or probes, keep them outside the repository or remove
  them before completing the stage.
- Do not leave scratch files directly under `.aidd/`, such as `.aidd/research_repro.py`.
  Preserve useful evidence by citing commands, outputs, logs, or canonical Markdown artifacts instead.
- If research commands run tests, import modules, or execute repro snippets inside the target
  checkout, inspect ignored verification residue before completing the stage, for example with
  `git status --ignored --short --untracked-files=all`. Newly created `.pytest_cache/`,
  `.ruff_cache/`, `coverage/`, `.coverage*`, `__pycache__/`, build, dist, or dependency-cache artifacts are
  workspace pollution unless they are selected research evidence and explicitly justified. Prefer
  citing command output in `research-notes.md`, then remove generated residue before terminal
  output; do not claim the workspace is clean unless the cited evidence checks these residue
  classes.
- Canonical stage documents live under `.aidd/workitems/...` from the repository root. Do not create
  top-level `workitems/...`.

## Execution instructions

1. Read required inputs and `contracts/stages/research.md` before drafting outputs.
2. Draft `research-notes.md` with complete required sections and stable citation ids (`[S1]`, `[S2]`, ...).
3. Link each material finding to evidence; avoid unsupported absolute statements.
4. If constraints, target repository boundaries, or research goals are ambiguous, write decisive
   questions with stable ids and `[blocking]` / `[non-blocking]` markers.
5. Update `validator-report.md` so findings and verdict match citation coverage and uncertainty state.
6. Update `stage-result.md` so status, blockers, and next actions are consistent with validator and
   question artifacts.
7. If a critical decision is still unclear, raise a question instead of inventing an answer.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- required outputs exist and are Markdown,
- material findings reference citation ids that exist in `Sources`,
- `Evidence trace` covers major findings/recommendations,
- temporary research probes are removed or cited as evidence without stray scratch files,
- ignored verification residue from research commands is absent, removed, or explicitly reported as
  workspace pollution instead of hidden behind a clean stage status,
- unresolved uncertainty is explicit and not masked as fact,
- unresolved `[blocking]` questions prevent `succeeded`.
