from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ProviderAuthRuntime = Literal["codex", "claude-code"]
ProviderAuthSeedStatus = Literal["seeded"]

MAX_PROVIDER_AUTH_SEED_BYTES = 1024 * 1024
_COPY_CHUNK_SIZE = 64 * 1024
_AUTH_RELATIVE_PATHS: dict[ProviderAuthRuntime, Path] = {
    "codex": Path(".codex/auth.json"),
    "claude-code": Path(".claude.json"),
}


class LiveProviderAuthSeedError(RuntimeError):
    """Raised when provider authentication cannot be copied safely."""


@dataclass(frozen=True, slots=True)
class ProviderAuthSeedRequest:
    runtime: str
    operator_home: Path
    provider_private_home: Path


@dataclass(frozen=True, slots=True)
class ProviderAuthSeedResult:
    runtime: ProviderAuthRuntime
    relative_destination: str
    size_bytes: int
    status: ProviderAuthSeedStatus


@dataclass(frozen=True, slots=True)
class _SourceIdentity:
    device: int
    inode: int
    mode: int
    link_count: int
    size_bytes: int
    modified_ns: int


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(path.expanduser()))


def _safe_lstat(path: Path, *, label: str) -> os.stat_result:
    try:
        return path.lstat()
    except OSError as exc:
        raise LiveProviderAuthSeedError(f"Unable to inspect {label}.") from exc


def _optional_lstat(path: Path, *, label: str) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise LiveProviderAuthSeedError(f"Unable to inspect {label}.") from exc


def _require_directory(path: Path, *, label: str) -> os.stat_result:
    metadata = _safe_lstat(path, label=label)
    if stat.S_ISLNK(metadata.st_mode):
        raise LiveProviderAuthSeedError(f"{label} must not be a symlink.")
    if not stat.S_ISDIR(metadata.st_mode):
        raise LiveProviderAuthSeedError(f"{label} must be a directory.")
    return metadata


def _validate_distinct_homes(operator_home: Path, private_home: Path) -> None:
    if (
        operator_home == private_home
        or operator_home.is_relative_to(private_home)
        or private_home.is_relative_to(operator_home)
    ):
        raise LiveProviderAuthSeedError(
            "Operator and provider-private homes must be separate."
        )


def _source_identity(
    *,
    operator_home: Path,
    relative_path: Path,
) -> tuple[Path, _SourceIdentity]:
    _require_directory(operator_home, label="operator home")
    current = operator_home
    for index, component in enumerate(relative_path.parts):
        if component in {"", ".", ".."}:
            raise LiveProviderAuthSeedError(
                "Provider auth path contains a non-canonical component."
            )
        current /= component
        metadata = _safe_lstat(
            current,
            label=f"provider auth component {component!r}",
        )
        is_last = index == len(relative_path.parts) - 1
        if stat.S_ISLNK(metadata.st_mode):
            raise LiveProviderAuthSeedError(
                f"Provider auth component {component!r} must not be a symlink."
            )
        if not is_last and not stat.S_ISDIR(metadata.st_mode):
            raise LiveProviderAuthSeedError(
                f"Provider auth component {component!r} must be a directory."
            )
        if is_last:
            if not stat.S_ISREG(metadata.st_mode):
                raise LiveProviderAuthSeedError(
                    "Provider auth source must be a regular file."
                )
            if metadata.st_nlink != 1:
                raise LiveProviderAuthSeedError(
                    "Provider auth source must not be hard linked."
                )
            if metadata.st_size > MAX_PROVIDER_AUTH_SEED_BYTES:
                raise LiveProviderAuthSeedError(
                    "Provider auth source exceeds the 1 MiB size limit."
                )
            return current, _SourceIdentity(
                device=metadata.st_dev,
                inode=metadata.st_ino,
                mode=metadata.st_mode,
                link_count=metadata.st_nlink,
                size_bytes=metadata.st_size,
                modified_ns=metadata.st_mtime_ns,
            )
    raise LiveProviderAuthSeedError("Provider auth path is empty.")


def _matches_source(
    metadata: os.stat_result,
    expected: _SourceIdentity,
) -> bool:
    return (
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_dev == expected.device
        and metadata.st_ino == expected.inode
        and metadata.st_mode == expected.mode
        and metadata.st_nlink == expected.link_count
        and metadata.st_size == expected.size_bytes
        and metadata.st_mtime_ns == expected.modified_ns
    )


def _prepare_destination_parent(
    *,
    private_home: Path,
    relative_path: Path,
) -> Path:
    _require_directory(private_home, label="provider-private home")
    try:
        private_home.chmod(0o700)
    except OSError as exc:
        raise LiveProviderAuthSeedError(
            "Unable to protect provider-private home."
        ) from exc

    current = private_home
    for component in relative_path.parent.parts:
        if component in {"", ".", ".."}:
            raise LiveProviderAuthSeedError(
                "Provider auth destination contains a non-canonical component."
            )
        current /= component
        metadata = _optional_lstat(
            current,
            label=f"provider auth destination component {component!r}",
        )
        if metadata is None:
            try:
                current.mkdir(mode=0o700)
            except OSError as exc:
                raise LiveProviderAuthSeedError(
                    "Unable to create provider auth destination directory."
                ) from exc
            metadata = _safe_lstat(
                current,
                label=f"provider auth destination component {component!r}",
            )
        if stat.S_ISLNK(metadata.st_mode):
            raise LiveProviderAuthSeedError(
                f"Provider auth destination component {component!r} "
                "must not be a symlink."
            )
        if not stat.S_ISDIR(metadata.st_mode):
            raise LiveProviderAuthSeedError(
                f"Provider auth destination component {component!r} "
                "must be a directory."
            )
        try:
            current.chmod(0o700)
        except OSError as exc:
            raise LiveProviderAuthSeedError(
                "Unable to protect provider auth destination directory."
            ) from exc
    return current


