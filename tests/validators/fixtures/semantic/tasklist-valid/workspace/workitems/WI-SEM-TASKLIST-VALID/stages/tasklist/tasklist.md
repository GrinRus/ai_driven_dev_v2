# Tasklist

## Task summary

Decompose approved planning artifacts into sequential, reviewable tasks that preserve dependency
order and concrete verification coverage.

## Ordered tasks

- TL-1 Define tasklist contract refinements for dependency notation.
- TL-2 Implement validator wiring for task-id dependency checks.
- TL-3 Add regression tests for dependency and verification mapping behavior.

## Dependencies

- TL-1: none
- TL-2: TL-1
- TL-3: TL-2

## Verification notes

- TL-1: uv run pytest tests/test_contract_registry.py -q
- TL-2: uv run pytest tests/validators/test_semantic.py -q
- TL-3: uv run pytest tests/validators/test_semantic.py tests/validators/test_structural.py -q
