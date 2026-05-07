from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.contracts import repo_root_from
from aidd.core.resources import resolve_resource_layout
from aidd.harness.eval_models import EvalRunPreparation
from aidd.harness.repo_prep import prepare_workspace
from aidd.harness.result_bundle import ensure_result_bundle_layout
from aidd.harness.scenarios import Scenario, ScenarioIssueSeed, load_scenario


def derive_run_id(*, scenario_id: str, runtime_id: str) -> str:
    suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    normalized_scenario = scenario_id.strip().lower().replace("aidd-", "")
    normalized_scenario = normalized_scenario.replace("_", "-")
    return f"eval-{normalized_scenario}-{runtime_id}-{suffix}"


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


def select_issue_seed(scenario: Scenario) -> ScenarioIssueSeed | None:
    if scenario.feature_source is None or not scenario.feature_source.issues:
        return None
    return scenario.feature_source.issues[0]


def derive_source_repository_root(scenario_path: Path) -> Path | None:
    try:
        return repo_root_from(scenario_path.resolve(strict=False))
    except FileNotFoundError:
        try:
            return repo_root_from(Path.cwd().resolve(strict=False))
        except FileNotFoundError:
            return None


def build_issue_selection_payload(
    *,
    scenario: Scenario,
    selected_issue: ScenarioIssueSeed | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "automation_lane": scenario.automation_lane,
        "canonical_runtime": scenario.canonical_runtime,
        "feature_size": scenario.feature_size,
        "fixture_seed": None,
        "scenario_id": scenario.scenario_id,
        "scenario_class": scenario.scenario_class,
        "is_live": scenario.is_live,
        "mode": None if scenario.feature_source is None else scenario.feature_source.mode,
        "selection_policy": (
            None
            if scenario.feature_source is None
            else scenario.feature_source.selection_policy
        ),
        "selected_issue": None,
    }
    if selected_issue is not None:
        payload["selected_issue"] = {
            "id": selected_issue.issue_id,
            "labels": list(selected_issue.labels),
            "summary": selected_issue.summary,
            "title": selected_issue.title,
            "url": selected_issue.url,
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

    selected_issue = select_issue_seed(scenario)
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
        published_package_spec=os.environ.get(
            "AIDD_EVAL_PUBLISHED_PACKAGE_SPEC",
            "",
        ).strip()
        or None,
        resource_layout=resolve_resource_layout(),
        aidd_command=None if scenario.is_live else derive_aidd_command(scenario),
        work_item=derive_work_item(scenario),
        selected_issue=selected_issue,
        issue_selection_payload=build_issue_selection_payload(
            scenario=scenario,
            selected_issue=selected_issue,
        ),
        teardown_commands=derive_teardown_commands(scenario),
    )
