"""Export and verify sanitized, immutable result-bundle archives.

The exporter is intentionally filesystem-only and runtime-agnostic.  It snapshots a sealed
W48 result bundle into a deterministic tar archive, writes retention metadata beside it, and
never changes the source bundle.  Readers verify the outer digest and the inner manifest before
returning any archive contents.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from aidd.harness.evidence_archive_contract import (
    EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    EvidenceArchiveContractError,
    EvidenceArchiveRetention,
    EvidenceRedaction,
    dump_evidence_archive_retention,
    validate_evidence_archive_retention,
)
from aidd.harness.result_bundle_contract import (
    RESULT_BUNDLE_INVENTORY_FILENAME,
    ResultBundleContractError,
    ResultBundleIdentity,
    ResultBundleInventory,
    validate_result_bundle_inventory,
)

EVIDENCE_ARCHIVE_MANIFEST_FILENAME = "evidence-archive-manifest.json"
EVIDENCE_ARCHIVE_RETENTION_SUFFIX = ".retention.json"
_ARCHIVE_STATUSES = frozenset({"pass", "fail", "blocked", "infra-fail"})


class EvidenceArchiveError(ValueError):
    """Raised when an archive cannot be exported or verified safely."""


@dataclass(frozen=True, slots=True)
class EvidenceArchiveFile:
    """Digest-backed file entry in an archive manifest."""

    path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class EvidenceArchiveSnapshot:
    """Verified archive metadata and the files available for read-back."""

    archive_path: Path
    retention: EvidenceArchiveRetention
    identity: ResultBundleIdentity
    status: str
    files: tuple[EvidenceArchiveFile, ...]
    excluded_paths: tuple[str, ...]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceArchiveError(f"{field} must be a non-empty path.")
    normalized = value.strip()
    if "\\" in normalized:
        raise EvidenceArchiveError(f"{field} must use POSIX separators.")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise EvidenceArchiveError(f"{field} must be a contained relative path.")
    return path.as_posix()


def _bundle_files(bundle_root: Path) -> tuple[tuple[str, Path], ...]:
    resolved_root = bundle_root.resolve(strict=True)
    files: list[tuple[str, Path]] = []
    for path in sorted(resolved_root.rglob("*")):
        relative = path.relative_to(resolved_root).as_posix()
        if path.is_symlink():
            raise EvidenceArchiveError(f"bundle contains an untrusted symlink: {relative!r}.")
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise EvidenceArchiveError(f"bundle contains an unsupported node: {relative!r}.")
        if relative in {RESULT_BUNDLE_INVENTORY_FILENAME, "artifact-digests.json"}:
            continue
        files.append((relative, path))
    return tuple(files)


def _load_sealed_inventory(bundle_root: Path) -> ResultBundleInventory:
    inventory_path = bundle_root / RESULT_BUNDLE_INVENTORY_FILENAME
    try:
        payload = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory = ResultBundleInventory.from_dict(payload)
        return validate_result_bundle_inventory(inventory=inventory, bundle_root=bundle_root)
    except (OSError, json.JSONDecodeError, ResultBundleContractError) as exc:
        raise EvidenceArchiveError("source bundle inventory is missing or invalid.") from exc


def _manifest_bytes(
    *,
    identity: ResultBundleIdentity,
    status: str,
    source_revision: str,
    target_pin: str,
    evidence_schema_version: int,
    redaction: EvidenceRedaction,
    files: tuple[EvidenceArchiveFile, ...],
    excluded_paths: tuple[str, ...],
) -> bytes:
    payload = {
        "evidence_schema_version": evidence_schema_version,
        "excluded_paths": list(excluded_paths),
        "files": [
            {"path": item.path, "sha256": item.sha256, "size_bytes": item.size_bytes}
            for item in files
        ],
        "identity": identity.to_dict(),
        "redaction": redaction.to_dict(),
        "schema_version": EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION,
        "source_revision": source_revision,
        "status": status,
        "target_pin": target_pin,
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _tar_info(path: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(path)
    info.size = size
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def _write_archive(
    *,
    archive_path: Path,
    manifest: bytes,
    files: tuple[tuple[str, bytes], ...],
) -> None:
    with tarfile.open(archive_path, mode="w", format=tarfile.PAX_FORMAT) as archive:
        archive.addfile(
            _tar_info(EVIDENCE_ARCHIVE_MANIFEST_FILENAME, len(manifest)),
            io.BytesIO(manifest),
        )
        for relative, data in files:
            archive.addfile(_tar_info(relative, len(data)), io.BytesIO(data))


def retention_sidecar_path(archive_path: Path) -> Path:
    """Return the deterministic sidecar path for an exported archive."""

    return archive_path.with_name(archive_path.name + EVIDENCE_ARCHIVE_RETENTION_SUFFIX)


def export_evidence_archive(
    *,
    bundle_root: Path,
    archive_path: Path,
    source_revision: str,
    target_pin: str,
    redaction: EvidenceRedaction,
    evidence_schema_version: int = EVIDENCE_SCHEMA_VERSION,
) -> EvidenceArchiveRetention:
    """Export a sealed result bundle and return its digest-backed retention record."""

    try:
        resolved_bundle = bundle_root.resolve(strict=True)
    except OSError as exc:
        raise EvidenceArchiveError("source bundle root is not retrievable.") from exc
    if not resolved_bundle.is_dir():
        raise EvidenceArchiveError("source bundle root must be a directory.")
    resolved_archive = archive_path.resolve(strict=False)
    if resolved_archive.is_relative_to(resolved_bundle):
        raise EvidenceArchiveError("archive destination must be outside the source bundle.")
    sidecar = retention_sidecar_path(resolved_archive)
    if (
        archive_path.exists()
        or archive_path.is_symlink()
        or sidecar.exists()
        or sidecar.is_symlink()
    ):
        raise EvidenceArchiveError("archive destination is already present and immutable.")

    inventory = _load_sealed_inventory(resolved_bundle)
    try:
        normalized_inputs = validate_evidence_archive_retention(
            EvidenceArchiveRetention(
                locator=resolved_archive.as_posix(),
                sha256="0" * 64,
                size_bytes=1,
                source_revision=source_revision,
                target_pin=target_pin,
                evidence_schema_version=evidence_schema_version,
                redaction=redaction,
            )
        )
    except EvidenceArchiveContractError as exc:
        raise EvidenceArchiveError("archive retention inputs are invalid.") from exc
    normalized_redaction = normalized_inputs.redaction
    normalized_source_revision = normalized_inputs.source_revision
    normalized_target_pin = normalized_inputs.target_pin
    normalized_evidence_schema_version = normalized_inputs.evidence_schema_version
    declared_exclusions = set(normalized_redaction.redacted_paths)
    source_files = _bundle_files(resolved_bundle)
    included = tuple(
        (path, source) for path, source in source_files if path not in declared_exclusions
    )
    excluded_paths = tuple(sorted(declared_exclusions))
    included_payloads = tuple((path, source.read_bytes()) for path, source in included)
    included_records = tuple(
        EvidenceArchiveFile(path=path, sha256=_sha256_bytes(data), size_bytes=len(data))
        for path, data in included_payloads
    )
    included_paths = {item.path for item in included_records}
    sanitized_inventory = ResultBundleInventory(
        identity=inventory.identity,
        status=inventory.status,
        artifacts=tuple(item for item in inventory.artifacts if item.path in included_paths),
        requirements=tuple(item for item in inventory.requirements if item.path in included_paths),
    ).normalized()
    inventory_payload = (
        json.dumps(sanitized_inventory.to_dict(), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    digest_payload = (
        json.dumps(
            {
                "artifacts": [item.to_dict() for item in included_records],
                "schema_version": 2,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    archive_payloads = tuple(
        sorted(
            included_payloads
            + (
                (RESULT_BUNDLE_INVENTORY_FILENAME, inventory_payload),
                ("artifact-digests.json", digest_payload),
            ),
            key=lambda item: item[0],
        )
    )
    archive_files = tuple(
        EvidenceArchiveFile(path=path, sha256=_sha256_bytes(data), size_bytes=len(data))
        for path, data in archive_payloads
    )
    manifest = _manifest_bytes(
        identity=inventory.identity,
        status=inventory.status,
        source_revision=normalized_source_revision,
        target_pin=normalized_target_pin,
        evidence_schema_version=normalized_evidence_schema_version,
        redaction=normalized_redaction,
        files=archive_files,
        excluded_paths=excluded_paths,
    )

    resolved_archive.parent.mkdir(parents=True, exist_ok=True)
    archive_fd, archive_name = tempfile.mkstemp(
        prefix=f".{resolved_archive.name}.", suffix=".tmp", dir=resolved_archive.parent
    )
    sidecar_fd, sidecar_name = tempfile.mkstemp(
        prefix=f".{sidecar.name}.", suffix=".tmp", dir=sidecar.parent
    )
    os.close(archive_fd)
    os.close(sidecar_fd)
    temporary_archive = Path(archive_name)
    temporary_sidecar = Path(sidecar_name)
    try:
        _write_archive(
            archive_path=temporary_archive,
            manifest=manifest,
            files=archive_payloads,
        )
        retention = validate_evidence_archive_retention(
            EvidenceArchiveRetention(
                locator=resolved_archive.as_posix(),
                sha256=_sha256_path(temporary_archive),
                size_bytes=temporary_archive.stat().st_size,
                source_revision=normalized_source_revision,
                target_pin=normalized_target_pin,
                evidence_schema_version=normalized_evidence_schema_version,
                redaction=normalized_redaction,
            )
        )
        temporary_sidecar.write_text(
            dump_evidence_archive_retention(retention),
            encoding="utf-8",
        )
        os.replace(temporary_archive, resolved_archive)
        os.replace(temporary_sidecar, sidecar)
        return retention
    finally:
        temporary_archive.unlink(missing_ok=True)
        temporary_sidecar.unlink(missing_ok=True)


def _parse_archive_file(raw: object, *, index: int) -> EvidenceArchiveFile:
    if not isinstance(raw, dict):
        raise EvidenceArchiveError(f"archive manifest file {index} is invalid.")
    path = _safe_relative_path(raw.get("path"), field=f"archive manifest file {index}.path")
    sha256 = raw.get("sha256")
    if (
        not isinstance(sha256, str)
        or len(sha256) != 64
        or any(character not in "0123456789abcdef" for character in sha256.lower())
    ):
        raise EvidenceArchiveError(f"archive manifest file {index}.sha256 is invalid.")
    size_bytes = raw.get("size_bytes")
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
        raise EvidenceArchiveError(f"archive manifest file {index}.size_bytes is invalid.")
    return EvidenceArchiveFile(path=path, sha256=sha256.lower(), size_bytes=size_bytes)


def _read_members(archive_path: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    members: dict[str, bytes] = {}
    manifest: dict[str, Any] | None = None
    try:
        with tarfile.open(archive_path, mode="r:") as archive:
            for member in archive.getmembers():
                path = _safe_relative_path(member.name, field="archive member")
                if (
                    path in members
                    or path == EVIDENCE_ARCHIVE_MANIFEST_FILENAME
                    and manifest is not None
                ):
                    raise EvidenceArchiveError(f"archive contains duplicate member: {path!r}.")
                if not member.isreg():
                    raise EvidenceArchiveError(f"archive contains a non-regular member: {path!r}.")
                stream = archive.extractfile(member)
                if stream is None:
                    raise EvidenceArchiveError(f"archive member is unreadable: {path!r}.")
                data = stream.read()
                if path == EVIDENCE_ARCHIVE_MANIFEST_FILENAME:
                    try:
                        raw_manifest = json.loads(data.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise EvidenceArchiveError("archive manifest is invalid JSON.") from exc
                    if not isinstance(raw_manifest, dict):
                        raise EvidenceArchiveError("archive manifest must be an object.")
                    manifest = raw_manifest
                else:
                    members[path] = data
    except (OSError, tarfile.TarError) as exc:
        raise EvidenceArchiveError("archive is unreadable or malformed.") from exc
    if manifest is None:
        raise EvidenceArchiveError("archive manifest is missing.")
    return members, manifest


def _retention_for_archive(
    *,
    resolved_archive: Path,
    retention: EvidenceArchiveRetention | None,
) -> EvidenceArchiveRetention:
    sidecar = retention_sidecar_path(resolved_archive)
    if retention is None:
        if sidecar.is_symlink():
            raise EvidenceArchiveError("archive retention sidecar must not be a symlink.")
        try:
            retention = EvidenceArchiveRetention.from_dict(
                json.loads(sidecar.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError, EvidenceArchiveContractError) as exc:
            raise EvidenceArchiveError("archive retention sidecar is missing or invalid.") from exc
    try:
        normalized = validate_evidence_archive_retention(retention)
    except EvidenceArchiveContractError as exc:
        raise EvidenceArchiveError("archive retention metadata is invalid.") from exc
    if normalized.locator != resolved_archive.as_posix():
        raise EvidenceArchiveError("retention locator does not match the archive path.")
    return normalized


def _verify_archive_digest(*, archive_path: Path, retention: EvidenceArchiveRetention) -> None:
    actual_size = archive_path.stat().st_size
    actual_digest = _sha256_path(archive_path)
    if actual_size != retention.size_bytes:
        raise EvidenceArchiveError("archive size does not match retention metadata.")
    if actual_digest != retention.sha256:
        raise EvidenceArchiveError("archive digest does not match retention metadata.")


def _manifest_provenance(
    *, manifest: dict[str, Any], retention: EvidenceArchiveRetention
) -> tuple[ResultBundleIdentity, str, EvidenceRedaction]:
    if manifest.get("schema_version") != EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION:
        raise EvidenceArchiveError("archive manifest schema is unsupported.")
    if manifest.get("source_revision") != retention.source_revision:
        raise EvidenceArchiveError("archive source revision does not match retention metadata.")
    if manifest.get("target_pin") != retention.target_pin:
        raise EvidenceArchiveError("archive target pin does not match retention metadata.")
    if manifest.get("evidence_schema_version") != retention.evidence_schema_version:
        raise EvidenceArchiveError("archive evidence schema does not match retention metadata.")
    try:
        redaction = EvidenceRedaction.from_dict(manifest.get("redaction"))
        identity = ResultBundleIdentity.from_dict(manifest.get("identity"))
    except EvidenceArchiveContractError as exc:
        raise EvidenceArchiveError("archive redaction metadata is invalid.") from exc
    except ResultBundleContractError as exc:
        raise EvidenceArchiveError("archive identity is invalid.") from exc
    status = manifest.get("status")
    if not isinstance(status, str) or status not in _ARCHIVE_STATUSES:
        raise EvidenceArchiveError("archive status is invalid.")
    return identity, status, redaction


def _manifest_files(
    *, manifest: dict[str, Any], members: dict[str, bytes]
) -> tuple[EvidenceArchiveFile, ...]:
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list):
        raise EvidenceArchiveError("archive manifest files must be a list.")
    files = tuple(_parse_archive_file(raw, index=index) for index, raw in enumerate(raw_files))
    if len({item.path for item in files}) != len(files):
        raise EvidenceArchiveError("archive manifest contains duplicate file paths.")
    if {item.path for item in files} != set(members):
        raise EvidenceArchiveError("archive manifest does not match archive members.")
    for item in files:
        data = members[item.path]
        if len(data) != item.size_bytes or _sha256_bytes(data) != item.sha256:
            raise EvidenceArchiveError(f"archive file integrity mismatch: {item.path!r}.")
    return files


def _manifest_excluded_paths(
    *, manifest: dict[str, Any], retention: EvidenceArchiveRetention, file_paths: set[str]
) -> tuple[str, ...]:
    raw_excluded = manifest.get("excluded_paths")
    if not isinstance(raw_excluded, list) or not all(
        isinstance(item, str) for item in raw_excluded
    ):
        raise EvidenceArchiveError("archive excluded_paths must be a string list.")
    excluded_paths = tuple(
        sorted({_safe_relative_path(item, field="excluded path") for item in raw_excluded})
    )
    if set(excluded_paths) & file_paths:
        raise EvidenceArchiveError("archive redaction overlaps an included file.")
    if excluded_paths != retention.redaction.redacted_paths:
        raise EvidenceArchiveError("archive excluded paths do not match redaction metadata.")
    return excluded_paths


def _verified_archive(
    *,
    archive_path: Path,
    retention: EvidenceArchiveRetention | None,
) -> tuple[EvidenceArchiveSnapshot, dict[str, bytes]]:
    if archive_path.is_symlink():
        raise EvidenceArchiveError("archive path must not be a symlink.")
    try:
        resolved_archive = archive_path.resolve(strict=True)
    except OSError as exc:
        raise EvidenceArchiveError("archive path is not retrievable.") from exc
    if not resolved_archive.is_file():
        raise EvidenceArchiveError("archive path is not a regular file.")
    normalized_retention = _retention_for_archive(
        resolved_archive=resolved_archive,
        retention=retention,
    )
    _verify_archive_digest(archive_path=resolved_archive, retention=normalized_retention)
    members, manifest = _read_members(resolved_archive)
    identity, raw_status, manifest_redaction = _manifest_provenance(
        manifest=manifest,
        retention=normalized_retention,
    )
    if manifest_redaction != normalized_retention.redaction:
        raise EvidenceArchiveError("archive redaction metadata does not match retention metadata.")
    files = _manifest_files(manifest=manifest, members=members)
    excluded_paths = _manifest_excluded_paths(
        manifest=manifest,
        retention=normalized_retention,
        file_paths={item.path for item in files},
    )
    return (
        EvidenceArchiveSnapshot(
            archive_path=resolved_archive,
            retention=normalized_retention,
            identity=identity,
            status=raw_status,
            files=files,
            excluded_paths=excluded_paths,
        ),
        members,
    )


def read_evidence_archive(
    *,
    archive_path: Path,
    retention: EvidenceArchiveRetention | None = None,
) -> EvidenceArchiveSnapshot:
    """Verify an archive and return its read-only snapshot."""

    snapshot, _members = _verified_archive(archive_path=archive_path, retention=retention)
    return snapshot


def extract_evidence_archive(
    *,
    archive_path: Path,
    destination: Path,
    retention: EvidenceArchiveRetention | None = None,
) -> EvidenceArchiveSnapshot:
    """Verify an archive and extract its sanitized files into a fresh destination."""

    snapshot, members = _verified_archive(archive_path=archive_path, retention=retention)
    resolved_destination = destination.resolve(strict=False)
    if destination.exists() and destination.is_symlink():
        raise EvidenceArchiveError("archive extraction destination must not be a symlink.")
    try:
        resolved_destination.mkdir(parents=True, exist_ok=True)
        for item in snapshot.files:
            path = (resolved_destination / PurePosixPath(item.path)).resolve(strict=False)
            if not path.is_relative_to(resolved_destination):
                raise EvidenceArchiveError("archive extraction path escapes the destination.")
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() or path.is_symlink():
                raise EvidenceArchiveError(
                    f"archive extraction target already exists: {item.path!r}."
                )
            path.write_bytes(members[item.path])
    except EvidenceArchiveError:
        raise
    except OSError as exc:
        raise EvidenceArchiveError("archive extraction destination is not writable.") from exc
    return snapshot


__all__ = [
    "EVIDENCE_ARCHIVE_MANIFEST_FILENAME",
    "EVIDENCE_ARCHIVE_RETENTION_SUFFIX",
    "EvidenceArchiveError",
    "EvidenceArchiveFile",
    "EvidenceArchiveSnapshot",
    "export_evidence_archive",
    "extract_evidence_archive",
    "read_evidence_archive",
    "retention_sidecar_path",
]
