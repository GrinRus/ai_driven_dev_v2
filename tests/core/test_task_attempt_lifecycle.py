from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from aidd.core.implementation_finalization import prepare_task_finalization
from aidd.core.implementation_service import (
    ImplementationExecutionRequest,
    ImplementationExecutionService,
    _complete_task_execution,
    _prepare_task_execution,
)
from aidd.core.mutation_lease import (
    RunMutationConflict,
    acquire_run_mutation_lease,
    acquire_run_mutation_lease_handle,
    use_transferred_run_mutation_lease,
)
from aidd.core.run_store import (
    create_run_manifest,
    load_stage_metadata,
    persist_stage_status,
    run_stage_metadata_path,
)
from aidd.core.stage_preparation import persist_execution_state
from aidd.core.state_machine import StageState
from aidd.core.task_attempt_lifecycle import (
    TaskExecutionContext,
    TaskResumeBlockedError,
    prepare_task_attempt,
    reconcile_task_execution_state,
)
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    ensure_task_ledger,
    load_task_ledger,
    persist_task_ledger,
)
from aidd.core.task_plan import parse_task_plan


def _tasklist(*, second_dependency: str = "TL-1") -> str:
    return f"""# Tasklist

## Task summary

Two bounded tasks with complete dependency and verification evidence.

## Ordered tasks

### TL-1 — Add the contract

- Outcome: The contract is explicit.
- Dominant deliverable: `contracts/example.md` is updated.
- In scope: `contracts/example.md` and `tests/test_contract.py`.
- Acceptance criteria:
  - TL-1-AC1: The required field is documented.

### TL-2 — Add enforcement

- Outcome: Invalid content is rejected.
- Dominant deliverable: `src/example.py` validates the field.
- In scope: `src/example.py` and `tests/test_validator.py`.
- Acceptance criteria:
  - TL-2-AC1: Missing content produces a stable finding.

## Dependencies

- TL-1: none
- TL-2: {second_dependency}

## Verification notes

- TL-1: `pytest tests/test_contract.py -q`
- TL-2: `pytest tests/test_validator.py -q`
"""



def prepare_task_execution(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    project_root: Path,
) -> TaskExecutionContext:
    return _prepare_task_execution(
        request=ImplementationExecutionRequest(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            project_root=project_root,
        ),
        task_id=task_id,
    )


def complete_task_execution(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    project_root: Path,
    succeeded: bool,
    blocker: str | None = None,
) -> TaskLedger:
    return _complete_task_execution(
        context=context,
        request=ImplementationExecutionRequest(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            project_root=project_root,
        ),
        succeeded=succeeded,
        blocker=blocker,
    )

def test_task_ledger_enforces_dependencies_and_hash(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    plan = parse_task_plan(_tasklist())
    ledger = ensure_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        plan=plan,
    )

    assert ledger.ready_task_ids() == ("TL-1",)
    with pytest.raises(ValueError, match="incomplete dependencies"):
        ledger.transition("TL-2", TaskExecutionStatus.EXECUTING)

    ledger = ledger.transition("TL-1", TaskExecutionStatus.EXECUTING)
    ledger = ledger.transition("TL-1", TaskExecutionStatus.SUCCEEDED)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        ledger=ledger,
    )
    assert (
        load_task_ledger(
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
        )
        == ledger
    )
    assert ledger.ready_task_ids() == ("TL-2",)

    changed_plan = parse_task_plan(
        _tasklist().replace("The contract is explicit", "The contract is durable")
    )
    with pytest.raises(ValueError, match="Published tasklist changed"):
        ensure_task_ledger(
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
            plan=changed_plan,
        )

def test_task_ledger_rejects_v1_without_upgrading_finalization() -> None:
    retired = TaskLedger.create(parse_task_plan(_tasklist())).to_dict()
    retired["schema_version"] = 1
    retired.pop("finalization")
    with pytest.raises(ValueError, match="schema_version=2"):
        TaskLedger.from_dict(retired)


def test_task_ledger_v2_round_trip_preserves_finalization_transitions() -> None:
    ledger = TaskLedger.create(parse_task_plan(_tasklist()))
    restored = TaskLedger.from_dict(ledger.to_dict())

    assert restored.schema_version == 2
    assert restored.finalization.status is TaskFinalizationStatus.PENDING
    first = restored.transition("TL-1", TaskExecutionStatus.EXECUTING)
    first = first.transition("TL-1", TaskExecutionStatus.SUCCEEDED)
    first = first.transition("TL-2", TaskExecutionStatus.EXECUTING)
    first = first.transition("TL-2", TaskExecutionStatus.SUCCEEDED)
    finalizing = first.transition_finalization(TaskFinalizationStatus.EXECUTING)
    assert finalizing.finalization.attempt_count == 1
    assert (
        finalizing.transition_finalization(
            TaskFinalizationStatus.FAILED, blocker="publish"
        ).finalization.blocker
        == "publish"
    )

