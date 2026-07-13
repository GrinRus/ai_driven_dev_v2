from __future__ import annotations

from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.cli.stage_run import StageRunOptions
from aidd.cli.support import _runtime_command_for_runtime, _runtime_execution_mode_for_runtime
from aidd.cli.task import execute_all_tasks, execute_task_by_id, finalize_implementation
from aidd.config import load_config
from aidd.core.run_store import create_run_manifest
from aidd.core.task_ledger import load_task_ledger
from aidd.validators.models import ValidationFinding

runner = CliRunner()


def _manifest_config_snapshot(workspace_root: Path, runtime: str) -> dict[str, str]:
    cfg = load_config(Path("aidd.example.toml"))
    runtime_cfg = cfg.runtime_config(runtime)
    return {
        "workspace_root": workspace_root.as_posix(),
        "runtime_command": _runtime_command_for_runtime(runtime=runtime, cfg=cfg),
        "runtime_execution_mode": _runtime_execution_mode_for_runtime(
            runtime=runtime, cfg=cfg
        ).value,
        "runtime_permission_policy": runtime_cfg.permission_policy.value,
        "runtime_interaction_mode": runtime_cfg.interaction_mode.value,
        "runtime_auto_approval_preset": runtime_cfg.auto_approval_preset.value,
    }


