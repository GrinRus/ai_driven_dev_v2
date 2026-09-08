"""Verify exact-wheel installation and replacement through supported tool channels."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scripts.release.candidate_manifest import (
    CandidateManifestError,
    read_candidate_manifest,
    validate_candidate_manifest,
)

CHANNELS: tuple[Literal["pipx", "uv-tool"], ...] = ("pipx", "uv-tool")
PHASES = ("clean-install", "upgrade")
PACKAGE_NAME = "ai-driven-dev-v2"
SCHEMA_VERSION = 1
COMMAND_TIMEOUT_SECONDS = 900.0
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


class ChannelVerificationError(ValueError):
    """Raised when exact-wheel channel verification cannot be trusted."""


@dataclass(frozen=True, slots=True)
class CommandObservation:
    return_code: int
    stdout: str
    stderr: str

    @property
    def stdout_sha256(self) -> str:
        return _digest(self.stdout)

    @property
    def stderr_sha256(self) -> str:
        return _digest(self.stderr)


@dataclass(frozen=True, slots=True)
class ChannelExecution:
    channel: str
    phase: str
    install_return_code: int
    install_stdout_sha256: str
    install_stderr_sha256: str
    version_return_code: int
    version_output: str
    version_stdout_sha256: str
    version_stderr_sha256: str
    doctor_return_code: int
    doctor_output: str
    doctor_stdout_sha256: str
    doctor_stderr_sha256: str
    provenance_return_code: int
    provenance_output: str
    provenance_stdout_sha256: str
    provenance_stderr_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "doctor_output": self.doctor_output,
            "doctor_return_code": self.doctor_return_code,
            "doctor_stderr_sha256": self.doctor_stderr_sha256,
            "doctor_stdout_sha256": self.doctor_stdout_sha256,
            "install_return_code": self.install_return_code,
            "install_stderr_sha256": self.install_stderr_sha256,
            "install_stdout_sha256": self.install_stdout_sha256,
            "phase": self.phase,
            "provenance_output": self.provenance_output,
            "provenance_return_code": self.provenance_return_code,
            "provenance_stderr_sha256": self.provenance_stderr_sha256,
            "provenance_stdout_sha256": self.provenance_stdout_sha256,
            "version_output": self.version_output,
            "version_return_code": self.version_return_code,
            "version_stderr_sha256": self.version_stderr_sha256,
            "version_stdout_sha256": self.version_stdout_sha256,
        }


@dataclass(frozen=True, slots=True)
class InstalledChannelVerification:
    candidate_manifest_sha256: str
    project_version: str
    source_commit: str
    source_tree: str
    wheel_sha256: str
    wheel_size_bytes: int
    executions: tuple[ChannelExecution, ...]
    success: bool
    verification_sha256: str
    schema_version: int = SCHEMA_VERSION

    def _payload(self) -> dict[str, object]:
        return {
            "candidate_manifest_sha256": self.candidate_manifest_sha256,
            "executions": [execution.to_dict() for execution in self.executions],
            "project_version": self.project_version,
            "schema_version": self.schema_version,
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "success": self.success,
            "wheel_sha256": self.wheel_sha256,
            "wheel_size_bytes": self.wheel_size_bytes,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._payload(), "verification_sha256": self.verification_sha256}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_sha256(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _SHA256_PATTERN.fullmatch(normalized) is None:
        raise ChannelVerificationError(f"{label} must be a lowercase SHA-256 digest.")
    return normalized


def _validate_git_object(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _GIT_OBJECT_PATTERN.fullmatch(normalized) is None:
        raise ChannelVerificationError(f"{label} must be a full hexadecimal Git object id.")
    return normalized


def _wheel_identity(path: Path) -> tuple[str, int]:
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_file() or not resolved.name.lower().endswith(".whl"):
            raise ChannelVerificationError("Candidate wheel must be a regular .whl file.")
        size = resolved.stat().st_size
        if size <= 0:
            raise ChannelVerificationError("Candidate wheel must not be empty.")
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except ChannelVerificationError:
        raise
    except OSError as exc:
        raise ChannelVerificationError(f"Candidate wheel is not readable: {path}") from exc
    return digest, size


def _run(
    argv: Sequence[str | Path],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: float = COMMAND_TIMEOUT_SECONDS,
) -> CommandObservation:
    try:
        completed = subprocess.run(
            tuple(str(item) for item in argv),
            cwd=cwd,
            env=dict(env),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandObservation(return_code=127, stdout="", stderr=str(exc))
    return CommandObservation(
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _python_path(root: Path) -> Path:
    path = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return path


def _aidd_path(root: Path) -> Path:
    path = root / ("Scripts/aidd.exe" if os.name == "nt" else "bin/aidd")
    return path


def _provenance_script() -> str:
    return (
        "import importlib.metadata as m, json; "
        "d=m.distribution('ai-driven-dev-v2'); "
        "raw=d.read_text('direct_url.json'); "
        "payload=json.loads(raw or '{}'); "
        "print(payload.get('archive_info', {}).get('hash', ''))"
    )


def _missing_observation(detail: str) -> CommandObservation:
    return CommandObservation(return_code=127, stdout="", stderr=detail)


def _execution(
    *,
    channel: str,
    phase: str,
    install: CommandObservation,
    version: CommandObservation,
    doctor: CommandObservation,
    provenance: CommandObservation,
) -> ChannelExecution:
    return ChannelExecution(
        channel=channel,
        phase=phase,
        install_return_code=install.return_code,
        install_stdout_sha256=install.stdout_sha256,
        install_stderr_sha256=install.stderr_sha256,
        version_return_code=version.return_code,
        version_output=version.stdout.strip(),
        version_stdout_sha256=version.stdout_sha256,
        version_stderr_sha256=version.stderr_sha256,
        doctor_return_code=doctor.return_code,
        doctor_output=doctor.stdout.strip(),
        doctor_stdout_sha256=doctor.stdout_sha256,
        doctor_stderr_sha256=doctor.stderr_sha256,
        provenance_return_code=provenance.return_code,
        provenance_output=provenance.stdout.strip(),
        provenance_stdout_sha256=provenance.stdout_sha256,
        provenance_stderr_sha256=provenance.stderr_sha256,
    )


def _run_channel(
    *,
    channel: Literal["pipx", "uv-tool"],
    phase: str,
    project_root: Path,
    wheel_path: Path,
    version: str,
    wheel_sha256: str,
    channel_root: Path,
) -> ChannelExecution:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    wheel = wheel_path.resolve(strict=True)
    if channel == "pipx":
        executable = shutil.which("pipx")
        tool_home = channel_root / "pipx-home"
        tool_bin = channel_root / "pipx-bin"
        environment.update({"PIPX_HOME": str(tool_home), "PIPX_BIN_DIR": str(tool_bin)})
        install_command: tuple[str | Path, ...] = (
            executable or "pipx",
            "install",
            "--force",
            "--backend",
            "pip",
            wheel,
        )
        environment_root = tool_home / "venvs" / PACKAGE_NAME
        aidd = _aidd_path(tool_bin)
    else:
        executable = shutil.which("uv")
        tool_dir = channel_root / "uv-tools"
        tool_bin = channel_root / "uv-tool-bin"
        environment.update({"UV_TOOL_DIR": str(tool_dir), "UV_TOOL_BIN_DIR": str(tool_bin)})
        install_command = (executable or "uv", "tool", "install", "--force", wheel)
        environment_root = tool_dir / PACKAGE_NAME
        aidd = _aidd_path(tool_bin)

    # Neither tool accepts a local wheel as an argument to its registry-oriented `upgrade`
    # command. Force-installing the exact wheel is the channel-safe replacement operation and
    # prevents an unpinned registry artifact from entering candidate evidence.
    install = _run(install_command, cwd=project_root, env=environment)

    if install.return_code != 0:
        missing = _missing_observation("install command did not complete successfully")
        return _execution(
            channel=channel,
            phase=phase,
            install=install,
            version=missing,
            doctor=missing,
            provenance=missing,
        )

    python = _python_path(environment_root)
    version_command = _run((aidd, "--version"), cwd=project_root, env=environment)
    doctor_command = _run((aidd, "doctor"), cwd=project_root, env=environment)
    provenance_command = _run(
        (python, "-c", _provenance_script()), cwd=project_root, env=environment
    )
    return _execution(
        channel=channel,
        phase=phase,
        install=install,
        version=version_command,
        doctor=doctor_command,
        provenance=provenance_command,
    )


def _execution_success(
    execution: ChannelExecution,
    *,
    project_version: str,
    wheel_sha256: str,
) -> bool:
    return (
        execution.channel in CHANNELS
        and execution.phase in PHASES
        and execution.install_return_code == 0
        and execution.version_return_code == 0
        and execution.doctor_return_code == 0
        and execution.provenance_return_code == 0
        and execution.version_output.splitlines() == [f"aidd {project_version}"]
        and f"Version {project_version}" in execution.doctor_output.splitlines()
        and execution.provenance_output == f"sha256={wheel_sha256}"
    )


def build_installed_channel_verification(
    manifest_path: Path,
    wheel_path: Path,
    executions: Sequence[ChannelExecution],
) -> InstalledChannelVerification:
    """Build and hash a fail-closed exact-wheel channel report."""

    try:
        manifest = read_candidate_manifest(manifest_path)
    except (CandidateManifestError, OSError, ValueError) as exc:
        raise ChannelVerificationError(f"Unable to read candidate manifest: {exc}") from exc
    wheel_sha256, wheel_size = _wheel_identity(wheel_path)
    if (wheel_sha256, wheel_size) != (manifest.wheel.sha256, manifest.wheel.size_bytes):
        raise ChannelVerificationError("Candidate wheel digest or size does not match manifest.")
    expected = tuple((channel, phase) for channel in CHANNELS for phase in PHASES)
    actual = tuple((execution.channel, execution.phase) for execution in executions)
    if actual != expected:
        raise ChannelVerificationError(
            f"Installed channel execution mismatch: expected={expected}, actual={actual}"
        )
    for execution in executions:
        for value, label in (
            (execution.install_stdout_sha256, "install_stdout_sha256"),
            (execution.install_stderr_sha256, "install_stderr_sha256"),
            (execution.version_stdout_sha256, "version_stdout_sha256"),
            (execution.version_stderr_sha256, "version_stderr_sha256"),
            (execution.doctor_stdout_sha256, "doctor_stdout_sha256"),
            (execution.doctor_stderr_sha256, "doctor_stderr_sha256"),
            (execution.provenance_stdout_sha256, "provenance_stdout_sha256"),
            (execution.provenance_stderr_sha256, "provenance_stderr_sha256"),
        ):
            _validate_sha256(value, label=f"channel execution {label}")
    successful = all(
        _execution_success(
            execution,
            project_version=manifest.project_version,
            wheel_sha256=wheel_sha256,
        )
        for execution in executions
    )
    provisional = InstalledChannelVerification(
        candidate_manifest_sha256=manifest.manifest_sha256,
        project_version=manifest.project_version,
        source_commit=manifest.source_commit,
        source_tree=manifest.source_tree,
        wheel_sha256=wheel_sha256,
        wheel_size_bytes=wheel_size,
        executions=tuple(executions),
        success=successful,
        verification_sha256="",
    )
    return InstalledChannelVerification(
        candidate_manifest_sha256=provisional.candidate_manifest_sha256,
        project_version=provisional.project_version,
        source_commit=provisional.source_commit,
        source_tree=provisional.source_tree,
        wheel_sha256=provisional.wheel_sha256,
        wheel_size_bytes=provisional.wheel_size_bytes,
        executions=provisional.executions,
        success=provisional.success,
        verification_sha256=_canonical_digest(provisional._payload()),
    )


def run_installed_channel_verification(
    *,
    project_root: Path,
    manifest_path: Path,
    wheel_path: Path,
) -> InstalledChannelVerification:
    """Run clean-install and exact-wheel replacement checks for both channels."""

    root = project_root.resolve(strict=True)
    manifest = validate_candidate_manifest(
        manifest_path,
        project_root=root,
        wheel_path=wheel_path,
    )
    wheel_sha256, _wheel_size = _wheel_identity(wheel_path)
    executions: list[ChannelExecution] = []
    with tempfile.TemporaryDirectory(prefix="aidd-channel-verification-") as temporary:
        temporary_root = Path(temporary)
        for channel in CHANNELS:
            channel_root = temporary_root / channel
            channel_root.mkdir()
            for phase in PHASES:
                executions.append(
                    _run_channel(
                        channel=channel,
                        phase=phase,
                        project_root=root,
                        wheel_path=wheel_path,
                        version=manifest.project_version,
                        wheel_sha256=wheel_sha256,
                        channel_root=channel_root,
                    )
                )
    return build_installed_channel_verification(manifest_path, wheel_path, executions)


def _parse_execution(raw: object) -> ChannelExecution:
    if not isinstance(raw, dict):
        raise ChannelVerificationError("channel execution entries must be objects.")

    def text(key: str) -> str:
        value = raw.get(key)
        if not isinstance(value, str):
            raise ChannelVerificationError(f"channel execution {key} must be a string.")
        return value

    def integer(key: str) -> int:
        value = raw.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ChannelVerificationError(f"channel execution {key} must be an integer.")
        return value

    return ChannelExecution(
        channel=text("channel"),
        phase=text("phase"),
        install_return_code=integer("install_return_code"),
        install_stdout_sha256=text("install_stdout_sha256"),
        install_stderr_sha256=text("install_stderr_sha256"),
        version_return_code=integer("version_return_code"),
        version_output=text("version_output"),
        version_stdout_sha256=text("version_stdout_sha256"),
        version_stderr_sha256=text("version_stderr_sha256"),
        doctor_return_code=integer("doctor_return_code"),
        doctor_output=text("doctor_output"),
        doctor_stdout_sha256=text("doctor_stdout_sha256"),
        doctor_stderr_sha256=text("doctor_stderr_sha256"),
        provenance_return_code=integer("provenance_return_code"),
        provenance_output=text("provenance_output"),
        provenance_stdout_sha256=text("provenance_stdout_sha256"),
        provenance_stderr_sha256=text("provenance_stderr_sha256"),
    )


def read_installed_channel_verification(
    path: Path,
    *,
    manifest_path: Path | None = None,
) -> InstalledChannelVerification:
    """Read and integrity-check a channel report without executing tools."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ChannelVerificationError(
            f"Installed channel verification is missing or invalid: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise ChannelVerificationError("Installed channel verification must be an object.")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ChannelVerificationError("Unsupported installed channel verification schema.")
    raw_executions = payload.get("executions")
    if not isinstance(raw_executions, list):
        raise ChannelVerificationError("channel verification executions must be a list.")
    executions = tuple(_parse_execution(raw) for raw in raw_executions)
    source_commit = _validate_git_object(
        str(payload.get("source_commit", "")), label="verification source_commit"
    )
    source_tree = _validate_git_object(
        str(payload.get("source_tree", "")), label="verification source_tree"
    )
    manifest_digest = _validate_sha256(
        str(payload.get("candidate_manifest_sha256", "")),
        label="verification candidate_manifest_sha256",
    )
    wheel_sha256 = _validate_sha256(
        str(payload.get("wheel_sha256", "")), label="verification wheel_sha256"
    )
    verification_digest = _validate_sha256(
        str(payload.get("verification_sha256", "")), label="verification verification_sha256"
    )
    project_version = payload.get("project_version")
    wheel_size = payload.get("wheel_size_bytes")
    success = payload.get("success")
    if not isinstance(project_version, str) or not project_version.strip():
        raise ChannelVerificationError("verification project_version is invalid.")
    if not isinstance(wheel_size, int) or isinstance(wheel_size, bool) or wheel_size <= 0:
        raise ChannelVerificationError("verification wheel_size_bytes is invalid.")
    if not isinstance(success, bool):
        raise ChannelVerificationError("verification success must be a boolean.")
    record = InstalledChannelVerification(
        candidate_manifest_sha256=manifest_digest,
        project_version=project_version.strip(),
        source_commit=source_commit,
        source_tree=source_tree,
        wheel_sha256=wheel_sha256,
        wheel_size_bytes=wheel_size,
        executions=executions,
        success=success,
        verification_sha256=verification_digest,
    )
    expected = tuple((channel, phase) for channel in CHANNELS for phase in PHASES)
    if tuple((item.channel, item.phase) for item in executions) != expected:
        raise ChannelVerificationError("verification execution order is invalid.")
    for item in executions:
        for value, label in (
            (item.install_stdout_sha256, "install_stdout_sha256"),
            (item.install_stderr_sha256, "install_stderr_sha256"),
            (item.version_stdout_sha256, "version_stdout_sha256"),
            (item.version_stderr_sha256, "version_stderr_sha256"),
            (item.doctor_stdout_sha256, "doctor_stdout_sha256"),
            (item.doctor_stderr_sha256, "doctor_stderr_sha256"),
            (item.provenance_stdout_sha256, "provenance_stdout_sha256"),
            (item.provenance_stderr_sha256, "provenance_stderr_sha256"),
        ):
            _validate_sha256(value, label=f"verification {label}")
    expected_success = all(
        _execution_success(item, project_version=record.project_version, wheel_sha256=wheel_sha256)
        for item in executions
    )
    if expected_success != success:
        raise ChannelVerificationError("verification success does not match channel results.")
    if verification_digest != _canonical_digest(record._payload()):
        raise ChannelVerificationError("Installed channel verification digest does not match.")
    if manifest_path is not None:
        manifest = read_candidate_manifest(manifest_path)
        if (
            manifest.manifest_sha256 != manifest_digest
            or manifest.project_version != record.project_version
            or manifest.source_commit != source_commit
            or manifest.source_tree != source_tree
            or manifest.wheel.sha256 != wheel_sha256
            or manifest.wheel.size_bytes != wheel_size
        ):
            raise ChannelVerificationError("Installed channel verification identity mismatch.")
    return record


