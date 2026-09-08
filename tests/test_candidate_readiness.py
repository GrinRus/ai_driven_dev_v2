from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.release.candidate_manifest import freeze_candidate, write_candidate_manifest
from scripts.release.candidate_readiness import (
    REQUIRED_GATE_NAMES,
    CandidateReadinessError,
    build_candidate_readiness,
    main,
    read_candidate_readiness,
    write_candidate_readiness,
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
    return root, manifest, manifest_path


def _evidence(manifest, *, status: str = "pass") -> dict[str, object]:
    return {
        "candidate_manifest_sha256": manifest.manifest_sha256,
        "captured_at_utc": "2026-09-09T00:00:00Z",
        "gates": [
            {
                "name": name,
                "observed_commit": manifest.source_commit,
                "result_id": f"run-{index}",
                "result_url": f"https://github.com/example/project/actions/runs/{index}",
                "status": status,
            }
            for index, name in enumerate(REQUIRED_GATE_NAMES, start=1)
        ],
        "project_version": manifest.project_version,
        "source_commit": manifest.source_commit,
        "source_tree": manifest.source_tree,
    }


def test_build_write_read_binds_all_required_gates(tmp_path: Path) -> None:
    _root, manifest, manifest_path = _candidate(tmp_path)
    evidence_path = tmp_path / "candidate-gates.json"
    evidence_path.write_text(json.dumps(_evidence(manifest)), encoding="utf-8")

    record = build_candidate_readiness(manifest_path, evidence_path)
    output = write_candidate_readiness(record, tmp_path / "candidate-readiness.json")
    loaded = read_candidate_readiness(output, manifest_path=manifest_path)

    assert loaded == record
    assert record.success is True
    assert tuple(gate.name for gate in record.gates) == REQUIRED_GATE_NAMES
    assert record.readiness_sha256 in output.read_text(encoding="utf-8")


def test_readiness_rejects_missing_duplicate_and_mismatched_gates(tmp_path: Path) -> None:
    _root, manifest, manifest_path = _candidate(tmp_path)
    evidence = _evidence(manifest)

    evidence["gates"] = evidence["gates"][:-1]
    missing_path = tmp_path / "missing.json"
    missing_path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(CandidateReadinessError, match="missing"):
        build_candidate_readiness(manifest_path, missing_path)

    evidence = _evidence(manifest)
    evidence["gates"] = [*evidence["gates"], evidence["gates"][0]]
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(CandidateReadinessError, match="duplicate"):
        build_candidate_readiness(manifest_path, duplicate_path)

    evidence = _evidence(manifest)
    evidence["gates"][0]["observed_commit"] = "f" * 40
    mismatch_path = tmp_path / "mismatch.json"
    mismatch_path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(CandidateReadinessError, match="does not match"):
        build_candidate_readiness(manifest_path, mismatch_path)


def test_failed_gate_is_recorded_but_not_ready_and_tampering_fails_closed(tmp_path: Path) -> None:
    _root, manifest, manifest_path = _candidate(tmp_path)
    evidence_path = tmp_path / "candidate-gates.json"
    evidence_path.write_text(json.dumps(_evidence(manifest, status="fail")), encoding="utf-8")
    record = build_candidate_readiness(manifest_path, evidence_path)
    assert record.success is False
    output = write_candidate_readiness(record, tmp_path / "candidate-readiness.json")
    with pytest.raises(CandidateReadinessError, match="overwrite"):
        write_candidate_readiness(record, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["gates"][0]["status"] = "pass"
    output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CandidateReadinessError, match="digest"):
        read_candidate_readiness(output, manifest_path=manifest_path)


def test_cli_writes_ready_record_and_returns_blocked_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _root, manifest, manifest_path = _candidate(tmp_path)
    evidence_path = tmp_path / "candidate-gates.json"
    evidence_path.write_text(json.dumps(_evidence(manifest)), encoding="utf-8")
    output = tmp_path / "candidate-readiness.json"

    assert (
        main(
            (
                "--manifest",
                manifest_path.as_posix(),
                "--evidence",
                evidence_path.as_posix(),
                "--output",
                output.as_posix(),
            )
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["success"] is True

    blocked = _evidence(manifest, status="pending")
    evidence_path.write_text(json.dumps(blocked), encoding="utf-8")
    blocked_output = tmp_path / "blocked-readiness.json"
    assert (
        main(
            (
                "--manifest",
                manifest_path.as_posix(),
                "--evidence",
                evidence_path.as_posix(),
                "--output",
                blocked_output.as_posix(),
            )
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["success"] is False
