# Run prompt for `research`

## Goal

Collect relevant technical and product context before a plan is written.

## Inputs to read first

- `../idea/output/idea-brief.md`
- `../idea/output/stage-result.md`
- `context/repository-state.md`
- optional context when available: business context, constraints, previous decisions
- stage contract: `contracts/stages/research.md`

## Required outputs

- `research-notes.md`
- `stage-result.md`
- `validator-report.md`

## Instructions

1. Read the required and optional stage inputs before writing outputs.
2. Write `research-notes.md` with complete sections required by the document contract, including `Evidence trace`.
3. Use stable citation ids in `Sources` (for example `[S1]`) and reference those ids from `Findings` for material claims.
4. Ensure `Evidence trace` maps major findings or recommendations to citation ids.
5. Record unresolved uncertainty explicitly in `Trade-offs` or `Open questions`; do not present uncertain claims as facts.
6. Mark time-sensitive evidence with freshness context (access date or stale-risk note) when findings depend on it.
7. If target repositories, constraints, or research goals are ambiguous, write decisive questions with stable ids and `[blocking]`/`[non-blocking]` markers.
8. Write or update `stage-result.md` and `validator-report.md` so status and evidence references are consistent.
9. If a critical decision remains unclear after available inputs are exhausted, raise a question instead of inventing an answer.

## Completion checklist

- all required output files exist and are Markdown,
- material findings reference citation ids that exist in `Sources`,
- `Evidence trace` covers major findings or recommendations,
- unresolved uncertainty is explicit (not implicit),
- question markers and stage status are consistent (`[blocking]` unresolved => no `succeeded`).
