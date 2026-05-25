from __future__ import annotations

import json
import os
import re
import shlex
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
    RuntimeOperatorRisk,
    RuntimePermissionPolicy,
)

OPERATOR_REQUESTS_FILENAME = "operator-requests.jsonl"
OPERATOR_DECISIONS_FILENAME = "operator-decisions.jsonl"

_WRITE_STAGES = frozenset({"implement", "review", "qa"})
_AIDD_WORKSPACE_DIRNAME = ".aidd"
_READ_KINDS = frozenset(
    {
        RuntimeOperatorRequestKind.FILE_READ,
        RuntimeOperatorRequestKind.FILE_LIST,
        RuntimeOperatorRequestKind.FILE_GLOB,
        RuntimeOperatorRequestKind.FILE_GREP,
    }
)
_WRITE_KINDS = frozenset(
    {
        RuntimeOperatorRequestKind.FILE_CREATE,
        RuntimeOperatorRequestKind.FILE_EDIT,
        RuntimeOperatorRequestKind.FILE_WRITE,
    }
)
_PROTECTED_NAMES = frozenset(
    {
        ".git",
        ".ssh",
        ".aws",
        ".config",
        ".claude",
        ".codex",
        ".opencode",
        ".qwen",
    }
)
_PROTECTED_AIDD_DIR_NAMES = frozenset(
    {
        "auth",
        "auths",
        "credential",
        "credentials",
        "secret",
        "secrets",
        "token",
        "tokens",
        "provider-auth",
        "provider_auth",
        "runtime-auth",
        "runtime_auth",
    }
)
_PROTECTED_FILE_NAMES = frozenset(
    {
        OPERATOR_DECISIONS_FILENAME,
        OPERATOR_REQUESTS_FILENAME,
        "auth.json",
        "claude.json",
        "codex.json",
        "credentials.json",
        "opencode.json",
        "qwen.json",
        "repair-brief.md",
        "settings.json",
        "token.json",
        "tokens.json",
        "credentials",
        "known_hosts",
        "id_rsa",
        "id_ed25519",
    }
)
_SHELL_CONTROL_RE = re.compile(r"(\|\||&&|;|>>?|<|\$\(|`)")
_SAFE_INSPECT_COMMANDS = frozenset({"pwd", "ls", "find", "rg", "grep"})
_SAFE_GIT_SUBCOMMANDS = frozenset({"status", "diff", "log"})
_ASK_GIT_SUBCOMMANDS = frozenset({"commit", "tag", "push"})
_PACKAGE_MANAGERS = frozenset(
    {
        "npm",
        "pnpm",
        "yarn",
        "uv",
        "pip",
        "pip3",
        "pipx",
        "brew",
        "apt",
        "apt-get",
        "cargo",
        "go",
        "gem",
        "bundle",
    }
)
_NETWORK_COMMANDS = frozenset({"curl", "wget"})
_PUBLISH_COMMANDS = frozenset({"release", "publish", "twine"})
_NETWORK_GIT_SUBCOMMANDS = frozenset({"clone", "fetch", "pull", "push"})
_AIDD_WORKSPACE_PATH_RE = re.compile(
    r"(?<![\w./-])(?:\./)?\.aidd(?:/[^\s'\"`$<>|;&)]+)?"
)
_ABSOLUTE_PATH_RE = re.compile(r"(?<![\w./:-])/[^\s'\"`$<>|;&)]+")
_SHELL_DELETE_OR_PERMISSION_COMMANDS = frozenset(
    {
        "rm",
        "rmdir",
        "unlink",
        "chmod",
        "chown",
    }
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _enum_value(value: object) -> object:
    return value.value if hasattr(value, "value") else value


def _path_to_json(path: Path | None) -> str | None:
    return None if path is None else path.as_posix()


def _paths_to_json(paths: Iterable[Path]) -> list[str]:
    return [path.as_posix() for path in paths]


@dataclass(frozen=True, slots=True)
class RuntimeOperatorRequest:
    id: str
    runtime_id: str
    stage: str
    kind: RuntimeOperatorRequestKind
    tool_name: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    cwd: Path | None = None
    paths: tuple[Path, ...] = ()
    risk: RuntimeOperatorRisk = RuntimeOperatorRisk.MEDIUM
    suggestions: tuple[RuntimeOperatorDecisionAction, ...] = (
        RuntimeOperatorDecisionAction.ALLOW_ONCE,
        RuntimeOperatorDecisionAction.DENY,
    )
    created_at_utc: str = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        *,
        runtime_id: str,
        stage: str,
        kind: RuntimeOperatorRequestKind,
        tool_name: str | None = None,
        payload: Mapping[str, Any] | None = None,
        cwd: Path | None = None,
        paths: Iterable[Path] = (),
        risk: RuntimeOperatorRisk = RuntimeOperatorRisk.MEDIUM,
        suggestions: Iterable[RuntimeOperatorDecisionAction] = (
            RuntimeOperatorDecisionAction.ALLOW_ONCE,
            RuntimeOperatorDecisionAction.DENY,
        ),
    ) -> RuntimeOperatorRequest:
        return cls(
            id=f"opr-{uuid4().hex}",
            runtime_id=runtime_id,
            stage=stage,
            kind=kind,
            tool_name=tool_name,
            payload=dict(payload or {}),
            cwd=cwd,
            paths=tuple(paths),
            risk=risk,
            suggestions=tuple(suggestions),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "runtime_id": self.runtime_id,
            "stage": self.stage,
            "kind": self.kind.value,
            "tool_name": self.tool_name,
            "payload": dict(self.payload),
            "cwd": _path_to_json(self.cwd),
            "paths": _paths_to_json(self.paths),
            "risk": self.risk.value,
            "suggestions": [_enum_value(suggestion) for suggestion in self.suggestions],
            "created_at_utc": self.created_at_utc,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> RuntimeOperatorRequest:
        return cls(
            id=str(payload["id"]),
            runtime_id=str(payload["runtime_id"]),
            stage=str(payload["stage"]),
            kind=RuntimeOperatorRequestKind(str(payload.get("kind", "unknown"))),
            tool_name=(
                None
                if payload.get("tool_name") is None
                else str(payload.get("tool_name"))
            ),
            payload=dict(payload.get("payload", {})),
            cwd=None if payload.get("cwd") is None else Path(str(payload["cwd"])),
            paths=tuple(Path(str(path)) for path in payload.get("paths", ())),
            risk=RuntimeOperatorRisk(str(payload.get("risk", RuntimeOperatorRisk.MEDIUM))),
            suggestions=tuple(
                RuntimeOperatorDecisionAction(str(suggestion))
                for suggestion in payload.get("suggestions", ())
            ),
            created_at_utc=str(payload.get("created_at_utc", _utc_now())),
        )


@dataclass(frozen=True, slots=True)
class RuntimeOperatorDecision:
    request_id: str
    action: RuntimeOperatorDecisionAction
    source: RuntimeOperatorDecisionSource
    reason: str | None = None
    created_at_utc: str = field(default_factory=_utc_now)

    @property
    def is_approval(self) -> bool:
        return self.action in {
            RuntimeOperatorDecisionAction.ALLOW_ONCE,
            RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action": self.action.value,
            "source": self.source.value,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> RuntimeOperatorDecision:
        return cls(
            request_id=str(payload["request_id"]),
            action=RuntimeOperatorDecisionAction(str(payload["action"])),
            source=RuntimeOperatorDecisionSource(str(payload["source"])),
            reason=None if payload.get("reason") is None else str(payload["reason"]),
            created_at_utc=str(payload.get("created_at_utc", _utc_now())),
        )


class RuntimeOperatorDecisionProvider(Protocol):
    def request_decision(
        self,
        request: RuntimeOperatorRequest,
        *,
        requests_path: Path,
        decisions_path: Path,
    ) -> RuntimeOperatorDecision | None:
        """Return a human/operator decision for a persisted runtime request."""


@dataclass(frozen=True, slots=True)
class RuntimeOperatorPolicy:
    permission_policy: RuntimePermissionPolicy
    auto_approval_preset: AutoApprovalPreset
    project_roots: tuple[Path, ...]
    workspace_root: Path
    configured_command_prefixes: tuple[str, ...] = ()

    def evaluate(
        self,
        request: RuntimeOperatorRequest,
    ) -> RuntimeOperatorDecision | None:
        if self.permission_policy is RuntimePermissionPolicy.FULL_ACCESS:
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="full-access policy allows runtime request",
            )

        denied_reason = self._deny_reason(request)
        if denied_reason is not None:
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.DENY,
                reason=denied_reason,
            )

        auto_decision = self._auto_decision(request)
        if auto_decision is not None:
            return auto_decision

        if self.permission_policy is RuntimePermissionPolicy.DENY_UNAPPROVED:
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.DENY,
                reason="deny-unapproved policy rejected request without an auto-approval rule",
            )
        return None

    def _deny_reason(self, request: RuntimeOperatorRequest) -> str | None:
        if request.kind in _WRITE_KINDS | {RuntimeOperatorRequestKind.FILE_DELETE}:
            protected_path = self._first_protected_path(request)
            if protected_path is not None:
                return f"protected path is not writable: {protected_path.as_posix()}"
        if request.kind is RuntimeOperatorRequestKind.SHELL:
            return _shell_deny_reason(
                command=_request_command(request),
                cwd=request.cwd,
                project_roots=self._resolved_project_roots(),
            )
        if request.paths and not self._paths_within_project_roots(request):
            if any(".." in path.parts for path in request.paths):
                return "path traversal outside declared project roots is denied"
            return None
        return None

    def _auto_decision(
        self,
        request: RuntimeOperatorRequest,
    ) -> RuntimeOperatorDecision | None:
        if self.auto_approval_preset is AutoApprovalPreset.OFF:
            return None

        if request.kind in _READ_KINDS and self._paths_within_read_roots(request):
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="auto-approved safe project/AIDD read/list/search request",
            )
        if request.kind is RuntimeOperatorRequestKind.SHELL:
            return self._shell_auto_decision(request)
        if self.permission_policy is RuntimePermissionPolicy.PLAN:
            return None
        if self.auto_approval_preset is not AutoApprovalPreset.BROAD:
            return None
        if request.kind not in _WRITE_KINDS or not request.paths:
            return None
        if self._paths_within_workspace_root(request):
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="auto-approved broad preset AIDD workspace write request",
            )
        if request.stage in _WRITE_STAGES and self._paths_within_project_roots(request):
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="auto-approved broad preset project write request",
            )
        return None

    def _shell_auto_decision(
        self,
        request: RuntimeOperatorRequest,
    ) -> RuntimeOperatorDecision | None:
        command = _request_command(request)
        if not command.strip():
            return None
        if not self._cwd_within_project_roots(request):
            return None
        if _requires_operator_for_shell(command):
            return None
        if (
            self.permission_policy is not RuntimePermissionPolicy.PLAN
            and self.auto_approval_preset is AutoApprovalPreset.BROAD
            and _is_bounded_aidd_workspace_shell(
                command=command,
                cwd=request.cwd,
                workspace_root=self.workspace_root.resolve(strict=False),
                allowed_roots=(
                    *self._resolved_project_roots(),
                    self.workspace_root.resolve(strict=False),
                ),
            )
        ):
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="auto-approved broad preset bounded AIDD workspace shell request",
            )
        if (
            self.permission_policy is not RuntimePermissionPolicy.PLAN
            and self.auto_approval_preset is AutoApprovalPreset.BROAD
            and _is_broad_project_local_shell(
                command=command,
                cwd=request.cwd,
                project_roots=self._resolved_project_roots(),
                workspace_root=self.workspace_root.resolve(strict=False),
            )
        ):
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="auto-approved broad preset project-local shell request",
            )
        if _shell_references_external_path(
            command=command,
            cwd=request.cwd,
            project_roots=self._resolved_project_roots(),
        ):
            return None
        if _is_configured_command(command, self.configured_command_prefixes):
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="auto-approved configured project command",
            )
        if _is_safe_inspect_shell(command):
            return _decision(
                request=request,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                reason="auto-approved safe inspect shell command",
            )
        return None

    def _first_protected_path(self, request: RuntimeOperatorRequest) -> Path | None:
        for path in self._resolved_request_paths(request):
            if _is_protected_path(path):
                return path
        return None

    def _paths_within_project_roots(self, request: RuntimeOperatorRequest) -> bool:
        resolved_paths = self._resolved_request_paths(request)
        if not resolved_paths:
            return self._cwd_within_project_roots(request)
        if request.cwd is None and any(not path.is_absolute() for path in request.paths):
            return False
        project_roots = self._resolved_project_roots()
        return all(_is_relative_to_any(path, project_roots) for path in resolved_paths)

    def _paths_within_workspace_root(self, request: RuntimeOperatorRequest) -> bool:
        resolved_paths = self._resolved_request_paths(request)
        if not resolved_paths:
            return self._cwd_within_workspace_root(request)
        if request.cwd is None and any(not path.is_absolute() for path in request.paths):
            return False
        workspace_root = self.workspace_root.resolve(strict=False)
        return all(_is_relative_to(path, workspace_root) for path in resolved_paths)

    def _paths_within_read_roots(self, request: RuntimeOperatorRequest) -> bool:
        resolved_paths = self._resolved_request_paths(request)
        if not resolved_paths:
            return self._cwd_within_project_roots(request) or self._cwd_within_workspace_root(
                request
            )
        if request.cwd is None and any(not path.is_absolute() for path in request.paths):
            return False
        roots = (*self._resolved_project_roots(), self.workspace_root.resolve(strict=False))
        return all(_is_relative_to_any(path, roots) for path in resolved_paths)

    def _cwd_within_project_roots(self, request: RuntimeOperatorRequest) -> bool:
        if request.cwd is None:
            return False
        return _is_relative_to_any(
            request.cwd.resolve(strict=False),
            self._resolved_project_roots(),
        )

    def _cwd_within_workspace_root(self, request: RuntimeOperatorRequest) -> bool:
        if request.cwd is None:
            return False
        return _is_relative_to(
            request.cwd.resolve(strict=False),
            self.workspace_root.resolve(strict=False),
        )

    def _resolved_project_roots(self) -> tuple[Path, ...]:
        if self.project_roots:
            return tuple(path.resolve(strict=False) for path in self.project_roots)
        return (self.workspace_root.resolve(strict=False),)

    def _resolved_request_paths(self, request: RuntimeOperatorRequest) -> tuple[Path, ...]:
        base = (
            request.cwd.resolve(strict=False)
            if request.cwd is not None
            else self.workspace_root.resolve(strict=False)
        )
        resolved_paths: list[Path] = []
        for path in request.paths:
            resolved_paths.append(
                path.resolve(strict=False)
                if path.is_absolute()
                else (base / path).resolve(strict=False)
            )
        return tuple(resolved_paths)


