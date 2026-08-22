# Tasklist

## Task summary

Two bounded tasks with complete dependency and verification evidence.

## Ordered tasks

### **TL-1** — Add the contract

* **Outcome**: The contract is explicit.
* `Dominant deliverable`: `contracts/example.md` is updated.
* __In scope__: `contracts/example.md` and `tests/test_contract.py`.
* *Acceptance criteria*:
  * **TL-1-AC1**: The required field is documented.

### `TL-2`: Add enforcement

* **Outcome**: Invalid content is rejected.
* `Dominant deliverable`: `src/example.py` validates the field.
* __In scope__: `src/example.py` and `tests/test_validator.py`.
* *Acceptance criteria*:
  * `TL-2-AC1`: Missing content produces a stable finding.

## Dependencies

* **TL-1**: none
* `TL-2`: **TL-1**

## Verification notes

* **TL-1**: `pytest tests/test_contract.py -q`
* `TL-2`: `pytest tests/test_validator.py -q`
