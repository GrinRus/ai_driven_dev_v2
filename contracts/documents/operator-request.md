# Document Contract: `operator-request.md`

## Purpose

Capture an operator-authored, stage-scoped intervention request that becomes durable AIDD input for a new attempt.

`operator-request.md` is AIDD/operator-owned input. Runtime providers may read it and act on it, but it is not a model-authored stage output and must not be rewritten by the runtime.

## Required sections

- `Request`
- `Target stage`
- `Target documents`
- `Constraints`
- `Created by`

## Field notes

- `Request`
  - Must contain the operator's requested correction, additional analysis, or scoped document change.
  - Must not be empty.
- `Target stage`
  - Must name exactly one canonical stage id.
- `Target documents`
  - Must list zero or more workspace-relative current-stage Markdown documents.
  - Must not point outside the selected stage scope.
- `Constraints`
  - Must preserve document-first execution, existing valid sections, and stage scope.
  - Must state that `repair-brief.md` is read-only when present.
- `Created by`
  - Must identify the operator surface and creation timestamp in UTC.

## Authoring rules

- Only AIDD UI, CLI, or another operator integration writes this document.
- Runtime/model attempts read this document as input only.
- Use workspace-relative paths for target document references.
- Keep the request auditable and bounded to one stage.
- Do not use this document as a chat transcript or persistent conversation state.

## Validation cues

- the required heading set is present exactly once,
- request text is non-empty,
- target documents are Markdown files inside the selected stage scope,
- created metadata is present,
- constraints do not authorize downstream cascade reruns.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
