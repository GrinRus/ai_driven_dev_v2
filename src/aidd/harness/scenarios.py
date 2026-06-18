from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from aidd.core.stages import STAGES
from aidd.runtime_catalog import runtime_ids


class ScenarioManifestError(ValueError):
    """Raised when a scenario manifest is missing required fields or has invalid values."""


_PLACEHOLDER_PATTERN = re.compile(r"\$\{(?P<key>[a-zA-Z0-9_.-]+)\}")
_SCENARIO_CLASSES = {
    "deterministic-stage",
    "deterministic-workflow",
    "live-full-flow",
    "live-full-flow-interview",
}
_LIVE_SCENARIO_CLASSES = {"live-full-flow", "live-full-flow-interview"}
_FEATURE_SIZES = {"tiny", "small", "medium", "large", "xlarge"}
_AUTOMATION_LANES = {"ci", "manual"}
_SUPPORTED_RUNTIME_IDS = set(runtime_ids())
_LIVE_RUNTIME_IDS = {"codex", "opencode", "claude-code", "qwen"}
_LIVE_FLOW_DRIVERS = {"stepwise-black-box"}
_LIVE_FLOW_CHECKPOINT_POLICIES = {"after-each-step"}
_LIVE_FLOW_ANSWER_POLICIES = {"agent-decides"}


@dataclass(frozen=True)
class ScenarioRepoSource:
    url: str
    default_branch: str | None
    revision: str | None


@dataclass(frozen=True)
class ScenarioCommandSteps:
    commands: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioAuthoredTask:
    task_id: str
    title: str
    summary: str
    intent: str
    target_change: str
    expected_scope: str
    acceptance_criteria: tuple[str, ...]
    verification: tuple[str, ...]
    quality_bar: str
    size_rationale: str
    interview: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioFeatureSource:
    mode: str
    selection_policy: str
    tasks: tuple[ScenarioAuthoredTask, ...]
    fixture_path: str | None
    seed_id: str | None
    summary: str | None


@dataclass(frozen=True)
class ScenarioRunConfig:
    stage_start: str | None
    stage_end: str | None
    runtime_targets: tuple[str, ...]
    patch_budget_files: int | None
    timeout_minutes: int | None
    interview_required: bool


@dataclass(frozen=True)
class ScenarioLiveFlowConfig:
    driver: str
    checkpoint_policy: str
    answer_policy: str
    frontend_checkpoints: bool


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    scenario_class: str
    feature_size: str
    automation_lane: str
    canonical_runtime: str
    task: str
    repo: ScenarioRepoSource
    setup: ScenarioCommandSteps
    run: ScenarioRunConfig
    verify: ScenarioCommandSteps
    feature_source: ScenarioFeatureSource | None
    live_flow: ScenarioLiveFlowConfig | None
    runtime_targets: tuple[str, ...]
    is_live: bool
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


def _to_non_empty_string_tuple(
    *,
    payload: dict[str, Any],
    key: str,
    parent_key: str,
    required: bool = True,
) -> tuple[str, ...]:
    raw_items = payload.get(key)
    if raw_items is None:
        if required:
            raise ScenarioManifestError(
                f"Scenario manifest missing required key: {parent_key}.{key}."
            )
        return tuple()
    if not isinstance(raw_items, list):
        raise ScenarioManifestError(
            f"Scenario manifest key '{parent_key}.{key}' must be a non-empty list of strings."
        )
    items = tuple(str(item).strip() for item in raw_items if str(item).strip())
    if required and not items:
        raise ScenarioManifestError(
            f"Scenario manifest key '{parent_key}.{key}' must be a non-empty list of strings."
        )
    return items


