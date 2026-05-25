from __future__ import annotations

import shlex
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aidd.core.runtime_operator import RuntimeOperatorDecision, RuntimeOperatorRequest
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorRequestKind,
    RuntimeOperatorRisk,
)

_PATH_KEYS = (
    "path",
    "paths",
    "file",
    "files",
    "file_path",
    "filePath",
    "absolute_path",
    "absolutePath",
    "target_path",
    "targetPath",
    "grantRoot",
)
_PATH_CONTAINER_KEYS = (
    "changes",
    "commandActions",
    "edits",
    "files",
    "modifiedFiles",
    "patches",
)


def codex_approval_request_to_operator_request(
    *,
    method: str,
    payload: Mapping[str, Any],
    runtime_id: str,
    stage: str,
    cwd: Path | None,
) -> RuntimeOperatorRequest:
    request_id = str(
        payload.get("request_id")
        or payload.get("id")
        or payload.get("approvalId")
        or payload.get("itemId")
        or payload.get("item_id")
        or ""
    ).strip()
    kind = _kind_for_method(method)
    paths = tuple(Path(str(path)) for path in _payload_paths(payload))
    normalized_payload = dict(payload)
    command = _payload_command(payload)
    if command is not None:
        normalized_payload["command"] = command
    return RuntimeOperatorRequest(
        id=request_id or RuntimeOperatorRequest.create(
            runtime_id=runtime_id,
            stage=stage,
            kind=kind,
        ).id,
        runtime_id=runtime_id,
        stage=stage,
        kind=kind,
        tool_name=str(payload.get("tool_name") or method),
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


def operator_decision_to_codex_response(
    decision: RuntimeOperatorDecision,
) -> dict[str, object]:
    mapped_action = {
        RuntimeOperatorDecisionAction.ALLOW_ONCE: "accept",
        RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION: "acceptForSession",
        RuntimeOperatorDecisionAction.DENY: "decline",
        RuntimeOperatorDecisionAction.CANCEL: "cancel",
    }[decision.action]
    return {
        "request_id": decision.request_id,
        "decision": mapped_action,
        "reason": decision.reason,
    }


def _kind_for_method(method: str) -> RuntimeOperatorRequestKind:
    normalized = method.lower()
    if (
        "commandexecution" in normalized
        or "command_execution" in normalized
        or "execcommand" in normalized
    ):
        return RuntimeOperatorRequestKind.SHELL
    if (
        "filechange" in normalized
        or "file_change" in normalized
        or "applypatch" in normalized
    ):
        return RuntimeOperatorRequestKind.FILE_EDIT
    if "permissions" in normalized or "permission" in normalized:
        return RuntimeOperatorRequestKind.RUNTIME_PERMISSION
    return RuntimeOperatorRequestKind.UNKNOWN


def _payload_command(payload: Mapping[str, Any]) -> str | None:
    raw_command = (
        payload.get("command")
        or payload.get("cmd")
        or payload.get("commandLine")
        or payload.get("command_line")
    )
    if raw_command is None:
        return None
    if isinstance(raw_command, list | tuple):
        return shlex.join(str(token) for token in raw_command)
    return str(raw_command)


def _payload_paths(payload: Mapping[str, Any]) -> tuple[object, ...]:
    paths: list[object] = []
    for key in _PATH_KEYS:
        _collect_path_value(payload.get(key), paths)
    for key in _PATH_CONTAINER_KEYS:
        raw_container = payload.get(key)
        if isinstance(raw_container, Mapping):
            _collect_mapping_paths(raw_container, paths)
        elif isinstance(raw_container, list | tuple):
            for item in raw_container:
                _collect_path_value(item, paths)
    return _dedupe_paths(paths)


def _collect_path_value(value: object, paths: list[object]) -> None:
    if value is None:
        return
    if isinstance(value, str):
        paths.append(value)
        return
    if isinstance(value, Mapping):
        _collect_mapping_paths(value, paths)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _collect_path_value(item, paths)


def _collect_mapping_paths(value: Mapping[str, Any], paths: list[object]) -> None:
    for key in _PATH_KEYS:
        raw_path = value.get(key)
        if isinstance(raw_path, Mapping):
            _collect_mapping_paths(raw_path, paths)
        elif isinstance(raw_path, list | tuple):
            for item in raw_path:
                _collect_path_value(item, paths)
        elif raw_path is not None:
            paths.append(raw_path)


def _dedupe_paths(paths: list[object]) -> tuple[object, ...]:
    deduped: list[object] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return tuple(deduped)
