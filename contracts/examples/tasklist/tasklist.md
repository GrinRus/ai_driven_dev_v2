# Tasklist

## Source summary

- Plan source: `workitems/WI-TASKLIST-EXAMPLE/stages/plan/output/plan.md`
- Review-spec source: `workitems/WI-TASKLIST-EXAMPLE/stages/review-spec/output/review-spec-report.md`
- Readiness baseline: `approved-with-conditions` with required rollback and ownership clarifications already applied.

## Ordered task decomposition

### TL-1 Define rollout guardrails contract update

- Dominant output artifact: `contracts/stages/implement.md`
- Dependencies: `none`
- Verification notes:
  - `uv run pytest tests/test_contract_registry.py tests/core/test_stage_registry.py -q`
  - Confirm `implement` contract includes explicit rollback trigger requirements.

### TL-2 Add execution-state persistence wiring

- Dominant output artifact: `src/aidd/core/stage_runner.py`
- Dependencies: `TL-1`
- Verification notes:
  - `uv run pytest tests/core/test_stage_runner.py -q`
  - Verify persisted stage state records unresolved blocking questions as `blocked`.

### TL-3 Cover unblock transition behavior with tests

- Dominant output artifact: `tests/core/test_stage_runner.py`
- Dependencies: `TL-2`
- Verification notes:
  - `uv run pytest tests/core/test_stage_runner.py -q`
  - Validate unblock transition once matching `[resolved]` answers are present.

## Assumptions

- [non-blocking] Existing workspace layout remains unchanged for this iteration.
- [non-blocking] Adapter runtime interface remains stable while tasklist work is executed.

## Handoff notes

- Execute tasks in listed order because TL-2 consumes contract behavior defined in TL-1.
- Do not start TL-3 before TL-2 is merged; assertions depend on new state transitions.
