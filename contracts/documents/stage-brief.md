# Document Contract: `stage-brief.md`

## Purpose

AIDD prepares this runtime-facing Markdown brief before each attempt. It names the stage,
substantive content to write, prepared inputs, and document ownership without granting the
runtime authority over workflow records.

## Required sections

Use these top-level headings in order:

- `Stage`
- `Purpose`
- `Expected input bundle`
- `Runtime write targets`
- `AIDD-generated records`
- `Interview/control documents`
- `Published documents`
- `Workspace path discipline`

`Declared project set` appears after `Expected input bundle` when multiple project roots are
declared. `Required output skeletons` may follow path discipline when runtime content has a
known scaffold. Skeleton headings are nested beneath that section, not additional top-level
stage-brief fields.

## Field notes

- `Stage` names one lowercase canonical stage id.
- `Purpose` describes the stage outcome without committing downstream work.
- `Expected input bundle` lists prepared input documents as workspace-relative paths.
- `Runtime write targets` lists only substantive runtime-authored documents. These are the
  only document-completion targets; do not include lifecycle records or operator answers.
- `AIDD-generated records` lists lifecycle and validation documents for read-only context.
  AIDD writes `stage-result.md` and `validator-report.md`; runtimes never repair their text.
- `Interview/control documents` lists controlled question/intervention inputs and read-only
  answers or repair evidence. Use the declared interview path for raw question candidates;
  AIDD merges them by stable QID and preserves operator answers.
- `Published documents` lists the complete canonical source set that AIDD publishes into the
  stage `output/` directory after validation. Publication does not grant authoring permission
  for AIDD-generated records.
- `Workspace path discipline` states that `workitems/...` resolves under the configured
  `.aidd/` workspace, not under the repository root.
- `Declared project set` names the context path, project ids, and roots. Runtime content must
  preserve those boundaries. AIDD authors the `Project-set evidence` section in `stage-result.md`.
- `Required output skeletons` contains only runtime-content scaffolds. A scaffold is prompt
  input; placeholders must be replaced before the output is validated.

## Authoring rules

- AIDD owns this brief; runtime and operator attempts do not edit it in place.
- Keep document paths in backticks and workspace-relative form, one document per bullet.
- Use `- none` for an empty AIDD-generated or interview/control document list.
- Do not include duplicate compatibility output inventories or writable skeletons for
  `stage-result.md`, `validator-report.md`, `repair-brief.md`, or `answers.md`.
- Preserve unresolved questions and existing answers; never invent an operator decision.
- Keep the brief Markdown-first without embedded model-authored JSON schemas.

## Validation cues

- stage and purpose match the stage contract;
- input, runtime-content, control, and published paths preserve their distinct ownership;
- project-set evidence remains AIDD-authored;
- skeletons cannot direct the runtime to overwrite canonical workflow records.
