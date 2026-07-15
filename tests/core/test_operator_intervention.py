from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.operator_intervention import (
    ensure_intervention_allowed_for_downstream,
    persist_operator_intervention_request,
    resolve_intervention_run_id,
    validate_operator_target_documents,
)
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    load_stage_metadata,
    persist_stage_status,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_runner import (
    AdapterExecutionOutcome,
    AdapterInvocationBundle,
    StageExecutionState,
    prepare_stage_bundle,
    run_single_stage_orchestration,
)
from aidd.core.state_machine import StageState


def _materialize_plan_inputs(*, workspace_root: Path, work_item: str) -> None:
    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="plan",
    )
    for index, path in enumerate(bundle.expected_input_bundle, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Input {index}\n\nPrepared.\n", encoding="utf-8")


def _valid_plan_outputs() -> dict[str, str]:
    return {
        "plan.md": (
            "# Plan\n\n"
            "## Goals\n\n- Deliver a reviewable execution plan.\n\n"
            "## Out of scope\n\n- Runtime migration is excluded.\n\n"
            "## Milestones\n\n- M1: Draft and validate plan.\n\n"
            "## Implementation strategy\n\n- Use staged, document-first increments.\n\n"
            "## Risks\n\n- Risk: Missing constraints; mitigation: clarify assumptions.\n\n"
            "## Dependencies\n\n- Research artifacts from prior stage.\n\n"
            "## Verification approach\n\n- Run structural and semantic checks.\n\n"
            "## Verification notes\n\n"
            "- M1: Validate highest-risk milestone with targeted tests.\n"
        ),
        "stage-result.md": (
            "# Stage result\n\n"
            "## Stage\n\nplan\n\n"
            "## Attempt history\n\n- Attempt 1 (`intervention`): applied operator request.\n\n"
            "## Status\n\nsucceeded\n\n"
            "## Produced outputs\n\n- plan.md\n\n"
            "## Validation summary\n\n- structural: pass\n\n"
            "## Blockers\n\n- none\n\n"
            "## Next actions\n\n- advance\n\n"
            "## Terminal state notes\n\nReady.\n"
        ),
        "validator-report.md": (
            "# Validator Report\n\n"
            "## Summary\n\n- Total issues: 0\n\n"
            "## Structural checks\n\n- none\n\n"
            "## Semantic checks\n\n- none\n\n"
            "## Cross-document checks\n\n- none\n\n"
            "## Result\n\n- Verdict: `pass`\n"
        ),
        "questions.md": "# Questions\n\n- none\n",
        "answers.md": "# Answers\n\n- none\n",
    }


def test_operator_request_artifact_allocates_markdown_path(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-OP")
    stage_root = workspace_root / "workitems" / "WI-OP" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("plan.md").write_text("# Plan\n", encoding="utf-8")

    first = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item="WI-OP",
        stage="plan",
        request_text="Add rollback risks.",
        target_documents=("plan.md",),
        created_by="cli",
    )
    second = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item="WI-OP",
        stage="plan",
        request_text="Tighten verification notes.",
    )

    assert first.request_id == "request-0001"
    assert second.request_id == "request-0002"
    assert first.request_path == (
        workspace_root
        / "workitems"
        / "WI-OP"
        / "stages"
        / "plan"
        / "operator-requests"
        / "request-0001.md"
    )
    text = first.request_path.read_text(encoding="utf-8")
    assert "## Request\n\nAdd rollback risks." in text
    assert "- `workitems/WI-OP/stages/plan/plan.md`" in text
    assert "Operator: `cli`" in text


