from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityReport:
    runtime_id: str
    available: bool
    command: str
    version_text: str | None = None
    supports_raw_log_stream: bool = True
    supports_structured_log_stream: bool = False
    supports_questions: bool = False
    supports_resume: bool = False
    supports_subagents: bool = False
    supports_non_interactive_mode: bool = True
    supports_working_directory_control: bool = True
    supports_env_injection: bool = True
    supports_permission_policy: bool = False
    supports_live_decisions: bool = False
    supports_deferred_resume: bool = False
    preferred_transport: str = "subprocess"