def test_run_mutation_lease_is_reentrant_and_conflicts_between_threads(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run-1"
    with acquire_run_mutation_lease(run_root, operation="outer"):
        with acquire_run_mutation_lease(run_root, operation="inner"):
            assert (run_root / ".mutation-lease").exists()

        import concurrent.futures

        def _acquire_other() -> None:
            with acquire_run_mutation_lease(run_root, operation="other"):
                pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_acquire_other)
            with pytest.raises(RunMutationConflict):
                future.result()

    assert not (run_root / ".mutation-lease").exists()

def test_run_mutation_lease_reclaims_dead_same_host_owner(tmp_path: Path) -> None:
    run_root = tmp_path / "run-1"
    lease_path = run_root / ".mutation-lease"
    lease_path.mkdir(parents=True)
    (lease_path / "owner.json").write_text(
        json.dumps(
            {
                "operation": "crashed",
                "token": "old",
                "pid": 999_999_999,
                "hostname": socket.gethostname(),
            }
        ),
        encoding="utf-8",
    )

    with acquire_run_mutation_lease(run_root, operation="resume") as lease:
        assert lease.operation == "resume"

    assert not lease_path.exists()

def test_run_mutation_lease_can_transfer_to_worker_thread(tmp_path: Path) -> None:
    import concurrent.futures

    run_root = tmp_path / "run-1"
    lease = acquire_run_mutation_lease_handle(run_root, operation="ui-task")

    def _worker() -> str:
        with use_transferred_run_mutation_lease(lease):
            return lease.operation

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        assert executor.submit(_worker).result() == "ui-task"
    assert not (run_root / ".mutation-lease").exists()

def test_interrupted_executing_task_is_abandoned_and_resumed_with_new_attempt(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(_tasklist(), encoding="utf-8")
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        stage="implement",
        status=StageState.EXECUTING.value,
    )

    first = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )
    second = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )

    first_state = json.loads(
        (first.task_attempt_path / "attempt-state.json").read_text(encoding="utf-8")
    )
    assert first_state["status"] == "abandoned"
    assert first_state["created_at_utc"]
    assert first_state["updated_at_utc"]
    assert first_state["created_at_utc"] <= first_state["updated_at_utc"]
    assert second.ledger.entry("TL-1").status is TaskExecutionStatus.EXECUTING
    assert second.ledger.entry("TL-1").attempt_count == 2
    metadata = load_stage_metadata(workspace_root, "WI-1", "run-1", "implement")
    assert metadata is not None
    assert metadata.status == StageState.FAILED.value
    assert [entry.status for entry in metadata.status_history[-2:]] == [
        StageState.EXECUTING.value,
        StageState.FAILED.value,
    ]


def test_reconciliation_repairs_stage_projection_after_ledger_commit(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(_tasklist(), encoding="utf-8")
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        stage="implement",
        status=StageState.EXECUTING.value,
    )
    first = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )
    interrupted = first.ledger.transition(
        "TL-1",
        TaskExecutionStatus.FAILED,
        blocker="Task execution was interrupted; resume creates a new attempt.",
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        ledger=interrupted,
    )

    resumed = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )

    metadata = load_stage_metadata(workspace_root, "WI-1", "run-1", "implement")
    assert metadata is not None
    assert metadata.status == StageState.FAILED.value
    assert [entry.status for entry in metadata.status_history[-2:]] == [
        StageState.EXECUTING.value,
        StageState.FAILED.value,
    ]
    assert resumed.ledger.entry("TL-1").attempt_count == 2

