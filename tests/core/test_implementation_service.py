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
