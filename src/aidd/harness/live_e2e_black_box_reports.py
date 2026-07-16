from __future__ import annotations

import json
import os
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aidd.harness.runner import HarnessCommandTranscript


def _write_json(path: Path, payload: object) -> Path:
    return _write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_text_atomic(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)
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


def _command_text(command: Sequence[str]) -> str:
    return " ".join(command)


def write_flow_report(
    *,
    path: Path,
    scenario_id: str,
    runtime_id: str,
    run_id: str,
    work_item: str,
    state: dict[str, Any],
    steps: list[dict[str, Any]],
) -> Path:
    lines = [
        "# Black-Box Live E2E Flow Report",
        "",
        "## Run",
        f"- Scenario: `{scenario_id}`",
        f"- Runtime: `{runtime_id}`",
        f"- Run ID: `{run_id}`",
        f"- Work item: `{work_item}`",
        f"- Status: `{state.get('status', 'running')}`",
        f"- Next action: `{state.get('next_action', 'unknown')}`",
        "",
        "## Steps",
    ]
    if not steps:
        lines.append("- No steps recorded yet.")
    for step in steps:
        stage = step.get("stage") or "n/a"
        lines.extend(
            (
                "",
                f"### {step.get('step_index', '?')}. {step.get('action', 'unknown')}",
                f"- Stage: `{stage}`",
                f"- Plan: {step.get('plan', '')}",
                f"- Classification: `{step.get('classification', 'unknown')}`",
                f"- Decision: {step.get('decision', '')}",
            )
        )
        raw_commands = step.get("commands")
        commands = raw_commands if isinstance(raw_commands, list) else []
        for command in commands:
            if not isinstance(command, dict):
                continue
            command_text = _command_text(
                tuple(str(item) for item in command.get("command", []))
                if isinstance(command.get("command"), list)
                else tuple()
            )
            lines.append(f"- Command: `{command_text}` exit=`{command.get('exit_code', 'n/a')}`")
    return _write_text_atomic(path, "\n".join(lines).rstrip() + "\n")


def write_json_markdown_bundle(
    *,
    json_path: Path,
    markdown_path: Path,
    payload: object,
    markdown: str,
) -> tuple[Path, Path]:
    _write_json(json_path, payload)
    _write_text_atomic(markdown_path, markdown)
    return json_path, markdown_path


__all__ = [
    "_command_transcript_payload",
    "_read_json_object",
    "_read_jsonl_objects",
    "_transcript_duration",
    "_write_json",
    "_write_step_transcript",
    "_write_text_atomic",
    "write_flow_report",
    "write_json_markdown_bundle",
]