@dataclass(frozen=True, slots=True)
class RuntimeOperatorBroker:
    policy: RuntimeOperatorPolicy
    attempt_path: Path

    @property
    def requests_path(self) -> Path:
        return self.attempt_path / OPERATOR_REQUESTS_FILENAME

    @property
    def decisions_path(self) -> Path:
        return self.attempt_path / OPERATOR_DECISIONS_FILENAME

    def handle_request(
        self,
        request: RuntimeOperatorRequest,
        *,
        decision_provider: RuntimeOperatorDecisionProvider | None = None,
    ) -> RuntimeOperatorDecision | None:
        append_operator_request(path=self.requests_path, request=request)
        decision = self.policy.evaluate(request)
        if decision is None and decision_provider is not None:
            decision = decision_provider.request_decision(
                request,
                requests_path=self.requests_path,
                decisions_path=self.decisions_path,
            )
        if decision is not None:
            if not _operator_decision_recorded(
                path=self.decisions_path,
                request_id=decision.request_id,
            ):
                append_operator_decision(path=self.decisions_path, decision=decision)
        return decision


def _decision(
    *,
    request: RuntimeOperatorRequest,
    action: RuntimeOperatorDecisionAction,
    reason: str,
) -> RuntimeOperatorDecision:
    return RuntimeOperatorDecision(
        request_id=request.id,
        action=action,
        source=RuntimeOperatorDecisionSource.POLICY,
        reason=reason,
    )


