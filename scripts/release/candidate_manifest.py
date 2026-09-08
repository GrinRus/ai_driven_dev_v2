"""Freeze and validate the exact identity of an AIDD release candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from aidd.harness.ci_scenario_lane import discover_ci_scenarios
from aidd.harness.scenarios import load_scenario

CANDIDATE_MANIFEST_SCHEMA_VERSION = 1
DEFAULT_SCENARIO_ROOT = Path("harness/scenarios")
DEFAULT_OUTPUT_PATH = Path(".aidd/candidate-manifest.json")
DEFAULT_VERIFICATION_COMMANDS = (
    "uv sync --locked --extra dev",
    "uv run --extra dev ruff check .",
    "uv run --extra dev python -m mypy src scripts",
    "uv run --extra dev pytest -q",
)
_GIT_OBJECT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CandidateManifestError(ValueError):
    """Raised when a candidate cannot be frozen or verified."""


@dataclass(frozen=True, slots=True)
class CandidateArtifact:
    path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "sha256": self.sha256, "size_bytes": self.size_bytes}


@dataclass(frozen=True, slots=True)
class CandidateScenario:
    scenario_id: str
    path: str
    sha256: str
    size_bytes: int
    scenario_class: str
    runtime_targets: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "runtime_targets": list(self.runtime_targets),
            "scenario_class": self.scenario_class,
            "scenario_id": self.scenario_id,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class CandidateManifest:
    project_name: str
    project_version: str
    source_branch: str
    source_commit: str
    source_tree: str
    scenario_root: str
    scenario_inventory: tuple[CandidateScenario, ...]
    wheel: CandidateArtifact
    verification_commands: tuple[str, ...]
    manifest_sha256: str
    schema_version: int = CANDIDATE_MANIFEST_SCHEMA_VERSION

    def _payload(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "project_version": self.project_version,
            "schema_version": self.schema_version,
            "scenario_inventory": [item.to_dict() for item in self.scenario_inventory],
            "scenario_root": self.scenario_root,
            "source_branch": self.source_branch,
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "verification_commands": list(self.verification_commands),
            "wheel": self.wheel.to_dict(),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._payload(), "manifest_sha256": self.manifest_sha256}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _canonical_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_git_object(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _GIT_OBJECT_RE.fullmatch(normalized) is None:
        raise CandidateManifestError(f"{label} must be a full hexadecimal Git object id.")
    return normalized


def _validate_sha256(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _SHA256_RE.fullmatch(normalized) is None:
        raise CandidateManifestError(f"{label} must be a lowercase SHA-256 digest.")
    return normalized


def _run_git(project_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CandidateManifestError(f"Git command failed: {' '.join(arguments)}: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise CandidateManifestError(f"Git command failed: {' '.join(arguments)}: {detail}")
    return completed.stdout.strip()


def _assert_clean_worktree(project_root: Path) -> None:
    status = _run_git(project_root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise CandidateManifestError(
            "Candidate source checkout is dirty; commit or remove changes before freezing."
        )


def _project_metadata(project_root: Path) -> tuple[str, str]:
    try:
        with (project_root / "pyproject.toml").open("rb") as stream:
            payload = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CandidateManifestError(f"Unable to read pyproject.toml: {exc}") from exc
    project = payload.get("project")
    if not isinstance(project, dict):
        raise CandidateManifestError("pyproject.toml must contain a [project] table.")
    name = project.get("name")
    version = project.get("version")
    if not isinstance(name, str) or not name.strip():
        raise CandidateManifestError("pyproject.toml project.name must be non-empty.")
    if not isinstance(version, str) or not version.strip():
        raise CandidateManifestError("pyproject.toml project.version must be non-empty.")
    return name.strip(), version.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise CandidateManifestError(f"Unable to hash artifact {path}: {exc}") from exc
    return digest.hexdigest()


def _display_path(project_root: Path, path: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_input_path(project_root: Path, path: Path) -> Path:
    candidate = path if path.is_absolute() else project_root / path
    return candidate.resolve(strict=False)


def _artifact(project_root: Path, path: Path, *, label: str) -> CandidateArtifact:
    try:
        resolved = _resolve_input_path(project_root, path).resolve(strict=True)
    except OSError as exc:
        raise CandidateManifestError(f"{label} is not readable: {path}") from exc
    if not resolved.is_file():
        raise CandidateManifestError(f"{label} must be a regular file: {path}")
    size = resolved.stat().st_size
    if size <= 0:
        raise CandidateManifestError(f"{label} must not be empty: {path}")
    return CandidateArtifact(
        path=_display_path(project_root, resolved),
        sha256=_sha256(resolved),
        size_bytes=size,
    )


def _scenario_inventory(project_root: Path, scenario_root: Path) -> tuple[CandidateScenario, ...]:
    try:
        resolved_root = _resolve_input_path(project_root, scenario_root).resolve(strict=True)
    except OSError as exc:
        raise CandidateManifestError(f"Scenario root is not readable: {scenario_root}") from exc
    if not resolved_root.is_dir():
        raise CandidateManifestError(f"Scenario root must be a directory: {scenario_root}")
    try:
        manifests = discover_ci_scenarios(resolved_root)
    except (OSError, ValueError) as exc:
        raise CandidateManifestError(f"Unable to discover CI scenarios: {exc}") from exc
    inventory: list[CandidateScenario] = []
    for item in manifests:
        scenario_path = item.path.resolve(strict=True)
        try:
            scenario = load_scenario(scenario_path)
        except (OSError, ValueError) as exc:
            raise CandidateManifestError(
                f"Unable to load CI scenario {scenario_path}: {exc}"
            ) from exc
        artifact = _artifact(project_root, scenario_path, label="Scenario manifest")
        inventory.append(
            CandidateScenario(
                scenario_id=item.scenario_id,
                path=artifact.path,
                sha256=artifact.sha256,
                size_bytes=artifact.size_bytes,
                scenario_class=scenario.scenario_class,
                runtime_targets=tuple(sorted(scenario.runtime_targets)),
            )
        )
    return tuple(inventory)


def _normalize_commands(commands: Sequence[str] | None) -> tuple[str, ...]:
    source = DEFAULT_VERIFICATION_COMMANDS if commands is None else commands
    values = tuple(command.strip() for command in source)
    if not values or any(not command for command in values):
        raise CandidateManifestError("verification_commands must contain non-empty commands.")
    if len(set(values)) != len(values):
        raise CandidateManifestError("verification_commands must not contain duplicates.")
    return values


def freeze_candidate(
    *,
    project_root: Path,
    wheel_path: Path,
    scenario_root: Path = DEFAULT_SCENARIO_ROOT,
    verification_commands: Sequence[str] | None = None,
    expected_version: str | None = None,
) -> CandidateManifest:
    """Capture a deterministic candidate manifest from a clean checkout."""

    root = project_root.resolve(strict=True)
    if not root.is_dir():
        raise CandidateManifestError(f"Project root must be a directory: {project_root}")
    _assert_clean_worktree(root)
    project_name, project_version = _project_metadata(root)
    if expected_version is not None and project_version != expected_version.strip():
        raise CandidateManifestError(
            f"Candidate version mismatch: source={project_version} expected={expected_version}."
        )
    source_commit = _validate_git_object(_run_git(root, "rev-parse", "HEAD"), label="source_commit")
    source_tree = _validate_git_object(
        _run_git(root, "rev-parse", "HEAD^{tree}"), label="source_tree"
    )
    source_branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if not source_branch:
        raise CandidateManifestError("Candidate source branch cannot be empty.")
    wheel = _artifact(root, wheel_path, label="Wheel")
    if not wheel.path.lower().endswith(".whl"):
        raise CandidateManifestError("Wheel artifact must have a .whl suffix.")
    inventory = _scenario_inventory(root, scenario_root)
    if not inventory:
        raise CandidateManifestError("Candidate scenario inventory cannot be empty.")
    provisional = CandidateManifest(
        project_name=project_name,
        project_version=project_version,
        source_branch=source_branch,
        source_commit=source_commit,
        source_tree=source_tree,
        scenario_root=_display_path(root, _resolve_input_path(root, scenario_root)),
        scenario_inventory=inventory,
        wheel=wheel,
        verification_commands=_normalize_commands(verification_commands),
        manifest_sha256="",
    )
    return replace(provisional, manifest_sha256=_canonical_digest(provisional._payload()))


def _mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise CandidateManifestError(f"{label} must be an object.")
    return value


def _string(payload: Mapping[str, Any], key: str, *, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CandidateManifestError(f"{label}.{key} must be a non-empty string.")
    return value.strip()


def _parse_artifact(raw: Any, *, label: str) -> CandidateArtifact:
    payload = _mapping(raw, label=label)
    path = _string(payload, "path", label=label)
    if Path(path).is_absolute() is False and ".." in Path(path).parts:
        raise CandidateManifestError(f"{label}.path must not traverse parent directories.")
    sha256 = _validate_sha256(_string(payload, "sha256", label=label), label=f"{label}.sha256")
    size = payload.get("size_bytes")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise CandidateManifestError(f"{label}.size_bytes must be a positive integer.")
    return CandidateArtifact(path=path, sha256=sha256, size_bytes=size)


def _parse_scenario(raw: Any) -> CandidateScenario:
    payload = _mapping(raw, label="scenario_inventory entry")
    scenario_id = _string(payload, "scenario_id", label="scenario_inventory entry")
    artifact = _parse_artifact(payload, label="scenario_inventory entry")
    scenario_class = _string(payload, "scenario_class", label="scenario_inventory entry")
    raw_targets = payload.get("runtime_targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise CandidateManifestError("scenario_inventory entry.runtime_targets must be non-empty.")
    targets = tuple(
        sorted({item.strip() for item in raw_targets if isinstance(item, str) and item.strip()})
    )
    if len(targets) != len(raw_targets):
        raise CandidateManifestError(
            "scenario_inventory entry.runtime_targets must be unique strings."
        )
    return CandidateScenario(
        scenario_id=scenario_id,
        path=artifact.path,
        sha256=artifact.sha256,
        size_bytes=artifact.size_bytes,
        scenario_class=scenario_class,
        runtime_targets=targets,
    )


def read_candidate_manifest(path: Path) -> CandidateManifest:
    """Read and integrity-check a candidate manifest without touching Git."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateManifestError(f"Candidate manifest is missing or invalid: {path}") from exc
    raw = _mapping(payload, label="candidate manifest")
    if raw.get("schema_version") != CANDIDATE_MANIFEST_SCHEMA_VERSION:
        raise CandidateManifestError("Unsupported candidate manifest schema.")
    raw_inventory = raw.get("scenario_inventory")
    if not isinstance(raw_inventory, list) or not raw_inventory:
        raise CandidateManifestError("candidate manifest scenario_inventory must be non-empty.")
    inventory = tuple(_parse_scenario(item) for item in raw_inventory)
    if len({item.scenario_id for item in inventory}) != len(inventory):
        raise CandidateManifestError("candidate manifest scenario ids must be unique.")
    raw_commands = raw.get("verification_commands")
    if not isinstance(raw_commands, list):
        raise CandidateManifestError("candidate manifest verification_commands must be a list.")
    if not all(isinstance(item, str) for item in raw_commands):
        raise CandidateManifestError("candidate manifest verification_commands must be strings.")
    commands = _normalize_commands(tuple(item for item in raw_commands if isinstance(item, str)))
    manifest = CandidateManifest(
        project_name=_string(raw, "project_name", label="candidate manifest"),
        project_version=_string(raw, "project_version", label="candidate manifest"),
        source_branch=_string(raw, "source_branch", label="candidate manifest"),
        source_commit=_validate_git_object(
            _string(raw, "source_commit", label="candidate manifest"), label="source_commit"
        ),
        source_tree=_validate_git_object(
            _string(raw, "source_tree", label="candidate manifest"), label="source_tree"
        ),
        scenario_root=_string(raw, "scenario_root", label="candidate manifest"),
        scenario_inventory=inventory,
        wheel=_parse_artifact(raw.get("wheel"), label="wheel"),
        verification_commands=commands,
        manifest_sha256=_validate_sha256(
            _string(raw, "manifest_sha256", label="candidate manifest"),
            label="manifest_sha256",
        ),
    )
    expected_digest = _canonical_digest(manifest._payload())
    if manifest.manifest_sha256 != expected_digest:
        raise CandidateManifestError("Candidate manifest digest does not match its contents.")
    return manifest


