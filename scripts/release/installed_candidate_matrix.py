"""Run deterministic scenarios through an exact installed candidate wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from aidd.harness.ci_scenario_lane import discover_ci_scenarios
from scripts.release.candidate_manifest import (
    CandidateManifestError,
    read_candidate_manifest,
    validate_candidate_manifest,
)

MATRIX_SCHEMA_VERSION = 1
DEFAULT_OUTPUT_PATH = Path(".aidd/installed-candidate-matrix.json")
DEFAULT_WORKSPACE_ROOT = Path(".aidd/installed-candidate-workspace")
INSTALL_TIMEOUT_SECONDS = 900.0
SCENARIO_TIMEOUT_SECONDS = 900.0
_GIT_OBJECT_RE = r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$"
_GIT_OBJECT_PATTERN = re.compile(_GIT_OBJECT_RE)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class CandidateMatrixError(ValueError):
    """Raised when an installed candidate matrix cannot be executed or verified."""


@dataclass(frozen=True, slots=True)
class ScenarioExecution:
    scenario_id: str
    path: str
    return_code: int
    bundle_path: str
    stdout_sha256: str
    stderr_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "bundle_path": self.bundle_path,
            "path": self.path,
            "return_code": self.return_code,
            "scenario_id": self.scenario_id,
            "stderr_sha256": self.stderr_sha256,
            "stdout_sha256": self.stdout_sha256,
        }


@dataclass(frozen=True, slots=True)
class InstalledCandidateMatrix:
    candidate_manifest_sha256: str
    project_version: str
    source_commit: str
    source_tree: str
    wheel_sha256: str
    wheel_size_bytes: int
    executions: tuple[ScenarioExecution, ...]
    success: bool
    matrix_sha256: str
    schema_version: int = MATRIX_SCHEMA_VERSION

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
        return {**self._payload(), "matrix_sha256": self.matrix_sha256}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _canonical_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise CandidateMatrixError(f"Unable to hash wheel {path}: {exc}") from exc
    return digest.hexdigest()


def _wheel_identity(path: Path) -> tuple[str, int]:
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CandidateMatrixError(f"Candidate wheel is not readable: {path}") from exc
    if not resolved.is_file() or not resolved.name.lower().endswith(".whl"):
        raise CandidateMatrixError("Candidate wheel must be a regular .whl file.")
    size = resolved.stat().st_size
    if size <= 0:
        raise CandidateMatrixError("Candidate wheel must not be empty.")
    return _sha256_file(resolved), size


def _digest_output(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_sha256(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _SHA256_PATTERN.fullmatch(normalized) is None:
        raise CandidateMatrixError(f"{label} must be a lowercase SHA-256 digest.")
    return normalized


def _validate_git_object(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _GIT_OBJECT_PATTERN.fullmatch(normalized) is None:
        raise CandidateMatrixError(f"{label} must be a full hexadecimal Git object id.")
    return normalized


def _extract_bundle_path(output: str) -> str:
    marker = "Evidence bundle:"
    for line in output.splitlines():
        if line.startswith(marker):
            return line.removeprefix(marker).strip()
    return ""


def _python_in_venv(venv_root: Path) -> Path:
    candidate = venv_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not candidate.is_file():
        raise CandidateMatrixError(f"Virtualenv Python executable is missing: {candidate}")
    return candidate


def _aidd_in_venv(venv_root: Path) -> Path:
    candidate = venv_root / ("Scripts/aidd.exe" if os.name == "nt" else "bin/aidd")
    if not candidate.is_file():
        raise CandidateMatrixError(f"Installed aidd executable is missing: {candidate}")
    return candidate


def _run(
    argv: Sequence[str | Path],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            tuple(str(item) for item in argv),
            cwd=cwd,
            env=None if env is None else dict(env),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CandidateMatrixError(f"Candidate command failed: {exc}") from exc


def _assert_empty_workspace(workspace_root: Path) -> None:
    if workspace_root.exists():
        if not workspace_root.is_dir():
            raise CandidateMatrixError(f"Workspace root must be a directory: {workspace_root}")
        if any(workspace_root.iterdir()):
            raise CandidateMatrixError(
                "Workspace root must be empty to preserve self-contained evidence: "
                f"{workspace_root}"
            )
    else:
        workspace_root.mkdir(parents=True)


def build_installed_candidate_matrix(
    manifest_path: Path,
    wheel_path: Path,
    executions: Sequence[ScenarioExecution],
) -> InstalledCandidateMatrix:
    """Build a hashed report from installed scenario executions."""

    try:
        manifest = read_candidate_manifest(manifest_path)
    except (CandidateManifestError, OSError, ValueError) as exc:
        raise CandidateMatrixError(f"Unable to read candidate manifest: {exc}") from exc
    wheel_sha256, wheel_size = _wheel_identity(wheel_path)
    if (wheel_sha256, wheel_size) != (manifest.wheel.sha256, manifest.wheel.size_bytes):
        raise CandidateMatrixError("Candidate wheel digest or size does not match manifest.")
    expected = tuple(item.scenario_id for item in manifest.scenario_inventory)
    actual = tuple(execution.scenario_id for execution in executions)
    if len(set(actual)) != len(actual):
        raise CandidateMatrixError("Installed scenario executions contain duplicate ids.")
    if actual != expected:
        raise CandidateMatrixError(
            f"Installed scenario execution mismatch: expected={expected}, actual={actual}"
        )
    expected_paths = tuple(item.path for item in manifest.scenario_inventory)
    actual_paths = tuple(execution.path for execution in executions)
    if actual_paths != expected_paths:
        raise CandidateMatrixError(
            f"Installed scenario path mismatch: expected={expected_paths}, actual={actual_paths}"
        )
    for execution in executions:
        _validate_sha256(execution.stdout_sha256, label="scenario stdout_sha256")
        _validate_sha256(execution.stderr_sha256, label="scenario stderr_sha256")
    successful = all(
        execution.return_code == 0
        and bool(execution.bundle_path)
        and Path(execution.bundle_path).is_dir()
        for execution in executions
    )
    provisional = InstalledCandidateMatrix(
        candidate_manifest_sha256=manifest.manifest_sha256,
        project_version=manifest.project_version,
        source_commit=manifest.source_commit,
        source_tree=manifest.source_tree,
        wheel_sha256=wheel_sha256,
        wheel_size_bytes=wheel_size,
        executions=tuple(executions),
        success=successful,
        matrix_sha256="",
    )
    return InstalledCandidateMatrix(
        candidate_manifest_sha256=provisional.candidate_manifest_sha256,
        project_version=provisional.project_version,
        source_commit=provisional.source_commit,
        source_tree=provisional.source_tree,
        wheel_sha256=provisional.wheel_sha256,
        wheel_size_bytes=provisional.wheel_size_bytes,
        executions=provisional.executions,
        success=provisional.success,
        matrix_sha256=_canonical_digest(provisional._payload()),
    )


def run_installed_candidate_matrix(
    *,
    project_root: Path,
    manifest_path: Path,
    wheel_path: Path,
    scenario_root: Path,
    workspace_root: Path,
) -> InstalledCandidateMatrix:
    """Install the exact wheel and execute every CI-marked deterministic scenario."""

    root = project_root.resolve(strict=True)
    manifest = validate_candidate_manifest(
        manifest_path,
        project_root=root,
        wheel_path=wheel_path,
        scenario_root=scenario_root,
    )
    resolved_scenarios = discover_ci_scenarios(scenario_root.resolve(strict=True))
    if tuple(item.scenario_id for item in resolved_scenarios) != tuple(
        item.scenario_id for item in manifest.scenario_inventory
    ):
        raise CandidateMatrixError("Scenario inventory changed after candidate validation.")
    workspace = workspace_root.resolve(strict=False)
    _assert_empty_workspace(workspace)
    with tempfile.TemporaryDirectory(prefix="aidd-candidate-venv-") as temporary:
        venv_root = Path(temporary) / "venv"
        created = _run(
            (sys.executable, "-m", "venv", "--system-site-packages", venv_root),
            cwd=root,
            timeout=INSTALL_TIMEOUT_SECONDS,
        )
        if created.returncode != 0:
            raise CandidateMatrixError(
                f"Unable to create isolated candidate environment: {created.stderr.strip()}"
            )
        installed_python = _python_in_venv(venv_root)
        installed = _run(
            (
                installed_python,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--force-reinstall",
                wheel_path.resolve(strict=True),
            ),
            cwd=root,
            timeout=INSTALL_TIMEOUT_SECONDS,
        )
        if installed.returncode != 0:
            raise CandidateMatrixError(
                f"Unable to install exact candidate wheel: {installed.stderr.strip()}"
            )
        version_check = _run(
            (
                installed_python,
                "-c",
                "import importlib.metadata as m; print(m.version('ai-driven-dev-v2'))",
            ),
            cwd=root,
            timeout=60.0,
        )
        if (
            version_check.returncode != 0
            or version_check.stdout.strip() != manifest.project_version
        ):
            raise CandidateMatrixError(
                "Installed candidate version does not match manifest: "
                f"{version_check.stdout.strip() or version_check.stderr.strip()}"
            )
        aidd = _aidd_in_venv(venv_root)
        executions: list[ScenarioExecution] = []
        clean_env = dict(os.environ)
        clean_env.pop("PYTHONPATH", None)
        for scenario in resolved_scenarios:
            completed = _run(
                (aidd, "eval", "execute", scenario.path, "--root", workspace),
                cwd=root,
                env=clean_env,
                timeout=SCENARIO_TIMEOUT_SECONDS,
            )
            combined = f"{completed.stdout}\n{completed.stderr}"
            bundle_path = _extract_bundle_path(combined)
            if bundle_path and not Path(bundle_path).is_dir():
                bundle_path = ""
            executions.append(
                ScenarioExecution(
                    scenario_id=scenario.scenario_id,
                    path=scenario.path.as_posix(),
                    return_code=completed.returncode,
                    bundle_path=bundle_path,
                    stdout_sha256=_digest_output(completed.stdout),
                    stderr_sha256=_digest_output(completed.stderr),
                )
            )
    return build_installed_candidate_matrix(manifest_path, wheel_path, executions)


def read_installed_candidate_matrix(
    path: Path,
    *,
    manifest_path: Path | None = None,
) -> InstalledCandidateMatrix:
    """Read and integrity-check a matrix report without executing anything."""

    try:
        raw_payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateMatrixError(
            f"Installed candidate matrix is missing or invalid: {path}"
        ) from exc
    if not isinstance(raw_payload, dict):
        raise CandidateMatrixError("Installed candidate matrix must be a JSON object.")
    if raw_payload.get("schema_version") != MATRIX_SCHEMA_VERSION:
        raise CandidateMatrixError("Unsupported installed candidate matrix schema.")
    raw_executions = raw_payload.get("executions")
    if not isinstance(raw_executions, list) or not raw_executions:
        raise CandidateMatrixError("candidate matrix executions must be a non-empty list.")
    executions: list[ScenarioExecution] = []
    for raw in raw_executions:
        if not isinstance(raw, dict):
            raise CandidateMatrixError("candidate matrix execution entries must be objects.")
        scenario_id = raw.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise CandidateMatrixError("candidate matrix scenario_id must be a non-empty string.")
        path_value = raw.get("path")
        bundle_path = raw.get("bundle_path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise CandidateMatrixError("candidate matrix path must be a non-empty string.")
        if not isinstance(bundle_path, str):
            raise CandidateMatrixError("candidate matrix bundle_path must be a string.")
        return_code = raw.get("return_code")
        if not isinstance(return_code, int) or isinstance(return_code, bool):
            raise CandidateMatrixError("candidate matrix return_code must be an integer.")
        stdout_sha256 = raw.get("stdout_sha256")
        stderr_sha256 = raw.get("stderr_sha256")
        if not isinstance(stdout_sha256, str):
            raise CandidateMatrixError("candidate matrix stdout_sha256 is invalid.")
        if not isinstance(stderr_sha256, str):
            raise CandidateMatrixError("candidate matrix stderr_sha256 is invalid.")
        executions.append(
            ScenarioExecution(
                scenario_id=scenario_id.strip(),
                path=path_value.strip(),
                return_code=return_code,
                bundle_path=bundle_path.strip(),
                stdout_sha256=_validate_sha256(
                    stdout_sha256, label="candidate matrix stdout_sha256"
                ),
                stderr_sha256=_validate_sha256(
                    stderr_sha256, label="candidate matrix stderr_sha256"
                ),
            )
        )
    source_commit = _validate_git_object(
        str(raw_payload.get("source_commit", "")), label="candidate matrix source_commit"
    )
    source_tree = _validate_git_object(
        str(raw_payload.get("source_tree", "")), label="candidate matrix source_tree"
    )
    manifest_digest = _validate_sha256(
        str(raw_payload.get("candidate_manifest_sha256", "")),
        label="candidate matrix candidate_manifest_sha256",
    )
    project_version = raw_payload.get("project_version")
    wheel_sha256 = _validate_sha256(
        str(raw_payload.get("wheel_sha256", "")), label="candidate matrix wheel_sha256"
    )
    wheel_size = raw_payload.get("wheel_size_bytes")
    success = raw_payload.get("success")
    matrix_sha256 = _validate_sha256(
        str(raw_payload.get("matrix_sha256", "")), label="candidate matrix matrix_sha256"
    )
    if not isinstance(project_version, str) or not project_version.strip():
        raise CandidateMatrixError("candidate matrix project_version is invalid.")
    if not isinstance(wheel_size, int) or isinstance(wheel_size, bool) or wheel_size <= 0:
        raise CandidateMatrixError("candidate matrix wheel_size_bytes is invalid.")
    if not isinstance(success, bool):
        raise CandidateMatrixError("candidate matrix success must be a boolean.")
    provisional = InstalledCandidateMatrix(
        candidate_manifest_sha256=manifest_digest,
        project_version=project_version.strip(),
        source_commit=source_commit,
        source_tree=source_tree,
        wheel_sha256=wheel_sha256,
        wheel_size_bytes=wheel_size,
        executions=tuple(executions),
        success=success,
        matrix_sha256=matrix_sha256,
    )
    expected_success = all(
        execution.return_code == 0 and bool(execution.bundle_path)
        for execution in provisional.executions
    )
    if expected_success != success:
        raise CandidateMatrixError("candidate matrix success does not match execution results.")
    if matrix_sha256 != _canonical_digest(provisional._payload()):
        raise CandidateMatrixError("Installed candidate matrix digest does not match contents.")
    if manifest_path is not None:
        manifest = read_candidate_manifest(manifest_path)
        if (
            manifest.manifest_sha256 != manifest_digest
            or manifest.project_version != provisional.project_version
            or manifest.source_commit != source_commit
            or manifest.source_tree != source_tree
            or manifest.wheel.sha256 != wheel_sha256
            or manifest.wheel.size_bytes != wheel_size
        ):
            raise CandidateMatrixError(
                "Installed candidate matrix identity does not match manifest."
            )
        expected_ids = tuple(item.scenario_id for item in manifest.scenario_inventory)
        if tuple(execution.scenario_id for execution in executions) != expected_ids:
            raise CandidateMatrixError(
                "Installed candidate matrix scenarios do not match manifest."
            )
    return provisional


def write_installed_candidate_matrix(record: InstalledCandidateMatrix, output_path: Path) -> Path:
    """Write a matrix report atomically, refusing accidental overwrite."""

    destination = output_path.resolve(strict=False)
    if destination.exists() or destination.is_symlink():
        raise CandidateMatrixError(f"Refusing to overwrite existing matrix report: {destination}")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp")
        temporary.write_text(record.to_json(), encoding="utf-8")
        temporary.replace(destination)
    except OSError as exc:
        raise CandidateMatrixError(f"Unable to write matrix report: {destination}") from exc
    return destination


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--scenario-root", type=Path, default=Path("harness/scenarios"))
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args(tuple(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        record = run_installed_candidate_matrix(
            project_root=args.project_root,
            manifest_path=args.manifest,
            wheel_path=args.wheel,
            scenario_root=args.scenario_root,
            workspace_root=args.workspace_root,
        )
        output = write_installed_candidate_matrix(record, args.output)
    except (CandidateMatrixError, CandidateManifestError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "success": False}, sort_keys=True))
        return 1
    print(json.dumps({"matrix": output.as_posix(), "success": record.success}, sort_keys=True))
    return 0 if record.success else 1


__all__ = [
    "CandidateMatrixError",
    "DEFAULT_OUTPUT_PATH",
    "DEFAULT_WORKSPACE_ROOT",
    "InstalledCandidateMatrix",
    "MATRIX_SCHEMA_VERSION",
    "ScenarioExecution",
    "build_installed_candidate_matrix",
    "main",
    "read_installed_candidate_matrix",
    "run_installed_candidate_matrix",
    "write_installed_candidate_matrix",
]


if __name__ == "__main__":
    raise SystemExit(main())
