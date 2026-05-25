from __future__ import annotations

import shlex
from enum import StrEnum
from pathlib import Path


class RuntimePermissionPolicy(StrEnum):
    FULL_ACCESS = "full-access"
    BROKERED = "brokered"
    PLAN = "plan"
    DENY_UNAPPROVED = "deny-unapproved"


class RuntimeInteractionMode(StrEnum):
    BATCH = "batch"
    EVENTED = "evented"
    LIVE = "live"


class AutoApprovalPreset(StrEnum):
    OFF = "off"
    CONSERVATIVE = "conservative"
    BROAD = "broad"


class RuntimeOperatorRequestKind(StrEnum):
    FILE_READ = "file_read"
    FILE_LIST = "file_list"
    FILE_GLOB = "file_glob"
    FILE_GREP = "file_grep"
    FILE_CREATE = "file_create"
    FILE_EDIT = "file_edit"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SHELL = "shell"
    NETWORK = "network"
    MCP_TOOL = "mcp_tool"
    SUBAGENT = "subagent"
    RUNTIME_PERMISSION = "runtime_permission"
    UNKNOWN = "unknown"


class RuntimeOperatorRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RuntimeOperatorDecisionAction(StrEnum):
    ALLOW_ONCE = "allow_once"
    ALLOW_FOR_SESSION = "allow_for_session"
    DENY = "deny"
    CANCEL = "cancel"


class RuntimeOperatorDecisionSource(StrEnum):
    POLICY = "policy"
    UI = "ui"
    CLI = "cli"


_BYPASS_FLAGS = frozenset(
    {
        "--dangerously-skip-permissions",
        "--dangerously-bypass-approvals-and-sandbox",
        "--full-auto",
        "--yolo",
    }
)


def normalize_permission_policy(
    value: str | RuntimePermissionPolicy | None,
) -> RuntimePermissionPolicy:
    if value is None:
        return RuntimePermissionPolicy.FULL_ACCESS
    if isinstance(value, RuntimePermissionPolicy):
        return value
    raw_value = value.strip()
    if not raw_value:
        return RuntimePermissionPolicy.FULL_ACCESS
    try:
        return RuntimePermissionPolicy(raw_value)
    except ValueError as exc:
        supported = ", ".join(policy.value for policy in RuntimePermissionPolicy)
        raise ValueError(
            f"Unsupported runtime permission_policy {raw_value!r}. Supported: {supported}."
        ) from exc


def normalize_interaction_mode(
    value: str | RuntimeInteractionMode | None,
) -> RuntimeInteractionMode:
    if value is None:
        return RuntimeInteractionMode.BATCH
    if isinstance(value, RuntimeInteractionMode):
        return value
    raw_value = value.strip()
    if not raw_value:
        return RuntimeInteractionMode.BATCH
    try:
        return RuntimeInteractionMode(raw_value)
    except ValueError as exc:
        supported = ", ".join(mode.value for mode in RuntimeInteractionMode)
        raise ValueError(
            f"Unsupported runtime interaction_mode {raw_value!r}. Supported: {supported}."
        ) from exc


def normalize_auto_approval_preset(
    value: str | AutoApprovalPreset | None,
) -> AutoApprovalPreset:
    if value is None:
        return AutoApprovalPreset.BROAD
    if isinstance(value, AutoApprovalPreset):
        return value
    raw_value = value.strip()
    if not raw_value:
        return AutoApprovalPreset.BROAD
    try:
        return AutoApprovalPreset(raw_value)
    except ValueError as exc:
        supported = ", ".join(preset.value for preset in AutoApprovalPreset)
        raise ValueError(
            f"Unsupported runtime auto_approval_preset {raw_value!r}. "
            f"Supported: {supported}."
        ) from exc


def command_contains_permission_bypass(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    executable = Path(tokens[0]).name if tokens else ""
    for index, token in enumerate(tokens):
        if token in _BYPASS_FLAGS or any(
            token.startswith(f"{flag}=") for flag in _BYPASS_FLAGS
        ):
            return True
        if executable == "qwen" and token == "-y":
            return True
        if token.startswith("--approval-mode=") and token.split("=", 1)[1] == "yolo":
            return True
        if token.startswith("--approval-policy=") and token.split("=", 1)[1] == "never":
            return True
        if (
            token.startswith("--permission-mode=")
            and token.split("=", 1)[1] == "bypassPermissions"
        ):
            return True
        if token.startswith("--sandbox=") and token.split("=", 1)[1] in {
            "danger-full-access",
            "full-access",
        }:
            return True
        if token == "--approval-mode" and index + 1 < len(tokens) and tokens[index + 1] == "yolo":
            return True
        if (
            token == "--approval-policy"
            and index + 1 < len(tokens)
            and tokens[index + 1] == "never"
        ):
            return True
        if (
            token == "--permission-mode"
            and index + 1 < len(tokens)
            and tokens[index + 1] == "bypassPermissions"
        ):
            return True
        if token == "--sandbox" and index + 1 < len(tokens) and tokens[index + 1] in {
            "danger-full-access",
            "full-access",
        }:
            return True
    return False


__all__ = [
    "AutoApprovalPreset",
    "RuntimeInteractionMode",
    "RuntimeOperatorDecisionAction",
    "RuntimeOperatorDecisionSource",
    "RuntimeOperatorRequestKind",
    "RuntimeOperatorRisk",
    "RuntimePermissionPolicy",
    "command_contains_permission_bypass",
    "normalize_auto_approval_preset",
    "normalize_interaction_mode",
    "normalize_permission_policy",
]