def _copy_file_bytes(
    source_descriptor: int,
    destination_descriptor: int,
) -> tuple[int, bytes]:
    digest = hashlib.sha256()
    copied_size = 0
    while chunk := os.read(source_descriptor, _COPY_CHUNK_SIZE):
        remaining = memoryview(chunk)
        while remaining:
            written = os.write(destination_descriptor, remaining)
            if written <= 0:
                raise OSError("provider auth staging write made no progress")
            remaining = remaining[written:]
        digest.update(chunk)
        copied_size += len(chunk)
    return copied_size, digest.digest()


def _digest_descriptor(descriptor: int) -> bytes:
    digest = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    while chunk := os.read(descriptor, _COPY_CHUNK_SIZE):
        digest.update(chunk)
    return digest.digest()


def _open_source(path: Path) -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        return os.open(path, flags)
    except OSError as exc:
        raise LiveProviderAuthSeedError(
            "Unable to open provider auth source."
        ) from exc


def _seed_file(
    *,
    source: Path,
    source_identity: _SourceIdentity,
    destination: Path,
) -> int:
    if _optional_lstat(destination, label="provider auth destination") is not None:
        raise LiveProviderAuthSeedError(
            "Provider auth destination already exists."
        )

    source_descriptor = _open_source(source)
    temporary_path: Path | None = None
    published = False
    try:
        before = os.fstat(source_descriptor)
        if not _matches_source(before, source_identity):
            raise LiveProviderAuthSeedError(
                "Provider auth source changed before copy."
            )
        try:
            temporary_descriptor, temporary_name = tempfile.mkstemp(
                prefix=".provider-auth-seed-",
                dir=destination.parent,
            )
        except OSError as exc:
            raise LiveProviderAuthSeedError(
                "Unable to create provider auth staging file."
            ) from exc
        temporary_path = Path(temporary_name)
        try:
            os.fchmod(temporary_descriptor, 0o600)
            copied_size, source_digest = _copy_file_bytes(
                source_descriptor,
                temporary_descriptor,
            )
            os.fsync(temporary_descriptor)
            staged_digest = _digest_descriptor(temporary_descriptor)
        except OSError as exc:
            raise LiveProviderAuthSeedError(
                "Unable to copy provider auth source."
            ) from exc
        finally:
            os.close(temporary_descriptor)

        after = os.fstat(source_descriptor)
        if (
            not _matches_source(after, source_identity)
            or copied_size != source_identity.size_bytes
        ):
            raise LiveProviderAuthSeedError(
                "Provider auth source changed during copy."
            )
        if staged_digest != source_digest:
            raise LiveProviderAuthSeedError(
                "Provider auth staging verification failed."
            )
        staged = _safe_lstat(temporary_path, label="provider auth staging file")
        if (
            not stat.S_ISREG(staged.st_mode)
            or staged.st_nlink != 1
            or staged.st_size != copied_size
            or stat.S_IMODE(staged.st_mode) != 0o600
        ):
            raise LiveProviderAuthSeedError(
                "Provider auth staging metadata is invalid."
            )
        if _optional_lstat(destination, label="provider auth destination") is not None:
            raise LiveProviderAuthSeedError(
                "Provider auth destination appeared during copy."
            )
        try:
            os.link(
                temporary_path,
                destination,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise LiveProviderAuthSeedError(
                "Unable to publish provider auth destination."
            ) from exc
        published = True
        temporary_path.unlink()
        final = _safe_lstat(destination, label="published provider auth")
        if (
            not stat.S_ISREG(final.st_mode)
            or final.st_nlink != 1
            or final.st_size != copied_size
            or stat.S_IMODE(final.st_mode) != 0o600
        ):
            raise LiveProviderAuthSeedError(
                "Published provider auth metadata is invalid."
            )
        return copied_size
    except Exception:
        if published:
            destination.unlink(missing_ok=True)
        raise
    finally:
        os.close(source_descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def seed_provider_auth_state(
    request: ProviderAuthSeedRequest,
) -> ProviderAuthSeedResult:
    if request.runtime not in _AUTH_RELATIVE_PATHS:
        raise LiveProviderAuthSeedError(
            "Provider auth seed runtime must be 'codex' or 'claude-code'."
        )
    runtime: ProviderAuthRuntime = request.runtime
    runtime_path = _AUTH_RELATIVE_PATHS[runtime]
    operator_home = _absolute_lexical(request.operator_home)
    private_home = _absolute_lexical(request.provider_private_home)
    _validate_distinct_homes(operator_home, private_home)

    source, source_identity = _source_identity(
        operator_home=operator_home,
        relative_path=runtime_path,
    )
    destination_parent = _prepare_destination_parent(
        private_home=private_home,
        relative_path=runtime_path,
    )
    destination = destination_parent / runtime_path.name
    size_bytes = _seed_file(
        source=source,
        source_identity=source_identity,
        destination=destination,
    )
    return ProviderAuthSeedResult(
        runtime=runtime,
        relative_destination=runtime_path.as_posix(),
        size_bytes=size_bytes,
        status="seeded",
    )


__all__ = [
    "LiveProviderAuthSeedError",
    "MAX_PROVIDER_AUTH_SEED_BYTES",
    "ProviderAuthRuntime",
    "ProviderAuthSeedRequest",
    "ProviderAuthSeedResult",
    "seed_provider_auth_state",
]
