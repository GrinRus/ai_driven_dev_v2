from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, cast

from aidd.core.identifiers import SafeIdentifier

LIVE_RESULT_INDEX_FILENAME = "live-result-index.json"
LIVE_RESULT_MATERIALIZED_DIRNAME = "canonical-evidence"
LIVE_RESULT_INDEX_SCHEMA_VERSION = 1
_LATER_SEAL_OUTPUT_NAMES = frozenset(
    {
        "command-evidence",
        "live-bundle-manifest.json",
        "provenance",
    }
)

ArtifactCategory = Literal[
    "browser",
    "final-report",
    "stage",
    "target-patch",
    "task-run",
]
ReferenceMode = Literal["bundle-relative", "legacy-degraded"]


class LiveResultBundleError(RuntimeError):
    """Raised when canonical live evidence cannot be materialized or verified."""


@dataclass(frozen=True, slots=True)
class LiveResultBundleIdentity:
    scenario_id: str
    runtime_id: str
    run_id: str
    work_item: str

    def normalized(self) -> LiveResultBundleIdentity:
        return LiveResultBundleIdentity(
            scenario_id=SafeIdentifier.parse(
                self.scenario_id, label="scenario_id"
            ).value,
            runtime_id=SafeIdentifier.parse(self.runtime_id, label="runtime_id").value,
            run_id=SafeIdentifier.parse(self.run_id, label="run_id").value,
            work_item=SafeIdentifier.parse(self.work_item, label="work_item").value,
        )


@dataclass(frozen=True, slots=True)
class LiveResultArtifact:
    category: ArtifactCategory
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class LiveResultBundle:
    bundle_root: Path
    identity: LiveResultBundleIdentity
    artifacts: tuple[LiveResultArtifact, ...]
    reference_mode: ReferenceMode


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_reference(*, bundle_root: Path, path: Path) -> str:
    resolved_root = bundle_root.resolve(strict=True)
    resolved_path = path.resolve(strict=True)
    if not resolved_path.is_relative_to(resolved_root):
        raise LiveResultBundleError(
            f"Artifact escapes the live result bundle: {path.as_posix()}."
        )
    return resolved_path.relative_to(resolved_root).as_posix()


def _safe_relative_path(reference: str) -> PurePosixPath:
    relative = PurePosixPath(reference)
    if relative.is_absolute() or not relative.parts:
        raise LiveResultBundleError(
            f"Canonical artifact reference must be bundle-relative: {reference!r}."
        )
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise LiveResultBundleError(
            f"Canonical artifact reference is not contained: {reference!r}."
        )
    return relative


def resolve_live_result_reference(
    *,
    bundle_root: Path,
    reference: str,
    allow_legacy_absolute: bool = False,
) -> tuple[Path, ReferenceMode]:
    candidate = Path(reference)
    if candidate.is_absolute():
        if not allow_legacy_absolute:
            raise LiveResultBundleError(
                "Absolute live result references are legacy evidence and require "
                "allow_legacy_absolute=True."
            )
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file():
            raise LiveResultBundleError(
                f"Legacy live result reference is not a file: {reference!r}."
            )
        return resolved, "legacy-degraded"

    relative = _safe_relative_path(reference)
    resolved_root = bundle_root.resolve(strict=True)
    path = resolved_root.joinpath(*relative.parts)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise LiveResultBundleError(
            f"Live result reference is dangling or escapes the bundle: {reference!r}."
        ) from exc
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise LiveResultBundleError(
            f"Live result reference is dangling or escapes the bundle: {reference!r}."
        )
    return resolved, "bundle-relative"


