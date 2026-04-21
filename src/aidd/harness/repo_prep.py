from __future__ import annotations

from pathlib import Path

def prepare_workspace(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
