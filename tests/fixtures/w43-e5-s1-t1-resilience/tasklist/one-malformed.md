# Tasklist

## Task summary

One malformed task card must fail closed.

## Ordered tasks

### TL-1 — Missing outcome

- Dominant deliverable: `src/example.py` validates the field.
- In scope: `src/example.py` and `tests/test_validator.py`.
- Acceptance criteria:
  - TL-1-AC1: Missing outcome is reported at the card heading.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: `pytest tests/test_validator.py -q`
