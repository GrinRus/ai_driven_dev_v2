# Document Contracts

## 1. Why document contracts exist

AIDD v2 is intentionally **document-first**.

The runtime works with Markdown files because they are:

- readable,
- reviewable in Git,
- easy to inspect after failures,
- portable across runtimes,
- easier for humans to repair or continue from.

The model is not asked to emit canonical JSON as the main stage output.

## 2. Contract model

A document contract defines:

- the path pattern,
- the document purpose,
- required frontmatter,
- required sections,
- required links or references,
- cross-document dependencies,
- validation rules,
- ownership,
- and repair behavior.

Contracts live under `contracts/` as Markdown.

## 3. Runtime-facing vs system-facing artifacts

### Runtime-facing artifacts

Markdown only.

Examples:

- `prd.md`
- `research.md`
- `plan.md`
- `tasklist.md`
- `review-report.md`
- `qa-report.md`
- `questions.md`
- `answers.md`
- `stage-result.md`

### System-facing artifacts

JSON / JSONL / text allowed.

Examples:

- raw runtime logs,
- normalized event streams,
- eval metadata,
- replay indexes,
- machine-readable run summaries.

## 4. Recommended Markdown metadata pattern

Frontmatter is allowed and recommended for stable metadata.

Example:

```md
---
doc_kind: aidd.plan
work_item: TICKET-123
stage: plan
status: draft
run_id: run-2026-04-21-001
---
```

Frontmatter is not enough by itself. Validators must also check the document body.

## 5. Required document elements

Every contract should be explicit about:

- required headings,
- required tables or checklists when needed,
- required references to upstream docs,
- and required decisions or evidence.

Example for `plan.md`:

- goals
- scope boundaries
- implementation strategy
- risks
- dependencies
- rollout / validation approach
- open questions

## 6. Validation layers

### 6.1 Structural validation

Verifies:

- file existence,
- frontmatter presence,
- required headings,
- required subsections,
- obvious malformed structure.

### 6.2 Semantic validation

Verifies whether the content actually answers the stage's purpose.

Example:
a plan with headings but no real implementation sequencing should fail semantic validation.

### 6.3 Cross-document validation

Verifies consistency with upstream artifacts.

Example:
`tasklist.md` should map back to `plan.md`.
`qa-report.md` should reference implemented behavior and test evidence.

### 6.4 Environment validation

Verifies runtime evidence such as test output, command logs, or generated artifacts.

## 7. Stage result document

Every stage must write a `stage-result.md` document.

This document records:

- whether the stage passed,
- which output documents were produced,
- validator status,
- open blockers,
- open questions,
- next actions,
- links to logs and reports.

It is the durable checkpoint for workflow progression.

## 8. Question and answer documents

When a stage needs clarification, the system should write:

- `questions.md`
- `answers.md` once the user replies

These documents must be durable because:
- the run might pause,
- the user might answer later,
- the reasoning behind later decisions should remain visible.

## 9. Self-repair flow

When validation fails:

1. archive the failed attempt snapshot,
2. write a repair brief in Markdown,
3. rerun the stage against the same target documents,
4. validate again,
5. repeat within the repair budget.

The repair brief should explain:

- which contract checks failed,
- what is missing,
- what must be corrected,
- which upstream documents matter.

## 10. Why not JSON schemas for stage IO

JSON schemas are useful for machine-owned telemetry, but they are the wrong primary contract for runtime-authored stage outputs because they:

- push formatting fragility into the runtime loop,
- reduce human readability,
- encourage "schema compliance theater" instead of useful content,
- make partial human intervention less natural.

The right place for strictness is the validator layer, not a JSON-output demand placed on the runtime.

## 11. Contract authoring guidance

A contract should be strict enough to be useful, but not so rigid that it only rewards templated filler.

Good contracts focus on:

- required decisions,
- required evidence,
- required cross-links,
- required clarity for the next stage.

## 12. Summary

In AIDD v2:

- stages operate on Markdown,
- validators enforce structure and meaning,
- repair loops recover from failures,
- and durable documents remain the workflow source of truth.