def test_operator_request_validation_rejects_empty_and_out_of_scope_targets(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-OP")

    with pytest.raises(ValueError, match="must not be empty"):
        persist_operator_intervention_request(
            workspace_root=workspace_root,
            work_item="WI-OP",
            stage="plan",
            request_text=" ",
        )
    with pytest.raises(ValueError, match="outside current stage scope"):
        validate_operator_target_documents(
            workspace_root=workspace_root,
            work_item="WI-OP",
            stage="plan",
            target_documents=("workitems/WI-OP/stages/research/research-notes.md",),
        )
    with pytest.raises(ValueError, match="AIDD-owned"):
        validate_operator_target_documents(
            workspace_root=workspace_root,
            work_item="WI-OP",
            stage="plan",
            target_documents=("repair-brief.md",),
        )


def test_intervention_uses_latest_run_and_blocks_succeeded_downstream(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-OP",
        run_id="run-op",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-OP",
        run_id="run-op",
        stage="implement",
        status=StageState.SUCCEEDED.value,
    )

    assert resolve_intervention_run_id(
        workspace_root=workspace_root,
        work_item="WI-OP",
    ) == "run-op"
    with pytest.raises(ValueError, match="downstream stages already succeeded"):
        ensure_intervention_allowed_for_downstream(
            workspace_root=workspace_root,
            work_item="WI-OP",
            run_id="run-op",
            stage="plan",
        )


def test_intervention_attempt_includes_existing_outputs_request_and_answers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-OP"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    stage_root = workspace_root / "workitems" / work_item / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("plan.md").write_text("# Plan\n\nExisting plan.\n", encoding="utf-8")
    stage_root.joinpath("questions.md").write_text(
        "# Questions\n\n- `Q1` `[blocking]` Confirm rollback policy.\n",
        encoding="utf-8",
    )
    stage_root.joinpath("answers.md").write_text(
        "# Answers\n\n- `Q1` `[resolved]` Rollback is required.\n",
        encoding="utf-8",
    )
    request = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="plan",
        request_text="Add rollback risks.",
        target_documents=("plan.md",),
    )
    captured: dict[str, AdapterInvocationBundle] = {}

    def _executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        captured["invocation"] = invocation
        for name, content in _valid_plan_outputs().items():
            stage_root.joinpath(name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True)

    result = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        stage="plan",
        adapter_executor=_executor,
        intervention_request_path=request.request_path,
    )

    invocation = captured["invocation"]
    input_paths = {
        workspace_relative_path(workspace_root, path)
        for path in invocation.expected_input_bundle
    }
    assert invocation.attempt_mode == "intervention"
    assert invocation.repair_mode is False
    assert invocation.operator_request_path == request.request_path
    assert "Add rollback risks." in invocation.input_bundle_markdown
    assert "Existing plan." in invocation.input_bundle_markdown
    assert "Rollback is required." in invocation.input_bundle_markdown
    assert workspace_relative_path(workspace_root, request.request_path) in input_paths
    assert result.transition.next_state is StageState.SUCCEEDED


def test_first_intervention_attempt_records_intervention_history(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-OP"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    stage_root = workspace_root / "workitems" / work_item / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("plan.md").write_text("# Plan\n\nExisting plan.\n", encoding="utf-8")
    request = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="plan",
        request_text="Add rollback risks.",
        target_documents=("plan.md",),
    )

    def _executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        assert invocation.attempt_mode == "intervention"
        assert execution_state.attempt_number == 1
        for name, content in _valid_plan_outputs().items():
            stage_root.joinpath(name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True)

    result = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        stage="plan",
        adapter_executor=_executor,
        intervention_request_path=request.request_path,
    )

    assert result.transition.next_state is StageState.SUCCEEDED
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        stage="plan",
    )
    assert metadata is not None
    assert [(entry.attempt_number, entry.trigger) for entry in metadata.repair_history] == [
        (1, "intervention")
    ]
    stage_result_text = stage_root.joinpath("stage-result.md").read_text(encoding="utf-8")
    assert "- Attempt `1` (`intervention`) -> succeeded." in stage_result_text


def test_intervention_terminal_attempt_records_intervention_history_after_prior_attempt(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-OP"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        stage="plan",
        status=StageState.FAILED.value,
    )
    stage_root = workspace_root / "workitems" / work_item / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("plan.md").write_text("# Plan\n\nExisting plan.\n", encoding="utf-8")
    request = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="plan",
        request_text="Add rollback risks.",
        target_documents=("plan.md",),
    )

    def _executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        assert invocation.attempt_mode == "intervention"
        assert execution_state.attempt_number == 2
        for name, content in _valid_plan_outputs().items():
            stage_root.joinpath(name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True)

    result = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        stage="plan",
        adapter_executor=_executor,
        intervention_request_path=request.request_path,
    )

    assert result.transition.next_state is StageState.SUCCEEDED
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-op",
        stage="plan",
    )
    assert metadata is not None
    assert [(entry.attempt_number, entry.trigger) for entry in metadata.repair_history] == [
        (2, "intervention")
    ]
    stage_result_text = stage_root.joinpath("stage-result.md").read_text(encoding="utf-8")
    assert "- Attempt `2` (`intervention`) -> succeeded." in stage_result_text


def test_operator_intervention_rejects_symlinked_overlay_escape(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_root = workspace_root / "workitems" / "WI-OP" / "stages" / "plan"
    stage_root.mkdir(parents=True)
    outside = tmp_path / "outside-operator-requests"
    outside.mkdir()
    (stage_root / "operator-requests").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="owning root|storage boundary"):
        persist_operator_intervention_request(
            workspace_root=workspace_root,
            work_item="WI-OP",
            stage="plan",
            request_text="Add rollback risks.",
        )

    assert list(outside.iterdir()) == []
