from __future__ import annotations

import os
import sys
import threading
import time
from enum import StrEnum
from pathlib import Path

import pytest

from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.adapters.subprocess_streaming import run_streamed_subprocess


class StopReason(StrEnum):
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


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
