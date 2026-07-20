from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.contracts import repo_root_from
from aidd.core.identifiers import SafeIdentifier
from aidd.core.resources import resolve_resource_layout
from aidd.harness.eval_models import EvalRunPreparation
from aidd.harness.repo_prep import prepare_workspace
from aidd.harness.result_bundle import ensure_result_bundle_layout
from aidd.harness.scenarios import Scenario, ScenarioAuthoredTask, load_scenario


def derive_run_id(*, scenario_id: str, runtime_id: str) -> str:
    safe_scenario_id = SafeIdentifier.parse(scenario_id, label="scenario_id").value
    safe_runtime_id = SafeIdentifier.parse(runtime_id, label="runtime_id").value
    suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    normalized_scenario = safe_scenario_id.lower().replace("aidd-", "")
    normalized_scenario = normalized_scenario.replace("_", "-")
    return SafeIdentifier.parse(
        f"eval-{normalized_scenario}-{safe_runtime_id}-{suffix}",
        label="eval run_id",
    ).value


def derive_aidd_command(scenario: Scenario) -> tuple[str, ...]:
    raw_invocation = scenario.raw.get("aidd_invocation")
    if isinstance(raw_invocation, dict):
        raw_command = raw_invocation.get("command")
        if isinstance(raw_command, list):
            command_tokens = tuple(
                str(token).strip() for token in raw_command if str(token).strip()
            )
            if command_tokens:
                if command_tokens[-1] == "run":
                    command_tokens = command_tokens[:-1]
                if command_tokens:
                    return command_tokens

    return (sys.executable, "-m", "aidd.cli.main")


def derive_work_item(scenario: Scenario) -> str:
    raw_invocation = scenario.raw.get("aidd_invocation")
    if isinstance(raw_invocation, dict):
        raw_work_item = raw_invocation.get("work_item")
        if isinstance(raw_work_item, str) and raw_work_item.strip():
            return raw_work_item.strip()

    normalized = scenario.scenario_id.strip().upper().replace("-", "_")
    return f"WI-EVAL-{normalized}"


def derive_teardown_commands(scenario: Scenario) -> tuple[str, ...]:
    raw_teardown = scenario.raw.get("teardown")
    if not isinstance(raw_teardown, dict):
        return tuple()

    raw_commands = raw_teardown.get("commands")
    if not isinstance(raw_commands, list):
        return tuple()

    return tuple(
        str(command).strip()
        for command in raw_commands
        if str(command).strip()
    )


def select_authored_task(scenario: Scenario) -> ScenarioAuthoredTask | None:
    if scenario.feature_source is None or not scenario.feature_source.tasks:
        return None
    return scenario.feature_source.tasks[0]


def derive_source_repository_root(scenario_path: Path) -> Path | None:
    try:
        return repo_root_from(scenario_path.resolve(strict=False))
    except FileNotFoundError:
        try:
            return repo_root_from(Path.cwd().resolve(strict=False))
        except FileNotFoundError:
            return None


def build_feature_selection_payload(
    *,
    scenario: Scenario,
    selected_task: ScenarioAuthoredTask | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "automation_lane": scenario.automation_lane,
        "canonical_runtime": scenario.canonical_runtime,
        "feature_size": scenario.feature_size,
        "fixture_seed": None,
        "live_matrix_role": scenario.live_matrix_role,
        "scenario_id": scenario.scenario_id,
        "scenario_class": scenario.scenario_class,
        "is_live": scenario.is_live,
        "mode": None if scenario.feature_source is None else scenario.feature_source.mode,
        "selection_policy": (
            None
            if scenario.feature_source is None
            else scenario.feature_source.selection_policy
        ),
        "selected_task": None,
    }
    if selected_task is not None:
        payload["selected_task"] = {
            "acceptance_criteria": list(selected_task.acceptance_criteria),
            "allowed_write_scope": list(selected_task.allowed_write_scope),
            "expected_scope": selected_task.expected_scope,
            "id": selected_task.task_id,
            "intent": selected_task.intent,
            "interview": list(selected_task.interview),
            "audit_rubric": selected_task.audit_rubric,
            "complexity_axes": list(selected_task.complexity_axes),
            "quality_bar": selected_task.quality_bar,
            "size_rationale": selected_task.size_rationale,
            "summary": selected_task.summary,
            "target_change": selected_task.target_change,
            "title": selected_task.title,
            "visible_request": selected_task.visible_request,
            "verification": list(selected_task.verification),
        }
    if scenario.feature_source is not None and scenario.feature_source.mode == "fixture-seed":
        payload["fixture_seed"] = {
            "fixture_path": scenario.feature_source.fixture_path,
            "seed_id": scenario.feature_source.seed_id,
            "summary": scenario.feature_source.summary,
        }
    return payload


def prepare_eval_run(
    *,
    scenario_path: Path,
    runtime_id: str,
    workspace_root: Path,
) -> EvalRunPreparation:
    scenario = load_scenario(
        scenario_path,
        runtime_id=runtime_id,
        workspace_root=workspace_root,
    )
    run_id = derive_run_id(scenario_id=scenario.scenario_id, runtime_id=runtime_id)
    layout = ensure_result_bundle_layout(workspace_root=workspace_root, run_id=run_id)
    prepare_workspace(workspace_root)

    selected_task = select_authored_task(scenario)
    return EvalRunPreparation(
        scenario_path=scenario_path,
        scenario=scenario,
        run_id=run_id,
        runtime_id=runtime_id,
        workspace_root=workspace_root,
        source_repository_root=derive_source_repository_root(scenario_path),
        layout=layout,
        cache_root=workspace_root / "harness-cache",
        live_scenario=scenario.is_live,
        resource_layout=resolve_resource_layout(),
        aidd_command=None if scenario.is_live else derive_aidd_command(scenario),
        work_item=derive_work_item(scenario),
        selected_task=selected_task,
        feature_selection_payload=build_feature_selection_payload(
            scenario=scenario,
            selected_task=selected_task,
        ),
        teardown_commands=derive_teardown_commands(scenario),
    )
