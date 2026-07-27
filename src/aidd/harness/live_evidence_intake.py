from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

EvidenceSourceKind = Literal["file", "directory"]
_COPY_CHUNK_SIZE = 1024 * 1024


class LiveEvidenceIntakeError(RuntimeError):
    """Raised when browser/manual evidence cannot be imported safely."""


@dataclass(frozen=True, slots=True)
class LiveEvidenceFile:
    relative_path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class LiveEvidenceIntakeResult:
    source_kind: EvidenceSourceKind
    source_path: Path
    authorized_root: Path
    published_root: Path
    directories: tuple[str, ...]
    files: tuple[LiveEvidenceFile, ...]
    total_size_bytes: int
    tree_sha256: str


@dataclass(frozen=True, slots=True)
class _SourceFile:
    source_path: Path
    relative_path: Path
    device: int
    inode: int
    mode: int
    link_count: int
    size_bytes: int
    modified_ns: int


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(path.expanduser()))


def _lstat(path: Path, *, label: str) -> os.stat_result:
    try:
        return path.lstat()
    except OSError as exc:
        raise LiveEvidenceIntakeError(f"Unable to inspect {label}: {exc}") from exc


def _require_real_directory(path: Path, *, label: str) -> os.stat_result:
    metadata = _lstat(path, label=label)
    if stat.S_ISLNK(metadata.st_mode):
        raise LiveEvidenceIntakeError(f"{label} must not be a symlink.")
    if not stat.S_ISDIR(metadata.st_mode):
        raise LiveEvidenceIntakeError(f"{label} must be a directory.")
    return metadata


def _validate_source_chain(*, source: Path, authorized_root: Path) -> os.stat_result:
    _require_real_directory(authorized_root, label="authorized browser root")
    try:
        relative = source.relative_to(authorized_root)
    except ValueError as exc:
        raise LiveEvidenceIntakeError(
            "Evidence source must stay inside the authorized browser root."
        ) from exc
    current = authorized_root
    metadata = _lstat(current, label="authorized browser root")
    for component in relative.parts:
        if component in {"", ".", ".."}:
            raise LiveEvidenceIntakeError(
                "Evidence source contains a non-canonical path component."
            )
        current /= component
        metadata = _lstat(current, label=f"evidence component {component!r}")
        if stat.S_ISLNK(metadata.st_mode):
            raise LiveEvidenceIntakeError(
                f"Evidence component {component!r} must not be a symlink."
            )
    if not stat.S_ISREG(metadata.st_mode) and not stat.S_ISDIR(metadata.st_mode):
        raise LiveEvidenceIntakeError(
            "Evidence source must be a regular file or directory."
        )
    if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1:
        raise LiveEvidenceIntakeError("Evidence files must not be hard linked.")
    return metadata


def _source_file(
    *,
    source_path: Path,
    relative_path: Path,
    metadata: os.stat_result,
) -> _SourceFile:
    if stat.S_ISLNK(metadata.st_mode):
        raise LiveEvidenceIntakeError(
            f"Evidence path {relative_path.as_posix()!r} must not be a symlink."
        )
    if not stat.S_ISREG(metadata.st_mode):
        raise LiveEvidenceIntakeError(
            f"Evidence path {relative_path.as_posix()!r} must be a regular file."
        )
    if metadata.st_nlink != 1:
        raise LiveEvidenceIntakeError(
            f"Evidence path {relative_path.as_posix()!r} must not be hard linked."
        )
    return _SourceFile(
        source_path=source_path,
        relative_path=relative_path,
        device=metadata.st_dev,
        inode=metadata.st_ino,
        mode=metadata.st_mode,
        link_count=metadata.st_nlink,
        size_bytes=metadata.st_size,
        modified_ns=metadata.st_mtime_ns,
    )


