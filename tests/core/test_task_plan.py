from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.identifiers import SafeIdentifier, resolve_contained_component
from aidd.core.task_plan import (
    TaskExecutionMode,
    TaskPlanIssueKind,
    TaskPlanIssueRelation,
    TaskPlanParseError,
    parse_task_plan,
)


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




def _safe_presentation_variant() -> str:
    return (
        _tasklist()
        .replace("### TL-1 — Add the contract", "### **TL-1** — Add the contract")
        .replace("### TL-2 — Add enforcement", "### `TL-2`: Add enforcement")
        .replace("- Outcome:", "* **Outcome**:")
        .replace("- Dominant deliverable:", "- `Dominant deliverable`:")
        .replace("- In scope:", "* __In scope__:")
        .replace("- Acceptance criteria:", "* *Acceptance criteria*:")
        .replace("  - TL-1-AC1:", "  * **TL-1-AC1**:")
        .replace("  - TL-2-AC1:", "  * `TL-2-AC1`:")
        .replace("- TL-1: none", "* **TL-1**: none")
        .replace("- TL-2: TL-1", "- `TL-2`: **TL-1**")
        .replace("- TL-1: `pytest", "* **TL-1**: `pytest")
        .replace("- TL-2: `pytest", "- `TL-2`: `pytest")
    )


def test_parse_task_plan_accepts_safe_presentation_variants_without_inference() -> None:
    canonical = parse_task_plan(_tasklist())
    variant = parse_task_plan(_safe_presentation_variant())

    assert variant.tasks == canonical.tasks


def test_parse_task_plan_reports_structured_missing_field_at_card_heading() -> None:
    markdown = _tasklist().replace("- Outcome: The contract is explicit.\n", "")

    with pytest.raises(TaskPlanParseError) as captured:
        parse_task_plan(markdown)

    issue = next(
        issue for issue in captured.value.issues if issue.kind is TaskPlanIssueKind.MISSING_FIELD
    )
    assert issue.task_id == "TL-1"
    assert issue.field == "outcome"
    assert issue.missing_fields == ("outcome",)
    assert issue.line_number == 9
    assert issue.relation is TaskPlanIssueRelation.ROOT
    assert "missing required field `outcome`" in str(captured.value)


def test_parse_task_plan_does_not_emit_derivative_scope_issue_for_missing_field() -> None:
    markdown = _tasklist().replace(
        "- In scope: `contracts/example.md` and `tests/test_contract.py`.\n",
        "",
    )

    with pytest.raises(TaskPlanParseError) as captured:
        parse_task_plan(markdown)

    task_one_issues = [issue for issue in captured.value.issues if issue.task_id == "TL-1"]
    assert [issue.kind for issue in task_one_issues] == [TaskPlanIssueKind.MISSING_FIELD]


def test_parse_task_plan_reports_exact_acceptance_and_dependency_lines() -> None:
    markdown = _tasklist(second_dependency="TL-9").replace(
        "  - TL-1-AC1: The required field is documented.",
        "  - TL-1-C1: The required field is documented.",
    )

    with pytest.raises(TaskPlanParseError) as captured:
        parse_task_plan(markdown)

    acceptance_issue = next(
        issue
        for issue in captured.value.issues
        if issue.kind is TaskPlanIssueKind.MALFORMED_ACCEPTANCE_ID
    )
    dependency_issue = next(
        issue
        for issue in captured.value.issues
        if issue.kind is TaskPlanIssueKind.UNKNOWN_DEPENDENCY
    )
    assert acceptance_issue.task_id == "TL-1"
    assert acceptance_issue.line_number == 15
    assert dependency_issue.task_id == "TL-2"
    assert dependency_issue.line_number == 28


