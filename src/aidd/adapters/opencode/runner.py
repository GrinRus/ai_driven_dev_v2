from __future__ import annotations

from pathlib import Path


def command_preview(workspace_root: Path, stage: str) -> str:
    """Return a placeholder command preview for bootstrap use."""
    return f"opencode run {stage} in {workspace_root}".format(
        stage=stage,
        workspace_root=workspace_root,
    )
