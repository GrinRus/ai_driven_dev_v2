from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.runner import (
    HarnessTeardownError,
    run_teardown_steps,
    run_with_teardown,
)


def test_run_teardown_steps_executes_commands_in_order(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)

    result = run_teardown_steps(
        teardown_commands=(
            "printf 'first\\n' > teardown.log",
            "printf 'second\\n' >> teardown.log",
        ),
        working_copy_path=working_copy_path,
    )

    assert result.executed_commands == (
        "printf 'first\\n' > teardown.log",
        "printf 'second\\n' >> teardown.log",
    )
    assert len(result.command_transcripts) == 2
    assert result.command_transcripts[0].exit_code == 0
    assert result.duration_seconds >= 0
    assert (working_copy_path / "teardown.log").read_text(encoding="utf-8") == "first\nsecond\n"


def test_run_with_teardown_executes_teardown_after_success(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)

    def _action() -> str:
        (working_copy_path / "action.log").write_text("ok\n", encoding="utf-8")
        return "done"

    action_result, teardown_result = run_with_teardown(
        action=_action,
        teardown_commands=("printf 'teardown\\n' > teardown.log",),
        working_copy_path=working_copy_path,
    )

    assert action_result == "done"
    assert teardown_result.executed_commands == ("printf 'teardown\\n' > teardown.log",)
    assert (working_copy_path / "action.log").exists()
    assert (working_copy_path / "teardown.log").read_text(encoding="utf-8") == "teardown\n"


def test_run_with_teardown_executes_teardown_after_action_failure(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)

    def _action() -> str:
        raise RuntimeError("scenario failed")

    with pytest.raises(RuntimeError, match="scenario failed"):
        run_with_teardown(
            action=_action,
            teardown_commands=("printf 'teardown\\n' > teardown.log",),
            working_copy_path=working_copy_path,
        )

    assert (working_copy_path / "teardown.log").read_text(encoding="utf-8") == "teardown\n"


def test_run_with_teardown_raises_exception_group_when_both_paths_fail(
    tmp_path: Path,
) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)

    def _action() -> str:
        raise RuntimeError("scenario failed")

    with pytest.raises(ExceptionGroup) as exc_info:
        run_with_teardown(
            action=_action,
            teardown_commands=("exit 5",),
            working_copy_path=working_copy_path,
        )

    errors = exc_info.value.exceptions
    assert len(errors) == 2
    assert isinstance(errors[0], RuntimeError)
    assert isinstance(errors[1], HarnessTeardownError)