def _request_command(request: RuntimeOperatorRequest) -> str:
    raw_command = request.payload.get("command", request.payload.get("cmd", ""))
    return str(raw_command)


def _shell_tokens(command: str) -> tuple[str, ...]:
    try:
        return tuple(shlex.split(command))
    except ValueError:
        return tuple(command.split())


def _is_safe_inspect_shell(command: str) -> bool:
    if _SHELL_CONTROL_RE.search(command):
        return False
    tokens = _shell_tokens(command)
    if not tokens:
        return False
    executable = Path(tokens[0]).name
    if executable in _SAFE_INSPECT_COMMANDS:
        return True
    return executable == "git" and len(tokens) >= 2 and tokens[1] in _SAFE_GIT_SUBCOMMANDS


def _requires_operator_for_shell(command: str) -> bool:
    tokens = _shell_tokens(command)
    if not tokens:
        return False
    guard_text = _shell_guard_text(command)
    executable = Path(tokens[0]).name
    if _contains_url(tokens):
        return True
    if _contains_operator_required_shell_action(guard_text):
        return True
    if executable in _NETWORK_COMMANDS:
        return True
    if executable in _PUBLISH_COMMANDS:
        return True
    if executable == "git" and len(tokens) >= 2 and tokens[1] in (
        _ASK_GIT_SUBCOMMANDS | _NETWORK_GIT_SUBCOMMANDS
    ):
        return True
    if executable in _PACKAGE_MANAGERS:
        return _package_command_requires_operator(executable=executable, tokens=tokens)
    return any(token in {"release", "publish"} for token in tokens[1:])


