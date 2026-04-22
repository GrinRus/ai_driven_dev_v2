from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

VerdictStatus = Literal["pass", "fail", "blocked", "infra-fail"]
VERDICT_STATUSES: tuple[VerdictStatus, ...] = ("pass", "fail", "blocked", "infra-fail")


@dataclass(frozen=True, slots=True)
class ScenarioVerdict:
    scenario_id: str
    run_id: str
    runtime_id: str
    status: VerdictStatus
    summary: str
    created_at_utc: str


def _normalize_required_field(*, field_name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty.")
    return normalized


def _normalize_verdict_status(status: str) -> VerdictStatus:
    normalized = status.strip()
    if normalized not in VERDICT_STATUSES:
        raise ValueError(
            "status must be one of: "
            + ", ".join(f"`{candidate}`" for candidate in VERDICT_STATUSES)
            + "."
        )
    return normalized


def _default_created_at_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_scenario_verdict(
    *,
    scenario_id: str,
    run_id: str,
    runtime_id: str,
    status: str,
    summary: str,
    created_at_utc: str | None = None,
) -> ScenarioVerdict:
    return ScenarioVerdict(
        scenario_id=_normalize_required_field(field_name="scenario_id", value=scenario_id),
        run_id=_normalize_required_field(field_name="run_id", value=run_id),
        runtime_id=_normalize_required_field(field_name="runtime_id", value=runtime_id),
        status=_normalize_verdict_status(status),
        summary=_normalize_required_field(field_name="summary", value=summary),
        created_at_utc=(
            _normalize_required_field(field_name="created_at_utc", value=created_at_utc)
            if created_at_utc is not None
            else _default_created_at_utc()
        ),
    )


def render_scenario_verdict_markdown(verdict: ScenarioVerdict) -> str:
    lines = [
        "# Verdict",
        "",
        "## Run",
        f"- Scenario ID: `{verdict.scenario_id}`",
        f"- Run ID: `{verdict.run_id}`",
        f"- Runtime ID: `{verdict.runtime_id}`",
        f"- Created At (UTC): `{verdict.created_at_utc}`",
        "",
        "## Outcome",
        f"- Status: `{verdict.status}`",
        f"- Summary: {verdict.summary}",
        "",
    ]
    return "\n".join(lines)


def write_scenario_verdict_markdown(*, path: Path, verdict: ScenarioVerdict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_scenario_verdict_markdown(verdict), encoding="utf-8")
    return path


__all__ = [
    "ScenarioVerdict",
    "VerdictStatus",
    "VERDICT_STATUSES",
    "build_scenario_verdict",
    "render_scenario_verdict_markdown",
    "write_scenario_verdict_markdown",
]
