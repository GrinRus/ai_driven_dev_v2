from __future__ import annotations

import json
import queue
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from aidd.adapters.codex.approvals import (
    codex_approval_request_to_operator_request,
    operator_decision_to_codex_response,
)
from aidd.adapters.codex.runner import (
    CodexCommandContext,
    CodexExitClassification,
    CodexRunResult,
    build_subprocess_spec,
)
from aidd.adapters.live_transport import (
    LiveTransportResult,
    append_jsonl,
    run_help_text,
    split_command,
    terminate_process,
)
from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.core.runtime_operator import (
    RuntimeOperatorBroker,
    RuntimeOperatorDecision,
    RuntimeOperatorDecisionProvider,
)
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_permissions import RuntimeOperatorDecisionAction

_CODEX_TRANSCRIPT_FILENAME = "codex-app-server.jsonl"
_APPROVAL_METHODS = frozenset(
    {
        "item/commandExecution/requestApproval",
        "item/fileChange/requestApproval",
        "item/permissions/requestApproval",
        "execCommandApproval",
        "applyPatchApproval",
        "item/execCommand/requestApproval",
    }
)
_AIDD_CODEX_APPROVAL_POLICY: dict[str, object] = {
    "granular": {
        "mcp_elicitations": True,
        "request_permissions": True,
        "rules": True,
        "sandbox_approval": True,
        "skill_approval": True,
    }
}


class _JsonRpcLineClient:
    def __init__(
        self,
        *,
        process: subprocess.Popen[str],
        transcript_path: Path,
        on_stdout: Callable[[str], None] | None,
        on_stderr: Callable[[str], None] | None,
    ) -> None:
        self.process = process
        self.transcript_path = transcript_path
        self._on_stdout = on_stdout
        self._on_stderr = on_stderr
        self._messages: queue.Queue[Mapping[str, Any]] = queue.Queue()
        self._stdout_lines: list[str] = []
        self._stderr_lines: list[str] = []
        self._threads: list[threading.Thread] = []
        self._next_id = 1

    @property
    def stdout_text(self) -> str:
        return "".join(self._stdout_lines)

    @property
    def stderr_text(self) -> str:
        return "".join(self._stderr_lines)

    @property
    def runtime_log_text(self) -> str:
        return self.stdout_text + self.stderr_text

    def start(self) -> None:
        if self.process.stdout is not None:
            thread = threading.Thread(target=self._read_stdout, daemon=True)
            thread.start()
            self._threads.append(thread)
        if self.process.stderr is not None:
            thread = threading.Thread(target=self._read_stderr, daemon=True)
            thread.start()
            self._threads.append(thread)

    def join(self) -> None:
        for thread in self._threads:
            thread.join(timeout=1.0)

    def request(self, method: str, params: Mapping[str, Any]) -> int:
        request_id = self._next_id
        self._next_id += 1
        self.send({"id": request_id, "method": method, "params": dict(params)})
        return request_id

    def notify(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"method": method}
        if params is not None:
            payload["params"] = dict(params)
        self.send(payload)

    def respond(self, request_id: object, result: Mapping[str, Any]) -> None:
        self.send({"id": request_id, "result": dict(result)})

    def send(self, payload: Mapping[str, Any]) -> None:
        append_jsonl(self.transcript_path, {"direction": "client", "payload": dict(payload)})
        if self.process.stdin is None:
            return
        self.process.stdin.write(json.dumps(dict(payload), sort_keys=True) + "\n")
        self.process.stdin.flush()

    def next_message(self, *, timeout_seconds: float) -> Mapping[str, Any] | None:
        try:
            return self._messages.get(timeout=timeout_seconds)
        except queue.Empty:
            return None

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        try:
            for line in self.process.stdout:
                self._stdout_lines.append(line)
                if self._on_stdout is not None:
                    self._on_stdout(line)
                message = _parse_json_line(line)
                if message is not None:
                    append_jsonl(
                        self.transcript_path,
                        {"direction": "server", "payload": dict(message)},
                    )
                    self._messages.put(message)
        finally:
            self.process.stdout.close()

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        try:
            for line in self.process.stderr:
                self._stderr_lines.append(line)
                if self._on_stderr is not None:
                    self._on_stderr(line)
        finally:
            self.process.stderr.close()


