# Plan

## Goals

- Ship incident follow-up tracking with durable ownership and completion state.

## Out of scope

- Chat-channel notifications in v1.

## Milestones

- M1: Add follow-up action data model and persistence path.
- M2: Expose operator lifecycle workflow for creating and closing actions.
- M3: Add assignment and due-date notification behavior.

## Implementation strategy

- Deliver milestones in dependency order and keep each increment reviewable.

## Risks

- R1: Reminder scheduling drift can hide overdue actions; mitigation: add schedule-boundary checks.
- R2: Notification dispatch errors can be missed; mitigation: verify retry/error logging behavior.

## Dependencies

- Existing notification adapter integration utilities.
- Storage migration path for follow-up action records.

## Verification approach

- Run milestone-focused checks before broad regression gates.

## Verification notes

- M1: verify schema migration and backward compatibility.
- M2: verify lifecycle transitions for create/update/close actions.
- M3: verify dispatch success/failure logging and retry behavior.
