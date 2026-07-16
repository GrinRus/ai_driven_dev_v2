from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.run_store import (
    create_run_manifest,
    persist_stage_status,
    run_manifest_path,
    work_item_runs_root,
)
from aidd.core.stage_registry import resolve_expected_output_documents
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    persist_task_ledger,
)
from aidd.core.task_plan import parse_task_plan
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
        if stage == "tasklist" and draft_path.name == "tasklist.md":
            content = """# Tasklist

## Task summary

One synthetic workflow task.

## Ordered tasks

### TL-1 — Complete workflow implementation

- Outcome: The workflow implementation is complete.
- Dominant deliverable: `src/example.py`.
- In scope: `src/example.py`.
- Acceptance criteria:
  - TL-1-AC1: The synthetic workflow evidence exists.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: `pytest -q`
"""
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
    if stage == "implement":
        tasklist_path = (
            workspace_root
            / "workitems"
            / work_item
            / "stages"
            / "tasklist"
            / "output"
            / "tasklist.md"
        )
        plan = parse_task_plan(tasklist_path.read_text(encoding="utf-8"))
        ledger = TaskLedger.create(plan)
        ledger = ledger.transition("TL-1", TaskExecutionStatus.EXECUTING, attempt_number=1)
        ledger = ledger.transition("TL-1", TaskExecutionStatus.SUCCEEDED)
        finalization_relative = (
            f"reports/runs/{work_item}/{run_id}/stages/implement/finalization-attempts/attempt-0001"
        )
        ledger = ledger.transition_finalization(
            TaskFinalizationStatus.EXECUTING,
            attempt_number=1,
            latest_attempt_path=finalization_relative,
        )
        ledger = ledger.transition_finalization(TaskFinalizationStatus.SUCCEEDED)
        persist_task_ledger(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            ledger=ledger,
        )
        (workspace_root / finalization_relative).mkdir(parents=True, exist_ok=True)


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


@pytest.mark.parametrize("stage_start", STAGES[1:])
def test_run_workflow_continues_each_non_first_stage_in_requested_run(
    tmp_path: Path,
    stage_start: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = f"WI-CONTINUE-{stage_start.upper()}"
    run_id = "run-existing"
    _seed_required_context(workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
        workflow_stage_start="idea",
        workflow_stage_end="qa",
    )
    for upstream in STAGES[: STAGES.index(stage_start)]:
        _mark_fake_stage_succeeded(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=upstream,
        )

    executed: list[str] = []

    def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
        executed.append(request.stage)
        _mark_fake_stage_succeeded(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
        )

    result = run_workflow(
        request=WorkflowRunRequest(
            work_item=work_item,
            runtime_id="generic-cli",
            workspace_root=workspace_root,
            config_path=Path("aidd.test.toml"),
            config_snapshot={"mode": "test"},
            stage_start=stage_start,
            stage_end=stage_start,
            run_id=run_id,
            continuation=True,
        ),
        stage_executor=_stage_executor,
    )

    assert result.completed is True
    assert result.run_id == run_id
    assert executed == [stage_start]


def test_run_workflow_rejects_non_first_start_without_run_before_allocation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    request = WorkflowRunRequest(
        work_item="WI-NO-RUN",
        runtime_id="generic-cli",
        workspace_root=workspace_root,
        config_path=Path("aidd.test.toml"),
        config_snapshot={"mode": "test"},
        stage_start="research",
        stage_end="research",
    )

    with pytest.raises(ValueError, match="requires an explicit run_id"):
        run_workflow(request=request, stage_executor=lambda _: None)

    assert not work_item_runs_root(workspace_root, "WI-NO-RUN").exists()


def test_run_workflow_rejects_missing_continuation_run_before_allocation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    request = WorkflowRunRequest(
        work_item="WI-MISSING-RUN",
        runtime_id="generic-cli",
        workspace_root=workspace_root,
        config_path=Path("aidd.test.toml"),
        config_snapshot={"mode": "test"},
        stage_start="research",
        stage_end="research",
        run_id="run-missing",
        continuation=True,
    )

    with pytest.raises(ValueError, match="does not exist"):
        run_workflow(request=request, stage_executor=lambda _: None)

    assert not work_item_runs_root(workspace_root, "WI-MISSING-RUN").exists()


@pytest.mark.parametrize(
    ("original_end", "request_start", "request_end", "runtime_id", "expected"),
    (
        ("plan", "research", "qa", "generic-cli", "outside"),
        ("qa", "research", "research", "codex", "immutable fields"),
    ),
)
def test_run_workflow_rejects_incompatible_continuation_without_manifest_mutation(
    tmp_path: Path,
    original_end: str,
    request_start: str,
    request_end: str,
    runtime_id: str,
    expected: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-INCOMPATIBLE"
    run_id = "run-existing"
    manifest_path = create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target=original_end,
        config_snapshot={"mode": "test"},
        workflow_stage_start="idea",
        workflow_stage_end=original_end,
    )
    before = manifest_path.read_bytes()

    with pytest.raises(ValueError, match=expected):
        run_workflow(
            request=WorkflowRunRequest(
                work_item=work_item,
                runtime_id=runtime_id,
                workspace_root=workspace_root,
                config_path=Path("aidd.test.toml"),
                config_snapshot={"mode": "test"},
                stage_start=request_start,
                stage_end=request_end,
                run_id=run_id,
                continuation=True,
            ),
            stage_executor=lambda _: None,
        )

    assert manifest_path.read_bytes() == before


def test_run_workflow_rejects_closed_continuation(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-CLOSED"
    run_id = "run-existing"
    _seed_required_context(workspace_root, work_item=work_item)
    manifest_path = create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target="research",
        config_snapshot={"mode": "test"},
        workflow_stage_start="idea",
        workflow_stage_end="research",
    )
    for stage in ("idea", "research"):
        _mark_fake_stage_succeeded(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
    before = manifest_path.read_bytes()

    with pytest.raises(ValueError, match="already closed"):
        run_workflow(
            request=WorkflowRunRequest(
                work_item=work_item,
                runtime_id="generic-cli",
                workspace_root=workspace_root,
                config_path=Path("aidd.test.toml"),
                config_snapshot={"mode": "test"},
                stage_start="research",
                stage_end="research",
                run_id=run_id,
                continuation=True,
            ),
            stage_executor=lambda _: None,
        )

    assert manifest_path.read_bytes() == before