def _contains_operator_required_shell_action(command: str) -> bool:
    return any(
        re.search(pattern, command)
        for pattern in (
            r"(?<![\w])https?://",
            r"(?<![\w./-])(curl|wget)(?![\w.-])",
            r"(?<![\w./-])(npm|pnpm|yarn)\s+(install|add|update|upgrade)\b",
            r"(?<![\w./-])(pip|pip3|pipx)\s+(install|upgrade)\b",
            r"(?<![\w./-])uv\s+(add|remove|pip)\b",
            r"(?<![\w./-])cargo\s+(add|install|update)\b",
            r"(?<![\w./-])go\s+(get|install)\b",
            r"(?<![\w./-])bundle\s+(add|install|update)\b",
            r"(?<![\w./-])git\s+(clone|fetch|pull|push|commit|tag)\b",
            r"(?<![\w./-])(release|publish|twine)(?![\w.-])",
        )
    )


def _package_command_requires_operator(*, executable: str, tokens: tuple[str, ...]) -> bool:
    if executable in {"npm", "pnpm", "yarn"}:
        return any(token in {"install", "add", "update", "upgrade"} for token in tokens[1:])
    if executable in {"pip", "pip3", "pipx"}:
        return any(token in {"install", "upgrade"} for token in tokens[1:])
    if executable == "uv":
        return len(tokens) >= 2 and tokens[1] in {"add", "remove", "pip"}
    if executable == "cargo":
        return len(tokens) >= 2 and tokens[1] in {"add", "install", "update"}
    if executable == "go":
        return len(tokens) >= 2 and tokens[1] in {"get", "install"}
    if executable == "bundle":
        return len(tokens) >= 2 and tokens[1] in {"add", "install", "update"}
    return True


