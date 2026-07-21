from __future__ import annotations

import os
import signal
import sys
import threading
import time
from enum import StrEnum
from pathlib import Path

import pytest

from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.adapters.subprocess_streaming import run_streamed_subprocess


class StopReason(StrEnum):
    COMPLETE = "complete"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    LAUNCH_FAILURE = "launch_failure"


@pytest.mark.parametrize(
    "timeout_seconds",
    (False, 0.0, -1.0, float("nan"), float("inf"), float("-inf")),
)
def test_streamed_subprocess_rejects_invalid_timeout_budget(
    tmp_path: Path,
    timeout_seconds: float,
) -> None:
    spec = RuntimeSubprocessSpec(
        command=(sys.executable, "-c", "raise AssertionError('must not launch')"),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    with pytest.raises(ValueError, match="finite number greater than zero"):
        run_streamed_subprocess(
            spec=spec,
            timeout_seconds=timeout_seconds,
            timeout_stop_reason=StopReason.TIMEOUT,
            cancel_stop_reason=StopReason.CANCELLED,
        )


def test_streamed_subprocess_normalizes_launch_oserror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aidd.adapters.process_supervisor import OwnedProcessSupervisor

    def fail_launch(_spec: RuntimeSubprocessSpec) -> OwnedProcessSupervisor:
        raise OSError("unsafe\nmultiline launch diagnostic")

    monkeypatch.setattr(OwnedProcessSupervisor, "launch", fail_launch)
    result = run_streamed_subprocess(
        spec=RuntimeSubprocessSpec(
            command=("runtime",),
            cwd=tmp_path,
            env={},
        ),
        timeout_seconds=None,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
        launch_failure_stop_reason=StopReason.LAUNCH_FAILURE,
    )

    assert result.exit_code is None
    assert result.stop_reason is StopReason.LAUNCH_FAILURE
    assert result.stdout_text == ""
    assert result.stderr_text == (
        "[launch-failure] OSError: unsafe multiline launch diagnostic\n"
    )
    assert result.runtime_log_text == result.stderr_text


def test_stream_callbacks_run_in_caller_thread(tmp_path: Path) -> None:
    caller_thread_id = threading.get_ident()
    callback_thread_ids: list[int] = []
    spec = RuntimeSubprocessSpec(
        command=(sys.executable, "-c", "print('hello', flush=True)"),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_streamed_subprocess(
        spec=spec,
        timeout_seconds=None,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
        on_stdout=lambda _chunk: callback_thread_ids.append(threading.get_ident()),
    )

    assert result.exit_code == 0
    assert callback_thread_ids == [caller_thread_id]


def test_stream_callback_exception_propagates_and_stops_process(tmp_path: Path) -> None:
    class CallbackError(RuntimeError):
        pass

    script = (
        "import time\n"
        "print('before-error', flush=True)\n"
        "time.sleep(2)\n"
    )
    spec = RuntimeSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    started_at = time.monotonic()
    with pytest.raises(CallbackError):
        run_streamed_subprocess(
            spec=spec,
            timeout_seconds=None,
            timeout_stop_reason=StopReason.TIMEOUT,
            cancel_stop_reason=StopReason.CANCELLED,
            on_stdout=lambda _chunk: (_ for _ in ()).throw(CallbackError()),
        )

    assert time.monotonic() - started_at < 1.5


def test_timeout_is_enforced_while_process_is_streaming_output(tmp_path: Path) -> None:
    script = (
        "import time\n"
        "while True:\n"
        "    print('tick', flush=True)\n"
        "    time.sleep(0.01)\n"
    )
    spec = RuntimeSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_streamed_subprocess(
        spec=spec,
        timeout_seconds=0.1,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
    )

    assert result.stop_reason is StopReason.TIMEOUT


@pytest.mark.parametrize("stop_mode", ("timeout", "cancellation"))
def test_supervision_starts_before_blocked_stdin_delivery(
    tmp_path: Path,
    stop_mode: str,
) -> None:
    script = (
        "import sys, time\n"
        "sys.stdout.write('x' * 200000)\n"
        "sys.stdout.flush()\n"
        "time.sleep(10)\n"
    )
    spec = RuntimeSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
        stdin_text="y" * 2_000_000,
    )
    started_at = time.monotonic()

    result = run_streamed_subprocess(
        spec=spec,
        timeout_seconds=0.2 if stop_mode == "timeout" else 2.0,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
        cancel_requested=(
            (lambda: time.monotonic() - started_at >= 0.2)
            if stop_mode == "cancellation"
            else None
        ),
    )

    expected = StopReason.TIMEOUT if stop_mode == "timeout" else StopReason.CANCELLED
    assert result.stop_reason is expected
    assert time.monotonic() - started_at < 1.5


def test_completion_request_stops_process_before_timeout(tmp_path: Path) -> None:
    spec = RuntimeSubprocessSpec(
        command=(sys.executable, "-c", "import time; print('ready', flush=True); time.sleep(5)"),
        cwd=tmp_path,
        env=dict(os.environ),
    )
    poll_count = 0

    def completion_requested() -> bool:
        nonlocal poll_count
        poll_count += 1
        return poll_count >= 2

    started_at = time.monotonic()
    result = run_streamed_subprocess(
        spec=spec,
        timeout_seconds=5.0,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
        completion_requested=completion_requested,
        completion_stop_reason=StopReason.COMPLETE,
    )

    assert result.stop_reason is StopReason.COMPLETE
    assert time.monotonic() - started_at < 1.5


@pytest.mark.skipif(os.name == "nt", reason="process groups are POSIX-specific")
def test_parent_exit_stops_child_process_before_runtime_timeout(tmp_path: Path) -> None:
    signal_path = tmp_path / "child-signal.txt"
    ready_path = tmp_path / "child-ready.txt"
    child_script = (
        "import pathlib\n"
        "import signal\n"
        "import sys\n"
        "import time\n"
        "signal_path = pathlib.Path(sys.argv[1])\n"
        "ready_path = pathlib.Path(sys.argv[2])\n"
        "def _handle_stop(signum, _frame):\n"
        "    signal_path.write_text(str(signum), encoding='utf-8')\n"
        "    raise SystemExit(0)\n"
        "signal.signal(signal.SIGTERM, _handle_stop)\n"
        "ready_path.write_text('ready', encoding='utf-8')\n"
        "print('child-started', flush=True)\n"
        "while True:\n"
        "    time.sleep(1)\n"
    )
    parent_script = (
        "import pathlib\n"
        "import subprocess\n"
        "import sys\n"
        "import time\n"
        "ready_path = pathlib.Path(sys.argv[3])\n"
        "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2], sys.argv[3]])\n"
        "deadline = time.monotonic() + 5\n"
        "while not ready_path.exists() and time.monotonic() < deadline:\n"
        "    time.sleep(0.01)\n"
        "print('parent-exit', flush=True)\n"
    )
    spec = RuntimeSubprocessSpec(
        command=(
            sys.executable,
            "-c",
            parent_script,
            child_script,
            signal_path.as_posix(),
            ready_path.as_posix(),
        ),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    started_at = time.monotonic()
    result = run_streamed_subprocess(
        spec=spec,
        timeout_seconds=1.5,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
        queue_timeout_seconds=1.0,
    )

    assert result.stop_reason is None
    assert time.monotonic() - started_at < 3.0
    assert signal_path.read_text(encoding="utf-8") == str(signal.SIGTERM)


@pytest.mark.skipif(os.name == "nt", reason="process groups are POSIX-specific")
def test_parent_exit_bounds_inherited_pipe_drain_without_runtime_timeout(
    tmp_path: Path,
) -> None:
    child_signal_path = tmp_path / "child-signal.txt"
    child_ready_path = tmp_path / "child-ready.txt"
    child_script = (
        "import pathlib, signal, sys, time\n"
        "signal_path = pathlib.Path(sys.argv[1])\n"
        "ready_path = pathlib.Path(sys.argv[2])\n"
        "def stop(signum, _frame):\n"
        "    signal_path.write_text(str(signum), encoding='utf-8')\n"
        "    raise SystemExit(0)\n"
        "signal.signal(signal.SIGTERM, stop)\n"
        "ready_path.write_text('ready', encoding='utf-8')\n"
        "while True: time.sleep(1)\n"
    )
    parent_script = (
        "import pathlib, subprocess, sys, time\n"
        "ready_path = pathlib.Path(sys.argv[3])\n"
        "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2], sys.argv[3]])\n"
        "while not ready_path.exists(): time.sleep(0.01)\n"
        "print('parent-exit', flush=True)\n"
    )
    spec = RuntimeSubprocessSpec(
        command=(
            sys.executable,
            "-c",
            parent_script,
            child_script,
            child_signal_path.as_posix(),
            child_ready_path.as_posix(),
        ),
        cwd=tmp_path,
        env=dict(os.environ),
    )
    started_at = time.monotonic()

    result = run_streamed_subprocess(
        spec=spec,
        timeout_seconds=None,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
    )

    assert result.stop_reason is None
    assert result.exit_code == 0
    assert time.monotonic() - started_at < 1.5
    assert child_signal_path.read_text(encoding="utf-8") == str(signal.SIGTERM)


@pytest.mark.skipif(os.name == "nt", reason="process groups are POSIX-specific")
@pytest.mark.parametrize("stop_mode", ("cancellation", "completion"))
def test_requested_stop_terminates_descendants(
    tmp_path: Path,
    stop_mode: str,
) -> None:
    child_signal_path = tmp_path / f"{stop_mode}-signal.txt"
    child_ready_path = tmp_path / f"{stop_mode}-ready.txt"
    script = (
        "import pathlib, signal, subprocess, sys, time\n"
        "signal_path = pathlib.Path(sys.argv[1])\n"
        "child = \"import pathlib,signal,sys,time; ready=pathlib.Path(sys.argv[2]); "
        "signal.signal(signal.SIGTERM, lambda s,f: "
        "(pathlib.Path(sys.argv[1]).write_text(str(s)), sys.exit(0))); "
        "ready.write_text('ready'); "
        "time.sleep(30)\"\n"
        "subprocess.Popen([sys.executable, '-c', child, str(signal_path), sys.argv[2]])\n"
        "print('ready', flush=True)\n"
        "time.sleep(30)\n"
    )
    spec = RuntimeSubprocessSpec(
        command=(
            sys.executable,
            "-c",
            script,
            child_signal_path.as_posix(),
            child_ready_path.as_posix(),
        ),
        cwd=tmp_path,
        env=dict(os.environ),
    )
    started_at = time.monotonic()

    def requested() -> bool:
        return child_ready_path.exists() and time.monotonic() - started_at >= 0.2

    result = run_streamed_subprocess(
        spec=spec,
        timeout_seconds=2.0,
        timeout_stop_reason=StopReason.TIMEOUT,
        cancel_stop_reason=StopReason.CANCELLED,
        cancel_requested=requested if stop_mode == "cancellation" else None,
        completion_requested=requested if stop_mode == "completion" else None,
        completion_stop_reason=(
            StopReason.COMPLETE if stop_mode == "completion" else None
        ),
    )

    expected = StopReason.CANCELLED if stop_mode == "cancellation" else StopReason.COMPLETE
    assert result.stop_reason is expected
    assert child_signal_path.read_text(encoding="utf-8") == str(signal.SIGTERM)
