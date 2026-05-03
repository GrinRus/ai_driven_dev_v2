from __future__ import annotations

from pathlib import Path


def workspace_relative_path(workspace_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def workspace_relative_paths(workspace_root: Path, paths: tuple[Path, ...]) -> tuple[str, ...]:
    resolved_workspace = workspace_root.resolve(strict=False)
    return tuple(
        path.resolve(strict=False).relative_to(resolved_workspace).as_posix() for path in paths
    )


__all__ = ["workspace_relative_path", "workspace_relative_paths"]
