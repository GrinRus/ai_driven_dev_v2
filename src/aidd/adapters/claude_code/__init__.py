"""claude-code adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="claude-code",
    protected_paths=(".claude", ".env"),
    credential_paths=(".claude/auth.json", ".claude/credentials.json", "claude.json"),
    config_paths=(".claude/settings.json", "claude.json"),
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
        "deferred-resume",
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
