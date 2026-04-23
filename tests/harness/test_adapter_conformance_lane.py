from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.contracts import repo_root_from
from aidd.harness.adapter_conformance import evaluate_conformance_matrix
from aidd.harness.conformance_matrix import load_runtime_conformance_matrix


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _matrix_path() -> Path:
    return _repo_root() / "docs" / "architecture" / "adapter-conformance-matrix.md"


def _matrix_runtime_ids() -> tuple[str, ...]:
    matrix = load_runtime_conformance_matrix(_matrix_path())
    return matrix.runtime_ids()


@pytest.mark.parametrize("runtime_id", _matrix_runtime_ids())
def test_adapter_conformance_lane_reports_per_runtime_pass(runtime_id: str) -> None:
    workspace_root = _repo_root() / ".aidd" / "conformance-lane"
    results = evaluate_conformance_matrix(
        matrix_path=_matrix_path(),
        workspace_root=workspace_root,
    )
    result_by_runtime = {result.runtime_id: result for result in results}
    assert runtime_id in result_by_runtime

    runtime_result = result_by_runtime[runtime_id]
    failed_dimensions = runtime_result.failed_required_dimensions()
    assert not failed_dimensions, (
        f"{runtime_id} failed required conformance dimensions: "
        f"{', '.join(failed_dimensions)}"
    )
