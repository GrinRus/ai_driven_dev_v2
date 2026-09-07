"""codex adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="codex",
    protected_paths=(".codex", ".env"),
    credential_paths=(".codex/auth.json", ".codex/credentials.json", "codex.json"),
    config_paths=(".codex/config.toml", "codex.json"),
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
        "live-decisions",
        "native-transport",
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
