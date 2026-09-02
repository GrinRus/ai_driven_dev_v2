from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.implementation_service import (
    AggregateFinalizationOutcome,
    ImplementationExecutionRequest,
    ImplementationExecutionService,
    ImplementationExecutionStatus,
    ImplementationFinalizationError,
    ImplementationNextTarget,
    ImplementationPortError,
    ImplementationSourceMismatchError,
    TaskAttemptOutcome,
)
from aidd.core.run_store import load_stage_metadata, persist_stage_status
from aidd.core.state_machine import StageState
from aidd.core.task_ledger import TaskExecutionStatus


def _write_tasklist(workspace_root: Path, *, suffix: str = "") -> Path:
    path = (
        workspace_root
        / "workitems"
        / "WI-SERVICE"
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Tasklist

## Task summary

Two tasks exercise the implementation service.{suffix}

## Ordered tasks

### TL-1 — Add the contract

- Outcome: The contract is explicit.
- Dominant deliverable: `contracts/example.md` records the contract.
- In scope: `contracts/example.md`.
- Acceptance criteria:
  - TL-1-AC1: The contract exists.

### TL-2 — Add enforcement

- Outcome: Enforcement is observable.
- Dominant deliverable: `src/example.py` enforces the contract.
- In scope: `src/example.py`.
- Acceptance criteria:
  - TL-2-AC1: Enforcement exists.

## Dependencies

- TL-1: none
- TL-2: TL-1

## Verification notes

- TL-1: `pytest tests/test_contract.py -q`
- TL-2: `pytest tests/test_example.py -q`
""",
        encoding="utf-8",
    )
    return path


def _request(tmp_path: Path) -> ImplementationExecutionRequest:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)
    return ImplementationExecutionRequest(
        workspace_root=workspace_root,
        work_item="WI-SERVICE",
        run_id="run-1",
        project_root=tmp_path,
    )


def _successful_executor(request: ImplementationExecutionRequest):
    def execute(context):  # type: ignore[no-untyped-def]
        target_path = context.task.scope_paths[0]
        target = request.project_root / target_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"completed = '{context.task.id}'\n", encoding="utf-8")
        report = (
            request.workspace_root
            / "workitems"
            / request.work_item
            / "stages"
            / "implement"
            / "implementation-report.md"
        )
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            "# Implementation Report\n\n"
            f"## Selected task\n\n- Task id: `{context.task.id}`\n\n"
            "## Change summary\n\nCompleted the selected task.\n\n"
            f"## Touched files\n\n- `{target_path}` - completed task.\n\n"
            "## Verification notes\n\n- check -> pass.\n\n"
            "## Follow-up notes\n\n- none\n",
            encoding="utf-8",
        )
        return TaskAttemptOutcome(succeeded=True)

    return execute


def test_run_all_preserves_dependency_order_and_finalizes(tmp_path: Path) -> None:
    request = _request(tmp_path)
    executed: list[str] = []
    executor = _successful_executor(request)

    def ordered(context):  # type: ignore[no-untyped-def]
        executed.append(context.task.id)
        return executor(context)

    service = ImplementationExecutionService(
        task_executor=ordered,
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(
            succeeded=True, published=True
        ),
    )

    result = service.run_all(request)

    assert executed == ["TL-1", "TL-2"]
    assert result.status is ImplementationExecutionStatus.SUCCEEDED
    assert result.next_target is ImplementationNextTarget.COMPLETE
    assert result.published is True
    assert result.ledger.all_succeeded()


def test_run_all_finalizes_after_clean_verification_only_task(tmp_path: Path) -> None:
    request = _request(tmp_path)
    tasklist_path = (
        request.workspace_root
        / "workitems"
        / request.work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    tasklist_path.write_text(
        tasklist_path.read_text(encoding="utf-8").replace(
            "- In scope: `src/example.py`.",
            "- In scope: `src/example.py`.\n- Execution mode: verification-only",
        ),
        encoding="utf-8",
    )
    executed: list[str] = []

    def executor(context):  # type: ignore[no-untyped-def]
        executed.append(context.task.id)
        report = (
            request.workspace_root
            / "workitems"
            / request.work_item
            / "stages"
            / "implement"
            / "implementation-report.md"
        )
        report.parent.mkdir(parents=True, exist_ok=True)
        if context.task.id == "TL-1":
            target = request.project_root / "contracts" / "example.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("contract\n", encoding="utf-8")
            touched = "- `contracts/example.md` - completed task."
        else:
            touched = "- none"
        report.write_text(
            "# Implementation Report\n\n"
            f"## Selected task\n\n- Task id: `{context.task.id}`\n\n"
            "## Change summary\n\nCompleted the selected task.\n\n"
            f"## Touched files\n\n{touched}\n\n"
            "## Verification notes\n\n- check -> pass.\n\n"
            "## Follow-up notes\n\n- none\n",
            encoding="utf-8",
        )
        return TaskAttemptOutcome(succeeded=True)

    service = ImplementationExecutionService(
        task_executor=executor,
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(
            succeeded=True,
            published=True,
        ),
    )

    result = service.run_all(request)

    assert executed == ["TL-1", "TL-2"]
    assert result.status is ImplementationExecutionStatus.SUCCEEDED
    assert result.published is True
    assert result.ledger.all_succeeded()


def test_run_task_does_not_publish_or_finalize(tmp_path: Path) -> None:
    request = _request(tmp_path)
    finalized = False

    def finalizer(context):  # type: ignore[no-untyped-def]
        nonlocal finalized
        finalized = True
        return AggregateFinalizationOutcome(succeeded=True, published=True)

    service = ImplementationExecutionService(
        task_executor=_successful_executor(request),
        aggregate_finalizer=finalizer,
    )

    result = service.run_task(request, task_id="TL-1")

    assert finalized is False
    assert result.next_target is ImplementationNextTarget.TASK
    assert result.next_task_id == "TL-2"
    assert result.published is False


def test_executor_exception_terminalizes_attempt_before_reraise(tmp_path: Path) -> None:
    request = _request(tmp_path)

    def explode(context):  # type: ignore[no-untyped-def]
        raise RuntimeError("adapter exploded")

    service = ImplementationExecutionService(
        task_executor=explode,
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(succeeded=True),
    )

    with pytest.raises(ImplementationPortError) as captured:
        service.run_task(request, task_id="TL-1")

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert captured.value.ledger is not None
    entry = captured.value.ledger.entry("TL-1")
    assert entry.status.value == "failed"
    assert entry.blocker == "adapter exploded"


def test_failed_task_keeps_implementation_stage_failed_not_blocked(tmp_path: Path) -> None:
    request = _request(tmp_path)

    service = ImplementationExecutionService(
        task_executor=lambda context: TaskAttemptOutcome(
            succeeded=False,
            blocker="validator failed",
        ),
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(succeeded=True),
    )

    result = service.run_task(request, task_id="TL-1")

    assert result.ledger.entry("TL-1").status is TaskExecutionStatus.FAILED
    metadata = load_stage_metadata(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage="implement",
    )
    assert metadata is not None
    assert metadata.status == "failed"


def test_retry_repairs_legacy_blocked_stage_status_for_failed_task(tmp_path: Path) -> None:
    request = _request(tmp_path)
    persist_stage_status(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage="implement",
        status=StageState.BLOCKED.value,
    )

    service = ImplementationExecutionService(
        task_executor=lambda context: TaskAttemptOutcome(
            succeeded=False,
            blocker="validator failed again",
        ),
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(succeeded=True),
    )

    result = service.run_task(request, task_id="TL-1")

    assert result.ledger.entry("TL-1").status is TaskExecutionStatus.FAILED
    metadata = load_stage_metadata(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage="implement",
    )
    assert metadata is not None
    assert metadata.status == StageState.FAILED.value
    assert [entry.status for entry in metadata.status_history[-2:]] == [
        StageState.PREPARING.value,
        StageState.FAILED.value,
    ]


def test_failed_task_preserves_genuine_question_block(tmp_path: Path) -> None:
    request = _request(tmp_path)
    stage_root = (
        request.workspace_root
        / "workitems"
        / request.work_item
        / "stages"
        / "implement"
    )
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n"
        "- Q1 [blocking] Confirm the release owner.\n",
        encoding="utf-8",
    )
    persist_stage_status(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage="implement",
        status=StageState.BLOCKED.value,
    )

    service = ImplementationExecutionService(
        task_executor=lambda context: TaskAttemptOutcome(
            succeeded=False,
            blocker="cannot proceed",
        ),
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(succeeded=True),
    )

    result = service.run_task(request, task_id="TL-1")

    assert result.ledger.entry("TL-1").status is TaskExecutionStatus.BLOCKED
    metadata = load_stage_metadata(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage="implement",
    )
    assert metadata is not None
    assert metadata.status == StageState.BLOCKED.value


def test_finalize_rejects_incomplete_ledger(tmp_path: Path) -> None:
    request = _request(tmp_path)
    service = ImplementationExecutionService(
        task_executor=_successful_executor(request),
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(succeeded=True),
    )
    service.run_task(request, task_id="TL-1")

    with pytest.raises(ImplementationFinalizationError, match="before every task"):
        service.finalize(request)


def test_changed_tasklist_source_fails_closed(tmp_path: Path) -> None:
    request = _request(tmp_path)
    service = ImplementationExecutionService(
        task_executor=_successful_executor(request),
        aggregate_finalizer=lambda context: AggregateFinalizationOutcome(succeeded=True),
    )
    service.run_task(request, task_id="TL-1")
    _write_tasklist(request.workspace_root, suffix=" Source changed.")

    with pytest.raises(ImplementationSourceMismatchError):
        service.run_all(request)


def test_service_has_no_cli_or_typer_imports() -> None:
    source = Path("src/aidd/core/implementation_service.py").read_text(encoding="utf-8")

    assert "aidd.cli" not in source
    assert "import typer" not in source