def _resolve_recorded_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def validate_candidate_manifest(
    manifest_path: Path,
    *,
    project_root: Path,
    wheel_path: Path | None = None,
    scenario_root: Path | None = None,
) -> CandidateManifest:
    """Verify a frozen manifest against the current clean checkout and artifacts."""

    manifest = read_candidate_manifest(manifest_path)
    root = project_root.resolve(strict=True)
    _assert_clean_worktree(root)
    project_name, project_version = _project_metadata(root)
    if (project_name, project_version) != (manifest.project_name, manifest.project_version):
        raise CandidateManifestError("Candidate project name or version no longer matches source.")
    current_commit = _validate_git_object(
        _run_git(root, "rev-parse", "HEAD"), label="source_commit"
    )
    current_tree = _validate_git_object(
        _run_git(root, "rev-parse", "HEAD^{tree}"), label="source_tree"
    )
    current_branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if (current_commit, current_tree, current_branch) != (
        manifest.source_commit,
        manifest.source_tree,
        manifest.source_branch,
    ):
        raise CandidateManifestError("Candidate Git identity no longer matches source checkout.")

    wheel = _artifact(
        root, wheel_path or _resolve_recorded_path(root, manifest.wheel.path), label="Wheel"
    )
    if wheel != manifest.wheel:
        raise CandidateManifestError("Candidate wheel digest or size no longer matches manifest.")
    selected_scenario_root = scenario_root or _resolve_recorded_path(root, manifest.scenario_root)
    current_inventory = _scenario_inventory(root, selected_scenario_root)
    if current_inventory != manifest.scenario_inventory:
        raise CandidateManifestError("Candidate scenario inventory no longer matches manifest.")
    return manifest