def _is_configured_command(command: str, prefixes: tuple[str, ...]) -> bool:
    normalized = command.strip()
    return any(normalized == prefix or normalized.startswith(f"{prefix} ") for prefix in prefixes)


def _contains_url(tokens: tuple[str, ...]) -> bool:
    return any(token.startswith(("http://", "https://")) for token in tokens)


def _shell_deny_reason(
    *,
    command: str,
    cwd: Path | None,
    project_roots: tuple[Path, ...],
) -> str | None:
    path_traversal_reason = _shell_path_traversal_reason(
        command=command,
        cwd=cwd,
        project_roots=project_roots,
    )
    if path_traversal_reason is not None:
        return path_traversal_reason
    return _destructive_shell_reason(
        command=command,
        cwd=cwd,
        project_roots=project_roots,
    )


def _destructive_shell_reason(
    *,
    command: str,
    cwd: Path | None,
    project_roots: tuple[Path, ...],
) -> str | None:
    tokens = _shell_tokens(command)
    if not tokens:
        return None
    executable = Path(tokens[0]).name
    if executable == "sudo":
        return "sudo is not auto-approved"
    if re.search(r"\b(curl|wget)\b.*\|\s*(sh|bash)\b", command):
        return "pipe-to-shell installers are denied"
    if _contains_destructive_root_or_home_remove(tokens):
        return "destructive root/home removal is denied"
    if executable in {"chmod", "chown"}:
        base = (cwd or Path.cwd()).resolve(strict=False)
        for token in tokens[1:]:
            if token.startswith("-") or re.fullmatch(r"[0-7]{3,4}", token):
                continue
            path = Path(token)
            resolved = (
                path.resolve(strict=False)
                if path.is_absolute()
                else (base / path).resolve(strict=False)
            )
            if not _is_relative_to_any(resolved, project_roots):
                return f"{executable} outside project roots is denied"
    return None


