from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aidd.harness.runner import HarnessCommandTranscript


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path.as_posix()}.")
    return payload


def _read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    objects: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            objects.append(payload)
    return objects


def _command_transcript_payload(transcript: HarnessCommandTranscript) -> dict[str, object]:
    return {
        "command": transcript.command,
        "duration_seconds": transcript.duration_seconds,
        "exit_code": transcript.exit_code,
        "stderr_text": transcript.stderr_text,
        "stdout_text": transcript.stdout_text,
        "timed_out": transcript.timed_out,
        "timeout_seconds": transcript.timeout_seconds,
    }


def _transcript_duration(transcripts: tuple[HarnessCommandTranscript, ...]) -> float:
    return sum(transcript.duration_seconds for transcript in transcripts)


def _write_step_transcript(
    *,
    path: Path,
    step: str,
    transcripts: tuple[HarnessCommandTranscript, ...],
    extra: dict[str, object] | None = None,
) -> Path:
    payload: dict[str, object] = {
        "command_count": len(transcripts),
        "commands": [_command_transcript_payload(transcript) for transcript in transcripts],
        "duration_seconds": _transcript_duration(transcripts),
        "step": step,
    }
    if extra:
        payload.update(extra)
    return _write_json(path, payload)


__all__ = [
    "_command_transcript_payload",
    "_read_json_object",
    "_read_jsonl_objects",
    "_transcript_duration",
    "_write_json",
    "_write_step_transcript",
]
