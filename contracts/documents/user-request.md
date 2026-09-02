# Document Contract: `user-request.md`

## Purpose

Capture the operator-owned Work Item request in a readable Markdown document. The request is
durable input for the governed workflow; it is not a runtime-authored stage result.

## Canonical authoring sections

New Work Items should use these sections in this order:

- `Title`
- `Brief`
- `Context`
- `Constraints`
- `Additional information`

`Title` and `Brief` are required for new UI-authored requests. The remaining sections are
optional and may be omitted when they have no content.

### Field notes

- `Title` is a short navigation label. Keep it to one line and do not put detailed context or
  links in it.
- `Brief` is the requested outcome in one or two short paragraphs.
- `Context` contains background, assumptions, and relevant repository or product information.
- `Constraints` contains non-negotiable boundaries, compatibility requirements, or exclusions.
- `Additional information` contains links, examples, references, and other helpful material that
  is not part of the outcome or constraints.

## Backward compatibility

Existing unsectioned `user-request.md` files remain readable. A compatibility reader may derive a
bounded title from the first meaningful line and a brief from the first paragraph, while exposing
the complete original Markdown as context. It must not rewrite a legacy document automatically.

## Ownership and lifecycle

- Only the operator-facing UI, CLI, or onboarding service writes this document.
- Runtime attempts read it as input and must not rewrite it.
- After a run consumes the request, revisions use a new intervention, remediation, or follow-up
  document; the consumed request remains immutable evidence.
- Markdown is the canonical representation. JSON fields exposed by a read model are projections,
  not a second source of truth.

## Validation cues

- new UI-authored documents contain exactly one `Title` and one `Brief` section;
- headings are unique and appear in the canonical order;
- section bodies are valid UTF-8 Markdown;
- detailed sections do not get copied into a Work Item header or navigation label;
- legacy unsectioned documents remain readable without data loss.
