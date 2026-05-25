from __future__ import annotations

from aidd.runtime_permissions import command_contains_permission_bypass


def test_command_contains_permission_bypass_covers_provider_bypass_flags() -> None:
    assert command_contains_permission_bypass("claude -p --dangerously-skip-permissions")
    assert command_contains_permission_bypass(
        "claude -p --permission-mode bypassPermissions"
    )
    assert command_contains_permission_bypass("codex exec --full-auto --json -")
    assert command_contains_permission_bypass(
        "codex exec --dangerously-bypass-approvals-and-sandbox --json -"
    )
    assert command_contains_permission_bypass(
        "codex exec --dangerously-bypass-approvals-and-sandbox=true --json -"
    )
    assert command_contains_permission_bypass(
        "claude -p --dangerously-skip-permissions=true"
    )
    assert command_contains_permission_bypass("qwen -y")
    assert command_contains_permission_bypass("qwen --approval-mode yolo")


def test_command_contains_permission_bypass_ignores_non_bypass_commands() -> None:
    assert not command_contains_permission_bypass("qwen --approval-mode default")
    assert not command_contains_permission_bypass("codex exec --sandbox workspace-write --json -")
