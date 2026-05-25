from __future__ import annotations

import shlex
import subprocess
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from aidd.adapters.live_transport import (
    LiveTransportResult,
    StreamCapture,
    append_jsonl,
    run_help_text,
    split_command,
    terminate_process,
)
from aidd.adapters.qwen.approvals import (
    operator_decision_to_qwen_confirmation,
    qwen_control_request_to_operator_request,
)
from aidd.adapters.qwen.runner import (
    QwenCommandContext,
    QwenExitClassification,
    QwenRunResult,
    build_subprocess_spec,
)
from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.core.runtime_operator import RuntimeOperatorBroker, RuntimeOperatorDecisionProvider
from aidd.core.stage_models import AdapterExecutionStatus

_QWEN_EVENTS_FILENAME = "qwen-events.jsonl"
_QWEN_INPUT_FILENAME = "qwen-input.jsonl"
_QWEN_CONTROL_EVENT_TYPES = frozenset({"control_request", "confirmation_request"})
_CONTROLLED_VALUE_FLAGS = frozenset(
    {
        "--approval-mode",
        "--output-format",
        "--json-file",
        "--input-file",
    }
)
_CONTROLLED_BOOL_FLAGS = frozenset({"-y", "--yolo"})


def qwen_live_transport_available(configured_command: str) -> bool:
    tokens = split_command(configured_command, runtime_label="qwen")
    if Path(tokens[0]).name != "qwen":
        return False
    if _has_explicit_dual_file_flags(tokens):
        return False
    help_text = run_help_text((tokens[0], "--help"))
    return all(marker in help_text for marker in ("--json-file", "--input-file"))


def execute_qwen_live_transport(
    *,
    configured_command: str,
    context: QwenCommandContext,
    base_env: Mapping[str, str],
    repository_root: Path,
    attempt_path: Path,
    broker: RuntimeOperatorBroker,
    operator_decision_provider: RuntimeOperatorDecisionProvider,
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
    timeout_seconds: float | None,
) -> LiveTransportResult[QwenExitClassification]:
    if not qwen_live_transport_available(configured_command):
        return LiveTransportResult(
            run_result=None,
            status=AdapterExecutionStatus.BLOCKED_FOR_OPERATOR,
            details=(
                "blocked_for_operator: qwen live broker requires managed native qwen "
                "command with --json-file and --input-file support"
            ),
        )

    attempt_path.mkdir(parents=True, exist_ok=True)
    events_path = attempt_path / _QWEN_EVENTS_FILENAME
    input_path = attempt_path / _QWEN_INPUT_FILENAME
    input_path.touch()
    controlled_command = _controlled_live_command(
        configured_command=configured_command,
        events_path=events_path,
        input_path=input_path,
    )
    spec = build_subprocess_spec(
        configured_command=shlex.join(controlled_command),
        context=context,
        base_env=base_env,
        repository_root=repository_root,
        execution_mode=RuntimeExecutionMode.NATIVE,
    )
    process = subprocess.Popen(
        spec.command,
        cwd=spec.cwd,
        env=spec.env,
        stdin=subprocess.PIPE if spec.stdin_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    if process.stdin is not None and spec.stdin_text is not None:
        process.stdin.write(spec.stdin_text)
        process.stdin.close()

    capture = StreamCapture(on_stdout=on_stdout, on_stderr=on_stderr)
    capture.attach(process)
    seen_request_ids: set[str] = set()
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
    stop_reason: QwenExitClassification | None = None
    pending_request_id: str | None = None
    denied_reason: str | None = None
    read_offset = 0

    while process.poll() is None:
        if deadline is not None and time.monotonic() >= deadline:
            stop_reason = QwenExitClassification.TIMEOUT
            terminate_process(process)
            break

        read_offset, pending_request_id, denied_reason = _handle_new_events(
            events_path=events_path,
            read_offset=read_offset,
            seen_request_ids=seen_request_ids,
            runtime_id="qwen",
            stage=context.stage,
            cwd=repository_root,
            broker=broker,
            operator_decision_provider=operator_decision_provider,
            input_path=input_path,
        )
        if pending_request_id is not None:
            terminate_process(process)
            break
        if denied_reason is not None:
            terminate_process(process)
            break
        time.sleep(0.05)

    if pending_request_id is None and denied_reason is None:
        read_offset, pending_request_id, denied_reason = _handle_new_events(
            events_path=events_path,
            read_offset=read_offset,
            seen_request_ids=seen_request_ids,
            runtime_id="qwen",
            stage=context.stage,
            cwd=repository_root,
            broker=broker,
            operator_decision_provider=operator_decision_provider,
            input_path=input_path,
        )
    capture.join()

    if pending_request_id is not None:
        return LiveTransportResult(
            run_result=None,
            status=AdapterExecutionStatus.BLOCKED_FOR_OPERATOR,
            details="blocked_for_operator: qwen live approval request pending",
            runtime_jsonl_path=events_path if events_path.exists() else None,
            events_jsonl_path=events_path if events_path.exists() else None,
            operator_requests_path=broker.requests_path,
            operator_decisions_path=(
                broker.decisions_path if broker.decisions_path.exists() else None
            ),
            pending_operator_request_ids=(pending_request_id,),
        )
    if denied_reason is not None:
        run_result = _run_result(
            process=process,
            capture=capture,
            stop_reason=None,
        )
        return LiveTransportResult(
            run_result=run_result,
            status=AdapterExecutionStatus.FAILED,
            details=denied_reason,
            runtime_jsonl_path=events_path if events_path.exists() else None,
            events_jsonl_path=events_path if events_path.exists() else None,
            operator_requests_path=broker.requests_path,
            operator_decisions_path=broker.decisions_path,
        )

    run_result = _run_result(process=process, capture=capture, stop_reason=stop_reason)
    status = (
        AdapterExecutionStatus.SUCCEEDED
        if run_result.exit_classification is QwenExitClassification.SUCCESS
        else AdapterExecutionStatus.FAILED
    )
    return LiveTransportResult(
        run_result=run_result,
        status=status,
        details=f"qwen-live: {run_result.exit_classification.value}",
        runtime_jsonl_path=events_path if events_path.exists() else None,
        events_jsonl_path=events_path if events_path.exists() else None,
        operator_requests_path=broker.requests_path if broker.requests_path.exists() else None,
        operator_decisions_path=(
            broker.decisions_path if broker.decisions_path.exists() else None
        ),
    )


def _handle_new_events(
    *,
    events_path: Path,
    read_offset: int,
    seen_request_ids: set[str],
    runtime_id: str,
    stage: str,
    cwd: Path,
    broker: RuntimeOperatorBroker,
    operator_decision_provider: RuntimeOperatorDecisionProvider,
    input_path: Path,
) -> tuple[int, str | None, str | None]:
    if not events_path.exists():
        return read_offset, None, None
    with events_path.open("r", encoding="utf-8") as handle:
        handle.seek(read_offset)
        lines = handle.readlines()
        read_offset = handle.tell()

    for line in lines:
        event = _parse_json_line(line)
        if event is None or not _is_control_request(event):
            continue
        operator_request = qwen_control_request_to_operator_request(
            event,
            runtime_id=runtime_id,
            stage=stage,
            cwd=cwd,
        )
        if operator_request.id in seen_request_ids:
            continue
        seen_request_ids.add(operator_request.id)
        decision = broker.handle_request(
            operator_request,
            decision_provider=operator_decision_provider,
        )
        if decision is None:
            return read_offset, operator_request.id, None
        append_jsonl(input_path, operator_decision_to_qwen_confirmation(decision))
        if not decision.is_approval:
            return read_offset, None, f"permission-denied: {decision.action.value}"
    return read_offset, None, None


def _parse_json_line(line: str) -> Mapping[str, Any] | None:
    import json

    stripped = line.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, Mapping) else None


