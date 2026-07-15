from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.identifiers import SafeIdentifier, resolve_contained_component
from aidd.core.task_plan import TaskPlanParseError, parse_task_plan


def _tasklist(*, second_dependency: str = "TL-1") -> str:
    return f"""# Tasklist

## Task summary

Two bounded tasks with complete dependency and verification evidence.

## Ordered tasks

### TL-1 — Add the contract

- Outcome: The contract is explicit.
- Dominant deliverable: `contracts/example.md` is updated.
- In scope: `contracts/example.md` and `tests/test_contract.py`.
- Acceptance criteria:
  - TL-1-AC1: The required field is documented.

### TL-2 — Add enforcement

- Outcome: Invalid content is rejected.
- Dominant deliverable: `src/example.py` validates the field.
- In scope: `src/example.py` and `tests/test_validator.py`.
- Acceptance criteria:
  - TL-2-AC1: Missing content produces a stable finding.

## Dependencies

- TL-1: none
- TL-2: {second_dependency}

## Verification notes

- TL-1: `pytest tests/test_contract.py -q`
- TL-2: `pytest tests/test_validator.py -q`
"""




def test_parse_task_plan_preserves_order_and_acceptance() -> None:
    plan = parse_task_plan(_tasklist())

    assert plan.ordered_ids() == ("TL-1", "TL-2")
    assert plan.tasks[1].dependencies == ("TL-1",)
    assert plan.tasks[1].acceptance_criteria[0].id == "TL-2-AC1"

@pytest.mark.parametrize("value", ("", ".", "..", "../task", "task/child", "/task"))
def test_safe_identifier_rejects_unsafe_path_components(tmp_path: Path, value: str) -> None:
    with pytest.raises(ValueError):
        SafeIdentifier.parse(value, label="task id")
    with pytest.raises(ValueError):
        resolve_contained_component(tmp_path, value, label="task id")

@pytest.mark.parametrize(
    "invalid_text",
    (
        "- Outcome: The contract is explicit.\n",
        "- Dominant deliverable: `contracts/example.md` is updated.\n",
        "- In scope: `contracts/example.md` and `tests/test_contract.py`.\n",
        "  - TL-1-AC1: The required field is documented.\n",
    ),
)
def test_parse_task_plan_rejects_each_missing_card_field(invalid_text: str) -> None:
    markdown = _tasklist().replace(invalid_text, "")

    with pytest.raises(TaskPlanParseError):
        parse_task_plan(markdown)

def test_parse_task_plan_rejects_unknown_dependency() -> None:
    with pytest.raises(TaskPlanParseError, match="unknown dependencies"):
        parse_task_plan(_tasklist(second_dependency="TL-9"))

def test_parse_task_plan_rejects_dependency_cycle() -> None:
    markdown = _tasklist().replace("- TL-1: none", "- TL-1: TL-2")

    with pytest.raises(TaskPlanParseError, match="cycle"):
        parse_task_plan(markdown)

def test_parse_task_plan_rejects_forward_dependency() -> None:
    markdown = _tasklist(second_dependency="none").replace("- TL-1: none", "- TL-1: TL-2")

    with pytest.raises(TaskPlanParseError, match="do not appear earlier"):
        parse_task_plan(markdown)

@pytest.mark.parametrize(
    "scope",
    (
        "Contract text without a concrete path.",
        "`../contracts/example.md`.",
        "`/tmp/example.md`.",
        "`src/**/*.py`.",
    ),
)
def test_parse_task_plan_rejects_missing_or_unsafe_scope_path(scope: str) -> None:
    markdown = _tasklist().replace("`contracts/example.md` and `tests/test_contract.py`.", scope)

    with pytest.raises(TaskPlanParseError, match="in-scope path|repository-relative"):
        parse_task_plan(markdown)

def test_parse_task_plan_rejects_duplicate_and_mixed_task_ids() -> None:
    duplicate = _tasklist().replace(
        "### TL-2 — Add enforcement",
        "### TL-1 — Add enforcement",
    )
    with pytest.raises(TaskPlanParseError, match="Duplicate task ids"):
        parse_task_plan(duplicate)

    mixed = _tasklist().replace("TL-2", "T2")
    with pytest.raises(TaskPlanParseError, match="must not mix"):
        parse_task_plan(mixed)

def test_parse_task_plan_rejects_malformed_and_duplicate_acceptance_ids() -> None:
    malformed = _tasklist().replace("TL-1-AC1", "TL-1-C1")
    with pytest.raises(TaskPlanParseError, match="malformed acceptance id"):
        parse_task_plan(malformed)

    duplicate = _tasklist().replace(
        "  - TL-1-AC1: The required field is documented.\n",
        "  - TL-1-AC1: The required field is documented.\n  - TL-1-AC1: The same id is repeated.\n",
    )
    with pytest.raises(TaskPlanParseError, match="duplicate acceptance ids"):
        parse_task_plan(duplicate)
