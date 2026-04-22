from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from aidd.evals.log_analysis import FailureTaxonomyCategory
from aidd.evals.verdicts import ScenarioVerdict, VerdictStatus

FAILURE_CLASSES: tuple[str, ...] = (
    "pass",
    "document_fail",
    "model_fail",
    "env_fail",
    "permission_fail",
    "auth_fail",
    "timeout",
    "adapter_fail",
    "harness_fail",
    "needs_user_input",
)
FAILURE_BOUNDARY_CATEGORIES: tuple[FailureTaxonomyCategory, ...] = (
    "environment",
    "adapter",
    "runtime",
    "validation",
    "scenario-verification",
    "none",
)


@dataclass(frozen=True, slots=True)
class ScenarioSummaryRow:
    scenario_id: str
    run_id: str
    runtime_id: str
    verdict_status: VerdictStatus
    duration_seconds: float
    failure_boundary: FailureTaxonomyCategory


@dataclass(frozen=True, slots=True)
class RuntimeSummaryRow:
    runtime_id: str
    scenario_count: int
    pass_count: int
    fail_count: int
    blocked_count: int
    infra_fail_count: int
    total_duration_seconds: float
    average_duration_seconds: float


def _normalize_failure_boundary(boundary: str) -> FailureTaxonomyCategory:
    normalized = boundary.strip()
    if normalized not in FAILURE_BOUNDARY_CATEGORIES:
        raise ValueError(
            "failure_boundary must be one of: "
            + ", ".join(f"`{candidate}`" for candidate in FAILURE_BOUNDARY_CATEGORIES)
            + "."
        )
    return normalized


def build_scenario_summary_row(
    *,
    verdict: ScenarioVerdict,
    duration_seconds: float,
    failure_boundary: str = "none",
) -> ScenarioSummaryRow:
    if not math.isfinite(duration_seconds):
        raise ValueError("duration_seconds must be finite.")
    if duration_seconds < 0:
        raise ValueError("duration_seconds must be greater than or equal to 0.")
    return ScenarioSummaryRow(
        scenario_id=verdict.scenario_id,
        run_id=verdict.run_id,
        runtime_id=verdict.runtime_id,
        verdict_status=verdict.status,
        duration_seconds=duration_seconds,
        failure_boundary=_normalize_failure_boundary(failure_boundary),
    )


def aggregate_runtime_summary_rows(
    rows: tuple[ScenarioSummaryRow, ...],
) -> tuple[RuntimeSummaryRow, ...]:
    if not rows:
        return tuple()

    grouped_rows: dict[str, list[ScenarioSummaryRow]] = defaultdict(list)
    for row in rows:
        grouped_rows[row.runtime_id].append(row)

    summaries: list[RuntimeSummaryRow] = []
    for runtime_id in sorted(grouped_rows):
        runtime_rows = grouped_rows[runtime_id]
        scenario_count = len(runtime_rows)
        total_duration_seconds = sum(row.duration_seconds for row in runtime_rows)
        pass_count = sum(1 for row in runtime_rows if row.verdict_status == "pass")
        fail_count = sum(1 for row in runtime_rows if row.verdict_status == "fail")
        blocked_count = sum(1 for row in runtime_rows if row.verdict_status == "blocked")
        infra_fail_count = sum(1 for row in runtime_rows if row.verdict_status == "infra-fail")

        summaries.append(
            RuntimeSummaryRow(
                runtime_id=runtime_id,
                scenario_count=scenario_count,
                pass_count=pass_count,
                fail_count=fail_count,
                blocked_count=blocked_count,
                infra_fail_count=infra_fail_count,
                total_duration_seconds=total_duration_seconds,
                average_duration_seconds=(
                    total_duration_seconds / scenario_count if scenario_count else 0.0
                ),
            )
        )

    return tuple(summaries)


def write_verdict(path: Path, status: str, summary: str) -> None:
    if status not in FAILURE_CLASSES:
        raise ValueError(f"Unknown failure class: {status}")
    path.write_text(
        f"# Verdict\n\n- Status: {status}\n- Summary: {summary}\n",
        encoding="utf-8",
    )


__all__ = [
    "FAILURE_BOUNDARY_CATEGORIES",
    "FAILURE_CLASSES",
    "RuntimeSummaryRow",
    "ScenarioSummaryRow",
    "aggregate_runtime_summary_rows",
    "build_scenario_summary_row",
    "write_verdict",
]