def _shell_path_traversal_reason(
    *,
    command: str,
    cwd: Path | None,
    project_roots: tuple[Path, ...],
) -> str | None:
    if cwd is None:
        return None
    for token, resolved_path in _shell_path_operands(command=command, cwd=cwd):
        if ".." in Path(token).parts and not _is_relative_to_any(
            resolved_path,
            project_roots,
        ):
            return "path traversal outside declared project roots is denied"
    return None


def _shell_references_external_path(
    *,
    command: str,
    cwd: Path | None,
    project_roots: tuple[Path, ...],
) -> bool:
    if cwd is None:
        return True
    return any(
        not _is_relative_to_any(resolved_path, project_roots)
        for _, resolved_path in _shell_path_operands(command=command, cwd=cwd)
    )


def _is_bounded_aidd_workspace_shell(
    *,
    command: str,
    cwd: Path | None,
    workspace_root: Path,
    allowed_roots: tuple[Path, ...],
) -> bool:
    if cwd is None:
        return False
    if not _command_mentions_aidd_workspace(command, workspace_root=workspace_root):
        return False
    if _shell_contains_delete_or_permission_command(command):
        return False
    explicit_paths = _explicit_shell_paths(command=command, cwd=cwd)
    if not explicit_paths:
        return False
    return all(
        _is_aidd_workspace_shell_path(
            path=path,
            workspace_root=workspace_root,
            allowed_roots=allowed_roots,
        )
        for path in explicit_paths
    )


def _is_broad_project_local_shell(
    *,
    command: str,
    cwd: Path | None,
    project_roots: tuple[Path, ...],
    workspace_root: Path,
) -> bool:
    if cwd is None or not _is_relative_to_any(cwd.resolve(strict=False), project_roots):
        return False
    if _shell_contains_delete_or_permission_command(command):
        return False
    explicit_paths = _explicit_shell_paths(command=command, cwd=cwd)
    allowed_roots = (*project_roots, workspace_root)
    return all(
        _is_relative_to_any(path, allowed_roots) and not _is_protected_path(path)
        for path in explicit_paths
    )


def _is_aidd_workspace_shell_path(
    *,
    path: Path,
    workspace_root: Path,
    allowed_roots: tuple[Path, ...],
) -> bool:
    if _is_relative_to(path, workspace_root):
        return True
    return (
        _AIDD_WORKSPACE_DIRNAME in path.parts
        and _is_relative_to_any(path, allowed_roots)
    )


def _command_mentions_aidd_workspace(command: str, *, workspace_root: Path) -> bool:
    return bool(_AIDD_WORKSPACE_PATH_RE.search(command)) or (
        workspace_root.as_posix() in command
    )


def _shell_contains_delete_or_permission_command(command: str) -> bool:
    guard_text = _shell_guard_text(command)
    tokens = _shell_tokens(guard_text)
    if any(Path(token).name in _SHELL_DELETE_OR_PERMISSION_COMMANDS for token in tokens):
        return True
    return any(
        re.search(rf"(?<![\w.-]){re.escape(executable)}(?![\w.-])", guard_text)
        for executable in _SHELL_DELETE_OR_PERMISSION_COMMANDS
    )


