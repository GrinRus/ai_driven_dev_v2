# Tasklist

## Task summary

Keep a coupled behavior correction and its regression contract reviewable without assigning a
tests-only task a production change that falls outside its task-local scope.

## Ordered tasks

### TL-1 — Implement the streaming behavior correction and regression contract

- Outcome: Milestone M1 delivers the bounded streaming behavior and the regression coverage that
  proves its public contract.
- Dominant deliverable: `src/streaming.py` and `tests/test_streaming.py` contain the behavior fix
  and its focused regression coverage.
- In scope: `src/streaming.py` and `tests/test_streaming.py`.
- Acceptance criteria:
  - TL-1-AC1: The behavior correction and regression test are reviewed as one bounded change.

### TL-2 — Run the bounded verification gate

- Outcome: Milestone M2 records verification evidence for the completed streaming correction.
- Dominant deliverable: focused test output for the completed behavior and regression contract.
- In scope: `src/streaming.py` and `tests/test_streaming.py`.
- Execution mode: verification-only
- Acceptance criteria:
  - TL-2-AC1: The authored focused verification command passes without changing repository files.

## Dependencies

- TL-1: none
- TL-2: TL-1

## Verification notes

- TL-1: `uv run pytest -q tests/test_streaming.py -> pass`
- TL-2: `uv run pytest -q tests/test_streaming.py -> pass`
