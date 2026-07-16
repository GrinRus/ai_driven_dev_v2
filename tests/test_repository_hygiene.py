from __future__ import annotations

import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _tracked_existing_paths() -> tuple[Path, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=True,
    )
    return tuple(
        Path(raw_path.decode("utf-8"))
        for raw_path in completed.stdout.split(b"\0")
        if raw_path and (REPOSITORY_ROOT / raw_path.decode("utf-8")).exists()
    )


def test_tracked_repository_inventory_excludes_generated_cache_surfaces() -> None:
    tracked_paths = _tracked_existing_paths()

    assert Path("manifest.txt") not in tracked_paths
    assert Path("MANIFEST.md") in tracked_paths
    assert all(
        "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and path.suffix != ".pyc"
        for path in tracked_paths
    )