def _explicit_shell_paths(*, command: str, cwd: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    tokens = _shell_tokens(command)
    executable = "" if not tokens else Path(tokens[0]).name
    is_shell_wrapper = executable in {"sh", "bash", "zsh"} and any(
        option.endswith("c") for option in tokens[1:] if option.startswith("-")
    )
    if is_shell_wrapper:
        inner_command = _shell_wrapper_command_argument(tokens)
        if inner_command is not None:
            stripped_inner = _strip_heredoc_bodies(inner_command)
            paths.extend(
                resolved_path
                for _, resolved_path in _shell_path_operands(
                    command=stripped_inner,
                    cwd=cwd,
                )
            )
            paths.extend(_aidd_workspace_path_literals(command=stripped_inner, cwd=cwd))
            paths.extend(
                _absolute_path_literals(tokens=_shell_tokens(stripped_inner), cwd=cwd)
            )
    else:
        paths.extend(
            resolved_path
            for _, resolved_path in _shell_path_operands(command=command, cwd=cwd)
        )
        paths.extend(_aidd_workspace_path_literals(command=command, cwd=cwd))
        paths.extend(_absolute_path_literals(tokens=tokens[1:], cwd=cwd))
    return _dedupe_paths(paths)


def _shell_guard_text(command: str) -> str:
    tokens = _shell_tokens(command)
    inner_command = _shell_wrapper_command_argument(tokens)
    if inner_command is None:
        return _strip_heredoc_bodies(command)
    return _strip_heredoc_bodies(inner_command)


def _shell_wrapper_command_argument(tokens: tuple[str, ...]) -> str | None:
    if not tokens or Path(tokens[0]).name not in {"sh", "bash", "zsh"}:
        return None
    for index, token in enumerate(tokens[1:], start=1):
        if token == "-c" or (token.startswith("-") and token.endswith("c")):
            if index + 1 < len(tokens):
                return tokens[index + 1]
            return None
    return None


def _strip_heredoc_bodies(command: str) -> str:
    lines = command.splitlines()
    if not lines:
        return command
    stripped: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped.append(line)
        delimiter = _heredoc_delimiter(line)
        if delimiter is None:
            index += 1
            continue
        index += 1
        while index < len(lines) and lines[index].strip() != delimiter:
            index += 1
        if index < len(lines):
            stripped.append(lines[index])
            index += 1
    return "\n".join(stripped)


def _heredoc_delimiter(line: str) -> str | None:
    match = re.search(r"<<-?\s*['\"]?([A-Za-z0-9_]+)['\"]?", line)
    if match is None:
        return None
    return match.group(1)


def _aidd_workspace_path_literals(*, command: str, cwd: Path) -> tuple[Path, ...]:
    return tuple(
        _resolve_shell_path_token(token=match.group(0), cwd=cwd)
        for match in _AIDD_WORKSPACE_PATH_RE.finditer(command)
    )


def _absolute_path_literals(*, tokens: tuple[str, ...], cwd: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for token in tokens:
        for match in _ABSOLUTE_PATH_RE.finditer(token):
            paths.append(_resolve_shell_path_token(token=match.group(0), cwd=cwd))
    return tuple(paths)


def _dedupe_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    seen: set[str] = set()
    deduped: list[Path] = []
    for path in paths:
        key = path.as_posix()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return tuple(deduped)


def _shell_path_operands(*, command: str, cwd: Path) -> tuple[tuple[str, Path], ...]:
    tokens = _shell_tokens(command)
    if not tokens:
        return ()

    executable = Path(tokens[0]).name
    positional = _shell_positionals(tokens[1:])
    if executable == "pwd":
        path_tokens: tuple[str, ...] = ()
    elif executable in {"ls", "find"}:
        path_tokens = positional
    elif executable in {"rg", "grep"}:
        path_tokens = positional[1:]
    elif executable == "git" and len(tokens) >= 2:
        path_tokens = _git_path_operands(tokens[2:])
    else:
        path_tokens = tuple(token for token in tokens[1:] if _looks_like_path(token))

    return tuple(
        (token, _resolve_shell_path_token(token=token, cwd=cwd))
        for token in path_tokens
        if _looks_like_path(token)
    )


def _shell_positionals(tokens: tuple[str, ...]) -> tuple[str, ...]:
    positionals: list[str] = []
    end_of_options = False
    for token in tokens:
        if token == "--":
            end_of_options = True
            continue
        if not end_of_options and token.startswith("-"):
            continue
        positionals.append(token)
    return tuple(positionals)


def _git_path_operands(tokens: tuple[str, ...]) -> tuple[str, ...]:
    if "--" not in tokens:
        return tuple(token for token in tokens if _looks_like_path(token))
    separator_index = tokens.index("--")
    return tuple(tokens[separator_index + 1 :])


def _looks_like_path(token: str) -> bool:
    if not token or token.startswith(("http://", "https://")):
        return False
    return (
        token in {".", "..", "~", "$HOME", "/"}
        or token.startswith(("./", "../", "~/", "$HOME/", "/"))
        or "/" in token
    )


def _resolve_shell_path_token(*, token: str, cwd: Path) -> Path:
    if token == "~":
        return _lexical_absolute_path(Path.home(), cwd=cwd)
    if token.startswith("~/"):
        return _lexical_absolute_path(Path.home() / token[2:], cwd=cwd)
    if token == "$HOME":
        return _lexical_absolute_path(Path.home(), cwd=cwd)
    if token.startswith("$HOME/"):
        return _lexical_absolute_path(Path.home() / token[6:], cwd=cwd)
    return _lexical_absolute_path(Path(token), cwd=cwd)


def _lexical_absolute_path(path: Path, *, cwd: Path) -> Path:
    candidate = path if path.is_absolute() else cwd / path
    return Path(os.path.abspath(os.path.normpath(os.fspath(candidate))))


def _contains_destructive_root_or_home_remove(tokens: tuple[str, ...]) -> bool:
    for index, token in enumerate(tokens):
        if Path(token).name != "rm":
            continue
        following = tokens[index + 1 :]
        recursive_force = any(
            option.startswith("-") and "r" in option and "f" in option
            for option in following
        )
        if not recursive_force:
            continue
        for target in following:
            if target.startswith("-"):
                continue
            if target in {"/", "~", "$HOME"} or target.startswith(("~/", "$HOME/")):
                return True
    return False


def _is_protected_path(path: Path) -> bool:
    lowered_parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()
    if name.startswith(".env"):
        return True
    if _AIDD_WORKSPACE_DIRNAME in lowered_parts:
        aidd_index = lowered_parts.index(_AIDD_WORKSPACE_DIRNAME)
        if any(part in _PROTECTED_AIDD_DIR_NAMES for part in lowered_parts[aidd_index + 1 :]):
            return True
    if any(part in _PROTECTED_NAMES for part in lowered_parts):
        return True
    if name in _PROTECTED_FILE_NAMES:
        return True
    return any(marker in name for marker in ("credential", "secret", "token"))


def _is_relative_to_any(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(_is_relative_to(path, root) for root in roots)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def append_operator_request(*, path: Path, request: RuntimeOperatorRequest) -> None:
    _append_jsonl(path=path, payload=request.to_dict())


def append_operator_decision(*, path: Path, decision: RuntimeOperatorDecision) -> None:
    _append_jsonl(path=path, payload=decision.to_dict())


def load_operator_requests(path: Path) -> tuple[RuntimeOperatorRequest, ...]:
    return tuple(RuntimeOperatorRequest.from_dict(payload) for payload in _load_jsonl(path))


def load_operator_decisions(path: Path) -> tuple[RuntimeOperatorDecision, ...]:
    return tuple(RuntimeOperatorDecision.from_dict(payload) for payload in _load_jsonl(path))


def pending_operator_request_ids(*, attempt_path: Path) -> tuple[str, ...]:
    requests = load_operator_requests(attempt_path / OPERATOR_REQUESTS_FILENAME)
    decisions = load_operator_decisions(attempt_path / OPERATOR_DECISIONS_FILENAME)
    decided_ids = {decision.request_id for decision in decisions}
    return tuple(request.id for request in requests if request.id not in decided_ids)


def unapproved_operator_request_ids(*, attempt_path: Path) -> tuple[str, ...]:
    requests = load_operator_requests(attempt_path / OPERATOR_REQUESTS_FILENAME)
    decisions_by_request_id = {
        decision.request_id: decision
        for decision in load_operator_decisions(attempt_path / OPERATOR_DECISIONS_FILENAME)
    }
    unapproved_ids: list[str] = []
    for request in requests:
        decision = decisions_by_request_id.get(request.id)
        if decision is None or not decision.is_approval:
            unapproved_ids.append(request.id)
    return tuple(unapproved_ids)


def _operator_decision_recorded(*, path: Path, request_id: str) -> bool:
    return any(decision.request_id == request_id for decision in load_operator_decisions(path))


def _append_jsonl(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(payload, sort_keys=True) + "\n")


def _load_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return tuple(rows)


__all__ = [
    "OPERATOR_DECISIONS_FILENAME",
    "OPERATOR_REQUESTS_FILENAME",
    "RuntimeOperatorBroker",
    "RuntimeOperatorDecision",
    "RuntimeOperatorDecisionProvider",
    "RuntimeOperatorPolicy",
    "RuntimeOperatorRequest",
    "append_operator_decision",
    "append_operator_request",
    "load_operator_decisions",
    "load_operator_requests",
    "pending_operator_request_ids",
    "unapproved_operator_request_ids",
]
