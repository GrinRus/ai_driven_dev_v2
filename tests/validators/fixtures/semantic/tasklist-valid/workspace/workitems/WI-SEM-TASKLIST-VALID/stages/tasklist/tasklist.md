# Tasklist

## Task summary

Decompose approved planning artifacts into sequential, reviewable rich task cards that preserve
dependency order, bounded scope, acceptance criteria, and concrete verification coverage.

## Ordered tasks

### TL-1 — Define dependency notation

- Outcome: Task dependencies use one canonical notation.
- Dominant deliverable: `contracts/documents/tasklist.md` defines the notation.
- In scope: `contracts/documents/tasklist.md` and `tests/test_contract_registry.py`.
- Acceptance criteria:
  - TL-1-AC1: The contract requires one dependency entry per task.

### TL-2 — Implement dependency validation

- Outcome: Invalid dependency references are rejected.
- Dominant deliverable: The tasklist semantic validator checks the dependency graph.
- In scope: `src/aidd/core/task_plan.py` and `src/aidd/validators/semantic_rules/tasklist.py`.
- Acceptance criteria:
  - TL-2-AC1: Unknown dependencies produce a stable finding.
  - TL-2-AC2: Dependency cycles produce a stable finding.

### TL-3 — Add regression coverage

- Outcome: Valid and invalid dependency behavior has deterministic tests.
- Dominant deliverable: `tests/validators/test_semantic.py` contains the matrix.
- In scope: `tests/validators/test_semantic.py`.
- Acceptance criteria:
  - TL-3-AC1: The valid fixture passes without findings.

## Dependencies

- TL-1: none
- TL-2: TL-1
- TL-3: TL-2

## Verification notes

- TL-1: `uv run pytest tests/test_contract_registry.py -q`
- TL-2: `uv run pytest tests/validators/test_semantic.py -q`
- TL-3: `uv run pytest tests/validators/test_semantic.py tests/validators/test_structural.py -q`
