from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class RuntimeCapabilities:
    runtime_id: str
    available: bool
    command: str
    version_text: str | None = None
    supports_tool_calls: bool = False
    supports_raw_log_stream: bool = True
    supports_structured_log_stream: bool = False
    supports_log_access: bool = True
    supports_questions: bool = False
    supports_resume: bool = False
    supports_interrupts: bool = False
    supports_subagents: bool = False
    supports_hooks: bool = False
    supports_non_interactive_mode: bool = True
    supports_working_directory_control: bool = True
    supports_env_injection: bool = True


# Backward-compatible alias used across probes/tests.
CapabilityReport = RuntimeCapabilities


RuntimeStream = Literal["stdout", "stderr"]


@dataclass(frozen=True, slots=True)
class RuntimeStartRequest:
    stage: str
    work_item: str
    run_id: str
    workspace_root: Path
    attempt_path: Path
    stage_brief_path: Path
    prompt_pack_paths: tuple[Path, ...]
    timeout_seconds: float | None = None
    extra_env: dict[str, str] | None = None
    repository_root: Path | None = None


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    stream: RuntimeStream
    chunk: str


@dataclass(frozen=True, slots=True)
class RuntimeStartResult:
    runtime_id: str
    exit_code: int
    exit_classification: str
    runtime_log_path: Path
    stdout_text: str
    stderr_text: str
    normalized_events_path: Path | None = None
    normalized_events: tuple[dict[str, Any], ...] = ()
    unresolved_blocking_question_ids: tuple[str, ...] = ()


@runtime_checkable
class RuntimeAdapter(Protocol):
    runtime_id: str

    def probe(self) -> RuntimeCapabilities: ...

    def start(self, request: RuntimeStartRequest) -> RuntimeStartResult: ...

    def send(self, *, session_id: str, payload: str) -> None: ...

    def interrupt(self, *, session_id: str) -> None: ...

    def stream_events(self, *, session_id: str) -> tuple[RuntimeEvent, ...]: ...

    def stop(self, *, session_id: str) -> None: ...
