from __future__ import annotations

from typing import Any, cast

import pytest

from aidd.core.operator_frontend_models import OperatorBlocker, OperatorStageRailItem
from aidd.core.operator_frontend_next_action import (
    OperatorNextActionContext,
    resolve_next_action,
)
from aidd.core.run_inspection import RunMetadataSummary
from aidd.core.state_machine import StageState

_DEFAULT_METADATA = cast(RunMetadataSummary, object())


def _rail(**overrides: Any) -> OperatorStageRailItem:
    values: dict[str, Any] = {
        "stage": "plan",
        "title": "Plan",
        "subtitle": "Design the approach",
        "status": StageState.PENDING.value,
        "attempt_count": 0,
        "can_run": False,
        "reason": "blocked by prerequisites",
        "question_count": 0,
        "unresolved_blocking_count": 0,
        "validator_pass_count": 0,
        "validator_fail_count": 0,
    }
    values.update(overrides)
    return OperatorStageRailItem(**values)


def _context(
    rail: OperatorStageRailItem,
    *,
    metadata: RunMetadataSummary | None = _DEFAULT_METADATA,
    blockers: tuple[OperatorBlocker, ...] = (),
    operator_request_stages: frozenset[str] = frozenset(),
) -> OperatorNextActionContext:
    return OperatorNextActionContext(
        metadata=metadata,
        active_stage="plan",
        active_stage_view=None,
        rail_by_stage={rail.stage: rail},
        report_blockers=blockers,
        stages_with_operator_requests=operator_request_stages,
    )


def _blocker(kind: str) -> OperatorBlocker:
    return OperatorBlocker(
        kind=kind,
        title=kind,
        detail=f"detail for {kind}",
        severity="error",
        stage="plan",
    )


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        (_context(_rail(), metadata=None), "choose-runtime"),
        (_context(_rail(stale=True, stale_reason="downstream changed")), "rerun-stale-downstream"),
        (_context(_rail(unresolved_blocking_count=1)), "answer-questions"),
        (_context(_rail(status=StageState.EXECUTING.value)), "wait-for-stage"),
        (
            _context(_rail(status=StageState.FAILED.value, validator_fail_count=1)),
            "inspect-validation",
        ),
        (
            _context(
                _rail(status=StageState.FAILED.value, validator_fail_count=1),
                operator_request_stages=frozenset({"plan"}),
            ),
            "review-intervention",
        ),
        (_context(_rail(status=StageState.BLOCKED.value)), "resume-stage"),
        (
            _context(
                _rail(status=StageState.SUCCEEDED.value),
                blockers=(_blocker("review-rejected"),),
            ),
            "review-findings",
        ),
        (
            _context(
                _rail(status=StageState.SUCCEEDED.value),
                blockers=(_blocker("qa-not-ready"),),
            ),
            "qa-verdict",
        ),
        (
            _context(
                _rail(status=StageState.SUCCEEDED.value),
                blockers=(_blocker("terminal-missing-evidence"),),
            ),
            "review-complete",
        ),
        (_context(_rail(status=StageState.SUCCEEDED.value)), "review-complete"),
        (_context(_rail(can_run=True, reason="ready")), "run-stage"),
        (_context(_rail()), "run-stage"),
    ],
)
def test_ordered_rules_produce_one_deterministic_action(
    context: OperatorNextActionContext,
    expected: str,
) -> None:
    first = resolve_next_action(context)
    second = resolve_next_action(context)

    assert first.action == expected
    assert first == second


def test_ordered_rules_keep_higher_priority_evidence_a_single_winner() -> None:
    context = _context(
        _rail(
            stale=True,
            stale_reason="downstream changed",
            unresolved_blocking_count=1,
            status=StageState.FAILED.value,
            validator_fail_count=1,
        ),
        blockers=(_blocker("review-rejected"), _blocker("qa-not-ready")),
    )

    action = resolve_next_action(context)

    assert action.action == "rerun-stale-downstream"
    assert action.stage == "plan"
