from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.repair import (
    RepairBudgetPolicy,
    count_stage_attempts,
    default_repair_budget,
    effective_repair_budget,
    evaluate_stage_repair_counter,
    remaining_repair_attempts,
    repair_attempts_used,
)


def _make_attempt_dir(root: Path, name: str) -> None:
    (root / name).mkdir(parents=True, exist_ok=True)


def test_default_repair_budget_is_two_attempts() -> None:
    assert default_repair_budget() == 2


def test_repair_budget_policy_validates_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        RepairBudgetPolicy(default_max_repair_attempts=-1)

    with pytest.raises(ValueError, match="Stage override key must not be empty"):
        RepairBudgetPolicy(stage_max_repair_attempts={"": 1})

    with pytest.raises(ValueError, match="non-negative"):
        RepairBudgetPolicy(stage_max_repair_attempts={"plan": -1})


def test_effective_repair_budget_uses_stage_override() -> None:
    policy = RepairBudgetPolicy(
        default_max_repair_attempts=2,
        stage_max_repair_attempts={"qa": 1},
    )

    assert effective_repair_budget(stage="plan", policy=policy) == 2
    assert effective_repair_budget(stage="qa", policy=policy) == 1


def test_count_stage_attempts_ignores_non_attempt_directories(tmp_path: Path) -> None:
    attempts_root = (
        tmp_path
        / ".aidd"
        / "reports"
        / "runs"
        / "WI-001"
        / "run-001"
        / "stages"
        / "plan"
        / "attempts"
    )
    _make_attempt_dir(attempts_root, "attempt-0001")
    _make_attempt_dir(attempts_root, "attempt-0002")
    _make_attempt_dir(attempts_root, "attempt-final")
    _make_attempt_dir(attempts_root, "misc")

    assert count_stage_attempts(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    ) == 2


def test_repair_attempts_used_treats_initial_attempt_as_non_repair() -> None:
    assert repair_attempts_used(stage_attempt_count=0) == 0
    assert repair_attempts_used(stage_attempt_count=1) == 0
    assert repair_attempts_used(stage_attempt_count=3) == 2


def test_remaining_repair_attempts_clamps_at_zero() -> None:
    assert remaining_repair_attempts(repair_attempts_used=0, max_repair_attempts=2) == 2
    assert remaining_repair_attempts(repair_attempts_used=2, max_repair_attempts=2) == 0
    assert remaining_repair_attempts(repair_attempts_used=4, max_repair_attempts=2) == 0


def test_evaluate_stage_repair_counter_reports_budget_state(tmp_path: Path) -> None:
    attempts_root = (
        tmp_path
        / ".aidd"
        / "reports"
        / "runs"
        / "WI-001"
        / "run-001"
        / "stages"
        / "plan"
        / "attempts"
    )
    _make_attempt_dir(attempts_root, "attempt-0001")
    _make_attempt_dir(attempts_root, "attempt-0002")
    _make_attempt_dir(attempts_root, "attempt-0003")

    counter = evaluate_stage_repair_counter(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        policy=RepairBudgetPolicy(default_max_repair_attempts=2),
    )

    assert counter.stage == "plan"
    assert counter.stage_attempt_count == 3
    assert counter.repair_attempts_used == 2
    assert counter.max_repair_attempts == 2
    assert counter.remaining_repair_attempts == 0
    assert counter.budget_exhausted is True
