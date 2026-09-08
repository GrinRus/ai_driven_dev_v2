from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.release.candidate_manifest import (
    DEFAULT_VERIFICATION_COMMANDS,
    CandidateManifestError,
    freeze_candidate,
    main,
    read_candidate_manifest,
    validate_candidate_manifest,
    write_candidate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FIXTURE = (
    REPO_ROOT / "harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml"
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _fixture_repository(tmp_path: Path) -> Path:
    root = tmp_path / "candidate"
    (root / "harness/scenarios").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "candidate-fixture"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    shutil.copyfile(SCENARIO_FIXTURE, root / "harness/scenarios/scenario.yaml")
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "candidate@example.test")
    _git(root, "config", "user.name", "Candidate Tests")
    _git(root, "add", "pyproject.toml", "harness/scenarios/scenario.yaml")
    _git(root, "commit", "--quiet", "-m", "candidate fixture")
    return root


def _wheel(tmp_path: Path, payload: bytes = b"wheel-bytes") -> Path:
    path = tmp_path / "dist" / "candidate-1.2.3-py3-none-any.whl"
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    return path


def test_freeze_write_read_and_validate_candidate_identity(tmp_path: Path) -> None:
    root = _fixture_repository(tmp_path)
    wheel = _wheel(tmp_path)

    manifest = freeze_candidate(project_root=root, wheel_path=wheel)
    output = write_candidate_manifest(manifest, tmp_path / "candidate-manifest.json")
    loaded = read_candidate_manifest(output)
    validated = validate_candidate_manifest(output, project_root=root)

    assert loaded == manifest == validated
    assert manifest.source_commit == _git(root, "rev-parse", "HEAD")
    assert manifest.source_tree == _git(root, "rev-parse", "HEAD^{tree}")
    assert manifest.wheel.size_bytes == len(b"wheel-bytes")
    assert manifest.verification_commands == DEFAULT_VERIFICATION_COMMANDS
    assert manifest.scenario_root == "harness/scenarios"
    assert len(manifest.scenario_inventory) == 1
    assert manifest.scenario_inventory[0].scenario_id == "AIDD-DETERMINISTIC-001"
    assert manifest.manifest_sha256 in output.read_text(encoding="utf-8")


def test_freeze_rejects_dirty_worktree_and_empty_or_non_wheel_artifact(tmp_path: Path) -> None:
    root = _fixture_repository(tmp_path)
    wheel = _wheel(tmp_path)
    (root / "untracked.txt").write_text("dirty", encoding="utf-8")

    with pytest.raises(CandidateManifestError, match="dirty"):
        freeze_candidate(project_root=root, wheel_path=wheel)

    (root / "untracked.txt").unlink()
    empty = _wheel(tmp_path / "empty", payload=b"")
    with pytest.raises(CandidateManifestError, match="must not be empty"):
        freeze_candidate(project_root=root, wheel_path=empty)
    not_wheel = _wheel(tmp_path / "not-wheel").with_suffix(".zip")
    not_wheel.write_bytes(b"archive")
    with pytest.raises(CandidateManifestError, match=".whl suffix"):
        freeze_candidate(project_root=root, wheel_path=not_wheel)


def test_validate_rejects_changed_git_identity_or_wheel_digest(tmp_path: Path) -> None:
    root = _fixture_repository(tmp_path)
    wheel = _wheel(tmp_path)
    output = write_candidate_manifest(
        freeze_candidate(project_root=root, wheel_path=wheel),
        tmp_path / "candidate-manifest.json",
    )

    wheel.write_bytes(b"tampered")
    with pytest.raises(CandidateManifestError, match="wheel digest"):
        validate_candidate_manifest(output, project_root=root)

    wheel.write_bytes(b"wheel-bytes")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "candidate-fixture"\nversion = "1.2.4"\n',
        encoding="utf-8",
    )
    _git(root, "add", "pyproject.toml")
    _git(root, "commit", "--quiet", "-m", "change candidate")
    with pytest.raises(CandidateManifestError, match="version"):
        validate_candidate_manifest(output, project_root=root)


def test_read_rejects_tampered_manifest_and_overwrite(tmp_path: Path) -> None:
    root = _fixture_repository(tmp_path)
    output = write_candidate_manifest(
        freeze_candidate(project_root=root, wheel_path=_wheel(tmp_path)),
        tmp_path / "candidate-manifest.json",
    )
    with pytest.raises(CandidateManifestError, match="overwrite"):
        write_candidate_manifest(read_candidate_manifest(output), output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["wheel"]["sha256"] = "0" * 64
    output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CandidateManifestError, match="digest"):
        read_candidate_manifest(output)


def test_freeze_requires_commands_and_scenario_inventory(tmp_path: Path) -> None:
    root = _fixture_repository(tmp_path)
    wheel = _wheel(tmp_path)
    with pytest.raises(CandidateManifestError, match="verification_commands"):
        freeze_candidate(project_root=root, wheel_path=wheel, verification_commands=("",))

    empty_root = tmp_path / "empty-scenarios"
    empty_root.mkdir()
    with pytest.raises(CandidateManifestError, match="inventory"):
        freeze_candidate(project_root=root, wheel_path=wheel, scenario_root=empty_root)


def test_cli_freezes_and_validates_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _fixture_repository(tmp_path)
    wheel = _wheel(tmp_path)
    output = tmp_path / "cli-manifest.json"

    assert (
        main(
            (
                "--project-root",
                root.as_posix(),
                "--wheel",
                wheel.as_posix(),
                "--output",
                output.as_posix(),
            )
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["success"] is True
    assert (
        main(
            (
                "--validate",
                "--project-root",
                root.as_posix(),
                "--manifest",
                output.as_posix(),
            )
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["valid"] is True
