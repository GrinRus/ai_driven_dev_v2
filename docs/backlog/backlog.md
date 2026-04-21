# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic, slice, and local task.

## Next

- `W2-E1-S1-T1` Write the required heading set, field notes, and authoring rules for `stage-brief.md`.
- `W2-E1-S1-T2` Write the required heading set, attempt-history rules, and terminal-state notes for `stage-result.md`.
- `W2-E1-S1-T3` Write the required heading set and blocking-question markers for `questions.md`.
- `W2-E2-S1-T1` Implement workspace-relative path resolution for stage documents and common documents.
- `W2-E2-S1-T2` Implement Markdown file loading that returns raw body text plus file metadata.
- `W3-E1-S1-T1` Define the canonical workspace directory layout and reserved file names.
- `W4-E1-S1-T1` Implement command discovery for the configured generic CLI executable.
- `W4-E2-S1-T1` Implement Claude Code command discovery for the configured executable name or path.

## Soon

- `W2-E1-S1-T4` Write the required heading set and answer-resolution markers for `answers.md`.
- `W2-E1-S1-T5` Write the required heading set, issue-code vocabulary, and severity rules for `validator-report.md`.
- `W2-E1-S1-T6` Write the required heading set, rerun-budget notes, and fix-plan rules for `repair-brief.md`.
- `W2-E1-S1-T7` Add one worked example bundle that includes every common document type and cross-links them correctly.
- `W2-E2-S1-T3` Implement optional frontmatter parsing without making frontmatter required.
- `W2-E2-S1-T4` Implement document-type classification from path and filename conventions.
- `W4-E1-S1-T2` Capture version or identity information from the discovered CLI.
- `W4-E2-S1-T2` Capture version or identity information from the Claude Code CLI.

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
