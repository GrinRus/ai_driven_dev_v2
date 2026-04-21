# Document Contract: `plan.md`

## Purpose

Capture the implementation plan, boundaries, risks, dependencies, and rollout or verification approach.

## Required sections

- `Goals`
- `Out of scope`
- `Milestones`
- `Implementation strategy`
- `Risks`
- `Dependencies`
- `Verification approach`
- `Verification notes`

## Field notes

- `Milestones`
  - Must list execution increments in planned order.
  - Each milestone should describe expected outcome and readiness signal.
- `Risks`
  - Must identify concrete delivery or quality risks, not generic cautions.
  - Each risk should include a mitigation direction.
- `Verification notes`
  - Must map planned checks to milestones, risks, or both.
  - Must include at least one note for the highest-risk milestone.

## Validation cues

- the file exists in the expected stage directory,
- the required headings are present,
- the content is non-placeholder and stage-relevant,
- upstream references are present when the stage requires them.

## Notes

This is a Markdown contract, not a runtime-output JSON schema.