def write_candidate_manifest(manifest: CandidateManifest, output_path: Path) -> Path:
    """Write a candidate manifest atomically, refusing accidental overwrite."""

    destination = output_path.resolve(strict=False)
    if destination.exists() or destination.is_symlink():
        raise CandidateManifestError(
            f"Refusing to overwrite existing candidate manifest: {destination}"
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp")
        temporary.write_text(manifest.to_json(), encoding="utf-8")
        temporary.replace(destination)
    except OSError as exc:
        raise CandidateManifestError(f"Unable to write candidate manifest: {destination}") from exc
    return destination


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--wheel", type=Path, default=None)
    parser.add_argument("--scenario-root", type=Path, default=DEFAULT_SCENARIO_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--version", default=None)
    parser.add_argument("--verify-command", action="append", dest="verification_commands")
    return parser.parse_args(tuple(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.validate:
            if args.manifest is None:
                raise CandidateManifestError("--manifest is required with --validate.")
            validate_candidate_manifest(
                args.manifest,
                project_root=args.project_root,
                wheel_path=args.wheel,
                scenario_root=args.scenario_root,
            )
            print(json.dumps({"manifest": args.manifest.as_posix(), "valid": True}, sort_keys=True))
            return 0
        if args.wheel is None:
            raise CandidateManifestError("--wheel is required when creating a candidate manifest.")
        manifest = freeze_candidate(
            project_root=args.project_root,
            wheel_path=args.wheel,
            scenario_root=args.scenario_root,
            verification_commands=args.verification_commands,
            expected_version=args.version,
        )
        output = write_candidate_manifest(manifest, args.output)
    except (CandidateManifestError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "success": False}, sort_keys=True))
        return 1
    print(json.dumps({"manifest": output.as_posix(), "success": True}, sort_keys=True))
    return 0


__all__ = [
    "CANDIDATE_MANIFEST_SCHEMA_VERSION",
    "CandidateArtifact",
    "CandidateManifest",
    "CandidateManifestError",
    "CandidateScenario",
    "DEFAULT_OUTPUT_PATH",
    "DEFAULT_SCENARIO_ROOT",
    "DEFAULT_VERIFICATION_COMMANDS",
    "freeze_candidate",
    "main",
    "read_candidate_manifest",
    "validate_candidate_manifest",
    "write_candidate_manifest",
]


if __name__ == "__main__":
    raise SystemExit(main())
