from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest


def configure_sleeping_fixture_runtime(
    project_root: Path,
    *,
    sleep_seconds: int = 30,
    process_marker: Path | None = None,
) -> None:
    fixture_runtime = (
        Path(__file__).parents[1]
        / "harness/fixtures/minimal-python/aidd_fixture_runtime.py"
    ).resolve()
    wrapper = project_root / "browser_fixture_runtime.py"
    marker_setup = (
        ""
        if process_marker is None
        else (
            "from pathlib import Path\n"
            f"Path({process_marker.as_posix()!r}).write_text(str(os.getpid()), encoding='utf-8')\n"
        )
    )
    wrapper_source = (
        "import os\n"
        "import runpy\n"
        "import time\n"
        + marker_setup
        + "try:\n"
        f"    runpy.run_path({fixture_runtime.as_posix()!r}, run_name='__main__')\n"
        "except SystemExit as error:\n"
        "    if error.code not in (None, 0):\n"
        "        raise\n"
        f"time.sleep({sleep_seconds})\n"
    )
    wrapper.write_text(
        wrapper_source,
        encoding="utf-8",
    )
    project_root.joinpath("aidd.example.toml").write_text(
        "[workspace]\n"
        'root = ".aidd"\n\n'
        "[runtime.generic_cli]\n"
        f'command = "{sys.executable} {wrapper.as_posix()}"\n'
        'mode = "adapter-flags"\n'
        'permission_policy = "full-access"\n\n'
        "[logging]\n"
        'mode = "both"\n\n'
        "[repair]\n"
        "max_attempts = 2\n",
        encoding="utf-8",
    )


def wait_for_recorded_process_exit(
    process_marker: Path,
    *,
    timeout_seconds: float = 5.0,
) -> None:
    """Prove that a fixture-owned runtime recorded in ``process_marker`` has exited."""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline and not process_marker.exists():
        time.sleep(0.05)
    if not process_marker.exists():
        pytest.fail(f"Fixture runtime did not publish PID marker: {process_marker.name}")
    pid = int(process_marker.read_text(encoding="utf-8").strip())
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            pass
        time.sleep(0.05)
    pytest.fail(f"Fixture runtime PID {pid} remained alive after browser cleanup.")
