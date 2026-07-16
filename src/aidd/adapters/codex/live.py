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
)
from aidd.adapters.process_supervisor import OwnedProcessSupervisor
from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.core.runtime_operator import (
    RuntimeOperatorBroker,
    RuntimeOperatorDecision,
    RuntimeOperatorDecisionProvider,
)
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_catalog import RuntimeExecutionMode
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
        self._item_cache: dict[str, dict[str, Any]] = {}
        self._threads: list[threading.Thread] = []
        self._errors: list[BaseException] = []
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

    @property
    def reader_threads(self) -> tuple[threading.Thread, ...]:
        return tuple(self._threads)

    @property
    def error(self) -> BaseException | None:
        return self._errors[0] if self._errors else None

    def cached_item(self, item_id: object) -> Mapping[str, Any] | None:
        normalized_item_id = str(item_id or "").strip()
        if not normalized_item_id:
            return None
        return self._item_cache.get(normalized_item_id)

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
                    self._remember_item(message)
                    self._messages.put(message)
        except BaseException as exc:
            self._errors.append(exc)
        finally:
            self.process.stdout.close()

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        try:
            for line in self.process.stderr:
                self._stderr_lines.append(line)
                if self._on_stderr is not None:
                    self._on_stderr(line)
        except BaseException as exc:
            self._errors.append(exc)
        finally:
            self.process.stderr.close()

    def _remember_item(self, message: Mapping[str, Any]) -> None:
        method = str(message.get("method") or "")
        if method not in {"item/started", "item/updated", "item/completed"}:
            return
        raw_params = message.get("params")
        if not isinstance(raw_params, Mapping):
            return
        raw_item = raw_params.get("item")
        if not isinstance(raw_item, Mapping):
            return
        raw_item_id = raw_item.get("id")
        item_id = str(raw_item_id or "").strip()
        if not item_id:
            return
        cached = dict(self._item_cache.get(item_id, {}))
        cached.update(dict(raw_item))
        self._item_cache[item_id] = cached


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
    cancel_requested: Callable[[], bool] | None = None,
) -> LiveTransportResult[CodexExitClassification]:
    if not codex_live_transport_available(configured_command):
        return LiveTransportResult(
            run_result=CodexRunResult(
                exit_code=None,
                stdout_text="",
                stderr_text="",
                runtime_log_text="",
                exit_classification=CodexExitClassification.BLOCKED,
            ),
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
    supervisor = OwnedProcessSupervisor.launch(
        RuntimeSubprocessSpec(
            command=(tokens[0], "app-server", "--listen", "stdio://"),
            cwd=repository_root,
            env=spec.env,
            stdin_text="",
        )
    )
    process = supervisor.process
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
    pending_request_id, denied_reason, stop_reason = _drain_until_response(
        client=client,
        response_id=initialize_id,
        deadline=deadline,
        cancel_requested=cancel_requested,
        supervisor=supervisor,
        repository_root=repository_root,
        context=context,
        broker=broker,
        operator_decision_provider=operator_decision_provider,
    )
    if (
        pending_request_id is not None
        or denied_reason is not None
        or stop_reason is not None
    ):
        return _early_stop_result(
            client=client,
            process=process,
            pending_request_id=pending_request_id,
            denied_reason=denied_reason,
            transcript_path=transcript_path,
            broker=broker,
            stop_reason=stop_reason,
            supervisor=supervisor,
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
    pending_request_id, denied_reason, stop_reason = _drain_until_response(
        client=client,
        response_id=thread_start_id,
        deadline=deadline,
        cancel_requested=cancel_requested,
        supervisor=supervisor,
        repository_root=repository_root,
        context=context,
        broker=broker,
        operator_decision_provider=operator_decision_provider,
    )
    if (
        pending_request_id is not None
        or denied_reason is not None
        or stop_reason is not None
    ):
        return _early_stop_result(
            client=client,
            process=process,
            pending_request_id=pending_request_id,
            denied_reason=denied_reason,
            transcript_path=transcript_path,
            broker=broker,
            stop_reason=stop_reason,
            supervisor=supervisor,
        )

    thread_id = _thread_id_from_transcript_response(
        transcript_path=transcript_path,
        response_id=thread_start_id,
    )
    if thread_id is None:
        _stop_client(supervisor=supervisor, client=client)
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
    early_classification = None
    pending_request_id = None
    while process.poll() is None and not completed:
        if cancel_requested is not None and cancel_requested():
            _stop_client(supervisor=supervisor, client=client)
            run_result = _run_result(
                process=process,
                client=client,
                stop_reason=CodexExitClassification.CANCELLED,
            )
            return LiveTransportResult(
                run_result=run_result,
                status=AdapterExecutionStatus.FAILED,
                details="codex-live: cancelled",
                events_jsonl_path=transcript_path,
            )
        if deadline is not None and time.monotonic() >= deadline:
            _stop_client(supervisor=supervisor, client=client)
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
        if client.error is not None:
            client_error = client.error
            _stop_client(supervisor=supervisor, client=client)
            assert client_error is not None
            return LiveTransportResult(
                run_result=_captured_run_result(
                    client=client,
                    exit_code=None,
                    exit_classification=CodexExitClassification.PROTOCOL_FAILURE,
                ),
                status=AdapterExecutionStatus.FAILED,
                details=f"codex-live: protocol failure: {client_error}",
                events_jsonl_path=transcript_path,
            )
        if message is None:
            continue
        if message.get("id") == turn_start_id and "error" in message:
            denied_reason = f"codex-live: turn/start failed: {message.get('error')}"
            early_classification = CodexExitClassification.PROTOCOL_FAILURE
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
                if denied_reason is not None:
                    early_classification = CodexExitClassification.DENIED
                break
        if message.get("method") == "turn/completed":
            completed = True
        elif message.get("method") == "thread/status/changed" and _status_is_idle(message):
            completed = True

    if cancel_requested is not None and cancel_requested():
        return _early_stop_result(
            client=client,
            process=process,
            pending_request_id=None,
            denied_reason=None,
            transcript_path=transcript_path,
            broker=broker,
            stop_reason=CodexExitClassification.CANCELLED,
            supervisor=supervisor,
        )
    if pending_request_id is not None or denied_reason is not None:
        return _early_stop_result(
            client=client,
            process=process,
            pending_request_id=pending_request_id,
            denied_reason=denied_reason,
            transcript_path=transcript_path,
            broker=broker,
            stop_reason=early_classification,
            supervisor=supervisor,
        )

    _stop_client(supervisor=supervisor, client=client)
    run_result = _run_result(
        process=process,
        client=client,
        stop_reason=CodexExitClassification.SUCCESS if completed else None,
    )
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
    cancel_requested: Callable[[], bool] | None,
    supervisor: OwnedProcessSupervisor,
    repository_root: Path,
    context: CodexCommandContext,
    broker: RuntimeOperatorBroker,
    operator_decision_provider: RuntimeOperatorDecisionProvider,
) -> tuple[str | None, str | None, CodexExitClassification | None]:
    while client.process.poll() is None:
        if cancel_requested is not None and cancel_requested():
            return None, None, CodexExitClassification.CANCELLED
        if deadline is not None and time.monotonic() >= deadline:
            return None, "codex-live: timeout", CodexExitClassification.TIMEOUT
        message = client.next_message(timeout_seconds=0.1)
        if client.error is not None:
            client_error = client.error
            _stop_client(supervisor=supervisor, client=client)
            assert client_error is not None
            return (
                None,
                f"codex-live: protocol failure: {client_error}",
                CodexExitClassification.PROTOCOL_FAILURE,
            )
        if message is None:
            continue
        if message.get("id") == response_id:
            if "error" in message:
                return (
                    None,
                    f"codex-live: request failed: {message.get('error')}",
                    CodexExitClassification.PROTOCOL_FAILURE,
                )
            return None, None, None
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
                if cancel_requested is not None and cancel_requested():
                    return None, None, CodexExitClassification.CANCELLED
                return (
                    pending_request_id,
                    denied_reason,
                    (
                        CodexExitClassification.DENIED
                        if denied_reason is not None
                        else None
                    ),
                )
    return (
        None,
        "codex-live: app-server exited before response",
        CodexExitClassification.PROTOCOL_FAILURE,
    )


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
    enriched_params = _enrich_approval_params_from_cached_item(
        params=params,
        cached_item=client.cached_item(params.get("itemId") or params.get("item_id")),
    )
    operator_request = codex_approval_request_to_operator_request(
        method=method,
        payload=enriched_params,
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
            params=enriched_params,
        ),
    )
    if not decision.is_approval:
        return None, f"permission-denied: {decision.action.value}"
    return None, None