def _inventory_directory(
    *,
    source: Path,
    relative_root: Path = Path(),
) -> tuple[list[Path], list[_SourceFile]]:
    directories: list[Path] = []
    files: list[_SourceFile] = []
    try:
        children = sorted(source.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise LiveEvidenceIntakeError(
            f"Unable to list evidence directory {source.as_posix()!r}: {exc}"
        ) from exc
    for child in children:
        relative = relative_root / child.name
        metadata = _lstat(child, label=f"evidence path {relative.as_posix()!r}")
        if stat.S_ISLNK(metadata.st_mode):
            raise LiveEvidenceIntakeError(
                f"Evidence path {relative.as_posix()!r} must not be a symlink."
            )
        if stat.S_ISDIR(metadata.st_mode):
            directories.append(relative)
            nested_directories, nested_files = _inventory_directory(
                source=child,
                relative_root=relative,
            )
            directories.extend(nested_directories)
            files.extend(nested_files)
            continue
        files.append(
            _source_file(
                source_path=child,
                relative_path=relative,
                metadata=metadata,
            )
        )
    return directories, files


def _same_source(metadata: os.stat_result, source: _SourceFile) -> bool:
    return (
        metadata.st_dev == source.device
        and metadata.st_ino == source.inode
        and metadata.st_mode == source.mode
        and metadata.st_nlink == source.link_count
        and metadata.st_size == source.size_bytes
        and metadata.st_mtime_ns == source.modified_ns
        and stat.S_ISREG(metadata.st_mode)
    )


def _copy_regular_file(source: _SourceFile, destination: Path) -> LiveEvidenceFile:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(source.source_path, flags)
    except OSError as exc:
        raise LiveEvidenceIntakeError(
            f"Unable to open evidence file {source.relative_path.as_posix()!r}: {exc}"
        ) from exc
    digest = hashlib.sha256()
    copied_size = 0
    try:
        before = os.fstat(descriptor)
        if not _same_source(before, source):
            raise LiveEvidenceIntakeError(
                f"Evidence file {source.relative_path.as_posix()!r} changed before copy."
            )
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            output = destination.open("xb")
        except OSError as exc:
            raise LiveEvidenceIntakeError(
                f"Unable to create staged evidence file: {exc}"
            ) from exc
        with output:
            while chunk := os.read(descriptor, _COPY_CHUNK_SIZE):
                output.write(chunk)
                digest.update(chunk)
                copied_size += len(chunk)
            output.flush()
            os.fsync(output.fileno())
        after = os.fstat(descriptor)
        if not _same_source(after, source) or copied_size != source.size_bytes:
            raise LiveEvidenceIntakeError(
                f"Evidence file {source.relative_path.as_posix()!r} changed during copy."
            )
    finally:
        os.close(descriptor)
    return LiveEvidenceFile(
        relative_path=source.relative_path.as_posix(),
        size_bytes=copied_size,
        sha256=digest.hexdigest(),
    )


def _digest_staged_file(path: Path, expected: LiveEvidenceFile) -> None:
    metadata = _lstat(path, label=f"staged evidence {expected.relative_path!r}")
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_size != expected.size_bytes
    ):
        raise LiveEvidenceIntakeError(
            f"Staged evidence metadata mismatch for {expected.relative_path!r}."
        )
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(_COPY_CHUNK_SIZE):
                digest.update(chunk)
    except OSError as exc:
        raise LiveEvidenceIntakeError(
            f"Unable to verify staged evidence {expected.relative_path!r}: {exc}"
        ) from exc
    if digest.hexdigest() != expected.sha256:
        raise LiveEvidenceIntakeError(
            f"Staged evidence digest mismatch for {expected.relative_path!r}."
        )


def _digest_source_file(source: _SourceFile) -> LiveEvidenceFile:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(source.source_path, flags)
    except OSError as exc:
        raise LiveEvidenceIntakeError(
            f"Unable to open trusted evidence {source.relative_path.as_posix()!r}: {exc}"
        ) from exc
    digest = hashlib.sha256()
    size_bytes = 0
    try:
        before = os.fstat(descriptor)
        if not _same_source(before, source):
            raise LiveEvidenceIntakeError(
                f"Trusted evidence {source.relative_path.as_posix()!r} changed before read."
            )
        while chunk := os.read(descriptor, _COPY_CHUNK_SIZE):
            digest.update(chunk)
            size_bytes += len(chunk)
        after = os.fstat(descriptor)
        if not _same_source(after, source) or size_bytes != source.size_bytes:
            raise LiveEvidenceIntakeError(
                f"Trusted evidence {source.relative_path.as_posix()!r} changed during read."
            )
    finally:
        os.close(descriptor)
    return LiveEvidenceFile(
        relative_path=source.relative_path.as_posix(),
        size_bytes=size_bytes,
        sha256=digest.hexdigest(),
    )


