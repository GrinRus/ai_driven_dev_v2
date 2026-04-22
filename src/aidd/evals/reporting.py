from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_EVALS_DIRNAME
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
SUMMARY_REPORT_FILENAME = "summary.md"


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


def _format_duration(duration_seconds: float) -> str:
    return f"{duration_seconds:.3f}"


def _default_created_at_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_eval_summary_markdown(
    *,
    scenario_rows: tuple[ScenarioSummaryRow, ...],
    runtime_summaries: tuple[RuntimeSummaryRow, ...] | None = None,
    created_at_utc: str | None = None,
) -> str:
    normalized_runtime_summaries = (
        aggregate_runtime_summary_rows(scenario_rows)
        if runtime_summaries is None
        else tuple(sorted(runtime_summaries, key=lambda row: row.runtime_id))
    )
    normalized_scenario_rows = tuple(
        sorted(scenario_rows, key=lambda row: (row.scenario_id, row.run_id))
    )

    lines = [
        "# Eval Summary",
        "",
        "## Overview",
        f"- Generated At (UTC): `{(created_at_utc or _default_created_at_utc()).strip()}`",
        f"- Scenario Rows: `{len(normalized_scenario_rows)}`",
        f"- Runtime Rows: `{len(normalized_runtime_summaries)}`",
        "",
        "## Runtime Summary",
    ]
    if not normalized_runtime_summaries:
        lines.append("- No runtime summary rows.")
    else:
        lines.extend(
            (
                "| Runtime | Scenarios | Pass | Fail | Blocked | Infra Fail | "
                "Total Duration (s) | Avg Duration (s) |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            )
        )
        for runtime_row in normalized_runtime_summaries:
            lines.append(
                "| "
                f"`{runtime_row.runtime_id}` | "
                f"{runtime_row.scenario_count} | "
                f"{runtime_row.pass_count} | "
                f"{runtime_row.fail_count} | "
                f"{runtime_row.blocked_count} | "
                f"{runtime_row.infra_fail_count} | "
                f"{_format_duration(runtime_row.total_duration_seconds)} | "
                f"{_format_duration(runtime_row.average_duration_seconds)} |"
            )

    lines.extend(("", "## Scenario Summary"))
    if not normalized_scenario_rows:
        lines.append("- No scenario summary rows.")
    else:
        lines.extend(
            (
                "| Scenario | Run | Runtime | Verdict | Duration (s) | Failure Boundary |",
                "| --- | --- | --- | --- | ---: | --- |",
            )
        )
        for scenario_row in normalized_scenario_rows:
            lines.append(
                "| "
                f"`{scenario_row.scenario_id}` | "
                f"`{scenario_row.run_id}` | "
                f"`{scenario_row.runtime_id}` | "
                f"`{scenario_row.verdict_status}` | "
                f"{_format_duration(scenario_row.duration_seconds)} | "
                f"`{scenario_row.failure_boundary}` |"
            )

    lines.append("")
    return "\n".join(lines)


def write_eval_summary_markdown(
    *,
    path: Path,
    scenario_rows: tuple[ScenarioSummaryRow, ...],
    runtime_summaries: tuple[RuntimeSummaryRow, ...] | None = None,
    created_at_utc: str | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_eval_summary_markdown(
            scenario_rows=scenario_rows,
            runtime_summaries=runtime_summaries,
            created_at_utc=created_at_utc,
        ),
        encoding="utf-8",
    )
    return path


def resolve_latest_eval_summary_report_path(*, workspace_root: Path) -> Path:
    eval_reports_root = workspace_root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_EVALS_DIRNAME
    if not eval_reports_root.exists() or not eval_reports_root.is_dir():
        raise ValueError(f"No eval reports found under: {eval_reports_root.as_posix()}")

    candidate_paths: list[Path] = []
    direct_summary_path = eval_reports_root / SUMMARY_REPORT_FILENAME
    if direct_summary_path.exists() and direct_summary_path.is_file():
        candidate_paths.append(direct_summary_path)

    for child in eval_reports_root.iterdir():
        if not child.is_dir():
            continue
        summary_path = child / SUMMARY_REPORT_FILENAME
        if summary_path.exists() and summary_path.is_file():
            candidate_paths.append(summary_path)

    if not candidate_paths:
        raise ValueError(
            "No eval summary reports found. "
            f"Expected `{SUMMARY_REPORT_FILENAME}` under {eval_reports_root.as_posix()}."
        )

    candidate_paths.sort(
        key=lambda path: (path.stat().st_mtime, path.as_posix()),
        reverse=True,
    )
    return candidate_paths[0]


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
    "SUMMARY_REPORT_FILENAME",
    "aggregate_runtime_summary_rows",
    "build_scenario_summary_row",
    "render_eval_summary_markdown",
    "resolve_latest_eval_summary_report_path",
    "write_eval_summary_markdown",
    "write_verdict",
]
