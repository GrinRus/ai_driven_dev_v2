from __future__ import annotations

import json
import shutil
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.release.candidate_manifest import freeze_candidate, write_candidate_manifest
from scripts.release.installed_channel_verification import (
    CHANNELS,
    PHASES,
    ChannelExecution,
    ChannelVerificationError,
    build_installed_channel_verification,
    read_installed_channel_verification,
    write_installed_channel_verification,
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
    return wheel, manifest, manifest_path


def _digest(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def _execution(manifest, wheel: Path, *, channel: str, phase: str, code: int = 0):
    version = f"aidd {manifest.project_version}"
    doctor = f"Version {manifest.project_version}\nRuntime readiness ok"
    provenance = f"sha256={sha256(wheel.read_bytes()).hexdigest()}"
    return ChannelExecution(
        channel=channel,
        phase=phase,
        install_return_code=code,
        install_stdout_sha256=_digest("install"),
        install_stderr_sha256=_digest(""),
        version_return_code=code,
        version_output=version if code == 0 else "",
        version_stdout_sha256=_digest(version if code == 0 else ""),
        version_stderr_sha256=_digest(""),
        doctor_return_code=code,
        doctor_output=doctor if code == 0 else "",
        doctor_stdout_sha256=_digest(doctor if code == 0 else ""),
        doctor_stderr_sha256=_digest(""),
        provenance_return_code=code,
        provenance_output=provenance if code == 0 else "",
        provenance_stdout_sha256=_digest(provenance if code == 0 else ""),
        provenance_stderr_sha256=_digest(""),
    )


def _executions(manifest, wheel: Path, *, code: int = 0):
    return tuple(
        _execution(manifest, wheel, channel=channel, phase=phase, code=code)
        for channel in CHANNELS
        for phase in PHASES
    )


def test_build_write_read_binds_exact_wheel_and_channels(tmp_path: Path) -> None:
    wheel, manifest, manifest_path = _candidate(tmp_path)
    record = build_installed_channel_verification(
        manifest_path,
        wheel,
        _executions(manifest, wheel),
    )
    output = write_installed_channel_verification(record, tmp_path / "verification.json")
    loaded = read_installed_channel_verification(output, manifest_path=manifest_path)

    assert loaded == record
    assert record.success is True
    assert record.verification_sha256 in output.read_text(encoding="utf-8")


def test_channel_verification_fails_closed_on_order_or_wheel_drift(tmp_path: Path) -> None:
    wheel, manifest, manifest_path = _candidate(tmp_path)
    executions = list(_executions(manifest, wheel))
    executions[0], executions[1] = executions[1], executions[0]
    with pytest.raises(ChannelVerificationError, match="execution mismatch"):
        build_installed_channel_verification(manifest_path, wheel, executions)

    wheel.write_bytes(b"tampered")
    with pytest.raises(ChannelVerificationError, match="wheel digest"):
        build_installed_channel_verification(manifest_path, wheel, _executions(manifest, wheel))


def test_failed_channel_is_reported_not_accepted_and_tampering_is_rejected(tmp_path: Path) -> None:
    wheel, manifest, manifest_path = _candidate(tmp_path)
    record = build_installed_channel_verification(
        manifest_path,
        wheel,
        _executions(manifest, wheel, code=1),
    )
    assert record.success is False
    output = write_installed_channel_verification(record, tmp_path / "verification.json")
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["success"] = True
    output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ChannelVerificationError, match="success"):
        read_installed_channel_verification(output, manifest_path=manifest_path)