def _tree_digest(
    *,
    directories: list[Path],
    files: tuple[LiveEvidenceFile, ...],
) -> str:
    digest = hashlib.sha256()
    for directory in directories:
        digest.update(b"directory\0")
        digest.update(directory.as_posix().encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
    for item in files:
        digest.update(b"file\0")
        digest.update(item.relative_path.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(str(item.size_bytes).encode("ascii"))
        digest.update(b"\0")
        digest.update(item.sha256.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def validate_live_evidence_publication(
    *,
    published_root: Path,
    expected_directories: tuple[str, ...],
    expected_files: tuple[LiveEvidenceFile, ...],
    expected_tree_sha256: str,
) -> None:
    lexical_root = _absolute_lexical(published_root)
    _require_real_directory(lexical_root, label="trusted evidence publication")
    directories, source_files = _inventory_directory(source=lexical_root)
    actual_directories = tuple(path.as_posix() for path in directories)
    if actual_directories != expected_directories:
        raise LiveEvidenceIntakeError(
            "Trusted evidence directory inventory changed after publication."
        )
    actual_files = tuple(_digest_source_file(item) for item in source_files)
    if actual_files != expected_files:
        raise LiveEvidenceIntakeError(
            "Trusted evidence file inventory changed after publication."
        )
    if (
        _tree_digest(directories=directories, files=actual_files)
        != expected_tree_sha256
    ):
        raise LiveEvidenceIntakeError(
            "Trusted evidence tree digest changed after publication."
        )


def intake_live_evidence(
    *,
    source: Path,
    authorized_root: Path,
    destination_root: Path,
) -> LiveEvidenceIntakeResult:
    lexical_source = _absolute_lexical(source)
    lexical_authorized = _absolute_lexical(authorized_root)
    lexical_destination = _absolute_lexical(destination_root)
    source_metadata = _validate_source_chain(
        source=lexical_source,
        authorized_root=lexical_authorized,
    )
    destination_parent = lexical_destination.parent
    _require_real_directory(destination_parent, label="evidence bundle root")
    if lexical_destination.exists() or lexical_destination.is_symlink():
        raise LiveEvidenceIntakeError(
            "Trusted evidence destination must not already exist."
        )

    if stat.S_ISDIR(source_metadata.st_mode):
        source_kind: EvidenceSourceKind = "directory"
        directories, source_files = _inventory_directory(source=lexical_source)
    else:
        source_kind = "file"
        directories = []
        source_files = [
            _source_file(
                source_path=lexical_source,
                relative_path=Path(lexical_source.name),
                metadata=source_metadata,
            )
        ]

    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{lexical_destination.name}.staging-",
            dir=destination_parent,
        )
    )
    published = False
    try:
        for relative in directories:
            (staging / relative).mkdir(parents=True, exist_ok=False, mode=0o700)
        copied_files = tuple(
            _copy_regular_file(item, staging / item.relative_path)
            for item in source_files
        )
        for item in copied_files:
            _digest_staged_file(staging / item.relative_path, item)
        os.replace(staging, lexical_destination)
        published = True
    except (LiveEvidenceIntakeError, OSError) as exc:
        if isinstance(exc, LiveEvidenceIntakeError):
            raise
        raise LiveEvidenceIntakeError(f"Unable to publish trusted evidence: {exc}") from exc
    finally:
        if not published and staging.exists():
            shutil.rmtree(staging)

    return LiveEvidenceIntakeResult(
        source_kind=source_kind,
        source_path=lexical_source,
        authorized_root=lexical_authorized,
        published_root=lexical_destination,
        directories=tuple(path.as_posix() for path in directories),
        files=copied_files,
        total_size_bytes=sum(item.size_bytes for item in copied_files),
        tree_sha256=_tree_digest(directories=directories, files=copied_files),
    )


__all__ = [
    "LiveEvidenceFile",
    "LiveEvidenceIntakeError",
    "LiveEvidenceIntakeResult",
    "intake_live_evidence",
    "validate_live_evidence_publication",
]
