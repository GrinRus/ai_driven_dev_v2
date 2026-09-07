"""Qwen Code runtime adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor, RuntimeAdapterRegistration

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="qwen",
    registration=RuntimeAdapterRegistration(
        runtime_id="qwen",
        config_section="qwen",
        support_tier="experimental",
        default_command="qwen --approval-mode auto --output-format stream-json",
        probe_command="qwen",
        default_execution_mode="native",
        supported_execution_modes=("native", "adapter-flags"),
        brokered_default_command="qwen --approval-mode default --output-format stream-json",
    ),
    protected_paths=(".qwen", ".env"),
    credential_paths=(".qwen/auth.json", ".qwen/credentials.json", "qwen.json"),
    config_paths=(".qwen/settings.json", "qwen.json"),
    capabilities=frozenset(
        {
            "raw-log-stream",
            "structured-log-stream",
            "questions",
            "subagents",
            "non-interactive",
            "working-directory",
            "env-injection",
            "permission-policy",
            "live-decisions",
            "native-transport",
        }
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
