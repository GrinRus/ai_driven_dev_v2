# Plan

## Goals

- Ship incident follow-up tracking with durable ownership, due dates, and completion state.
- Keep first release scoped to existing email notification capability.

## Out of scope

- Chat-channel notifications in v1.
- Cross-team analytics dashboard in v1.

## Milestones

- M1: Add data model and storage path for follow-up actions with ownership metadata.
- M2: Expose operator workflow for creating, updating, and closing actions.
- M3: Integrate email notification dispatch for assignment and due-date reminders.
- M4: Run release checks and document rollout/rollback steps.

## Implementation strategy

- Implement core action lifecycle first, then add notification integration on top.
- Keep interfaces explicit between workflow state and notification adapter.
- Deliver each milestone as a reviewable vertical increment.

## Risks

- R1: Existing data model may not support due-date reminder semantics; mitigation: add migration tests and fallback defaults.
- R2: Email dispatch failures can create silent delivery gaps; mitigation: add delivery error logging and retry policy checks.

## Dependencies

- Existing repository email integration utilities.
- Migration path for action storage schema.
- Operator acceptance on milestone-level rollout sequence.

## Verification approach

- Validate each milestone with targeted tests before broad regression runs.
- Run full lint/type/test gates before milestone closure.

## Verification notes

- M1: verify schema migration and backward-compatibility checks.
- M2: verify action lifecycle state transitions with integration tests.
- M3: verify notification dispatch success/failure handling and logging.
- M4: verify release checklist execution and rollback rehearsal notes.