def write_installed_channel_verification(
    record: InstalledChannelVerification,
    output_path: Path,
) -> Path:
    """Write a report atomically and refuse accidental overwrite."""

    destination = output_path.resolve(strict=False)
    if destination.exists() or destination.is_symlink():
        raise ChannelVerificationError(f"Refusing to overwrite existing report: {destination}")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp")
        temporary.write_text(record.to_json(), encoding="utf-8")
        temporary.replace(destination)
    except OSError as exc:
        raise ChannelVerificationError(
            f"Unable to write verification report: {destination}"
        ) from exc
    return destination


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(tuple(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        record = run_installed_channel_verification(
            project_root=args.project_root,
            manifest_path=args.manifest,
            wheel_path=args.wheel,
        )
        output = write_installed_channel_verification(record, args.output)
    except (CandidateManifestError, ChannelVerificationError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "success": False}, sort_keys=True))
        return 1
    print(
        json.dumps({"success": record.success, "verification": output.as_posix()}, sort_keys=True)
    )
    return 0 if record.success else 1


__all__ = [
    "CHANNELS",
    "ChannelExecution",
    "ChannelVerificationError",
    "InstalledChannelVerification",
    "PHASES",
    "SCHEMA_VERSION",
    "build_installed_channel_verification",
    "main",
    "read_installed_channel_verification",
    "run_installed_channel_verification",
    "write_installed_channel_verification",
]


if __name__ == "__main__":
    raise SystemExit(main())