def _copy_regular_file(*, source: Path, destination: Path) -> None:
    source_stat = source.lstat()
    if not stat.S_ISREG(source_stat.st_mode):
        raise LiveResultBundleError(
            f"Live result source must be a regular file: {source.as_posix()}."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as source_stream, destination.open("xb") as target_stream:
        shutil.copyfileobj(source_stream, target_stream, length=1024 * 1024)
    shutil.copymode(source, destination, follow_symlinks=False)


def _copy_tree(*, source: Path, destination: Path) -> tuple[Path, ...]:
    if not source.exists():
        return ()
    if source.is_symlink() or not source.is_dir():
        raise LiveResultBundleError(
            f"Live result source tree must be a real directory: {source.as_posix()}."
        )
    copied: list[Path] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise LiveResultBundleError(
                f"Symlink is not trusted live result evidence: {path.as_posix()}."
            )
        relative = path.relative_to(source)
        target = destination / relative
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            target.mkdir(parents=True, exist_ok=True)
        elif stat.S_ISREG(mode):
            _copy_regular_file(source=path, destination=target)
            copied.append(target)
        else:
            raise LiveResultBundleError(
                f"Unsupported live result evidence node: {path.as_posix()}."
            )
    return tuple(copied)


def _target_patch(target_root: Path) -> bytes:
    completed = subprocess.run(
        (
            "git",
            "diff",
            "--binary",
            "--no-ext-diff",
            "HEAD",
            "--",
            ".",
            ":(exclude).aidd/**",
        ),
        cwd=target_root,
        check=False,
        capture_output=True,
        timeout=120,
    )
    if completed.returncode != 0:
        reason = completed.stderr.decode("utf-8", errors="replace").strip()
        raise LiveResultBundleError(
            f"Failed to materialize target patch: {reason or completed.returncode}."
        )
    untracked = subprocess.run(
        ("git", "ls-files", "--others", "--exclude-standard", "-z"),
        cwd=target_root,
        check=False,
        capture_output=True,
        timeout=120,
    )
    if untracked.returncode != 0:
        reason = untracked.stderr.decode("utf-8", errors="replace").strip()
        raise LiveResultBundleError(
            "Failed to enumerate untracked target patch files: "
            f"{reason or untracked.returncode}."
        )
    patch = bytearray(completed.stdout)
    for raw_path in sorted(filter(None, untracked.stdout.split(b"\0"))):
        relative_text = os.fsdecode(raw_path)
        relative = _safe_relative_path(PurePosixPath(relative_text).as_posix())
        if relative.parts[0] == ".aidd":
            continue
        diff = subprocess.run(
            (
                "git",
                "diff",
                "--binary",
                "--no-index",
                "--",
                "/dev/null",
                relative.as_posix(),
            ),
            cwd=target_root,
            check=False,
            capture_output=True,
            timeout=120,
        )
        if diff.returncode not in {0, 1}:
            reason = diff.stderr.decode("utf-8", errors="replace").strip()
            raise LiveResultBundleError(
                f"Failed to include untracked target file {relative.as_posix()!r}: "
                f"{reason or diff.returncode}."
            )
        patch.extend(diff.stdout)
    return bytes(patch)


def _artifact(
    *,
    bundle_root: Path,
    path: Path,
    category: ArtifactCategory,
) -> LiveResultArtifact:
    return LiveResultArtifact(
        category=category,
        path=_relative_reference(bundle_root=bundle_root, path=path),
        sha256=_sha256(path),
        size_bytes=path.stat().st_size,
    )


def _write_index(
    *,
    path: Path,
    identity: LiveResultBundleIdentity,
    artifacts: tuple[LiveResultArtifact, ...],
) -> None:
    payload = {
        "artifacts": [
            {
                "category": item.category,
                "path": item.path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
            }
            for item in artifacts
        ],
        "identity": {
            "run_id": identity.run_id,
            "runtime_id": identity.runtime_id,
            "scenario_id": identity.scenario_id,
            "work_item": identity.work_item,
        },
        "reference_mode": "bundle-relative",
        "schema_version": LIVE_RESULT_INDEX_SCHEMA_VERSION,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize_live_result_bundle(
    *,
    bundle_root: Path,
    identity: LiveResultBundleIdentity,
    target_root: Path | None,
) -> LiveResultBundle:
    normalized_identity = identity.normalized()
    resolved_bundle_root = bundle_root.resolve(strict=True)
    final_root = resolved_bundle_root / LIVE_RESULT_MATERIALIZED_DIRNAME
    staging_root = Path(
        tempfile.mkdtemp(prefix=".canonical-evidence-", dir=resolved_bundle_root)
    )
    artifacts: list[LiveResultArtifact] = []
    try:
        final_files_root = staging_root / "final"
        for source in sorted(resolved_bundle_root.iterdir()):
            if (
                source.name == LIVE_RESULT_MATERIALIZED_DIRNAME
                or source.name == LIVE_RESULT_INDEX_FILENAME
                or source.name in _LATER_SEAL_OUTPUT_NAMES
                or source.name.startswith(".canonical-evidence-")
            ):
                continue
            if source.is_symlink():
                raise LiveResultBundleError(
                    f"Symlink is not trusted live result evidence: {source.as_posix()}."
                )
            destination = final_files_root / source.name
            if source.is_file():
                _copy_regular_file(source=source, destination=destination)
                artifacts.append(
                    _artifact(
                        bundle_root=staging_root,
                        path=destination,
                        category=(
                            "browser"
                            if source.name == "manual-frontend-evidence"
                            else "final-report"
                        ),
                    )
                )
            elif source.is_dir():
                category: ArtifactCategory = (
                    "browser"
                    if source.name == "manual-frontend-evidence"
                    else "final-report"
                )
                for copied in _copy_tree(source=source, destination=destination):
                    artifacts.append(
                        _artifact(
                            bundle_root=staging_root,
                            path=copied,
                            category=category,
                        )
                    )

        if target_root is not None:
            resolved_target = target_root.resolve(strict=True)
            workspace_root = resolved_target / ".aidd"
            work_item_root = (
                workspace_root / "workitems" / normalized_identity.work_item
            )
            run_root = (
                workspace_root
                / "reports"
                / "runs"
                / normalized_identity.work_item
                / normalized_identity.run_id
            )
            for copied in _copy_tree(
                source=work_item_root,
                destination=staging_root / "work-item",
            ):
                artifacts.append(
                    _artifact(
                        bundle_root=staging_root,
                        path=copied,
                        category="stage",
                    )
                )
            for copied in _copy_tree(
                source=run_root,
                destination=staging_root / "task-run",
            ):
                artifacts.append(
                    _artifact(
                        bundle_root=staging_root,
                        path=copied,
                        category="task-run",
                    )
                )
            patch_path = staging_root / "target" / "target.patch"
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            patch_path.write_bytes(_target_patch(resolved_target))
            artifacts.append(
                _artifact(
                    bundle_root=staging_root,
                    path=patch_path,
                    category="target-patch",
                )
            )

        artifacts.sort(key=lambda item: (item.category, item.path))
        if final_root.exists():
            shutil.rmtree(final_root)
        os.replace(staging_root, final_root)

        rebased_artifacts = tuple(
            LiveResultArtifact(
                category=item.category,
                path=f"{LIVE_RESULT_MATERIALIZED_DIRNAME}/{item.path}",
                sha256=item.sha256,
                size_bytes=item.size_bytes,
            )
            for item in artifacts
        )
        index_path = resolved_bundle_root / LIVE_RESULT_INDEX_FILENAME
        temporary_index = index_path.with_suffix(".json.tmp")
        _write_index(
            path=temporary_index,
            identity=normalized_identity,
            artifacts=rebased_artifacts,
        )
        os.replace(temporary_index, index_path)
        return validate_live_result_bundle(
            bundle_root=resolved_bundle_root,
            expected_identity=normalized_identity,
        )
    except BaseException:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise


def validate_live_result_bundle(
    *,
    bundle_root: Path,
    expected_identity: LiveResultBundleIdentity | None = None,
) -> LiveResultBundle:
    resolved_bundle_root = bundle_root.resolve(strict=True)
    index_path = resolved_bundle_root / LIVE_RESULT_INDEX_FILENAME
    try:
        payload = cast(
            dict[str, object],
            json.loads(index_path.read_text(encoding="utf-8")),
        )
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise LiveResultBundleError("Live result index is missing or invalid.") from exc
    if payload.get("schema_version") != LIVE_RESULT_INDEX_SCHEMA_VERSION:
        raise LiveResultBundleError("Unsupported live result index schema.")
    if payload.get("reference_mode") != "bundle-relative":
        raise LiveResultBundleError("Canonical live result index is not bundle-relative.")
    raw_identity = payload.get("identity")
    if not isinstance(raw_identity, dict):
        raise LiveResultBundleError("Live result index identity is missing.")
    try:
        identity = LiveResultBundleIdentity(
            scenario_id=str(raw_identity["scenario_id"]),
            runtime_id=str(raw_identity["runtime_id"]),
            run_id=str(raw_identity["run_id"]),
            work_item=str(raw_identity["work_item"]),
        ).normalized()
    except (KeyError, ValueError) as exc:
        raise LiveResultBundleError("Live result index identity is invalid.") from exc
    if expected_identity is not None and identity != expected_identity.normalized():
        raise LiveResultBundleError("Live result index identity does not match the run.")

    raw_artifacts = payload.get("artifacts")
    if not isinstance(raw_artifacts, list):
        raise LiveResultBundleError("Live result artifact list is missing.")
    artifacts: list[LiveResultArtifact] = []
    valid_categories = {
        "browser",
        "final-report",
        "stage",
        "target-patch",
        "task-run",
    }
    for raw in raw_artifacts:
        if not isinstance(raw, dict):
            raise LiveResultBundleError("Live result artifact record is invalid.")
        category = raw.get("category")
        reference = raw.get("path")
        sha256 = raw.get("sha256")
        size_bytes = raw.get("size_bytes")
        if (
            category not in valid_categories
            or not isinstance(reference, str)
            or not isinstance(sha256, str)
            or not isinstance(size_bytes, int)
        ):
            raise LiveResultBundleError("Live result artifact record is incomplete.")
        path, mode = resolve_live_result_reference(
            bundle_root=resolved_bundle_root,
            reference=reference,
        )
        if mode != "bundle-relative":
            raise LiveResultBundleError("Canonical artifact unexpectedly resolved as legacy.")
        if path.stat().st_size != size_bytes or _sha256(path) != sha256:
            raise LiveResultBundleError(
                f"Live result artifact does not match its index: {reference!r}."
            )
        artifacts.append(
            LiveResultArtifact(
                category=cast(ArtifactCategory, category),
                path=reference,
                sha256=sha256,
                size_bytes=size_bytes,
            )
        )
    return LiveResultBundle(
        bundle_root=resolved_bundle_root,
        identity=identity,
        artifacts=tuple(artifacts),
        reference_mode="bundle-relative",
    )
