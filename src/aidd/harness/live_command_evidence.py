from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from aidd.harness.runner import HarnessCommandTranscript

COMMAND_EVIDENCE_DIRNAME = "command-evidence"
COMMAND_EVIDENCE_SCHEMA_VERSION = 1
COMMAND_PREVIEW_BYTE_LIMIT = 2048


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _bounded_preview(value: str, *, byte_limit: int) -> tuple[str, bool]:
    raw = value.encode("utf-8")
    if len(raw) <= byte_limit:
        return value, False
    return raw[:byte_limit].decode("utf-8", errors="ignore"), True


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        temporary.write_bytes(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def persist_command_evidence(
    *,
    bundle_root: Path,
    command: Sequence[str] | str,
    exit_code: int,
    duration_seconds: float,
    stdout_text: str,
    stderr_text: str,
    timed_out: bool,
    timeout_seconds: float | None,
    projection_extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    normalized_command = (
        list(command) if not isinstance(command, str) else command
    )
    evidence_payload = {
        "command": normalized_command,
        "duration_seconds": duration_seconds,
        "exit_code": exit_code,
        "schema_version": COMMAND_EVIDENCE_SCHEMA_VERSION,
        "stderr_text": stderr_text,
        "stdout_text": stdout_text,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
    }
    content = _canonical_json_bytes(evidence_payload)
    digest = hashlib.sha256(content).hexdigest()
    relative_path = Path(COMMAND_EVIDENCE_DIRNAME) / f"{digest}.json"
    evidence_path = bundle_root / relative_path
    if evidence_path.exists():
        if evidence_path.read_bytes() != content:
            raise ValueError(
                f"Canonical command evidence digest collision at {evidence_path.as_posix()}."
            )
    else:
        _atomic_write_bytes(evidence_path, content)

    stdout_preview, stdout_truncated = _bounded_preview(
        stdout_text,
        byte_limit=COMMAND_PREVIEW_BYTE_LIMIT,
    )
    stderr_preview, stderr_truncated = _bounded_preview(
        stderr_text,
        byte_limit=COMMAND_PREVIEW_BYTE_LIMIT,
    )
    projection: dict[str, object] = {
        "command": normalized_command,
        "duration_seconds": duration_seconds,
        "evidence_path": relative_path.as_posix(),
        "evidence_sha256": digest,
        "evidence_size_bytes": len(content),
        "exit_code": exit_code,
        "stderr_preview": stderr_preview,
        "stderr_preview_truncated": stderr_truncated,
        "stdout_preview": stdout_preview,
        "stdout_preview_truncated": stdout_truncated,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
    }
    if projection_extra:
        projection.update(projection_extra)
    return projection


def persist_transcript_evidence(
    *,
    bundle_root: Path,
    transcript: HarnessCommandTranscript,
) -> dict[str, object]:
    return persist_command_evidence(
        bundle_root=bundle_root,
        command=transcript.command,
        exit_code=transcript.exit_code,
        duration_seconds=transcript.duration_seconds,
        stdout_text=transcript.stdout_text,
        stderr_text=transcript.stderr_text,
        timed_out=transcript.timed_out,
        timeout_seconds=transcript.timeout_seconds,
    )


def read_command_output(
    *,
    bundle_root: Path,
    command_payload: Mapping[str, Any],
) -> tuple[str, str]:
    legacy_stdout = command_payload.get("stdout_text")
    legacy_stderr = command_payload.get("stderr_text")
    if isinstance(legacy_stdout, str) or isinstance(legacy_stderr, str):
        return (
            legacy_stdout if isinstance(legacy_stdout, str) else "",
            legacy_stderr if isinstance(legacy_stderr, str) else "",
        )

    raw_relative_path = command_payload.get("evidence_path")
    expected_digest = command_payload.get("evidence_sha256")
    if not isinstance(raw_relative_path, str) or not isinstance(expected_digest, str):
        return "", ""
    relative_path = Path(raw_relative_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Command evidence path must be bundle-relative and contained.")
    root = bundle_root.resolve()
    evidence_path = (root / relative_path).resolve()
    if not evidence_path.is_relative_to(root):
        raise ValueError("Command evidence path escapes the live result bundle.")
    content = evidence_path.read_bytes()
    actual_digest = hashlib.sha256(content).hexdigest()
    if actual_digest != expected_digest:
        raise ValueError(
            "Command evidence digest mismatch: "
            f"expected {expected_digest}, observed {actual_digest}."
        )
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("Canonical command evidence must contain a JSON object.")
    stdout = payload.get("stdout_text")
    stderr = payload.get("stderr_text")
    return (
        stdout if isinstance(stdout, str) else "",
        stderr if isinstance(stderr, str) else "",
    )


__all__ = [
    "COMMAND_EVIDENCE_DIRNAME",
    "COMMAND_EVIDENCE_SCHEMA_VERSION",
    "COMMAND_PREVIEW_BYTE_LIMIT",
    "persist_command_evidence",
    "persist_transcript_evidence",
    "read_command_output",
]