def _write_tasklist(workspace_root: Path) -> None:
    path = (
        workspace_root / "workitems" / "WI-TASK" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Tasklist

## Task summary

One complete implementation-ready task for CLI inspection.

## Ordered tasks

### TL-1 — Add the bounded behavior

- Outcome: The behavior is observable.
- Dominant deliverable: `src/example.py` contains the behavior.
- In scope: `src/example.py` and `tests/test_example.py`.
- Acceptance criteria:
  - TL-1-AC1: The supported input returns the expected value.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: `pytest tests/test_example.py -q`
""",
        encoding="utf-8",
    )


def test_task_list_and_show_render_derived_pending_state(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)

    list_result = runner.invoke(
        app,
        ["task", "list", "--work-item", "WI-TASK", "--root", str(workspace_root)],
    )
    show_result = runner.invoke(
        app,
        [
            "task",
            "show",
            "TL-1",
            "--work-item",
            "WI-TASK",
            "--root",
            str(workspace_root),
        ],
    )

    assert list_result.exit_code == 0
    assert "TL-1" in list_result.stdout
    assert "pending" in list_result.stdout
    assert show_result.exit_code == 0
    assert "TL-1-AC1" in show_result.stdout


def test_task_show_rejects_unknown_task(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)

    result = runner.invoke(
        app,
        [
            "task",
            "show",
            "TL-9",
            "--work-item",
            "WI-TASK",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code != 0
    assert result.exception is not None
    assert "Unknown task id" in str(result.exception)


def test_task_run_rejects_runtime_mismatch_before_creating_ledger(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-TASK",
        run_id="run-1",
        runtime_id="generic-cli",
        stage_target="qa",
        workflow_stage_start="tasklist",
        workflow_stage_end="qa",
        config_snapshot=_manifest_config_snapshot(workspace_root, "generic-cli"),
    )

    try:
        execute_task_by_id(
            task_id="TL-1",
            work_item="WI-TASK",
            run_id="run-1",
            runtime="codex",
            root=workspace_root,
            config=Path("aidd.example.toml"),
            log_follow=False,
        )
    except ValueError as exc:
        assert "does not match run manifest runtime" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected runtime mismatch")

    assert (
        load_task_ledger(
            workspace_root=workspace_root,
            work_item="WI-TASK",
            run_id="run-1",
        )
        is None
    )


def test_automatic_tasks_fail_fast_and_manual_resume_publishes_aggregate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-TASK" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(
        """# Tasklist

## Task summary

Two dependent implementation-ready tasks exercise fail-fast and resume.

## Ordered tasks

### TL-1 — Update the contract

- Outcome: The contract records the behavior.
- Dominant deliverable: `contracts/example.md` records the behavior.
- In scope: `contracts/example.md`.
- Acceptance criteria:
  - TL-1-AC1: The contract file contains the behavior marker.

### TL-2 — Implement the behavior

- Outcome: The implementation exposes the behavior.
- Dominant deliverable: `src/example.py` exposes the behavior.
- In scope: `src/example.py`.
- Acceptance criteria:
  - TL-2-AC1: The implementation file contains the behavior marker.

## Dependencies

- TL-1: none
- TL-2: TL-1

## Verification notes

- TL-1: `python -c 'print("contract")'`
- TL-2: `python -c 'print("implementation")'`
""",
        encoding="utf-8",
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-TASK",
        run_id="run-1",
        runtime_id="generic-cli",
        stage_target="qa",
        workflow_stage_start="tasklist",
        workflow_stage_end="qa",
        config_snapshot=_manifest_config_snapshot(workspace_root, "generic-cli"),
    )
    second_attempts = 0

    def _stage_runner(options: StageRunOptions) -> None:
        nonlocal second_attempts
        selection_path = workspace_root / "workitems" / "WI-TASK" / "context" / "task-selection.md"
        selection = selection_path.read_text(encoding="utf-8")
        task_id = "TL-1" if "Task id: `TL-1`" in selection else "TL-2"
        if task_id == "TL-2":
            second_attempts += 1
            if second_attempts == 1:
                raise typer.Exit(code=1)
        touched_path = "contracts/example.md" if task_id == "TL-1" else "src/example.py"
        command = (
            "python -c 'print(\"contract\")'"
            if task_id == "TL-1"
            else "python -c 'print(\"implementation\")'"
        )
        target = tmp_path / touched_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"BEHAVIOR_{task_id.replace('-', '_')} = True\n", encoding="utf-8")
        stage_root = workspace_root / "workitems" / "WI-TASK" / "stages" / "implement"
        stage_root.mkdir(parents=True, exist_ok=True)
        (stage_root / "implementation-report.md").write_text(
            "# Implementation Report\n\n"
            f"## Selected task\n\n- Task id: `{task_id}`\n\n"
            "## Change summary\n\n"
            f"Completed {task_id} with a bounded observable implementation change.\n\n"
            f"## Touched files\n\n- `{touched_path}` - added behavior marker.\n\n"
            "## Verification notes\n\n"
            f"- `{task_id}-AC1`: `{command}` -> pass.\n\n"
            "## Follow-up notes\n\n- none\n",
            encoding="utf-8",
        )
        (stage_root / "stage-result.md").write_text("# Stage result\n", encoding="utf-8")
        (stage_root / "validator-report.md").write_text("# Validator report\n", encoding="utf-8")
        (stage_root / "questions.md").write_text("# Questions\n\n- none\n", encoding="utf-8")
        (stage_root / "answers.md").write_text("# Answers\n\n- none\n", encoding="utf-8")

    with pytest.raises(typer.Exit):
        execute_all_tasks(
            work_item="WI-TASK",
            run_id="run-1",
            runtime="generic-cli",
            root=workspace_root,
            config=Path("aidd.example.toml"),
            log_follow=False,
            stage_runner=_stage_runner,
        )
    failed = load_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-TASK",
        run_id="run-1",
    )
    assert failed is not None
    assert failed.entry("TL-1").status.value == "succeeded"
    assert failed.entry("TL-2").status.value == "failed"
    published_report = (
        workspace_root
        / "workitems"
        / "WI-TASK"
        / "stages"
        / "implement"
        / "output"
        / "implementation-report.md"
    )
    assert not published_report.exists()

    resumed = execute_task_by_id(
        task_id="TL-2",
        work_item="WI-TASK",
        run_id="run-1",
        runtime="generic-cli",
        root=workspace_root,
        config=Path("aidd.example.toml"),
        log_follow=False,
        stage_runner=_stage_runner,
    )

    assert resumed.all_succeeded()
    assert resumed.entry("TL-2").attempt_count == 2
    aggregate = published_report.read_text(encoding="utf-8")
    assert "`TL-1`" in aggregate
    assert "`TL-2`" in aggregate
    assert "`TL-1-AC1`" in aggregate
    assert "`TL-2-AC1`" in aggregate


def test_failed_aggregate_finalization_retries_without_rerunning_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-TASK",
        run_id="run-1",
        runtime_id="generic-cli",
        stage_target="qa",
        workflow_stage_start="tasklist",
        workflow_stage_end="qa",
        config_snapshot=_manifest_config_snapshot(workspace_root, "generic-cli"),
    )
    task_runs = 0

    def _stage_runner(options: StageRunOptions) -> None:
        nonlocal task_runs
        task_runs += 1
        source = tmp_path / "src" / "example.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("VALUE = 1\n", encoding="utf-8")
        stage_root = workspace_root / "workitems" / "WI-TASK" / "stages" / "implement"
        stage_root.mkdir(parents=True, exist_ok=True)
        (stage_root / "implementation-report.md").write_text(
            "# Implementation Report\n\n"
            "## Selected task\n\n- Task id: `TL-1`\n\n"
            "## Change summary\n\nImplemented the bounded behavior.\n\n"
            "## Touched files\n\n- `src/example.py` - added behavior.\n\n"
            "## Verification notes\n\n"
            "- `TL-1-AC1`: `pytest tests/test_example.py -q` -> pass.\n\n"
            "## Follow-up notes\n\n- none\n",
            encoding="utf-8",
        )
        (stage_root / "stage-result.md").write_text("# Stage result\n", encoding="utf-8")
        (stage_root / "validator-report.md").write_text(
            "# Validator report\n", encoding="utf-8"
        )
        (stage_root / "questions.md").write_text(
            "# Questions\n\n- none\n", encoding="utf-8"
        )
        (stage_root / "answers.md").write_text(
            "# Answers\n\n- none\n", encoding="utf-8"
        )

    validation_calls = 0

    def _aggregate_validation(**kwargs: object) -> tuple[ValidationFinding, ...]:
        nonlocal validation_calls
        del kwargs
        validation_calls += 1
        if validation_calls == 1:
            return (
                ValidationFinding(
                    code="SEM-AGGREGATE-TEST",
                    message="Injected aggregate validation failure.",
                ),
            )
        return ()

    monkeypatch.setattr("aidd.cli.task.validate_semantic_outputs", _aggregate_validation)

    with pytest.raises(ValueError, match="Aggregate implementation report failed"):
        execute_task_by_id(
            task_id="TL-1",
            work_item="WI-TASK",
            run_id="run-1",
            runtime="generic-cli",
            root=workspace_root,
            config=Path("aidd.example.toml"),
            log_follow=False,
            stage_runner=_stage_runner,
        )

    failed = load_task_ledger(
        workspace_root=workspace_root, work_item="WI-TASK", run_id="run-1"
    )
    assert failed is not None
    assert failed.entry("TL-1").status.value == "succeeded"
    assert failed.finalization.status.value == "failed"
    assert task_runs == 1

    finalized = finalize_implementation(
        work_item="WI-TASK",
        run_id="run-1",
        runtime="generic-cli",
        root=workspace_root,
        config=Path("aidd.example.toml"),
    )

    assert finalized.finalization.status.value == "succeeded"
    assert finalized.finalization.attempt_count == 2
    assert task_runs == 1
