"""Qwen Code runtime adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="qwen",
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
