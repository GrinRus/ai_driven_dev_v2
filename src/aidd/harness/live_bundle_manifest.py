from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from aidd.harness.live_result_bundle import (
    LIVE_RESULT_MATERIALIZED_DIRNAME,
    LiveResultBundleIdentity,
    validate_live_result_bundle,
)

LIVE_BUNDLE_MANIFEST_FILENAME = "live-bundle-manifest.json"
LIVE_BUNDLE_MANIFEST_SCHEMA_VERSION = 1
LIVE_BUNDLE_PROVENANCE_DIRNAME = "provenance"
SOURCE_ARCHIVE_FILENAME = "aidd-source.tar"


class LiveBundleManifestError(RuntimeError):
    """Raised when a live bundle cannot be sealed or its commit marker is invalid."""


@dataclass(frozen=True, slots=True)
class LiveBundleSealInputs:
    identity: LiveResultBundleIdentity
    source_repository_root: Path
    source_commit: str
    wheel_path: Path
    target_revision: str


@dataclass(frozen=True, slots=True)
class LiveBundleFile:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class BrowserArtifactIdentity:
    path: str
    run_id: str
    viewport: str


@dataclass(frozen=True, slots=True)
class LiveBundleManifest:
    bundle_root: Path
    identity: LiveResultBundleIdentity
    source_commit: str
    source_tree: str
    target_revision: str
    source_archive: LiveBundleFile
    wheel: LiveBundleFile
    files: tuple[LiveBundleFile, ...]
    browser_artifacts: tuple[BrowserArtifactIdentity, ...]
    tree_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(*, bundle_root: Path, path: Path) -> LiveBundleFile:
    resolved_root = bundle_root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise LiveBundleManifestError(
            f"Manifest artifact escapes the bundle: {path.as_posix()}."
        )
    return LiveBundleFile(
        path=resolved.relative_to(resolved_root).as_posix(),
        sha256=_sha256(resolved),
        size_bytes=resolved.stat().st_size,
    )


def _git_bytes(*, repository_root: Path, args: tuple[str, ...]) -> bytes:
    completed = subprocess.run(
        ("git", *args),
        cwd=repository_root,
        check=False,
        capture_output=True,
        timeout=120,
    )
    if completed.returncode != 0:
        reason = completed.stderr.decode("utf-8", errors="replace").strip()
        raise LiveBundleManifestError(
            f"Failed to read source Git provenance: {reason or completed.returncode}."
        )
    return completed.stdout


def _git_text(*, repository_root: Path, args: tuple[str, ...]) -> str:
    return _git_bytes(repository_root=repository_root, args=args).decode().strip()


def _validate_revision(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) < 7 or any(character not in "0123456789abcdef" for character in normalized):
        raise LiveBundleManifestError(f"{label} must be a hexadecimal Git object id.")
    return normalized


