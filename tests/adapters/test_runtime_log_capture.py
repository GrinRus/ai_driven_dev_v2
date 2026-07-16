from __future__ import annotations

import json
import os
import subprocess
import sys
from enum import StrEnum
from pathlib import Path

import pytest

from aidd.adapters.runner_support import persist_runtime_log_artifacts
from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.adapters.runtime_log_capture import (
    COMBINED_TAIL_BYTES,
    STDIO_TAIL_BYTES,
    DiskBackedRuntimeLogSink,
)
from aidd.adapters.subprocess_streaming import run_streamed_subprocess
from aidd.runtime_logs.events import structured_runtime_events


class _StopReason(StrEnum):
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


def test_disk_backed_sink_preserves_full_order_with_bounded_utf8_tails(
    tmp_path: Path,
) -> None:
    sink = DiskBackedRuntimeLogSink(directory=tmp_path)
    stdout_chunk = "🙂stdout\n" * 40_000
    stderr_chunk = "stderr-é\n" * 40_000

    sink.write("stdout", stdout_chunk)
    sink.write("stderr", stderr_chunk)
    snapshot = sink.finish()

    assert snapshot.runtime_log_source_path.read_text(encoding="utf-8") == (
        stdout_chunk + stderr_chunk
    )
    assert len(snapshot.stdout_text.encode("utf-8")) <= STDIO_TAIL_BYTES
    assert len(snapshot.stderr_text.encode("utf-8")) <= STDIO_TAIL_BYTES
    assert len(snapshot.runtime_log_text.encode("utf-8")) <= COMBINED_TAIL_BYTES
    assert snapshot.stdout_byte_count == len(stdout_chunk.encode("utf-8"))
    assert snapshot.stderr_byte_count == len(stderr_chunk.encode("utf-8"))
    assert snapshot.runtime_log_byte_count == len(
        (stdout_chunk + stderr_chunk).encode("utf-8")
    )
    assert snapshot.stdout_char_count == len(stdout_chunk)
    assert snapshot.stderr_char_count == len(stderr_chunk)
    assert snapshot.runtime_log_char_count == len(stdout_chunk + stderr_chunk)
    assert snapshot.stdout_truncated is True
    assert snapshot.stderr_truncated is True
    assert snapshot.runtime_log_truncated is True


def test_high_volume_subprocess_commits_full_log_and_bounded_tail_metadata(
    tmp_path: Path,
) -> None:
    chunk_size = 64 * 1024
    repetitions = 160
    script = (
        "import os\n"
        f"chunk = b'x' * {chunk_size}\n"
        f"for _ in range({repetitions}):\n"
        "    os.write(1, chunk)\n"
        "    os.write(2, chunk)\n"
    )
    result = run_streamed_subprocess(
        spec=RuntimeSubprocessSpec(
            command=(sys.executable, "-c", script),
            cwd=tmp_path,
            env=dict(os.environ),
        ),
        timeout_seconds=20.0,
        timeout_stop_reason=_StopReason.TIMEOUT,
        cancel_stop_reason=_StopReason.CANCELLED,
        capture_directory=tmp_path,
    )
    paths = persist_runtime_log_artifacts(
        attempt_path=tmp_path / "attempt",
        exit_code=result.exit_code,
        exit_classification="success",
        stdout_text=result.stdout_text,
        stderr_text=result.stderr_text,
        runtime_log_text=result.runtime_log_text,
        runtime_log_source_path=result.runtime_log_source_path,
        stdout_byte_count=result.stdout_byte_count,
        stderr_byte_count=result.stderr_byte_count,
        runtime_log_byte_count=result.runtime_log_byte_count,
        stdout_char_count=result.stdout_char_count,
        stderr_char_count=result.stderr_char_count,
        runtime_log_char_count=result.runtime_log_char_count,
        stdout_truncated=result.stdout_truncated,
        stderr_truncated=result.stderr_truncated,
        runtime_log_truncated=result.runtime_log_truncated,
    )

    expected_stream_bytes = chunk_size * repetitions
    assert paths.runtime_log_path.stat().st_size == expected_stream_bytes * 2
    assert len(result.stdout_text.encode("utf-8")) <= STDIO_TAIL_BYTES
    assert len(result.stderr_text.encode("utf-8")) <= STDIO_TAIL_BYTES
    assert len(result.runtime_log_text.encode("utf-8")) <= COMBINED_TAIL_BYTES
    metadata = json.loads(
        paths.runtime_exit_metadata_path.read_text(encoding="utf-8")
    )
    assert metadata["stdout_byte_count"] == expected_stream_bytes
    assert metadata["stderr_byte_count"] == expected_stream_bytes
    assert metadata["runtime_log_byte_count"] == expected_stream_bytes * 2
    assert metadata["stdout_char_count"] == expected_stream_bytes
    assert metadata["stderr_char_count"] == expected_stream_bytes
    assert metadata["runtime_log_char_count"] == expected_stream_bytes * 2
    assert metadata["stdout_tail_truncated"] is True
    assert metadata["stderr_tail_truncated"] is True
    assert metadata["runtime_log_tail_truncated"] is True


