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

## Citation and uncertainty discipline

1. Every material claim in `Findings` must reference citation ids declared in `Sources`.
2. `Sources` entries must include enough locator detail to revisit evidence (URL/path/reference).
3. `Evidence trace` must map major findings or recommendations to supporting citation ids.
4. Uncertain or weakly supported points must be explicit in `Trade-offs` or `Open questions`.
5. Time-sensitive evidence must include freshness context (access date or stale-risk note).

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

## Completion checklist

- required outputs exist and are Markdown,
- material findings reference citation ids that exist in `Sources`,
- `Evidence trace` covers major findings/recommendations,
- unresolved uncertainty is explicit and not masked as fact,
- unresolved `[blocking]` questions prevent `succeeded`.
