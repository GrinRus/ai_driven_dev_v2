from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

from aidd.cli.ui_assets import operator_static_asset_manifest
from aidd.core.contracts import repo_root_from


def _load_script() -> ModuleType:
    path = repo_root_from(Path(__file__).resolve()) / "scripts/check_packaged_javascript.py"
    spec = importlib.util.spec_from_file_location("check_packaged_javascript", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SCRIPT = _load_script()


def test_all_packaged_javascript_assets_pass_node_syntax_check() -> None:
    root = repo_root_from(Path(__file__).resolve())
    node_binary = shutil.which("node")
    if node_binary is None:
        pytest.fail("Node.js is required for the packaged JavaScript syntax gate")
    expected = tuple(
        asset.filename
        for asset in operator_static_asset_manifest()
        if asset.filename.endswith(".js")
    )

    checked = _SCRIPT.check_javascript_assets(
        static_root=root / "src/aidd/cli/static",
        expected_filenames=expected,
        node_binary=node_binary,
    )

    assert checked == tuple(sorted(expected))


def test_javascript_syntax_gate_rejects_invalid_asset(tmp_path: Path) -> None:
    node_binary = shutil.which("node")
    if node_binary is None:
        pytest.fail("Node.js is required for the packaged JavaScript syntax gate")
    (tmp_path / "broken.js").write_text("function broken( {\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="syntax check failed for broken.js"):
        _SCRIPT.check_javascript_assets(
            static_root=tmp_path,
            expected_filenames=("broken.js",),
            node_binary=node_binary,
        )


def test_javascript_asset_discovery_must_match_package_manifest(tmp_path: Path) -> None:
    node_binary = shutil.which("node") or "node"
    (tmp_path / "declared.js").write_text("const declared = true;\n", encoding="utf-8")
    (tmp_path / "orphan.js").write_text("const orphan = true;\n", encoding="utf-8")

    with pytest.raises(ValueError, match="discovery mismatch"):
        _SCRIPT.check_javascript_assets(
            static_root=tmp_path,
            expected_filenames=("declared.js",),
            node_binary=node_binary,
        )
