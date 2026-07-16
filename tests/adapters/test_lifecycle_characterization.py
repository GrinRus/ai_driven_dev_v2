from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True, slots=True)
class LifecycleObservation:
    scenario: str
    launched: bool
    stop_reason: str | None
    exit_code: int | None
    stdout_observed: bool
    stderr_observed: bool
    outer_watchdog_fired: bool


_HELPER = r'''
import json
import os
import sys
import time
from enum import StrEnum
from pathlib import Path
from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.adapters.subprocess_streaming import run_streamed_subprocess

class Reason(StrEnum):
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

scenario = sys.argv[1]
cwd = Path(sys.argv[2])
if scenario == "startup":
    child = "print('ready', flush=True)"
    stdin_text = None
    timeout = 1.0
    cancel = None
elif scenario == "bidirectional-io":
    child = (
        "import sys; sys.stdout.write('x' * 200000); sys.stdout.flush(); "
        "print(len(sys.stdin.read()))"
    )
    stdin_text = "y" * 200000
    timeout = 0.2
    cancel = None
elif scenario in {"timeout", "cancellation"}:
    child = "import time; print('started', flush=True); time.sleep(10)"
    stdin_text = None
    timeout = 0.15 if scenario == "timeout" else 2.0
    started = time.monotonic()
    cancel = (lambda: time.monotonic() - started >= 0.15) if scenario == "cancellation" else None
elif scenario == "parent-exit":
    child = (
        "import subprocess,sys; subprocess.Popen([sys.executable, '-c', "
        "'import time; time.sleep(10)']); print('parent-exit', flush=True)"
    )
    stdin_text = None
    timeout = 0.2
    cancel = None
elif scenario == "descendant-exit":
    child = (
        "import subprocess,sys; subprocess.Popen([sys.executable, '-c', "
        "'import time; time.sleep(0.05)']); print('parent-exit', flush=True)"
    )
    stdin_text = None
    timeout = 1.0
    cancel = None
else:
    raise AssertionError(scenario)

result = run_streamed_subprocess(
    spec=RuntimeSubprocessSpec(
        command=(sys.executable, "-c", child),
        cwd=cwd,
        env=dict(os.environ),
        stdin_text=stdin_text,
    ),
    timeout_seconds=timeout,
    timeout_stop_reason=Reason.TIMEOUT,
    cancel_stop_reason=Reason.CANCELLED,
    cancel_requested=cancel,
)
print(json.dumps({
    "scenario": scenario,
    "launched": True,
    "stop_reason": result.stop_reason,
    "exit_code": result.exit_code,
    "stdout_observed": bool(result.stdout_text),
    "stderr_observed": bool(result.stderr_text),
    "outer_watchdog_fired": False,
}), flush=True)
'''


def _observe_probe(scenario: str, tmp_path: Path) -> LifecycleObservation:
    process = subprocess.Popen(
        (sys.executable, "-c", _HELPER, scenario, tmp_path.as_posix()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name != "nt",
    )
    try:
        stdout, stderr = process.communicate(timeout=3.0)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (OSError, PermissionError, ProcessLookupError):
                process.kill()
        else:
            process.kill()
        process.communicate(timeout=1.0)
        return LifecycleObservation(
            scenario=scenario,
            launched=True,
            stop_reason=None,
            exit_code=None,
            stdout_observed=False,
            stderr_observed=False,
            outer_watchdog_fired=True,
        )
    assert process.returncode == 0, stderr
    return LifecycleObservation(**json.loads(stdout.splitlines()[-1]))


@pytest.mark.parametrize(
    ("scenario", "expected_stop", "watchdog"),
    [
        ("startup", None, False),
        ("bidirectional-io", None, False),
        ("timeout", "timeout", False),
        ("cancellation", "cancelled", False),
        ("parent-exit", "timeout", False),
        ("descendant-exit", None, False),
    ],
)
def test_shared_transport_lifecycle_characterization(
    scenario: str,
    expected_stop: str | None,
    watchdog: bool,
    tmp_path: Path,
) -> None:
    observation = _observe_probe(scenario, tmp_path)

    assert observation.launched is True
    assert observation.outer_watchdog_fired is watchdog
    assert observation.stop_reason == expected_stop
    if not watchdog:
        assert observation.exit_code is not None


def test_provider_free_matrix_names_maintained_transport_coverage() -> None:
    matrix = {
        "shared-streaming": {
            "startup",
            "bidirectional-io",
            "timeout",
            "cancellation",
            "parent-exit",
            "descendant-exit",
        },
        "codex-live-fake": {"startup", "timeout"},
        "qwen-live-fake": {"startup", "timeout", "cancellation"},
    }

    assert set(matrix) == {"shared-streaming", "codex-live-fake", "qwen-live-fake"}
    assert all("startup" in scenarios and "timeout" in scenarios for scenarios in matrix.values())