def _bundle_files(bundle_root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in sorted(bundle_root.rglob("*")):
        relative = path.relative_to(bundle_root)
        if relative.as_posix() == LIVE_BUNDLE_MANIFEST_FILENAME:
            continue
        if path.is_symlink():
            raise LiveBundleManifestError(
                f"Symlink cannot be committed as live bundle evidence: {relative.as_posix()}."
            )
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            files.append(path)
        elif not stat.S_ISDIR(mode):
            raise LiveBundleManifestError(
                f"Unsupported live bundle node: {relative.as_posix()}."
            )
    return tuple(files)


def _tree_digest(files: tuple[LiveBundleFile, ...]) -> str:
    digest = hashlib.sha256()
    for item in files:
        digest.update(item.path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item.size_bytes).encode("ascii"))
        digest.update(b"\0")
        digest.update(item.sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _viewport_identity(relative_path: str) -> str:
    stem = PurePosixPath(relative_path).stem.strip().lower()
    normalized = "".join(
        character if character.isalnum() or character in {"-", "_", "x"} else "-"
        for character in stem
    ).strip("-")
    if not normalized:
        raise LiveBundleManifestError(
            f"Browser artifact has no viewport identity: {relative_path!r}."
        )
    return normalized


def _browser_artifacts(
    *,
    files: tuple[LiveBundleFile, ...],
    run_id: str,
) -> tuple[BrowserArtifactIdentity, ...]:
    prefixes = (
        f"{LIVE_RESULT_MATERIALIZED_DIRNAME}/final/manual-frontend-evidence/",
        "manual-frontend-evidence/",
    )
    return tuple(
        BrowserArtifactIdentity(
            path=item.path,
            run_id=run_id,
            viewport=_viewport_identity(item.path),
        )
        for item in files
        if item.path.startswith(prefixes)
    )


def _write_manifest(path: Path, manifest: LiveBundleManifest) -> None:
    payload = {
        "aidd": {
            "source_archive": {
                "path": manifest.source_archive.path,
                "sha256": manifest.source_archive.sha256,
                "size_bytes": manifest.source_archive.size_bytes,
            },
            "source_commit": manifest.source_commit,
            "source_tree": manifest.source_tree,
            "wheel": {
                "path": manifest.wheel.path,
                "sha256": manifest.wheel.sha256,
                "size_bytes": manifest.wheel.size_bytes,
            },
        },
        "browser_artifacts": [
            {
                "path": item.path,
                "run_id": item.run_id,
                "viewport": item.viewport,
            }
            for item in manifest.browser_artifacts
        ],
        "files": [
            {
                "path": item.path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
            }
            for item in manifest.files
        ],
        "identity": {
            "run_id": manifest.identity.run_id,
            "runtime_id": manifest.identity.runtime_id,
            "scenario_id": manifest.identity.scenario_id,
            "target_revision": manifest.target_revision,
            "work_item": manifest.identity.work_item,
        },
        "schema_version": LIVE_BUNDLE_MANIFEST_SCHEMA_VERSION,
        "tree_sha256": manifest.tree_sha256,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seal_live_bundle(
    *,
    bundle_root: Path,
    inputs: LiveBundleSealInputs,
) -> LiveBundleManifest:
    identity = inputs.identity.normalized()
    resolved_bundle = bundle_root.resolve(strict=True)
    validate_live_result_bundle(
        bundle_root=resolved_bundle,
        expected_identity=identity,
    )
    source_root = inputs.source_repository_root.resolve(strict=True)
    source_commit = _validate_revision(inputs.source_commit, label="source_commit")
    actual_commit = _git_text(
        repository_root=source_root,
        args=("rev-parse", "HEAD"),
    ).lower()
    if actual_commit != source_commit:
        raise LiveBundleManifestError("Source checkout HEAD does not match source_commit.")
    source_tree = _validate_revision(
        _git_text(
            repository_root=source_root,
            args=("rev-parse", f"{source_commit}^{{tree}}"),
        ),
        label="source_tree",
    )
    target_revision = _validate_revision(
        inputs.target_revision, label="target_revision"
    )
    wheel_source = inputs.wheel_path.resolve(strict=True)
    if not wheel_source.is_file():
        raise LiveBundleManifestError("Wheel provenance input is not a file.")

    provenance_root = resolved_bundle / LIVE_BUNDLE_PROVENANCE_DIRNAME
    provenance_root.mkdir(parents=True, exist_ok=True)
    source_archive_path = provenance_root / SOURCE_ARCHIVE_FILENAME
    source_archive_path.write_bytes(
        _git_bytes(
            repository_root=source_root,
            args=("archive", "--format=tar", source_commit),
        )
    )
    wheel_path = provenance_root / wheel_source.name
    temporary_wheel = wheel_path.with_suffix(f"{wheel_path.suffix}.tmp")
    shutil.copyfile(wheel_source, temporary_wheel)
    os.replace(temporary_wheel, wheel_path)

    files = tuple(
        _file_record(bundle_root=resolved_bundle, path=path)
        for path in _bundle_files(resolved_bundle)
    )
    manifest = LiveBundleManifest(
        bundle_root=resolved_bundle,
        identity=identity,
        source_commit=source_commit,
        source_tree=source_tree,
        target_revision=target_revision,
        source_archive=_file_record(
            bundle_root=resolved_bundle,
            path=source_archive_path,
        ),
        wheel=_file_record(bundle_root=resolved_bundle, path=wheel_path),
        files=files,
        browser_artifacts=_browser_artifacts(files=files, run_id=identity.run_id),
        tree_sha256=_tree_digest(files),
    )
    manifest_path = resolved_bundle / LIVE_BUNDLE_MANIFEST_FILENAME
    temporary_manifest = manifest_path.with_suffix(".json.tmp")
    _write_manifest(temporary_manifest, manifest)
    os.replace(temporary_manifest, manifest_path)
    return validate_live_bundle_manifest(
        bundle_root=resolved_bundle,
        expected_identity=identity,
    )


def _parse_file(raw: object) -> LiveBundleFile:
    if not isinstance(raw, dict):
        raise LiveBundleManifestError("Manifest file record is invalid.")
    path = raw.get("path")
    sha256 = raw.get("sha256")
    size_bytes = raw.get("size_bytes")
    if (
        not isinstance(path, str)
        or Path(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or not isinstance(sha256, str)
        or not isinstance(size_bytes, int)
    ):
        raise LiveBundleManifestError("Manifest file record is incomplete.")
    return LiveBundleFile(path=path, sha256=sha256, size_bytes=size_bytes)


def validate_live_bundle_manifest(
    *,
    bundle_root: Path,
    expected_identity: LiveResultBundleIdentity | None = None,
) -> LiveBundleManifest:
    resolved_bundle = bundle_root.resolve(strict=True)
    manifest_path = resolved_bundle / LIVE_BUNDLE_MANIFEST_FILENAME
    try:
        payload = cast(
            dict[str, object],
            json.loads(manifest_path.read_text(encoding="utf-8")),
        )
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise LiveBundleManifestError("Live bundle commit manifest is missing or invalid.") from exc
    if payload.get("schema_version") != LIVE_BUNDLE_MANIFEST_SCHEMA_VERSION:
        raise LiveBundleManifestError("Unsupported live bundle manifest schema.")
    raw_identity = payload.get("identity")
    raw_aidd = payload.get("aidd")
    if not isinstance(raw_identity, dict) or not isinstance(raw_aidd, dict):
        raise LiveBundleManifestError("Live bundle provenance identity is missing.")
    try:
        identity = LiveResultBundleIdentity(
            scenario_id=str(raw_identity["scenario_id"]),
            runtime_id=str(raw_identity["runtime_id"]),
            run_id=str(raw_identity["run_id"]),
            work_item=str(raw_identity["work_item"]),
        ).normalized()
        target_revision = _validate_revision(
            str(raw_identity["target_revision"]), label="target_revision"
        )
        source_commit = _validate_revision(
            str(raw_aidd["source_commit"]), label="source_commit"
        )
        source_tree = _validate_revision(
            str(raw_aidd["source_tree"]), label="source_tree"
        )
        source_archive = _parse_file(raw_aidd["source_archive"])
        wheel = _parse_file(raw_aidd["wheel"])
    except (KeyError, ValueError) as exc:
        raise LiveBundleManifestError("Live bundle provenance identity is invalid.") from exc
    if expected_identity is not None and identity != expected_identity.normalized():
        raise LiveBundleManifestError("Live bundle identity does not match the run.")
    validate_live_result_bundle(
        bundle_root=resolved_bundle,
        expected_identity=identity,
    )

    raw_files = payload.get("files")
    if not isinstance(raw_files, list):
        raise LiveBundleManifestError("Live bundle file inventory is missing.")
    files = tuple(_parse_file(raw) for raw in raw_files)
    actual_paths = {
        path.relative_to(resolved_bundle).as_posix()
        for path in _bundle_files(resolved_bundle)
    }
    recorded_paths = {item.path for item in files}
    if len(recorded_paths) != len(files) or recorded_paths != actual_paths:
        raise LiveBundleManifestError(
            "Live bundle contains an orphan file or has incomplete materialization."
        )
    for item in files:
        path = resolved_bundle / item.path
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise LiveBundleManifestError(
                f"Manifest artifact is dangling: {item.path!r}."
            ) from exc
        if (
            not resolved.is_relative_to(resolved_bundle)
            or not resolved.is_file()
            or resolved.stat().st_size != item.size_bytes
            or _sha256(resolved) != item.sha256
        ):
            raise LiveBundleManifestError(
                f"Manifest artifact digest or size mismatch: {item.path!r}."
            )
    if source_archive not in files or wheel not in files:
        raise LiveBundleManifestError(
            "Source archive or wheel is not committed in the bundle inventory."
        )
    expected_tree = _tree_digest(files)
    if payload.get("tree_sha256") != expected_tree:
        raise LiveBundleManifestError("Live bundle tree digest does not match.")

    raw_browser = payload.get("browser_artifacts")
    if not isinstance(raw_browser, list):
        raise LiveBundleManifestError("Browser provenance inventory is missing.")
    expected_browser = _browser_artifacts(files=files, run_id=identity.run_id)
    browser: list[BrowserArtifactIdentity] = []
    for raw in raw_browser:
        if not isinstance(raw, dict):
            raise LiveBundleManifestError("Browser provenance record is invalid.")
        record = BrowserArtifactIdentity(
            path=str(raw.get("path", "")),
            run_id=str(raw.get("run_id", "")),
            viewport=str(raw.get("viewport", "")),
        )
        browser.append(record)
    if tuple(browser) != expected_browser:
        raise LiveBundleManifestError(
            "Browser artifact run or viewport identity does not match."
        )
    return LiveBundleManifest(
        bundle_root=resolved_bundle,
        identity=identity,
        source_commit=source_commit,
        source_tree=source_tree,
        target_revision=target_revision,
        source_archive=source_archive,
        wheel=wheel,
        files=files,
        browser_artifacts=tuple(browser),
        tree_sha256=expected_tree,
    )


__all__ = [
    "BrowserArtifactIdentity",
    "LIVE_BUNDLE_MANIFEST_FILENAME",
    "LiveBundleFile",
    "LiveBundleManifest",
    "LiveBundleManifestError",
    "LiveBundleSealInputs",
    "seal_live_bundle",
    "validate_live_bundle_manifest",
]
