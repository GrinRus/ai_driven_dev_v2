from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from aidd.core.implementation_service import (
    ImplementationExecutionRequest,
    _complete_task_execution,
    _prepare_task_execution,
)
from aidd.core.mutation_lease import (
    RunMutationConflict,
    acquire_run_mutation_lease,
    acquire_run_mutation_lease_handle,
    use_transferred_run_mutation_lease,
)
from aidd.core.run_store import persist_stage_status
from aidd.core.task_attempt_lifecycle import TaskExecutionContext, TaskResumeBlockedError
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

def test_task_ledger_v1_defaults_finalization_and_v2_transitions() -> None:
    ledger = TaskLedger.create(parse_task_plan(_tasklist()))
    legacy = ledger.to_dict()
    legacy["schema_version"] = 1
    legacy.pop("finalization")

    restored = TaskLedger.from_dict(legacy)

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
    assert second.ledger.entry("TL-1").status is TaskExecutionStatus.EXECUTING
    assert second.ledger.entry("TL-1").attempt_count == 2

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
