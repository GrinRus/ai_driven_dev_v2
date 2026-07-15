from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from aidd.core.identifiers import SafeIdentifier, resolve_contained_component
from aidd.core.mutation_lease import (
    RunMutationConflict,
    acquire_run_mutation_lease,
    acquire_run_mutation_lease_handle,
    use_transferred_run_mutation_lease,
)
from aidd.core.run_store import persist_stage_status
from aidd.core.task_attempt_lifecycle import TaskExecutionContext, TaskResumeBlockedError
from aidd.core.task_execution import complete_task_execution, prepare_task_execution
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    ensure_task_ledger,
    load_task_ledger,
    persist_task_ledger,
)
from aidd.core.task_plan import TaskPlanParseError, parse_task_plan
from aidd.core.task_repository_evidence import task_diff_evidence


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


def test_parse_task_plan_preserves_order_and_acceptance() -> None:
    plan = parse_task_plan(_tasklist())

    assert plan.ordered_ids() == ("TL-1", "TL-2")
    assert plan.tasks[1].dependencies == ("TL-1",)
    assert plan.tasks[1].acceptance_criteria[0].id == "TL-2-AC1"


@pytest.mark.parametrize("value", ("", ".", "..", "../task", "task/child", "/task"))
def test_safe_identifier_rejects_unsafe_path_components(tmp_path: Path, value: str) -> None:
    with pytest.raises(ValueError):
        SafeIdentifier.parse(value, label="task id")
    with pytest.raises(ValueError):
        resolve_contained_component(tmp_path, value, label="task id")


@pytest.mark.parametrize(
    "invalid_text",
    (
        "- Outcome: The contract is explicit.\n",
        "- Dominant deliverable: `contracts/example.md` is updated.\n",
        "- In scope: `contracts/example.md` and `tests/test_contract.py`.\n",
        "  - TL-1-AC1: The required field is documented.\n",
    ),
)
def test_parse_task_plan_rejects_each_missing_card_field(invalid_text: str) -> None:
    markdown = _tasklist().replace(invalid_text, "")

    with pytest.raises(TaskPlanParseError):
        parse_task_plan(markdown)


def test_parse_task_plan_rejects_unknown_dependency() -> None:
    with pytest.raises(TaskPlanParseError, match="unknown dependencies"):
        parse_task_plan(_tasklist(second_dependency="TL-9"))


def test_parse_task_plan_rejects_dependency_cycle() -> None:
    markdown = _tasklist().replace("- TL-1: none", "- TL-1: TL-2")

    with pytest.raises(TaskPlanParseError, match="cycle"):
        parse_task_plan(markdown)


def test_parse_task_plan_rejects_forward_dependency() -> None:
    markdown = _tasklist(second_dependency="none").replace("- TL-1: none", "- TL-1: TL-2")

    with pytest.raises(TaskPlanParseError, match="do not appear earlier"):
        parse_task_plan(markdown)


@pytest.mark.parametrize(
    "scope",
    (
        "Contract text without a concrete path.",
        "`../contracts/example.md`.",
        "`/tmp/example.md`.",
        "`src/**/*.py`.",
    ),
)
def test_parse_task_plan_rejects_missing_or_unsafe_scope_path(scope: str) -> None:
    markdown = _tasklist().replace("`contracts/example.md` and `tests/test_contract.py`.", scope)

    with pytest.raises(TaskPlanParseError, match="in-scope path|repository-relative"):
        parse_task_plan(markdown)


def test_parse_task_plan_rejects_duplicate_and_mixed_task_ids() -> None:
    duplicate = _tasklist().replace(
        "### TL-2 — Add enforcement",
        "### TL-1 — Add enforcement",
    )
    with pytest.raises(TaskPlanParseError, match="Duplicate task ids"):
        parse_task_plan(duplicate)

    mixed = _tasklist().replace("TL-2", "T2")
    with pytest.raises(TaskPlanParseError, match="must not mix"):
        parse_task_plan(mixed)