def test_structured_events_are_available_after_their_text_leaves_the_tail(
    tmp_path: Path,
) -> None:
    script = (
        "import json, sys\n"
        "print(json.dumps({'event': 'question_raised', 'id': 'Q1'}), flush=True)\n"
        f"sys.stdout.write('x' * {STDIO_TAIL_BYTES * 2})\n"
    )
    result = run_streamed_subprocess(
        spec=RuntimeSubprocessSpec(
            command=(sys.executable, "-c", script),
            cwd=tmp_path,
            env=dict(os.environ),
        ),
        timeout_seconds=10.0,
        timeout_stop_reason=_StopReason.TIMEOUT,
        cancel_stop_reason=_StopReason.CANCELLED,
        capture_directory=tmp_path,
    )

    assert "question_raised" not in result.stdout_text
    assert structured_runtime_events(run_result=result) == (
        {
            "payload": {"event": "question_raised", "id": "Q1"},
            "source": "stdout",
        },
    )


def test_high_volume_capture_stays_within_helper_memory_budget(tmp_path: Path) -> None:
    helper = """
import json
import os
import resource
import sys
from pathlib import Path
from enum import StrEnum
from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.adapters.subprocess_streaming import run_streamed_subprocess
class Reason(StrEnum):
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
root = Path(sys.argv[1])
chunk = 64 * 1024
repetitions = 256
script = (
    "import os\\n"
    f"chunk = b'x' * {chunk}\\n"
    f"for _ in range({repetitions}):\\n"
    "    os.write(1, chunk)\\n"
    "    os.write(2, chunk)\\n"
)
result = run_streamed_subprocess(
    spec=RuntimeSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=root,
        env=dict(os.environ),
    ),
    timeout_seconds=30.0,
    timeout_stop_reason=Reason.TIMEOUT,
    cancel_stop_reason=Reason.CANCELLED,
    capture_directory=root,
)
maximum_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if sys.platform != "darwin":
    maximum_rss *= 1024
print(json.dumps({
    "maximum_rss": maximum_rss,
    "combined_tail_bytes": len(result.runtime_log_text.encode("utf-8")),
    "runtime_log_bytes": result.runtime_log_byte_count,
}))
"""
    completed = subprocess.run(
        (sys.executable, "-c", helper, str(tmp_path)),
        capture_output=True,
        check=True,
        text=True,
        timeout=45,
        env=dict(os.environ),
    )
    observation = json.loads(completed.stdout)

    assert observation["runtime_log_bytes"] == 32 * 1024 * 1024
    assert observation["combined_tail_bytes"] <= COMBINED_TAIL_BYTES
    assert observation["maximum_rss"] < 192 * 1024 * 1024


def test_callback_failure_aborts_capture_without_published_evidence(
    tmp_path: Path,
) -> None:
    class CallbackFailure(RuntimeError):
        pass

    attempt_path = tmp_path / "attempt"
    with pytest.raises(CallbackFailure):
        run_streamed_subprocess(
            spec=RuntimeSubprocessSpec(
                command=(sys.executable, "-c", "print('before-failure', flush=True)"),
                cwd=tmp_path,
                env=dict(os.environ),
            ),
            timeout_seconds=5.0,
            timeout_stop_reason=_StopReason.TIMEOUT,
            cancel_stop_reason=_StopReason.CANCELLED,
            on_stdout=lambda _chunk: (_ for _ in ()).throw(CallbackFailure()),
            capture_directory=attempt_path,
        )

    assert not (attempt_path / "runtime.log").exists()
    assert not (attempt_path / "runtime-exit.json").exists()
    assert not tuple(attempt_path.glob(".runtime-*.tmp"))
