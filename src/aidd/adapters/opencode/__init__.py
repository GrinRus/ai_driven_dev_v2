"""opencode adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="opencode",
    protected_paths=(".opencode", ".env"),
    credential_paths=(".opencode/auth.json", ".opencode/credentials.json", "opencode.json"),
    config_paths=(".opencode/config.json", "opencode.json"),
    capabilities=(
        "raw-log-stream",
        "structured-log-stream",
        "questions",
        "resume",
        "subagents",
        "non-interactive",
        "working-directory",
        "env-injection",
        "permission-policy",
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