def _to_authored_task(*, raw: Any, key: str) -> ScenarioAuthoredTask:
    payload = _require_mapping(value=raw, key=key)
    task_id = _require_non_empty_string(payload=payload, key="id")
    title = _require_non_empty_string(payload=payload, key="title")
    summary = _require_non_empty_string(payload=payload, key="summary")
    intent = _require_non_empty_string(payload=payload, key="intent")
    target_change = _require_non_empty_string(payload=payload, key="target_change")
    expected_scope = _require_non_empty_string(payload=payload, key="expected_scope")
    acceptance_criteria = _to_non_empty_string_tuple(
        payload=payload,
        key="acceptance_criteria",
        parent_key=key,
    )
    verification = _to_non_empty_string_tuple(
        payload=payload,
        key="verification",
        parent_key=key,
    )
    quality_bar = _require_non_empty_string(payload=payload, key="quality_bar")
    size_rationale = _require_non_empty_string(payload=payload, key="size_rationale")
    interview = _to_non_empty_string_tuple(
        payload=payload,
        key="interview",
        parent_key=key,
        required=False,
    )
    return ScenarioAuthoredTask(
        task_id=task_id,
        title=title,
        summary=summary,
        intent=intent,
        target_change=target_change,
        expected_scope=expected_scope,
        acceptance_criteria=acceptance_criteria,
        verification=verification,
        quality_bar=quality_bar,
        size_rationale=size_rationale,
        interview=interview,
    )


def _to_feature_source(raw: Any) -> ScenarioFeatureSource:
    payload = _require_mapping(value=raw, key="feature_source")
    mode = _require_non_empty_string(payload=payload, key="mode")
    selection_policy = _require_non_empty_string(payload=payload, key="selection_policy")

    if mode == "authored-task-pool":
        if selection_policy != "first-listed":
            raise ScenarioManifestError(
                "Scenario manifest key 'feature_source.selection_policy' must be "
                "`first-listed` for authored task pools."
            )
        tasks_raw = payload.get("tasks")
        if not isinstance(tasks_raw, list) or not tasks_raw:
            raise ScenarioManifestError(
                "Scenario manifest key 'feature_source.tasks' must be a non-empty list."
            )
        tasks = tuple(
            _to_authored_task(raw=item, key=f"feature_source.tasks[{index}]")
            for index, item in enumerate(tasks_raw)
        )
        fixture_path = None
        seed_id = None
        summary = None
    elif mode == "fixture-seed":
        if selection_policy != "fixture-owned":
            raise ScenarioManifestError(
                "Scenario manifest key 'feature_source.selection_policy' must be "
                "`fixture-owned` for deterministic fixture seeds."
            )
        tasks = tuple()
        fixture_path = _require_non_empty_string(payload=payload, key="fixture_path")
        seed_id = _require_non_empty_string(payload=payload, key="seed_id")
        summary = _require_non_empty_string(payload=payload, key="summary")
    else:
        raise ScenarioManifestError(
            "Scenario manifest key 'feature_source.mode' must be either "
            "`fixture-seed` or `authored-task-pool`."
        )

    return ScenarioFeatureSource(
        mode=mode,
        selection_policy=selection_policy,
        tasks=tasks,
        fixture_path=fixture_path,
        seed_id=seed_id,
        summary=summary,
    )


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


def _to_live_flow_config(raw: Any) -> ScenarioLiveFlowConfig:
    payload = _require_mapping(value=raw, key="live_flow")
    driver = _require_choice(
        payload=payload,
        key="driver",
        supported=_LIVE_FLOW_DRIVERS,
    )
    checkpoint_policy = _require_choice(
        payload=payload,
        key="checkpoint_policy",
        supported=_LIVE_FLOW_CHECKPOINT_POLICIES,
    )
    answer_policy = _require_choice(
        payload=payload,
        key="answer_policy",
        supported=_LIVE_FLOW_ANSWER_POLICIES,
    )
    frontend_checkpoints_raw = payload.get("frontend_checkpoints", False)
    if not isinstance(frontend_checkpoints_raw, bool):
        raise ScenarioManifestError(
            "Scenario manifest key 'live_flow.frontend_checkpoints' must be a boolean."
        )
    return ScenarioLiveFlowConfig(
        driver=driver,
        checkpoint_policy=checkpoint_policy,
        answer_policy=answer_policy,
        frontend_checkpoints=frontend_checkpoints_raw,
    )


