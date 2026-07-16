from __future__ import annotations

import json
from pathlib import Path

from aidd.core.run_accountability import resolve_run_accountability
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    write_attempt_artifact_index,
)
from aidd.core.stage_registry import resolve_prompt_pack_file_paths
from aidd.core.stages import STAGES


def _active_prompts(stage: str, mode: str) -> tuple[Path, ...]:
    paths = resolve_prompt_pack_file_paths(stage=stage)
    if mode == "intervention":
        return tuple(
            path for path in paths if path.name not in {"run.md", "repair.md", "interview.md"}
        )
    if mode == "repair":
        return tuple(path for path in paths if path.name != "intervention.md")
    return tuple(path for path in paths if path.name not in {"repair.md", "intervention.md"})


def test_run_accountability_exposes_prompt_config_and_stage_graph(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-acc",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "ui-workflow", "runtime_command": "codex exec"},
        workflow_stage_start="idea",
        workflow_stage_end="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-acc",
        stage="plan",
        status="succeeded",
    )

    view = resolve_run_accountability(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-acc",
    )

    assert view.run_id == "run-acc"
    assert view.runtime_id == "codex"
    assert view.workflow_stage_start == "idea"
    assert view.workflow_stage_end == "plan"
    assert view.config_snapshot["mode"] == "ui-workflow"
    assert view.prompt_pack_provenance
    assert view.prompt_pack_provenance[0].sha256
    assert view.stage_graph[:3] == ("idea", "research", "plan")
    assert view.stages[0].stage == "plan"
    assert view.stages[0].status == "succeeded"


def test_run_accountability_warns_for_legacy_prompt_provenance(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest_path = create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-legacy",
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"mode": "legacy"},
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["prompt_pack_provenance"] = []
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    view = resolve_run_accountability(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-legacy",
    )

    assert view.prompt_pack_provenance == ()
    assert any("no prompt-pack provenance" in warning for warning in view.warnings)


def test_run_accountability_aggregates_ordered_per_attempt_prompt_provenance(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-FULL-FLOW",
        run_id="run-full",
        runtime_id="codex",
        stage_target="qa",
        config_snapshot={"mode": "workflow"},
        workflow_stage_start="idea",
        workflow_stage_end="qa",
    )
    expected_modes: list[tuple[str, int, str]] = []
    for stage in STAGES:
        attempt = create_next_attempt_directory(
            workspace_root=workspace_root,
            work_item="WI-FULL-FLOW",
            run_id="run-full",
            stage=stage,
        )
        _ = attempt
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item="WI-FULL-FLOW",
            run_id="run-full",
            stage=stage,
            attempt_number=1,
            attempt_mode="initial",
            prompt_pack_paths=_active_prompts(stage, "initial"),
        )
        expected_modes.append((stage, 1, "initial"))
        if stage in {"plan", "review"}:
            mode = "repair" if stage == "plan" else "intervention"
            create_next_attempt_directory(
                workspace_root=workspace_root,
                work_item="WI-FULL-FLOW",
                run_id="run-full",
                stage=stage,
            )
            write_attempt_artifact_index(
                workspace_root=workspace_root,
                work_item="WI-FULL-FLOW",
                run_id="run-full",
                stage=stage,
                attempt_number=2,
                attempt_mode=mode,
                prompt_pack_paths=_active_prompts(stage, mode),
            )
            expected_modes.append((stage, 2, mode))

    view = resolve_run_accountability(
        workspace_root=workspace_root,
        work_item="WI-FULL-FLOW",
        run_id="run-full",
    )

    assert [
        (attempt.stage, attempt.attempt_number, attempt.attempt_mode) for attempt in view.attempts
    ] == expected_modes
    plan_repair = next(
        attempt
        for attempt in view.attempts
        if attempt.stage == "plan" and attempt.attempt_number == 2
    )
    review_intervention = next(
        attempt
        for attempt in view.attempts
        if attempt.stage == "review" and attempt.attempt_number == 2
    )
    assert any(prompt.path.endswith("/repair.md") for prompt in plan_repair.prompt_pack_provenance)
    assert not any(
        prompt.path.endswith("/intervention.md") for prompt in plan_repair.prompt_pack_provenance
    )
    assert {Path(prompt.path).name for prompt in review_intervention.prompt_pack_provenance} == {
        "system.md",
        "intervention.md",
    }
    assert any(prompt.path.endswith("/plan/repair.md") for prompt in view.prompt_pack_provenance)
    assert any(
        prompt.path.endswith("/review/intervention.md") for prompt in view.prompt_pack_provenance
    )
    assert not any("Attempt mode is missing" in warning for warning in view.warnings)


def test_run_accountability_marks_legacy_attempt_mode_unknown(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-LEGACY-ATTEMPT",
        run_id="run-legacy",
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"mode": "legacy"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-LEGACY-ATTEMPT",
        run_id="run-legacy",
        stage="idea",
    )
    index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-LEGACY-ATTEMPT",
        run_id="run-legacy",
        stage="idea",
        attempt_number=1,
    )
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload.pop("attempt_mode", None)
    index_path.write_text(json.dumps(payload), encoding="utf-8")

    view = resolve_run_accountability(
        workspace_root=workspace_root,
        work_item="WI-LEGACY-ATTEMPT",
        run_id="run-legacy",
    )

    assert view.attempts[0].attempt_mode == "unknown"
    assert view.attempts[0].prompt_pack_provenance
    assert any("legacy idea attempt 1" in warning for warning in view.warnings)


def test_run_accountability_does_not_fabricate_prompts_for_corrupt_attempt(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-CORRUPT-ATTEMPT",
        run_id="run-corrupt",
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-CORRUPT-ATTEMPT",
        run_id="run-corrupt",
        stage="idea",
    )
    index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-CORRUPT-ATTEMPT",
        run_id="run-corrupt",
        stage="idea",
        attempt_number=1,
    )
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["attempt_mode"] = "invented"
    index_path.write_text(json.dumps(payload), encoding="utf-8")

    view = resolve_run_accountability(
        workspace_root=workspace_root,
        work_item="WI-CORRUPT-ATTEMPT",
        run_id="run-corrupt",
    )

    assert view.attempts[0].attempt_mode == "unknown"
    assert view.attempts[0].prompt_pack_provenance == ()
    assert view.prompt_pack_provenance == ()
    assert any("malformed for idea attempt 1" in warning for warning in view.warnings)