def test_task_diff_uses_canonical_scope_component_boundary_and_malformed_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    project_root = tmp_path / "project"
    project_root.mkdir()
    plan = parse_task_plan(
        _tasklist().replace(
            "`contracts/example.md` and `tests/test_contract.py`.",
            "`src`.",
        )
    )
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "repository-baseline.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "TL-1",
                "status": [],
                "files": {},
            }
        ),
        encoding="utf-8",
    )
    context = TaskExecutionContext(
        plan=plan,
        ledger=TaskLedger.create(plan),
        task=plan.tasks[0],
        global_attempt_start=1,
        task_attempt_path=attempt,
    )
    monkeypatch.setattr(
        "aidd.core.task_repository_evidence.repository_file_snapshot",
        lambda _: {"src2/app.py": "changed"},
    )
    scope_path = workspace_root / "workitems" / "WI-1" / "context" / "allowed-write-scope.md"
    scope_path.parent.mkdir(parents=True)
    scope_path.write_text("# Allowed Write Scope\n\n- `src`\n", encoding="utf-8")

    _, issues = task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        project_root=project_root,
        report="## Touched files\n\n- `src2/app.py`\n",
    )
    assert any("outside allowed write scope" in issue for issue in issues)

    scope_path.write_text("# Allowed Write Scope\n\n- `../escape`\n", encoding="utf-8")
    _, malformed_issues = task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        project_root=project_root,
        report="## Touched files\n\n- `src2/app.py`\n",
    )
    assert any("Allowed write scope" in issue for issue in malformed_issues)


def test_parse_task_plan_rejects_malformed_and_duplicate_acceptance_ids() -> None:
    malformed = _tasklist().replace("TL-1-AC1", "TL-1-C1")
    with pytest.raises(TaskPlanParseError, match="malformed acceptance id"):
        parse_task_plan(malformed)

    duplicate = _tasklist().replace(
        "  - TL-1-AC1: The required field is documented.\n",
        "  - TL-1-AC1: The required field is documented.\n  - TL-1-AC1: The same id is repeated.\n",
    )
    with pytest.raises(TaskPlanParseError, match="duplicate acceptance ids"):
        parse_task_plan(duplicate)


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


def test_task_attempt_records_diff_relative_to_its_own_baseline(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(_tasklist(), encoding="utf-8")
    source_path = tmp_path / "contracts" / "example.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("before\n", encoding="utf-8")

    context = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )
    source_path.write_text("after\n", encoding="utf-8")
    report_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "implement" / "implementation-report.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `contracts/example.md` - updated contract.\n",
        encoding="utf-8",
    )

    ledger = complete_task_execution(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        project_root=tmp_path,
        succeeded=True,
    )

    assert ledger.entry("TL-1").status is TaskExecutionStatus.SUCCEEDED
    diff_payload = (context.task_attempt_path / "task-diff.json").read_text(encoding="utf-8")
    assert '"observed_touched_paths": [\n    "contracts/example.md"' in diff_payload
    assert '"issues": []' in diff_payload


def test_task_attempt_fails_when_reported_paths_do_not_match_local_diff(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(_tasklist(), encoding="utf-8")
    source_path = tmp_path / "contracts" / "example.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("before\n", encoding="utf-8")
    context = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )
    source_path.write_text("after\n", encoding="utf-8")
    report_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "implement" / "implementation-report.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# Implementation Report\n\n## Touched files\n\n- `src/other.py` - claimed change.\n",
        encoding="utf-8",
    )

    ledger = complete_task_execution(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        project_root=tmp_path,
        succeeded=True,
    )

    entry = ledger.entry("TL-1")
    assert entry.status is TaskExecutionStatus.FAILED
    assert entry.blocker is not None
    assert "contracts/example.md" in entry.blocker
    assert "src/other.py" in entry.blocker


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