def test_blocked_task_preserves_questions_and_answers_until_resume(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(_tasklist(), encoding="utf-8")
    first = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )
    stage_root = workspace_root / "workitems" / "WI-1" / "stages" / "implement"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n- Q1 [blocking] Which boundary should be used?\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text("# Answers\n\n- none\n", encoding="utf-8")
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        stage="implement",
        status="blocked",
    )
    complete_task_execution(
        context=first,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        project_root=tmp_path,
        succeeded=False,
        blocker="questions",
    )

    with pytest.raises(TaskResumeBlockedError):
        prepare_task_execution(
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
            task_id="TL-1",
            project_root=tmp_path,
        )
    assert (stage_root / "questions.md").exists()
    assert (stage_root / "answers.md").exists()

    (stage_root / "answers.md").write_text(
        "# Answers\n\n- Q1 [resolved] Use the documented boundary.\n",
        encoding="utf-8",
    )
    resumed = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )

    assert (resumed.task_attempt_path / "questions.md").exists()
    assert "[resolved]" in (resumed.task_attempt_path / "answers.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("invalid_file", ("stage-metadata", "run-manifest"))
@pytest.mark.parametrize("operation", (
    "global-attempt", "task-attempt", "new-ledger-service", "reconciliation",
    "finalization", "finalization-service",
))
def test_invalid_current_state_stops_before_attempt_or_ledger_mutation(
    tmp_path: Path, invalid_file: str, operation: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item, run_id = "WI-1", "run-1"
    tasklist = workspace_root / "workitems" / work_item / "stages/tasklist/output/tasklist.md"
    tasklist.parent.mkdir(parents=True)
    tasklist.write_text(_tasklist(), encoding="utf-8")
    manifest_path = create_run_manifest(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id,
        runtime_id="generic-cli", stage_target="implement", config_snapshot={},
    )
    persist_stage_status(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id,
        stage="implement", status="executing",
    )
    ledger = TaskLedger.create(parse_task_plan(_tasklist()))
    if operation == "reconciliation":
        attempt = (
            workspace_root / "reports/runs/WI-1/run-1/stages/implement/tasks/TL-1/attempts"
            / "attempt-0001"
        )
        attempt.mkdir(parents=True)
        (attempt / "task-state.json").write_text('{"status":"executing"}\n')
        ledger = ledger.transition(
            "TL-1", TaskExecutionStatus.EXECUTING,
            latest_attempt_path=attempt.relative_to(workspace_root).as_posix(),
        )
    if operation.startswith("finalization"):
        for task in ledger.tasks:
            ledger = ledger.transition(task.id, TaskExecutionStatus.EXECUTING)
            ledger = ledger.transition(task.id, TaskExecutionStatus.SUCCEEDED)
    if operation != "new-ledger-service":
        persist_task_ledger(
            workspace_root=workspace_root, work_item=work_item, run_id=run_id, ledger=ledger,
        )
    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id, stage="implement",
    )
    invalid_path = metadata_path if invalid_file == "stage-metadata" else manifest_path
    payload = json.loads(invalid_path.read_text())
    payload.pop("schema_version")
    invalid_path.write_text(json.dumps(payload), encoding="utf-8")

    def snapshot() -> dict[str, bytes | None]:
        return {
            path.relative_to(workspace_root).as_posix(): (
                path.read_bytes() if path.is_file() else None
            )
            for path in workspace_root.rglob("*")
        }

    before = snapshot()
    calls: list[str] = []

    def forbidden_callback(context):
        calls.append("runtime/finalizer")
        raise AssertionError("Invalid persisted state must stop before execution")

    service = ImplementationExecutionService(
        task_executor=forbidden_callback, aggregate_finalizer=forbidden_callback,
    )
    request = ImplementationExecutionRequest(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id, project_root=tmp_path,
    )
    with pytest.raises(ValueError, match="schema_version"):
        if operation == "global-attempt":
            persist_execution_state(
                workspace_root=workspace_root, work_item=work_item, run_id=run_id,
                stage="implement", attempt_mode="initial",
            )
        elif operation == "task-attempt":
            prepare_task_attempt(
                workspace_root=workspace_root, work_item=work_item, run_id=run_id,
                task_id="TL-1", project_root=tmp_path,
                repository_baseline=lambda **kwargs: {
                    "schema_version": 1, "task_id": "TL-1", "status": [], "files": {},
                },
            )
        elif operation == "new-ledger-service":
            service.run_task(request, task_id="TL-1")
        elif operation == "reconciliation":
            reconcile_task_execution_state(
                workspace_root=workspace_root, work_item=work_item, run_id=run_id, ledger=ledger,
            )
        elif operation == "finalization-service":
            service.finalize(request)
        else:
            prepare_task_finalization(
                workspace_root=workspace_root, work_item=work_item, run_id=run_id, ledger=ledger,
            )
    assert calls == []
    assert snapshot() == before
