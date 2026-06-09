from __future__ import annotations

import json
from pathlib import Path

from aidd.core.run_store import persist_stage_status, run_manifest_path
from aidd.core.stage_registry import resolve_expected_output_documents
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState
from aidd.core.workflow_service import (
    WorkflowRunEvent,
    WorkflowRunRequest,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
    run_workflow,
)
from aidd.core.workspace import WorkspaceBootstrapService


def _workflow_request(workspace_root: Path) -> WorkflowRunRequest:
    return WorkflowRunRequest(
        work_item="WI-WORKFLOW",
        runtime_id="generic-cli",
        workspace_root=workspace_root,
        config_path=Path("aidd.test.toml"),
        config_snapshot={"mode": "test"},
    )


def _seed_required_context(workspace_root: Path, *, work_item: str) -> None:
    bootstrap = WorkspaceBootstrapService(root=workspace_root)
    bootstrap.bootstrap_work_item(work_item=work_item)
    bootstrap.seed_request_context(
        work_item=work_item,
        request_text=f"Run workflow test for {work_item}.",
        project_root=workspace_root.parent,
        force=True,
    )


def _write_fake_stage_outputs(
    workspace_root: Path,
    *,
    work_item: str,
    stage: str,
) -> None:
    for draft_path in resolve_expected_output_documents(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    ):
        content = f"# {draft_path.stem.title()}\n\nSynthetic output for {stage}.\n"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(content, encoding="utf-8")
        published_path = draft_path.parent / "output" / draft_path.name
        published_path.parent.mkdir(parents=True, exist_ok=True)
        published_path.write_text(content, encoding="utf-8")


def _mark_fake_stage_succeeded(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> None:
    _write_fake_stage_outputs(
        workspace_root,
        work_item=work_item,
        stage=stage,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.SUCCEEDED.value,
    )


def test_run_workflow_executes_stages_without_typer_dependency(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    executed: list[str] = []
    events: list[WorkflowRunEvent] = []
    _seed_required_context(workspace_root, work_item="WI-WORKFLOW")

    def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
        executed.append(request.stage)
        _mark_fake_stage_succeeded(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
        )

    result = run_workflow(
        request=_workflow_request(workspace_root),
        stage_executor=_stage_executor,
        emit=events.append,
    )

    assert result.completed is True
    assert result.executed_stage_count == len(STAGES)
    assert executed == list(STAGES)
    assert [event.kind for event in events if event.kind == "completed"] == ["completed"]
    manifest = json.loads(
        run_manifest_path(
            workspace_root=workspace_root,
            work_item="WI-WORKFLOW",
            run_id=result.run_id,
        ).read_text(encoding="utf-8")
    )
    assert manifest["workflow_bounds"] == {"start": "idea", "end": "qa"}


def test_run_workflow_persists_optional_lineage_in_manifest(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _seed_required_context(workspace_root, work_item="WI-FOLLOW-UP")

    def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
        _mark_fake_stage_succeeded(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
        )

    result = run_workflow(
        request=WorkflowRunRequest(
            work_item="WI-FOLLOW-UP",
            runtime_id="generic-cli",
            workspace_root=workspace_root,
            config_path=Path("aidd.test.toml"),
            config_snapshot={"mode": "test"},
            lineage={
                "source_work_item_id": "WI-SOURCE",
                "source_run_id": "run-source",
                "baseline_id": "run-source",
            },
            stage_start="idea",
            stage_end="idea",
        ),
        stage_executor=_stage_executor,
    )

    manifest = json.loads(
        run_manifest_path(
            workspace_root=workspace_root,
            work_item="WI-FOLLOW-UP",
            run_id=result.run_id,
        ).read_text(encoding="utf-8")
    )
    assert manifest["lineage"] == {
        "baseline_id": "run-source",
        "source_run_id": "run-source",
        "source_work_item_id": "WI-SOURCE",
    }


def test_run_workflow_returns_stopped_result_on_stage_failure(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _seed_required_context(workspace_root, work_item="WI-WORKFLOW")

    def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
        if request.stage == "idea":
            _mark_fake_stage_succeeded(
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=request.run_id,
                stage=request.stage,
            )
            return
        persist_stage_status(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
            status=StageState.FAILED.value,
        )
        raise WorkflowStageExecutionError(stage=request.stage, exit_code=7)

    result = run_workflow(
        request=_workflow_request(workspace_root),
        stage_executor=_stage_executor,
    )

    assert result.completed is False
    assert result.stopped_stage == "research"
    assert result.exit_code == 7
    assert [summary.stage for summary in result.incomplete][:1] == ["research"]
