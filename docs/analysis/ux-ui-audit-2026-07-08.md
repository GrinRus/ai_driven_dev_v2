# UX/UI Audit - Operator Flow - 2026-07-08

## Scope

- Product surface: local AIDD operator UI served by `aidd ui`.
- User model: first-time operator running a governed document-first workflow, then recovering from blocked, failed, or completed runs.
- Live evidence: `AIDD-LIVE-007` / `codex` / `eval-live-007-codex-20260708T094457Z`, checkpointed after `idea` and `research`.
- Local visual evidence: onboarding, first command center, runtime failure recovery, completed flow, follow-up wizard, and mobile completed-flow screenshots captured under `/tmp/aidd-ui-ux-e9daBL`, `/tmp/aidd-ui-ux-good-e2DDAN`, and `/tmp/aidd-ui-terminal-GV58Fp`.

## Quality Summary

The operator UI has the right product concepts: project/work item/run context, stage rail, global next action, evidence/logs, recovery, and next-flow handoff. The workflow is inspectable, and the live E2E bundle shows stage artifacts and runtime logs can be reached through public surfaces.

The main UX gap is not missing capability; it is decision priority. A new operator can see many panels but may not know which one matters now. Recovery also needs stronger failure-specific guidance: runtime failures should lead with logs and runtime-exit evidence, while validation failures should lead with repair/request-change actions.

## Findings

- P1: Runtime failure recovery can point the user at `Request Change` before `Open logs`. In the failed fixture run, the central recovery hero showed `Runtime failure` but the primary action was `Request Change`; the better evidence path was only visible in the sidebar.
- P1: Mobile topbar status chips collapse to single letters on a 390px viewport. This makes work item, run, and readiness state unreadable at exactly the size where first-time operators need more context.
- P2: Long live stages have weak perceived progress before runtime logs appear. During `stage-0002-research`, the bundle showed active `run-stage` state for several minutes while no stage runtime log was yet present.
- P2: First launch shows several similarly weighted setup surfaces. The safe deterministic runner is not visually distinguished enough from real provider commands.
- P2: The automated frontend checkpoint proves HTTP/API availability but not visual clarity, responsive layout, or whether the next operator action is understandable.
- P3: Long artifact paths are truncated aggressively in compact mobile rows. This avoids page overflow but reduces evidence traceability.

## Live E2E Stage Notes

- `stage-0001-idea`: acceptable. The idea brief framed the Hono non-Error throw task correctly, preserved compatibility constraints, and had no blocking questions. The frontend checkpoint passed API/page reachability only.
- `stage-0002-research`: strong. The research found both Hono error gates, cited source/tests, reproduced current behavior, and identified the correct Vitest verification path.
- Both checkpoints exposed a meta-UX issue: the live frontend checkpoint lacks visual QA assertions.

## First Improvement Plan

- Make runtime failure recovery prefer `Open logs` when `first_failure.kind` is a runtime failure and runtime evidence exists.
- Make the central recovery hero explain runtime evidence first: failure detail, runtime-exit metadata path, and raw log path.
- Fix mobile topbar status chip layout so run/work item/readiness labels remain readable instead of collapsing.
- Let mobile `.path-line` wrap within rows when necessary, preserving traceability without page-level horizontal scroll.
- Add static asset contract tests for these UX priorities.

## Deferred Work

- Add visual frontend checkpoints for live E2E, including desktop/mobile screenshots and assertions for visible next action, active stage, recovery primary action, and absence of clipped topbar text.
- Rebalance first-launch onboarding so the recommended deterministic/safe path is visually dominant while real provider runners remain available.
- Add a more explicit in-progress/pre-runtime state to the UI for long live stages before runtime log chunks exist.