def _enrich_approval_params_from_cached_item(
    *,
    params: Mapping[str, Any],
    cached_item: Mapping[str, Any] | None,
) -> dict[str, Any]:
    enriched = dict(params)
    if cached_item is None:
        return enriched
    for key in (
        "changes",
        "command",
        "commandActions",
        "file",
        "files",
        "modifiedFiles",
        "patches",
        "path",
        "paths",
    ):
        if key not in enriched and key in cached_item:
            enriched[key] = cached_item[key]
    return enriched


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
    stop_reason: CodexExitClassification | None,
    supervisor: OwnedProcessSupervisor,
) -> LiveTransportResult[CodexExitClassification]:
    _stop_client(supervisor=supervisor, client=client)
    if stop_reason is CodexExitClassification.CANCELLED:
        return LiveTransportResult(
            run_result=_run_result(process=process, client=client, stop_reason=stop_reason),
            status=AdapterExecutionStatus.FAILED,
            details="codex-live: cancelled",
            events_jsonl_path=transcript_path,
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
                client=client,
                exit_code=None,
                exit_classification=CodexExitClassification.BLOCKED,
            ),
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
        run_result=_captured_run_result(
            client=client,
            exit_code=(
                process.returncode
                if stop_reason
                in (
                    CodexExitClassification.CANCELLED,
                    CodexExitClassification.TIMEOUT,
                )
                else None
            ),
            exit_classification=(
                stop_reason or CodexExitClassification.PROTOCOL_FAILURE
            ),
        ),
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
        run_result=_captured_run_result(
            client=client,
            exit_code=None,
            exit_classification=CodexExitClassification.PROTOCOL_FAILURE,
        ),
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
    elif exit_code == 0:
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


def _captured_run_result(
    *,
    client: _JsonRpcLineClient,
    exit_code: int | None,
    exit_classification: CodexExitClassification,
) -> CodexRunResult:
    return CodexRunResult(
        exit_code=exit_code,
        stdout_text=client.stdout_text,
        stderr_text=client.stderr_text,
        runtime_log_text=client.runtime_log_text,
        exit_classification=exit_classification,
    )


def _stop_client(
    *,
    supervisor: OwnedProcessSupervisor,
    client: _JsonRpcLineClient,
) -> None:
    supervisor.request_stop()
    supervisor.drain_streams(client.reader_threads)


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
