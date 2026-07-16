from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import pytest

from aidd.adapters.process_supervisor import OwnedProcessSupervisor
from aidd.adapters.runtime_execution import RuntimeSubprocessSpec


def _reader(pipe: object) -> None:
    assert hasattr(pipe, "read")
    pipe.read()  # type: ignore[union-attr]


@pytest.mark.skipif(os.name == "nt", reason="process-group behavior is POSIX-specific")
def test_owned_supervisor_stops_parent_and_descendant(tmp_path: Path) -> None:
    child_ready = tmp_path / "child-ready"
    script = (
        "import pathlib, subprocess, sys, time\n"
        "ready = pathlib.Path(sys.argv[1])\n"
        "child = \"import pathlib,sys,time; pathlib.Path(sys.argv[1]).write_text('ready'); "
        "time.sleep(30)\"\n"
        "subprocess.Popen([sys.executable, '-c', child, str(ready)])\n"
        "while not ready.exists(): time.sleep(0.01)\n"
        "print('ready', flush=True)\n"
        "time.sleep(30)\n"
    )
    supervisor = OwnedProcessSupervisor.launch(
        RuntimeSubprocessSpec(
            command=(sys.executable, "-c", script, child_ready.as_posix()),
            cwd=tmp_path,
            env=dict(os.environ),
        )
    )
    assert supervisor.process.stdout is not None
    assert supervisor.process.stdout.readline().strip() == "ready"

    supervisor.request_stop(grace_seconds=0.2)

    assert supervisor.process.poll() is not None
    assert supervisor.process_group_exists() is False


@pytest.mark.skipif(os.name == "nt", reason="inherited-pipe behavior is POSIX-specific")
def test_owned_supervisor_bounds_inherited_pipe_drain(tmp_path: Path) -> None:
    script = (
        "import subprocess, sys\n"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "print('parent-exit', flush=True)\n"
    )
    supervisor = OwnedProcessSupervisor.launch(
        RuntimeSubprocessSpec(
            command=(sys.executable, "-c", script),
            cwd=tmp_path,
            env=dict(os.environ),
        )
    )
    assert supervisor.process.stdout is not None
    assert supervisor.process.stderr is not None
    readers = (
        threading.Thread(target=_reader, args=(supervisor.process.stdout,), daemon=True),
        threading.Thread(target=_reader, args=(supervisor.process.stderr,), daemon=True),
    )
    for thread in readers:
        thread.start()
    supervisor.process.wait(timeout=1.0)
    started_at = time.monotonic()

    drained = supervisor.drain_streams(readers, grace_seconds=0.1)

    assert drained is True
    assert time.monotonic() - started_at < 1.0
    assert all(not thread.is_alive() for thread in readers)
    assert supervisor.process_group_exists() is False
