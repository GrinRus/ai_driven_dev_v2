from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aidd.core.run_store import RUN_ATTEMPT_PREFIX, run_attempts_root


@dataclass(frozen=True, slots=True)
class RepairBudgetPolicy:
    default_max_repair_attempts: int = 2
    stage_max_repair_attempts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.default_max_repair_attempts < 0:
            raise ValueError("Default max repair attempts must be non-negative.")

        normalized: dict[str, int] = {}
        for stage, attempts in self.stage_max_repair_attempts.items():
            normalized_stage = stage.strip()
            if not normalized_stage:
                raise ValueError("Stage override key must not be empty.")
            if attempts < 0:
                raise ValueError(
                    f"Stage repair attempts override must be non-negative for '{normalized_stage}'."
                )
            normalized[normalized_stage] = attempts

        object.__setattr__(self, "stage_max_repair_attempts", normalized)


@dataclass(frozen=True, slots=True)
class StageRepairCounter:
    stage: str
    stage_attempt_count: int
    repair_attempts_used: int
    max_repair_attempts: int
    remaining_repair_attempts: int
    budget_exhausted: bool


def default_repair_budget() -> int:
    return RepairBudgetPolicy().default_max_repair_attempts


def effective_repair_budget(
    *,
    stage: str,
    policy: RepairBudgetPolicy | None = None,
) -> int:
    resolved_policy = policy or RepairBudgetPolicy()
    normalized_stage = stage.strip()
    if not normalized_stage:
        raise ValueError("Stage must not be empty when resolving repair budget.")

    if normalized_stage in resolved_policy.stage_max_repair_attempts:
        return resolved_policy.stage_max_repair_attempts[normalized_stage]
    return resolved_policy.default_max_repair_attempts


def count_stage_attempts(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> int:
    attempts_root = run_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not attempts_root.exists():
        return 0

    count = 0
    for child in attempts_root.iterdir():
        if not child.is_dir() or not child.name.startswith(RUN_ATTEMPT_PREFIX):
            continue

        suffix = child.name.removeprefix(RUN_ATTEMPT_PREFIX)
        if suffix.isdigit():
            count += 1

    return count


def repair_attempts_used(*, stage_attempt_count: int) -> int:
    if stage_attempt_count < 0:
        raise ValueError("Stage attempt count must be non-negative.")

    # The first stage attempt is the initial run, not a repair run.
    return max(0, stage_attempt_count - 1)


def remaining_repair_attempts(*, repair_attempts_used: int, max_repair_attempts: int) -> int:
    if repair_attempts_used < 0:
        raise ValueError("Repair attempts used must be non-negative.")
    if max_repair_attempts < 0:
        raise ValueError("Max repair attempts must be non-negative.")

    return max(0, max_repair_attempts - repair_attempts_used)


def evaluate_stage_repair_counter(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    policy: RepairBudgetPolicy | None = None,
) -> StageRepairCounter:
    resolved_policy = policy or RepairBudgetPolicy()
    stage_attempt_count = count_stage_attempts(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    max_repair_attempts = effective_repair_budget(stage=stage, policy=resolved_policy)
    used = repair_attempts_used(stage_attempt_count=stage_attempt_count)
    remaining = remaining_repair_attempts(
        repair_attempts_used=used,
        max_repair_attempts=max_repair_attempts,
    )

    return StageRepairCounter(
        stage=stage,
        stage_attempt_count=stage_attempt_count,
        repair_attempts_used=used,
        max_repair_attempts=max_repair_attempts,
        remaining_repair_attempts=remaining,
        budget_exhausted=remaining == 0,
    )
