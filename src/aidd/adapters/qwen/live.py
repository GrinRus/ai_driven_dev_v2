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
)
from aidd.adapters.process_io import ManagedStdinWriter
from aidd.adapters.process_supervisor import OwnedProcessSupervisor
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
from aidd.core.runtime_operator import RuntimeOperatorBroker, RuntimeOperatorDecisionProvider
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_catalog import RuntimeExecutionMode
from aidd.runtime_permissions import RuntimeOperatorDecisionAction

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
    cancel_requested: Callable[[], bool] | None = None,
) -> LiveTransportResult[QwenExitClassification]:
    if not qwen_live_transport_available(configured_command):
        return LiveTransportResult(
            run_result=QwenRunResult(
                exit_code=None,
                stdout_text="",
                stderr_text="",
                runtime_log_text="",
                exit_classification=QwenExitClassification.BLOCKED,
            ),
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
    supervisor = OwnedProcessSupervisor.launch(spec)
    process = supervisor.process
    capture = StreamCapture(
        directory=attempt_path,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
    )
    capture.attach(process)
    seen_request_ids: set[str] = set()
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
    stop_reason: QwenExitClassification | None = None
    pending_request_id: str | None = None
    denied_reason: str | None = None
    terminal_classification: QwenExitClassification | None = None
    read_offset = 0
    stdin_writer = ManagedStdinWriter.start(process.stdin, spec.stdin_text)

    while process.poll() is None:
        if cancel_requested is not None and cancel_requested():
            stop_reason = QwenExitClassification.CANCELLED
            break
        if capture.error is not None:
            capture_error = capture.error
            _stop_qwen_process(
                supervisor=supervisor,
                capture=capture,
                stdin_writer=stdin_writer,
            )
            assert capture_error is not None
            capture.abort()
            raise capture_error
        if stdin_writer is not None and stdin_writer.error is not None:
            writer_error = stdin_writer.error
            _stop_qwen_process(
                supervisor=supervisor,
                capture=capture,
                stdin_writer=stdin_writer,
            )
            assert writer_error is not None
            capture.abort()
            raise writer_error
        if deadline is not None and time.monotonic() >= deadline:
            stop_reason = QwenExitClassification.TIMEOUT
            break

        (
            read_offset,
            pending_request_id,
            denied_reason,
            terminal_classification,
        ) = _handle_new_events(
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
        if cancel_requested is not None and cancel_requested():
            stop_reason = QwenExitClassification.CANCELLED
            pending_request_id = None
            denied_reason = None
            break
        if pending_request_id is not None:
            break
        if denied_reason is not None:
            break
        time.sleep(0.05)

    if (
        stop_reason is not QwenExitClassification.CANCELLED
        and pending_request_id is None
        and denied_reason is None
    ):
        (
            read_offset,
            pending_request_id,
            denied_reason,
            terminal_classification,
        ) = _handle_new_events(
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
    _stop_qwen_process(
        supervisor=supervisor,
        capture=capture,
        stdin_writer=stdin_writer,
    )
    if capture.error is not None:
        capture.abort()
        raise capture.error
    if (
        stdin_writer is not None
        and stdin_writer.error is not None
        and stop_reason is None
    ):
        capture.abort()
        raise stdin_writer.error

    if stop_reason is QwenExitClassification.CANCELLED:
        run_result = _run_result(
            process=process,
            capture=capture,
            stop_reason=stop_reason,
        )
        return LiveTransportResult(
            run_result=run_result,
            status=AdapterExecutionStatus.FAILED,
            details="qwen-live: cancelled",
            runtime_jsonl_path=events_path if events_path.exists() else None,
            events_jsonl_path=events_path if events_path.exists() else None,
            operator_requests_path=(
                broker.requests_path if broker.requests_path.exists() else None
            ),
            operator_decisions_path=(
                broker.decisions_path if broker.decisions_path.exists() else None
            ),
        )
    if pending_request_id is not None:
        return LiveTransportResult(
            run_result=_captured_run_result(
                capture=capture,
                exit_code=None,
                exit_classification=QwenExitClassification.BLOCKED,
            ),
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
        run_result = _captured_run_result(
            capture=capture,
            exit_code=None,
            exit_classification=(
                terminal_classification or QwenExitClassification.DENIED
            ),
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
) -> tuple[
    int,
    str | None,
    str | None,
    QwenExitClassification | None,
]:
    read_offset, lines = _read_complete_event_lines(
        events_path=events_path,
        read_offset=read_offset,
    )

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
            return read_offset, operator_request.id, None, None
        append_jsonl(input_path, operator_decision_to_qwen_confirmation(decision))
        if not decision.is_approval:
            return (
                read_offset,
                None,
                f"permission-denied: {decision.action.value}",
                (
                    QwenExitClassification.CANCELLED
                    if decision.action is RuntimeOperatorDecisionAction.CANCEL
                    else QwenExitClassification.DENIED
                ),
            )
    return read_offset, None, None, None


def _read_complete_event_lines(
    *,
    events_path: Path,
    read_offset: int,
) -> tuple[int, tuple[bytes, ...]]:
    if not events_path.exists():
        return read_offset, ()
    with events_path.open("rb") as handle:
        handle.seek(read_offset)
        payload = handle.read()
    last_newline = payload.rfind(b"\n")
    if last_newline < 0:
        return read_offset, ()
    committed_payload = payload[: last_newline + 1]
    return (
        read_offset + len(committed_payload),
        tuple(committed_payload.splitlines()),
    )


def _parse_json_line(line: str | bytes) -> Mapping[str, Any] | None:
    import json

    if isinstance(line, bytes):
        try:
            line = line.decode("utf-8")
        except UnicodeDecodeError:
            return None
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
    snapshot = capture.snapshot
    return QwenRunResult(
        exit_code=exit_code,
        stdout_text=snapshot.stdout_text,
        stderr_text=snapshot.stderr_text,
        runtime_log_text=snapshot.runtime_log_text,
        exit_classification=classification,
        runtime_log_source_path=snapshot.runtime_log_source_path,
        structured_events_source_path=snapshot.structured_events_source_path,
        stdout_byte_count=snapshot.stdout_byte_count,
        stderr_byte_count=snapshot.stderr_byte_count,
        runtime_log_byte_count=snapshot.runtime_log_byte_count,
        stdout_char_count=snapshot.stdout_char_count,
        stderr_char_count=snapshot.stderr_char_count,
        runtime_log_char_count=snapshot.runtime_log_char_count,
        stdout_truncated=snapshot.stdout_truncated,
        stderr_truncated=snapshot.stderr_truncated,
        runtime_log_truncated=snapshot.runtime_log_truncated,
    )


def _captured_run_result(
    *,
    capture: StreamCapture,
    exit_code: int | None,
    exit_classification: QwenExitClassification,
) -> QwenRunResult:
    snapshot = capture.snapshot
    return QwenRunResult(
        exit_code=exit_code,
        stdout_text=snapshot.stdout_text,
        stderr_text=snapshot.stderr_text,
        runtime_log_text=snapshot.runtime_log_text,
        exit_classification=exit_classification,
        runtime_log_source_path=snapshot.runtime_log_source_path,
        structured_events_source_path=snapshot.structured_events_source_path,
        stdout_byte_count=snapshot.stdout_byte_count,
        stderr_byte_count=snapshot.stderr_byte_count,
        runtime_log_byte_count=snapshot.runtime_log_byte_count,
        stdout_char_count=snapshot.stdout_char_count,
        stderr_char_count=snapshot.stderr_char_count,
        runtime_log_char_count=snapshot.runtime_log_char_count,
        stdout_truncated=snapshot.stdout_truncated,
        stderr_truncated=snapshot.stderr_truncated,
        runtime_log_truncated=snapshot.runtime_log_truncated,
    )


def _stop_qwen_process(
    *,
    supervisor: OwnedProcessSupervisor,
    capture: StreamCapture,
    stdin_writer: ManagedStdinWriter | None,
) -> None:
    supervisor.request_stop()
    supervisor.drain_streams(capture.reader_threads)
    if stdin_writer is not None:
        stdin_writer.join()


__all__ = [
    "execute_qwen_live_transport",
    "qwen_live_transport_available",
]