def codex_live_transport_available(configured_command: str) -> bool:
    tokens = split_command(configured_command, runtime_label="codex")
    if Path(tokens[0]).name != "codex":
        return False
    help_text = run_help_text((tokens[0], "app-server", "--help"))
    return "--listen" in help_text and "generate-json-schema" in help_text


def execute_codex_live_transport(
    *,
    configured_command: str,
    context: CodexCommandContext,
    base_env: Mapping[str, str],
    repository_root: Path,
    attempt_path: Path,
    broker: RuntimeOperatorBroker,
    operator_decision_provider: RuntimeOperatorDecisionProvider,
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
    timeout_seconds: float | None,
) -> LiveTransportResult[CodexExitClassification]:
    if not codex_live_transport_available(configured_command):
        return LiveTransportResult(
            run_result=None,
            status=AdapterExecutionStatus.BLOCKED_FOR_OPERATOR,
            details=(
                "blocked_for_operator: codex live broker requires app-server "
                "stdio approval support"
            ),
        )

    tokens = split_command(configured_command, runtime_label="codex")
    spec = build_subprocess_spec(
        configured_command=tokens[0],
        context=context,
        base_env=base_env,
        repository_root=repository_root,
        execution_mode=RuntimeExecutionMode.NATIVE,
    )
    attempt_path.mkdir(parents=True, exist_ok=True)
    transcript_path = attempt_path / _CODEX_TRANSCRIPT_FILENAME
    process = subprocess.Popen(
        (tokens[0], "app-server", "--listen", "stdio://"),
        cwd=repository_root,
        env=spec.env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    client = _JsonRpcLineClient(
        process=process,
        transcript_path=transcript_path,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
    )
    client.start()
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds

    initialize_id = client.request(
        "initialize",
        {
            "clientInfo": {"name": "aidd", "version": "0"},
            "capabilities": {"experimentalApi": True},
        },
    )
    pending_request_id, denied_reason = _drain_until_response(
        client=client,
        response_id=initialize_id,
        deadline=deadline,
        repository_root=repository_root,
        context=context,
        broker=broker,
        operator_decision_provider=operator_decision_provider,
    )
    if pending_request_id is not None or denied_reason is not None:
        return _early_stop_result(
            client=client,
            process=process,
            pending_request_id=pending_request_id,
            denied_reason=denied_reason,
            transcript_path=transcript_path,
            broker=broker,
        )

    client.notify("initialized")
    thread_start_id = client.request(
            "thread/start",
            {
                "cwd": repository_root.as_posix(),
                "approvalPolicy": _AIDD_CODEX_APPROVAL_POLICY,
                "approvalsReviewer": "user",
                "sandbox": "read-only",
                "ephemeral": True,
                "serviceName": "aidd",
                "baseInstructions": "Run the AIDD stage request exactly as provided.",
        },
    )
    pending_request_id, denied_reason = _drain_until_response(
        client=client,
        response_id=thread_start_id,
        deadline=deadline,
        repository_root=repository_root,
        context=context,
        broker=broker,
        operator_decision_provider=operator_decision_provider,
    )
    if pending_request_id is not None or denied_reason is not None:
        return _early_stop_result(
            client=client,
            process=process,
            pending_request_id=pending_request_id,
            denied_reason=denied_reason,
            transcript_path=transcript_path,
            broker=broker,
        )

    thread_id = _thread_id_from_transcript_response(
        transcript_path=transcript_path,
        response_id=thread_start_id,
    )
    if thread_id is None:
        terminate_process(process)
        client.join()
        return _failed_result(
            client=client,
            process=process,
            transcript_path=transcript_path,
            details="codex-live: thread/start did not return a thread id",
        )

    turn_start_id = client.request(
        "turn/start",
        {
            "threadId": thread_id,
            "cwd": repository_root.as_posix(),
            "approvalPolicy": _AIDD_CODEX_APPROVAL_POLICY,
            "approvalsReviewer": "user",
            "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
            "input": [{"type": "text", "text": spec.stdin_text or ""}],
        },
    )
    completed = False
    denied_reason = None
    pending_request_id = None
    while process.poll() is None and not completed:
        if deadline is not None and time.monotonic() >= deadline:
            terminate_process(process)
            client.join()
            run_result = _run_result(
                process=process,
                client=client,
                stop_reason=CodexExitClassification.TIMEOUT,
            )
            return LiveTransportResult(
                run_result=run_result,
                status=AdapterExecutionStatus.FAILED,
                details="codex-live: timeout",
                events_jsonl_path=transcript_path,
            )
        message = client.next_message(timeout_seconds=0.1)
        if message is None:
            continue
        if message.get("id") == turn_start_id and "error" in message:
            denied_reason = f"codex-live: turn/start failed: {message.get('error')}"
            break
        if _message_is_approval_request(message):
            pending_request_id, denied_reason = _handle_approval_request(
                message=message,
                client=client,
                repository_root=repository_root,
                context=context,
                broker=broker,
                operator_decision_provider=operator_decision_provider,
            )
            if pending_request_id is not None or denied_reason is not None:
                break
        if message.get("method") == "turn/completed":
            completed = True
        elif message.get("method") == "thread/status/changed" and _status_is_idle(message):
            completed = True

    if pending_request_id is not None or denied_reason is not None:
        return _early_stop_result(
            client=client,
            process=process,
            pending_request_id=pending_request_id,
            denied_reason=denied_reason,
            transcript_path=transcript_path,
            broker=broker,
        )

    terminate_process(process)
    client.join()
    run_result = _run_result(process=process, client=client, stop_reason=None)
    status = (
        AdapterExecutionStatus.SUCCEEDED
        if completed and run_result.exit_classification is CodexExitClassification.SUCCESS
        else AdapterExecutionStatus.FAILED
    )
    details = "codex-live: success" if status is AdapterExecutionStatus.SUCCEEDED else (
        f"codex-live: {run_result.exit_classification.value}"
    )
    return LiveTransportResult(
        run_result=run_result,
        status=status,
        details=details,
        events_jsonl_path=transcript_path,
        operator_requests_path=broker.requests_path if broker.requests_path.exists() else None,
        operator_decisions_path=(
            broker.decisions_path if broker.decisions_path.exists() else None
        ),
    )


def _drain_until_response(
    *,
    client: _JsonRpcLineClient,
    response_id: int,
    deadline: float | None,
    repository_root: Path,
    context: CodexCommandContext,
    broker: RuntimeOperatorBroker,
    operator_decision_provider: RuntimeOperatorDecisionProvider,
) -> tuple[str | None, str | None]:
    while client.process.poll() is None:
        if deadline is not None and time.monotonic() >= deadline:
            terminate_process(client.process)
            return None, "codex-live: timeout"
        message = client.next_message(timeout_seconds=0.1)
        if message is None:
            continue
        if message.get("id") == response_id:
            if "error" in message:
                return None, f"codex-live: request failed: {message.get('error')}"
            return None, None
        if _message_is_approval_request(message):
            pending_request_id, denied_reason = _handle_approval_request(
                message=message,
                client=client,
                repository_root=repository_root,
                context=context,
                broker=broker,
                operator_decision_provider=operator_decision_provider,
            )
            if pending_request_id is not None or denied_reason is not None:
                return pending_request_id, denied_reason
    return None, "codex-live: app-server exited before response"


def _handle_approval_request(
    *,
    message: Mapping[str, Any],
    client: _JsonRpcLineClient,
    repository_root: Path,
    context: CodexCommandContext,
    broker: RuntimeOperatorBroker,
    operator_decision_provider: RuntimeOperatorDecisionProvider,
) -> tuple[str | None, str | None]:
    method = str(message.get("method") or "")
    raw_params = message.get("params")
    params = dict(raw_params) if isinstance(raw_params, Mapping) else {}
    cwd = Path(str(params.get("cwd"))) if params.get("cwd") is not None else repository_root
    operator_request = codex_approval_request_to_operator_request(
        method=method,
        payload=params,
        runtime_id="codex",
        stage=context.stage,
        cwd=cwd,
    )
    decision = broker.handle_request(
        operator_request,
        decision_provider=operator_decision_provider,
    )
    if decision is None:
        return operator_request.id, None
    client.respond(
        message.get("id"),
        _codex_jsonrpc_approval_result(
            method=method,
            decision=decision,
            params=params,
        ),
    )
    if not decision.is_approval:
        return None, f"permission-denied: {decision.action.value}"
    return None, None


def _codex_jsonrpc_approval_result(
    *,
    method: str,
    decision: RuntimeOperatorDecision,
    params: Mapping[str, Any],
) -> dict[str, object]:
    if "permissions/requestapproval" in method.lower():
        if not decision.is_approval:
            return {
                "permissions": {},
                "scope": "turn",
                "strictAutoReview": True,
            }
        return {
            "permissions": dict(params.get("permissions", {}))
            if isinstance(params.get("permissions"), Mapping)
            else {},
            "scope": (
                "session"
                if decision.action is RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION
                else "turn"
            ),
            "strictAutoReview": True,
        }
    response = operator_decision_to_codex_response(decision)
    return {"decision": response["decision"]}


def _early_stop_result(
    *,
    client: _JsonRpcLineClient,
    process: subprocess.Popen[str],
    pending_request_id: str | None,
    denied_reason: str | None,
    transcript_path: Path,
    broker: RuntimeOperatorBroker,
) -> LiveTransportResult[CodexExitClassification]:
    terminate_process(process)
    client.join()
    if pending_request_id is not None:
        return LiveTransportResult(
            run_result=None,
            status=AdapterExecutionStatus.BLOCKED_FOR_OPERATOR,
            details="blocked_for_operator: codex live approval request pending",
            events_jsonl_path=transcript_path,
            operator_requests_path=broker.requests_path,
            operator_decisions_path=(
                broker.decisions_path if broker.decisions_path.exists() else None
            ),
            pending_operator_request_ids=(pending_request_id,),
        )
    return LiveTransportResult(
        run_result=_run_result(process=process, client=client, stop_reason=None),
        status=AdapterExecutionStatus.FAILED,
        details=denied_reason or "codex-live: stopped",
        events_jsonl_path=transcript_path,
        operator_requests_path=broker.requests_path if broker.requests_path.exists() else None,
        operator_decisions_path=(
            broker.decisions_path if broker.decisions_path.exists() else None
        ),
    )


def _failed_result(
    *,
    client: _JsonRpcLineClient,
    process: subprocess.Popen[str],
    transcript_path: Path,
    details: str,
) -> LiveTransportResult[CodexExitClassification]:
    return LiveTransportResult(
        run_result=_run_result(process=process, client=client, stop_reason=None),
        status=AdapterExecutionStatus.FAILED,
        details=details,
        events_jsonl_path=transcript_path,
    )


def _run_result(
    *,
    process: subprocess.Popen[str],
    client: _JsonRpcLineClient,
    stop_reason: CodexExitClassification | None,
) -> CodexRunResult:
    exit_code = process.returncode if process.returncode is not None else -1
    if stop_reason is not None:
        classification = stop_reason
    elif exit_code in {0, -15}:
        classification = CodexExitClassification.SUCCESS
    else:
        classification = CodexExitClassification.NON_ZERO_EXIT
    return CodexRunResult(
        exit_code=exit_code,
        stdout_text=client.stdout_text,
        stderr_text=client.stderr_text,
        runtime_log_text=client.runtime_log_text,
        exit_classification=classification,
    )


def _message_is_approval_request(message: Mapping[str, Any]) -> bool:
    method = str(message.get("method") or "")
    return method in _APPROVAL_METHODS or (
        "approval" in method.lower() and "request" in method.lower()
    )


def _status_is_idle(message: Mapping[str, Any]) -> bool:
    raw_params = message.get("params")
    if not isinstance(raw_params, Mapping):
        return False
    raw_status = raw_params.get("status")
    if isinstance(raw_status, Mapping):
        return raw_status.get("type") == "idle"
    return False


def _thread_id_from_transcript_response(
    *,
    transcript_path: Path,
    response_id: int,
) -> str | None:
    if not transcript_path.exists():
        return None
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        payload = _parse_json_line(line)
        if payload is None or payload.get("direction") != "server":
            continue
        raw_message = payload.get("payload")
        if not isinstance(raw_message, Mapping) or raw_message.get("id") != response_id:
            continue
        raw_result = raw_message.get("result")
        if not isinstance(raw_result, Mapping):
            return None
        raw_thread = raw_result.get("thread")
        if isinstance(raw_thread, Mapping) and raw_thread.get("id") is not None:
            return str(raw_thread["id"])
    return None


def _parse_json_line(line: str) -> Mapping[str, Any] | None:
    stripped = line.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, Mapping) else None


__all__ = [
    "codex_live_transport_available",
    "execute_codex_live_transport",
]
