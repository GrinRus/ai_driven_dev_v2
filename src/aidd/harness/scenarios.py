from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True)
class ScenarioRepoSource:
    url: str
    default_branch: str | None
    revision: str | None


@dataclass(frozen=True)
class ScenarioCommandSteps:
    commands: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioRunConfig:
    stage_start: str | None
    stage_end: str | None
    runtime_targets: tuple[str, ...]
    patch_budget_files: int | None
    timeout_minutes: int | None
    interview_required: bool


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    task: str
    repo: ScenarioRepoSource
    setup: ScenarioCommandSteps
    run: ScenarioRunConfig
    verify: ScenarioCommandSteps
    runtime_targets: tuple[str, ...]
    raw: dict[str, Any]


def _to_command_steps(raw: Any) -> ScenarioCommandSteps:
    if not isinstance(raw, dict):
        return ScenarioCommandSteps(commands=())
    commands = raw.get("commands")
    if not isinstance(commands, list):
        return ScenarioCommandSteps(commands=())
    return ScenarioCommandSteps(commands=tuple(str(command) for command in commands))


def _to_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_repo_source(raw: Any) -> ScenarioRepoSource:
    if not isinstance(raw, dict):
        return ScenarioRepoSource(url="", default_branch=None, revision=None)
    url = str(raw.get("url", "")).strip()
    default_branch = str(raw.get("default_branch", "")).strip() or None
    revision = str(raw.get("revision", "")).strip() or None
    return ScenarioRepoSource(url=url, default_branch=default_branch, revision=revision)


def _to_run_config(raw: dict[str, Any]) -> ScenarioRunConfig:
    stage_scope = raw.get("stage_scope")
    limits = raw.get("limits")
    interview = raw.get("interview")
    runtime_targets_raw = raw.get("runtime_targets", [])

    if isinstance(stage_scope, dict):
        stage_start = str(stage_scope.get("start", "")).strip() or None
        stage_end = str(stage_scope.get("end", "")).strip() or None
    else:
        stage_start = None
        stage_end = None

    if isinstance(limits, dict):
        patch_budget_files = _to_optional_int(limits.get("patch_budget_files"))
        timeout_minutes = _to_optional_int(limits.get("timeout_minutes"))
    else:
        patch_budget_files = None
        timeout_minutes = None

    interview_required = bool(interview.get("required")) if isinstance(interview, dict) else False
    runtime_targets = (
        tuple(str(runtime) for runtime in runtime_targets_raw)
        if isinstance(runtime_targets_raw, list)
        else ()
    )
    return ScenarioRunConfig(
        stage_start=stage_start,
        stage_end=stage_end,
        runtime_targets=runtime_targets,
        patch_budget_files=patch_budget_files,
        timeout_minutes=timeout_minutes,
        interview_required=interview_required,
    )


def load_scenario(path: Path) -> Scenario:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Scenario manifest must be a mapping: {path.as_posix()}")
    scenario_id = str(data["id"])
    task = str(data["task"])
    run = _to_run_config(data)
    return Scenario(
        scenario_id=scenario_id,
        task=task,
        repo=_to_repo_source(data.get("repo")),
        setup=_to_command_steps(data.get("setup")),
        run=run,
        verify=_to_command_steps(data.get("verify")),
        runtime_targets=run.runtime_targets,
        raw=data,
    )
