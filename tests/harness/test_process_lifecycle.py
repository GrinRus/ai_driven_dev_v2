from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from aidd.harness.process_lifecycle import HarnessLifecycleBudget, run_owned_process


def test_lifecycle_budget_reports_one_shared_remaining_deadline() -> None:
    budget = HarnessLifecycleBudget.start(10.0, now=100.0)

    assert budget.remaining_seconds(now=103.5) == 6.5
    assert budget.exhausted(now=109.0) is False
    assert budget.exhausted(now=110.0) is True


def test_exhausted_budget_does_not_launch_command(tmp_path: Path) -> None:
    marker = tmp_path / "launched"

    result = run_owned_process(
        command=("/bin/sh", "-c", f"touch {marker.as_posix()}"),
        cwd=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=0.0,
    )

    assert result.timed_out is True
    assert result.exit_code == 124
    assert not marker.exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX process-group assertion")
def test_timeout_terminates_descendant_process_group(tmp_path: Path) -> None:
    child_pid_path = tmp_path / "child.pid"
    command = (
        "/bin/sh",
        "-c",
        f"sleep 60 & echo $! > {child_pid_path.as_posix()}; wait",
    )

    result = run_owned_process(
        command=command,
        cwd=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=0.1,
    )

    assert result.timed_out is True
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.02)
    else:
        pytest.fail(f"descendant process {child_pid} survived lifecycle timeout")
