# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic, slice, and local task.

## Next

- `W3-E2-S2-T5` Implement terminal transition handling for success, blocked, failed, and repair-needed outcomes.

## Soon

- `W3-E2-S2-T6` Add tests that cover happy-path, validator-failure, blocked-question, and adapter-failure transitions.

## Parking lot

- `W5-E3-S1-T1` Pin the Typer repository revision and record the target scenario objective.
- `W5-E3-S5-T1` Define the sqlite-utils scenario conditions that force at least one user question.
- `W6-E2-S3-T6` Add one harness or integration scenario that proves the `implement` repair loop end to end.
- `W7-E1-S1-T1` Implement Codex command discovery.
- `W7-E2-S1-T1` Implement OpenCode command discovery.
- `W7-E3-S2-T2` Finalize container publishing configuration and image tagging rules.

## Update rules

- Keep `roadmap.md` as the canonical plan and `backlog.md` as the short queue.
- Only local task ids belong in this file.
- If a task is too large, split it in `roadmap.md` before coding.
- Add new work to `roadmap.md` first, then promote it here only if it becomes immediate.
- Remove completed tasks rather than leaving stale queue entries behind.
