# Tasklist

## Task summary

Decompose the approved rollout work into three implementation-ready task cards with
explicit dependency order, bounded scope, acceptance criteria, and authored checks.

## Ordered tasks

### TL-1 — Define rollout guardrails

- Outcome: The implement-stage contract states the required rollback triggers.
- Dominant deliverable: `contracts/stages/implement.md` contains the guardrails.
- In scope: `contracts/stages/implement.md` and focused registry coverage under `tests/`.
- Acceptance criteria:
  - TL-1-AC1: The contract names explicit rollback trigger requirements.

### TL-2 — Add execution-state persistence

- Outcome: Blocked interview state is persisted and can be resumed after answers.
- Dominant deliverable: `src/aidd/core/stage_runner.py` persists the transition.
- In scope: `src/aidd/core/stage_runner.py` and `tests/core/test_stage_runner.py`.
- Implementation constraints: Keep adapter interfaces unchanged.
- Acceptance criteria:
  - TL-2-AC1: An unresolved blocking question persists stage status `blocked`.
  - TL-2-AC2: A matching resolved answer allows the next attempt to resume.

### TL-3 — Cover unblock transitions

- Outcome: Regression coverage proves the blocked-to-resume lifecycle.
- Dominant deliverable: `tests/core/test_stage_runner.py` covers both transitions.
- In scope: `tests/core/test_stage_runner.py`.
- Out of scope: Provider-authenticated external end-to-end validation.
- Acceptance criteria:
  - TL-3-AC1: The focused test fails without the persistence behavior and passes with it.

## Dependencies

- TL-1: none
- TL-2: TL-1
- TL-3: TL-2

## Verification notes

- TL-1: `uv run pytest tests/test_contract_registry.py tests/core/test_stage_registry.py -q`
- TL-2: `uv run pytest tests/core/test_stage_runner.py -q`
- TL-3: `uv run pytest tests/core/test_stage_runner.py -q`
