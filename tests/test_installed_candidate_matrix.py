from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.release.candidate_manifest import freeze_candidate, write_candidate_manifest
from scripts.release.installed_candidate_matrix import (
    CandidateMatrixError,
    ScenarioExecution,
    build_installed_candidate_matrix,
    read_installed_candidate_matrix,
    write_installed_candidate_matrix,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FIXTURE = (
    REPO_ROOT / "harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml"
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _candidate(tmp_path: Path):
    root = tmp_path / "candidate"
    (root / "harness/scenarios").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "candidate-fixture"\nversion = "1.2.3"\n', encoding="utf-8"
    )
    shutil.copyfile(SCENARIO_FIXTURE, root / "harness/scenarios/scenario.yaml")
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "candidate@example.test")
    _git(root, "config", "user.name", "Candidate Tests")
    _git(root, "add", "pyproject.toml", "harness/scenarios/scenario.yaml")
    _git(root, "commit", "--quiet", "-m", "candidate fixture")
    wheel = tmp_path / "dist" / "candidate-1.2.3-py3-none-any.whl"
    wheel.parent.mkdir()
    wheel.write_bytes(b"wheel-bytes")
    manifest = freeze_candidate(project_root=root, wheel_path=wheel)
    manifest_path = write_candidate_manifest(manifest, tmp_path / "candidate-manifest.json")
    return root, wheel, manifest, manifest_path


def _execution(manifest, bundle: Path, *, return_code: int = 0) -> ScenarioExecution:
    bundle.mkdir(parents=True)
    return ScenarioExecution(
        scenario_id=manifest.scenario_inventory[0].scenario_id,
        path=manifest.scenario_inventory[0].path,
        return_code=return_code,
        bundle_path=bundle.as_posix(),
        stdout_sha256="1" * 64,
        stderr_sha256="2" * 64,
    )


def test_build_write_read_matrix_binds_wheel_and_bundle(tmp_path: Path) -> None:
    _root, wheel, manifest, manifest_path = _candidate(tmp_path)
    execution = _execution(manifest, tmp_path / "bundle")

    record = build_installed_candidate_matrix(manifest_path, wheel, (execution,))
    output = write_installed_candidate_matrix(record, tmp_path / "matrix.json")
    loaded = read_installed_candidate_matrix(output, manifest_path=manifest_path)

    assert loaded == record
    assert record.success is True
    assert record.wheel_sha256 == manifest.wheel.sha256
    assert record.matrix_sha256 in output.read_text(encoding="utf-8")


def test_matrix_fails_closed_on_wheel_drift_or_execution_mismatch(tmp_path: Path) -> None:
    _root, wheel, manifest, manifest_path = _candidate(tmp_path)
    execution = _execution(manifest, tmp_path / "bundle")
    wheel.write_bytes(b"tampered")
    with pytest.raises(CandidateMatrixError, match="wheel digest"):
        build_installed_candidate_matrix(manifest_path, wheel, (execution,))

    _root, wheel, manifest, manifest_path = _candidate(tmp_path / "second")
    execution = _execution(manifest, tmp_path / "second" / "bundle")
    wrong = ScenarioExecution(
        scenario_id="UNKNOWN",
        path=execution.path,
        return_code=0,
        bundle_path=execution.bundle_path,
        stdout_sha256=execution.stdout_sha256,
        stderr_sha256=execution.stderr_sha256,
    )
    with pytest.raises(CandidateMatrixError, match="execution mismatch"):
        build_installed_candidate_matrix(manifest_path, wheel, (wrong,))


def test_failed_or_missing_bundle_is_not_ready_and_tampering_is_rejected(tmp_path: Path) -> None:
    _root, wheel, manifest, manifest_path = _candidate(tmp_path)
    failed = ScenarioExecution(
        scenario_id=manifest.scenario_inventory[0].scenario_id,
        path=manifest.scenario_inventory[0].path,
        return_code=1,
        bundle_path="",
        stdout_sha256="1" * 64,
        stderr_sha256="2" * 64,
    )
    record = build_installed_candidate_matrix(manifest_path, wheel, (failed,))
    assert record.success is False
    output = write_installed_candidate_matrix(record, tmp_path / "matrix.json")
    with pytest.raises(CandidateMatrixError, match="overwrite"):
        write_installed_candidate_matrix(record, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["success"] = True
    output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CandidateMatrixError, match="success"):
        read_installed_candidate_matrix(output, manifest_path=manifest_path)


def test_build_requires_manifest_path_shape(tmp_path: Path) -> None:
    _root, wheel, manifest, manifest_path = _candidate(tmp_path)
    bundle = tmp_path / "bundle"
    execution = _execution(manifest, bundle)
    absolute_path_execution = ScenarioExecution(
        scenario_id=execution.scenario_id,
        path=(manifest_path.parent / execution.path).resolve().as_posix(),
        return_code=execution.return_code,
        bundle_path=execution.bundle_path,
        stdout_sha256=execution.stdout_sha256,
        stderr_sha256=execution.stderr_sha256,
    )
    with pytest.raises(CandidateMatrixError, match="path mismatch"):
        build_installed_candidate_matrix(manifest_path, wheel, (absolute_path_execution,))
