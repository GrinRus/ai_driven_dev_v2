from __future__ import annotations

from pathlib import Path

from aidd.core.contracts import repo_root_from
from aidd.harness.conformance_matrix import load_runtime_conformance_matrix

_REQUIRED_MAINTAINED_RUNTIMES: set[str] = {
    "generic-cli",
    "claude-code",
    "codex",
    "opencode",
}
_REQUIRED_DIMENSIONS: set[str] = {
    "probe_behavior",
    "capability_declaration",
    "raw_log_capture",
    "failure_mapping",
    "question_surfacing",
    "timeout_behavior",
    "workspace_targeting",
}


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def test_conformance_matrix_covers_maintained_runtimes_and_required_dimensions() -> None:
    matrix_path = _repo_root() / "docs" / "architecture" / "adapter-conformance-matrix.md"
    matrix = load_runtime_conformance_matrix(matrix_path)

    assert set(matrix.runtime_ids()) == _REQUIRED_MAINTAINED_RUNTIMES
    assert set(matrix.dimensions) == _REQUIRED_DIMENSIONS
    assert matrix.dimensions
    assert matrix.rows

    for row in matrix.rows:
        for dimension in _REQUIRED_DIMENSIONS:
            assert row.dimensions[dimension] == "required"