def test_parse_task_plan_classifies_scope_derivative_as_related() -> None:
    markdown = _tasklist().replace(
        "`contracts/example.md` and `tests/test_contract.py`.",
        "`../contracts/example.md`.",
    )

    with pytest.raises(TaskPlanParseError) as captured:
        parse_task_plan(markdown)

    task_one_issues = [issue for issue in captured.value.issues if issue.task_id == "TL-1"]
    assert task_one_issues[0].kind is TaskPlanIssueKind.UNSAFE_SCOPE_PATH
    assert task_one_issues[0].relation is TaskPlanIssueRelation.ROOT
    assert task_one_issues[1].kind is TaskPlanIssueKind.MISSING_SCOPE_PATH
    assert task_one_issues[1].relation is TaskPlanIssueRelation.RELATED


def test_parse_task_plan_preserves_order_and_acceptance() -> None:
    plan = parse_task_plan(_tasklist())

    assert plan.ordered_ids() == ("TL-1", "TL-2")
    assert plan.tasks[1].dependencies == ("TL-1",)
    assert plan.tasks[1].acceptance_criteria[0].id == "TL-2-AC1"
    assert plan.tasks[0].execution_mode is TaskExecutionMode.REPOSITORY_CHANGE


def test_parse_task_plan_allows_dependency_rationale_after_machine_value() -> None:
    markdown = _tasklist().replace(
        "- TL-1: none\n",
        "- TL-1: none — establishes milestone M1\n",
    ).replace(
        "- TL-2: TL-1\n",
        "- TL-2: TL-1; preserves the bounded order\n",
    )

    plan = parse_task_plan(markdown)

    assert plan.tasks[0].dependencies == ()
    assert plan.tasks[1].dependencies == ("TL-1",)


def test_parse_task_plan_accepts_backticked_none_dependency() -> None:
    markdown = _tasklist().replace("- TL-1: none\n", "- TL-1: `none`.\n")

    plan = parse_task_plan(markdown)

    assert plan.tasks[0].dependencies == ()


def test_parse_task_plan_preserves_explicit_verification_only_mode() -> None:
    markdown = _tasklist().replace(
        "- In scope: `src/example.py` and `tests/test_validator.py`.",
        "- In scope: `src/example.py` and `tests/test_validator.py`.\n"
        "- Execution mode: verification-only",
    )

    plan = parse_task_plan(markdown)

    assert plan.tasks[1].execution_mode is TaskExecutionMode.VERIFICATION_ONLY


def test_parse_task_plan_rejects_unknown_execution_mode() -> None:
    markdown = _tasklist().replace(
        "- In scope: `src/example.py` and `tests/test_validator.py`.",
        "- In scope: `src/example.py` and `tests/test_validator.py`.\n"
        "- Execution mode: inferred-from-title",
    )

    with pytest.raises(TaskPlanParseError, match="execution mode"):
        parse_task_plan(markdown)

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


@pytest.mark.parametrize(
    "compact_tasks",
    (
        "- TL-1: add the contract; TL-2: add tests",
        "| Task | Outcome | Verification |\n"
        "| --- | --- | --- |\n"
        "| TL-1 | add the contract | run tests |",
    ),
)
def test_parse_task_plan_rejects_compact_or_table_like_presentation(
    compact_tasks: str,
) -> None:
    markdown = _tasklist().replace(
        "### TL-1 — Add the contract\n\n"
        "- Outcome: The contract is explicit.\n"
        "- Dominant deliverable: `contracts/example.md` is updated.\n"
        "- In scope: `contracts/example.md` and `tests/test_contract.py`.\n"
        "- Acceptance criteria:\n"
        "  - TL-1-AC1: The required field is documented.\n",
        compact_tasks + "\n",
    )

    with pytest.raises(TaskPlanParseError):
        parse_task_plan(markdown)


def test_canonical_tasklist_example_retains_executable_semantics() -> None:
    example = Path("contracts/examples/tasklist/tasklist.md").read_text(encoding="utf-8")

    plan = parse_task_plan(example)

    assert plan.ordered_ids() == ("TL-1", "TL-2", "TL-3")
    assert all(task.outcome and task.dominant_deliverable for task in plan.tasks)
    assert all(task.scope_paths for task in plan.tasks)
    assert all(task.acceptance_criteria for task in plan.tasks)
