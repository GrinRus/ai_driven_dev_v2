from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aidd.core.runtime_operator import RuntimeOperatorDecision, RuntimeOperatorRequest
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorRequestKind,
    RuntimeOperatorRisk,
)


def qwen_control_request_to_operator_request(
    event: Mapping[str, Any],
    *,
    runtime_id: str,
    stage: str,
    cwd: Path | None,
) -> RuntimeOperatorRequest:
    payload = _event_payload(event)
    request_id = str(
        payload.get("request_id")
        or payload.get("id")
        or event.get("request_id")
        or event.get("id")
        or ""
    ).strip()
    kind = _operator_kind(payload)
    paths = tuple(Path(str(path)) for path in _payload_paths(payload))
    command = payload.get("command") or payload.get("cmd")
    normalized_payload = dict(payload)
    if command is not None:
        normalized_payload["command"] = str(command)
    return RuntimeOperatorRequest(
        id=request_id or RuntimeOperatorRequest.create(
            runtime_id=runtime_id,
            stage=stage,
            kind=kind,
        ).id,
        runtime_id=runtime_id,
        stage=stage,
        kind=kind,
        tool_name=_payload_tool_name(payload),
        payload=normalized_payload,
        cwd=cwd,
        paths=paths,
        risk=RuntimeOperatorRisk.HIGH if kind is RuntimeOperatorRequestKind.SHELL else (
            RuntimeOperatorRisk.MEDIUM
        ),
        suggestions=(
            RuntimeOperatorDecisionAction.ALLOW_ONCE,
            RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION,
            RuntimeOperatorDecisionAction.DENY,
            RuntimeOperatorDecisionAction.CANCEL,
        ),
    )


def operator_decision_to_qwen_confirmation(
    decision: RuntimeOperatorDecision,
) -> dict[str, object]:
    return {
        "type": "confirmation_response",
        "request_id": decision.request_id,
        "allowed": decision.is_approval,
        "scope": (
            "session"
            if decision.action is RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION
            else "once"
        ),
        "cancel": decision.action is RuntimeOperatorDecisionAction.CANCEL,
        "reason": decision.reason,
    }


def _event_payload(event: Mapping[str, Any]) -> dict[str, Any]:
    raw_payload = event.get("payload")
    if isinstance(raw_payload, Mapping):
        payload = dict(raw_payload)
    else:
        payload = dict(event)
    raw_request = payload.get("request")
    if isinstance(raw_request, Mapping):
        payload.update(raw_request)
    _flatten_nested_tool_payload(payload)
    return payload


def _operator_kind(payload: Mapping[str, Any]) -> RuntimeOperatorRequestKind:
    raw_kind = str(payload.get("kind") or payload.get("type") or "").lower()
    tool_name = _payload_tool_name(payload).lower()
    if (
        "shell" in raw_kind
        or "command" in raw_kind
        or tool_name in {"bash", "shell", "run_command", "execute_command"}
        or "shell" in tool_name
    ):
        return RuntimeOperatorRequestKind.SHELL
    if "delete" in raw_kind:
        return RuntimeOperatorRequestKind.FILE_DELETE
    if "write" in raw_kind or tool_name in {"write_file", "write"}:
        return RuntimeOperatorRequestKind.FILE_WRITE
    if "edit" in raw_kind or tool_name in {"edit_file", "edit"}:
        return RuntimeOperatorRequestKind.FILE_EDIT
    if "read" in raw_kind or tool_name in {"read_file", "read"}:
        return RuntimeOperatorRequestKind.FILE_READ
    if "network" in raw_kind:
        return RuntimeOperatorRequestKind.NETWORK
    return RuntimeOperatorRequestKind.UNKNOWN


def _payload_tool_name(payload: Mapping[str, Any]) -> str:
    raw_tool_name = payload.get("tool_name") or payload.get("name")
    raw_tool = payload.get("tool")
    if raw_tool_name is None and isinstance(raw_tool, Mapping):
        raw_tool_name = raw_tool.get("name") or raw_tool.get("type")
    elif raw_tool_name is None:
        raw_tool_name = raw_tool
    return "" if raw_tool_name is None else str(raw_tool_name)


def _payload_paths(payload: Mapping[str, Any]) -> tuple[object, ...]:
    raw_paths = payload.get("paths")
    if isinstance(raw_paths, list | tuple):
        return tuple(raw_paths)
    raw_files = payload.get("files")
    if isinstance(raw_files, list | tuple):
        return tuple(raw_files)
    raw_path = payload.get("path") or payload.get("file_path") or payload.get("file")
    return () if raw_path is None else (raw_path,)


def _flatten_nested_tool_payload(payload: dict[str, Any]) -> None:
    for key in ("tool_call", "tool", "call"):
        raw_tool = payload.get(key)
        if not isinstance(raw_tool, Mapping):
            continue
        payload.setdefault("tool_name", raw_tool.get("name") or raw_tool.get("type"))
        raw_input = (
            raw_tool.get("input")
            or raw_tool.get("args")
            or raw_tool.get("arguments")
            or raw_tool.get("parameters")
        )
        if isinstance(raw_input, Mapping):
            for input_key, input_value in raw_input.items():
                payload.setdefault(str(input_key), input_value)