def _is_control_request(event: Mapping[str, Any]) -> bool:
    event_type = str(event.get("type") or event.get("event") or "").strip()
    return event_type in _QWEN_CONTROL_EVENT_TYPES


def _controlled_live_command(
    *,
    configured_command: str,
    events_path: Path,
    input_path: Path,
) -> tuple[str, ...]:
    tokens = list(split_command(configured_command, runtime_label="qwen"))
    command: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in _CONTROLLED_BOOL_FLAGS:
            index += 1
            continue
        if token in _CONTROLLED_VALUE_FLAGS:
            index += 2
            continue
        if any(token.startswith(f"{flag}=") for flag in _CONTROLLED_VALUE_FLAGS):
            index += 1
            continue
        command.append(token)
        index += 1
    command.extend(
        (
            "--approval-mode",
            "default",
            "--output-format",
            "stream-json",
            "--json-file",
            events_path.as_posix(),
            "--input-file",
            input_path.as_posix(),
        )
    )
    return tuple(command)


def _has_explicit_dual_file_flags(tokens: tuple[str, ...]) -> bool:
    return any(
        token in {"--json-file", "--input-file"}
        or token.startswith("--json-file=")
        or token.startswith("--input-file=")
        for token in tokens
    )


def _run_result(
    *,
    process: subprocess.Popen[str],
    capture: StreamCapture,
    stop_reason: QwenExitClassification | None,
) -> QwenRunResult:
    exit_code = process.returncode if process.returncode is not None else -1
    if stop_reason is not None:
        classification = stop_reason
    elif exit_code == 0:
        classification = QwenExitClassification.SUCCESS
    else:
        classification = QwenExitClassification.NON_ZERO_EXIT
    return QwenRunResult(
        exit_code=exit_code,
        stdout_text=capture.stdout_text,
        stderr_text=capture.stderr_text,
        runtime_log_text=capture.runtime_log_text,
        exit_classification=classification,
    )


__all__ = [
    "execute_qwen_live_transport",
    "qwen_live_transport_available",
]