def _is_live_scenario_path(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    return (
        resolved.parent.name == "live"
        and resolved.parent.parent.name == "scenarios"
        and resolved.suffix == ".yaml"
    )


def _require_choice(*, payload: dict[str, Any], key: str, supported: set[str]) -> str:
    value = _require_non_empty_string(payload=payload, key=key)
    if value not in supported:
        supported_values = ", ".join(sorted(supported))
        raise ScenarioManifestError(
            f"Scenario manifest key '{key}' must be one of: {supported_values}."
        )
    return value


def _validate_scenario_contract(
    *,
    path: Path,
    scenario_class: str,
    feature_size: str,
    automation_lane: str,
    canonical_runtime: str,
    run: ScenarioRunConfig,
    feature_source: ScenarioFeatureSource | None,
    live_flow: ScenarioLiveFlowConfig | None,
    raw: dict[str, Any],
) -> None:
    if run.stage_start is None or run.stage_end is None:
        raise ScenarioManifestError(
            "Scenario manifests must declare explicit `stage_scope.start` and "
            "`stage_scope.end` values."
        )
    unsupported_runtimes = sorted(set(run.runtime_targets) - _SUPPORTED_RUNTIME_IDS)
    if unsupported_runtimes:
        raise ScenarioManifestError(
            "Scenario manifest key 'runtime_targets' contains unsupported runtime ids: "
            + ", ".join(unsupported_runtimes)
            + "."
        )
    if canonical_runtime not in run.runtime_targets:
        raise ScenarioManifestError(
            "Scenario manifest key 'canonical_runtime' must also appear in "
            "'runtime_targets'."
        )

    is_live = scenario_class in _LIVE_SCENARIO_CLASSES
    if _is_live_scenario_path(path) != is_live:
        expected = "live" if is_live else "non-live"
        raise ScenarioManifestError(
            f"Scenario path '{path.as_posix()}' does not match declared {expected} "
            "scenario class."
        )

    if feature_size in {"large", "xlarge"} and automation_lane == "ci":
        raise ScenarioManifestError(
            "Scenario manifests with `feature_size: large` or `feature_size: xlarge` "
            "cannot use `automation_lane: ci`."
        )

    if is_live:
        if "workflow_bundle" in raw:
            raise ScenarioManifestError(
                "Live scenario manifests must not declare "
                "`workflow_bundle`; live evidence bundles are evaluator-owned artifacts."
            )
        unsupported_live_runtimes = sorted(set(run.runtime_targets) - _LIVE_RUNTIME_IDS)
        if unsupported_live_runtimes:
            allowed = ", ".join(sorted(_LIVE_RUNTIME_IDS))
            raise ScenarioManifestError(
                "Live scenario manifests may only target supported live runtimes "
                f"({allowed}); unsupported live runtime target(s): "
                + ", ".join(unsupported_live_runtimes)
                + "."
            )
        if canonical_runtime not in _LIVE_RUNTIME_IDS:
            allowed = ", ".join(sorted(_LIVE_RUNTIME_IDS))
            raise ScenarioManifestError(
                "Live scenario manifests must use a supported live canonical runtime "
                f"({allowed})."
            )
        if automation_lane != "manual":
            raise ScenarioManifestError(
                "Live scenario manifests must declare `automation_lane: manual`."
            )
        if run.stage_start != STAGES[0] or run.stage_end != STAGES[-1]:
            raise ScenarioManifestError(
                "Live scenario manifests must declare explicit full-flow stage scope "
                "`idea -> qa`."
            )
        if feature_source is None:
            raise ScenarioManifestError(
                f"Live scenario manifest missing required key: feature_source ({path.as_posix()})."
            )
        if feature_source.mode != "authored-task-pool":
            raise ScenarioManifestError(
                "Live scenario manifests must use `feature_source.mode: authored-task-pool`."
            )
        if "quality" in raw:
            raise ScenarioManifestError(
                "Live scenario manifests must not declare `quality`; live E2E "
                "execution bundles are separate from the manual post-run "
                "`quality-report.md`."
            )
        if live_flow is None:
            raise ScenarioManifestError(
                f"Live scenario manifest missing required key: live_flow ({path.as_posix()})."
            )
        if live_flow.frontend_checkpoints is not True:
            raise ScenarioManifestError(
                "Live scenario manifest black-box checkpoint contract mismatch: "
                "`live_flow.frontend_checkpoints` must be true so live E2E inspects "
                "the public `aidd ui` surface and UI/API endpoints after each stage."
            )
        expects_interview = scenario_class == "live-full-flow-interview"
        if live_flow.answer_policy != "agent-decides":
            raise ScenarioManifestError(
                "Live scenario manifest black-box answer contract mismatch: "
                "`live_flow.answer_policy` must be `agent-decides` so any live "
                "scenario can block on questions and resume after launching "
                "operator-agent answers."
            )
        if run.interview_required is not expects_interview:
            expected_value = "true" if expects_interview else "false"
            raise ScenarioManifestError(
                "Live scenario manifest interview contract mismatch: "
                f"`interview.required` must be {expected_value} for "
                f"`scenario_class: {scenario_class}`."
            )
        for index, task in enumerate(feature_source.tasks):
            if expects_interview and not task.interview:
                raise ScenarioManifestError(
                    "Live interview scenario authored tasks must include "
                    f"`feature_source.tasks[{index}].interview` guidance."
                )
        return

    if feature_source is None:
        raise ScenarioManifestError(
            "Deterministic scenario manifests must declare a `feature_source` block."
        )
    if feature_source.mode != "fixture-seed":
        raise ScenarioManifestError(
            "Deterministic scenario manifests must use `feature_source.mode: fixture-seed`."
        )
    if "quality" in raw:
        raise ScenarioManifestError(
            "Scenario manifests must not declare a `quality` block; quality review is "
            "manual post-run analysis."
        )
    if live_flow is not None:
        raise ScenarioManifestError(
            "Deterministic scenario manifests must not declare a `live_flow` block."
        )
    if scenario_class == "deterministic-stage" and (
        run.stage_start == STAGES[0] and run.stage_end == STAGES[-1]
    ):
        raise ScenarioManifestError(
            "Deterministic stage scenarios cannot declare the full-flow `idea -> qa` range."
        )
    if scenario_class == "deterministic-stage" and run.stage_start != run.stage_end:
        raise ScenarioManifestError(
            "Deterministic stage scenarios must declare the same start and end stage."
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
    scenario_class = _require_choice(
        payload=substituted,
        key="scenario_class",
        supported=_SCENARIO_CLASSES,
    )
    feature_size = _require_choice(
        payload=substituted,
        key="feature_size",
        supported=_FEATURE_SIZES,
    )
    automation_lane = _require_choice(
        payload=substituted,
        key="automation_lane",
        supported=_AUTOMATION_LANES,
    )
    canonical_runtime = _require_choice(
        payload=substituted,
        key="canonical_runtime",
        supported=_SUPPORTED_RUNTIME_IDS,
    )
    task = _require_non_empty_string(payload=substituted, key="task")
    run = _to_run_config(substituted)
    is_live = scenario_class in _LIVE_SCENARIO_CLASSES
    feature_source = (
        _to_feature_source(substituted.get("feature_source"))
        if substituted.get("feature_source") is not None
        else None
    )
    live_flow = (
        _to_live_flow_config(substituted.get("live_flow"))
        if substituted.get("live_flow") is not None
        else None
    )
    repo = _to_repo_source(substituted.get("repo"))
    setup = _to_command_steps(raw=substituted.get("setup"), key="setup")
    verify = _to_command_steps(raw=substituted.get("verify"), key="verify")
    _validate_scenario_contract(
        path=path,
        scenario_class=scenario_class,
        feature_size=feature_size,
        automation_lane=automation_lane,
        canonical_runtime=canonical_runtime,
        run=run,
        feature_source=feature_source,
        live_flow=live_flow,
        raw=substituted,
    )
    return Scenario(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        feature_size=feature_size,
        automation_lane=automation_lane,
        canonical_runtime=canonical_runtime,
        task=task,
        repo=repo,
        setup=setup,
        run=run,
        verify=verify,
        feature_source=feature_source,
        live_flow=live_flow,
        runtime_targets=run.runtime_targets,
        is_live=is_live,
        raw=substituted,
    )
