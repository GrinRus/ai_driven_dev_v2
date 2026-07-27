from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from aidd.harness.live_command_evidence import (
    COMMAND_PREVIEW_BYTE_LIMIT,
    persist_command_evidence,
    read_command_output,
)
from aidd.harness.live_e2e_black_box_reports import _write_step_transcript
from aidd.harness.runner import HarnessCommandTranscript


def _persist(bundle_root: Path, output: str) -> dict[str, object]:
    return persist_command_evidence(
        bundle_root=bundle_root,
        command=("python", "-c", "print('x')"),
        duration_seconds=1.25,
        exit_code=0,
        stdout_text=output,
        stderr_text="warning\n",
        timed_out=False,
        timeout_seconds=30.0,
    )


def test_command_evidence_is_content_addressed_and_projection_is_bounded(
    tmp_path: Path,
) -> None:
    output = "x" * 1_000_000

    first = _persist(tmp_path, output)
    second = _persist(tmp_path, output)

    assert first == second
    assert "stdout_text" not in first
    assert len(str(first["stdout_preview"]).encode("utf-8")) == COMMAND_PREVIEW_BYTE_LIMIT
    assert first["stdout_preview_truncated"] is True
    evidence_files = list((tmp_path / "command-evidence").glob("*.json"))
    assert len(evidence_files) == 1
    assert evidence_files[0].stat().st_size < 1_010_000
    derived_paths = [
        tmp_path / "flow-steps.json",
        tmp_path / "grader.json",
        tmp_path / "run-transcript.json",
    ]
    for path in derived_paths:
        path.write_text(
            json.dumps({"commands": [first]}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    assert sum(path.stat().st_size for path in derived_paths) < 20_000
    assert sum(
        path.stat().st_size for path in tmp_path.rglob("*") if path.is_file()
    ) < 1_030_000
    assert read_command_output(bundle_root=tmp_path, command_payload=first) == (
        output,
        "warning\n",
    )


def test_command_evidence_reader_accepts_legacy_inline_record(tmp_path: Path) -> None:
    assert read_command_output(
        bundle_root=tmp_path,
        command_payload={"stdout_text": "old out", "stderr_text": "old err"},
    ) == ("old out", "old err")


def test_command_evidence_reader_rejects_digest_mismatch(tmp_path: Path) -> None:
    projection = _persist(tmp_path, "trusted")
    evidence_path = tmp_path / str(projection["evidence_path"])
    evidence_path.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch"):
        read_command_output(bundle_root=tmp_path, command_payload=projection)


def test_step_transcript_references_one_canonical_command_record(tmp_path: Path) -> None:
    transcript = HarnessCommandTranscript(
        command="pytest -q",
        exit_code=1,
        stdout_text="test output\n",
        stderr_text="failure\n",
        duration_seconds=2.5,
        timed_out=False,
        timeout_seconds=60.0,
    )

    path = _write_step_transcript(
        path=tmp_path / "verify-transcript.json",
        step="verify",
        transcripts=(transcript,),
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    command = payload["commands"][0]
    assert "stdout_text" not in command
    assert command["stdout_preview"] == "test output\n"
    evidence_path = tmp_path / command["evidence_path"]
    assert hashlib.sha256(evidence_path.read_bytes()).hexdigest() == command[
        "evidence_sha256"
    ]
