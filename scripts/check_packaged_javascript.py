"""Validate every JavaScript asset declared by the packaged operator UI."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from aidd.cli.ui_assets import operator_static_asset_manifest
from aidd.core.contracts import repo_root_from

NODE_CHECK_TIMEOUT_SECONDS = 10.0


def check_javascript_assets(
    *,
    static_root: Path,
    expected_filenames: tuple[str, ...],
    node_binary: str,
    timeout_seconds: float = NODE_CHECK_TIMEOUT_SECONDS,
) -> tuple[str, ...]:
    discovered = tuple(
        path.name for path in sorted(static_root.glob("*.js"), key=lambda item: item.name)
    )
    expected = tuple(sorted(expected_filenames))
    if discovered != expected:
        raise ValueError(
            "Packaged JavaScript discovery mismatch: "
            f"expected={list(expected)} discovered={list(discovered)}"
        )

    for filename in discovered:
        path = static_root / filename
        try:
            completed = subprocess.run(
                (node_binary, "--check", path.as_posix()),
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"JavaScript syntax check timed out for {filename}."
            ) from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(
                f"JavaScript syntax check failed for {filename}: {detail}"
            )
    return discovered


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        raise ValueError("check_packaged_javascript accepts no arguments")
    root = repo_root_from(Path(__file__).resolve())
    static_root = root / "src" / "aidd" / "cli" / "static"
    expected = tuple(
        asset.filename
        for asset in operator_static_asset_manifest()
        if asset.filename.endswith(".js")
    )
    node_binary = shutil.which("node")
    if node_binary is None:
        raise RuntimeError("Node.js is required for the packaged JavaScript syntax gate.")
    checked = check_javascript_assets(
        static_root=static_root,
        expected_filenames=expected,
        node_binary=node_binary,
    )
    print(f"checked {len(checked)} packaged JavaScript assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
