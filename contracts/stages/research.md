# Stage Contract: `research`

## Purpose

Collect relevant technical and product context before a plan is written.

## Primary output

Required outputs for every `research` attempt:

- `research-notes.md`
- `stage-result.md`
- `validator-report.md`

Conditional outputs:

- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `../idea/output/idea-brief.md`
- `../idea/output/stage-result.md`
- `context/repository-state.md`

## Optional context inputs

- `context/business-context.md`
- `context/constraints.md`
- `context/previous-decisions.md`

Optional context documents may enrich research quality, but their absence must not block a `research` run.

## Research output expectations

- `research-notes.md` must include the required stage sections, including an explicit `Evidence trace` section.
- `Sources` must contain traceable citation ids (for example `[S1]`, `[S2]`) with enough metadata to re-open the source.
- `Findings` must reference supporting citation ids for claims that affect scope, feasibility, or risk.
- `Evidence trace` must map major findings or decisions to supporting citation ids.
- `stage-result.md` and `validator-report.md` must stay consistent with the documented citation coverage.

## Validation focus

Validators for `research` should check:

- required output existence and required heading coverage for `research-notes.md`, `stage-result.md`, and `validator-report.md`,
- source grounding:
  - material findings and recommendations must reference citation ids defined in `Sources`,
  - evidence trace links must resolve to declared citation ids,
  - unsupported claims must fail validation,
- uncertainty notes:
  - unresolved uncertainty must be explicit in `Trade-offs` or `Open questions`,
  - findings presented as certain must not hide missing or weak evidence,
- stale-fact handling:
  - time-sensitive sources must include an access date or freshness note,
  - findings that depend on possibly stale evidence must include a stale-risk note and follow-up action,
- cross-document consistency between citation coverage in `research-notes.md`, findings in `validator-report.md`, and terminal status in `stage-result.md`.

## Interview policy

optional when source selection or evaluation scope is unclear

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Prompt pack

- `prompt-packs/stages/research/system.md`
- `prompt-packs/stages/research/run.md`
- `prompt-packs/stages/research/repair.md`
- `prompt-packs/stages/research/interview.md`

## Exit evidence

A `research` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
