from __future__ import annotations

import json
from pathlib import Path

from aidd.core.run_store import persist_stage_status, run_manifest_path
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState
from aidd.core.workflow_service import (
    WorkflowRunEvent,
    WorkflowRunRequest,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
    run_workflow,
)


def _workflow_request(workspace_root: Path) -> WorkflowRunRequest:
    return WorkflowRunRequest(
        work_item="WI-WORKFLOW",
        runtime_id="generic-cli",
        workspace_root=workspace_root,
        config_path=Path("aidd.test.toml"),
        config_snapshot={"mode": "test"},
    )


def test_run_workflow_executes_stages_without_typer_dependency(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    executed: list[str] = []
    events: list[WorkflowRunEvent] = []

    def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
        executed.append(request.stage)
        persist_stage_status(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
            status=StageState.SUCCEEDED.value,
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


def test_run_workflow_returns_stopped_result_on_stage_failure(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
        if request.stage == "idea":
            persist_stage_status(
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=request.run_id,
                stage=request.stage,
                status=StageState.SUCCEEDED.value,
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
