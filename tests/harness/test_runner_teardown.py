from __future__ import annotations

from pathlib import Path

from aidd.harness.runner import (
    run_teardown_steps,
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
