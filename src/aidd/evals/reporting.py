from __future__ import annotations

import math
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
    "ScenarioSummaryRow",
    "build_scenario_summary_row",
    "write_verdict",
]
