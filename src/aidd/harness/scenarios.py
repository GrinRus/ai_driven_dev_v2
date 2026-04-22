from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


class ScenarioManifestError(ValueError):
    """Raised when a scenario manifest is missing required fields or has invalid values."""


_PLACEHOLDER_PATTERN = re.compile(r"\$\{(?P<key>[a-zA-Z0-9_.-]+)\}")


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


def _normalize_scenario_parameters(raw: Any) -> dict[str, str]:
    if raw is None:
        return {}
    payload = _require_mapping(value=raw, key="parameters")
    normalized: dict[str, str] = {}
    for raw_key, raw_value in payload.items():
        key = str(raw_key).strip()
        value = str(raw_value).strip()
        if not key or not value:
            raise ScenarioManifestError(
                "Scenario manifest key 'parameters' must map non-empty names to non-empty values."
            )
        normalized[key] = value
    return normalized


def _build_substitution_context(
    *,
    runtime_id: str | None,
    workspace_root: Path | None,
    scenario_parameters: dict[str, str],
) -> dict[str, str]:
    context = {f"scenario.{key}": value for key, value in scenario_parameters.items()}
    if runtime_id is not None and runtime_id.strip():
        context["runtime_id"] = runtime_id.strip()
    if workspace_root is not None:
        context["workspace_root"] = workspace_root.resolve(strict=False).as_posix()
    return context


def _substitute_placeholders_in_string(*, value: str, context: dict[str, str]) -> str:
    unresolved: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        key = match.group("key")
        replacement = context.get(key)
        if replacement is None:
            unresolved.append(key)
            return match.group(0)
        return replacement

    substituted = _PLACEHOLDER_PATTERN.sub(_replace, value)
    if unresolved:
        distinct = ", ".join(sorted(set(unresolved)))
        raise ScenarioManifestError(
            f"Scenario manifest contains unresolved placeholder(s): {distinct}."
        )
    return substituted


def _apply_substitutions(value: Any, *, context: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _apply_substitutions(item, context=context) for key, item in value.items()}
    if isinstance(value, list):
        return [_apply_substitutions(item, context=context) for item in value]
    if isinstance(value, str):
        return _substitute_placeholders_in_string(value=value, context=context)
    return value


def _require_mapping(*, value: Any, key: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScenarioManifestError(f"Scenario manifest key '{key}' must be a mapping.")
    return value


def _require_non_empty_string(*, payload: dict[str, Any], key: str) -> str:
    raw_value = payload.get(key)
    if raw_value is None:
        raise ScenarioManifestError(f"Scenario manifest missing required key: {key}.")
    value = str(raw_value).strip()
    if not value:
        raise ScenarioManifestError(
            f"Scenario manifest key '{key}' must be a non-empty string."
        )
    return value


def _to_optional_int(*, payload: dict[str, Any], key: str) -> int | None:
    raw_value = payload.get(key)
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ScenarioManifestError(
            f"Scenario manifest key '{key}' must be an integer when provided."
        ) from exc


def _to_repo_source(raw: Any) -> ScenarioRepoSource:
    payload = _require_mapping(value=raw, key="repo")
    url = _require_non_empty_string(payload=payload, key="url")
    default_branch = str(payload.get("default_branch", "")).strip() or None
    revision = str(payload.get("revision", "")).strip() or None
    return ScenarioRepoSource(url=url, default_branch=default_branch, revision=revision)


def _to_command_steps(*, raw: Any, key: str) -> ScenarioCommandSteps:
    payload = _require_mapping(value=raw, key=key)
    commands_raw = payload.get("commands")
    if not isinstance(commands_raw, list) or not commands_raw:
        raise ScenarioManifestError(
            f"Scenario manifest key '{key}.commands' must be a non-empty list of strings."
        )
    commands = tuple(str(command).strip() for command in commands_raw)
    if any(not command for command in commands):
        raise ScenarioManifestError(
            f"Scenario manifest key '{key}.commands' must be a non-empty list of strings."
        )
    return ScenarioCommandSteps(commands=commands)


def _to_run_config(raw: dict[str, Any]) -> ScenarioRunConfig:
    stage_scope = raw.get("stage_scope")
    limits = raw.get("limits")
    interview = raw.get("interview")
    runtime_targets_raw = raw.get("runtime_targets")

    if isinstance(stage_scope, dict):
        stage_start = str(stage_scope.get("start", "")).strip() or None
        stage_end = str(stage_scope.get("end", "")).strip() or None
    else:
        stage_start = None
        stage_end = None

    if isinstance(limits, dict):
        patch_budget_files = _to_optional_int(payload=limits, key="patch_budget_files")
        timeout_minutes = _to_optional_int(payload=limits, key="timeout_minutes")
    else:
        patch_budget_files = None
        timeout_minutes = None

    interview_required = bool(interview.get("required")) if isinstance(interview, dict) else False
    if not isinstance(runtime_targets_raw, list) or not runtime_targets_raw:
        raise ScenarioManifestError(
            "Scenario manifest key 'runtime_targets' must be a non-empty list of strings."
        )
    runtime_targets = tuple(str(runtime).strip() for runtime in runtime_targets_raw)
    if any(not runtime for runtime in runtime_targets):
        raise ScenarioManifestError(
            "Scenario manifest key 'runtime_targets' must be a non-empty list of strings."
        )

    return ScenarioRunConfig(
        stage_start=stage_start,
        stage_end=stage_end,
        runtime_targets=runtime_targets,
        patch_budget_files=patch_budget_files,
        timeout_minutes=timeout_minutes,
        interview_required=interview_required,
    )


def load_scenario(
    path: Path,
    *,
    runtime_id: str | None = None,
    workspace_root: Path | None = None,
) -> Scenario:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ScenarioManifestError(f"Scenario manifest must be a mapping: {path.as_posix()}")
    scenario_parameters = _normalize_scenario_parameters(data.get("parameters"))
    context = _build_substitution_context(
        runtime_id=runtime_id,
        workspace_root=workspace_root,
        scenario_parameters=scenario_parameters,
    )
    substituted = _apply_substitutions(data, context=context)
    if not isinstance(substituted, dict):
        raise ScenarioManifestError(f"Scenario manifest must be a mapping: {path.as_posix()}")

    scenario_id = _require_non_empty_string(payload=substituted, key="id")
    task = _require_non_empty_string(payload=substituted, key="task")
    run = _to_run_config(substituted)
    return Scenario(
        scenario_id=scenario_id,
        task=task,
        repo=_to_repo_source(substituted.get("repo")),
        setup=_to_command_steps(raw=substituted.get("setup"), key="setup"),
        run=run,
        verify=_to_command_steps(raw=substituted.get("verify"), key="verify"),
        runtime_targets=run.runtime_targets,
        raw=substituted,
    )
