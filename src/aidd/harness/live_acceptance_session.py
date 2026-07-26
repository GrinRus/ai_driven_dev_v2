from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from types import TracebackType
from typing import Literal, Protocol

from aidd.harness.live_acceptance_isolation import (
    LiveAcceptanceIsolationCapability,
    LiveAcceptanceIsolationError,
    require_live_acceptance_isolation_capability,
)

SESSION_INTEGRITY_FILENAME = "live-acceptance-session.json"
SESSION_SCHEMA_VERSION = 1
_SESSION_SENTINEL_FILENAME = ".live-acceptance-session-active"
_EXPECTED_PROVIDER_ROOTS = ("work", "reports", "browser")


class LiveAcceptanceSessionError(RuntimeError):
    """Raised when live-acceptance lifecycle integrity cannot be proven."""


class _DigestWriter(Protocol):
    def update(self, value: bytes, /) -> object: ...


@dataclass(frozen=True, slots=True)
class SourceIntegritySnapshot:
    revision: str
    tree: str
    tracked_file_count: int
    tracked_bytes_sha256: str
    tracked_status: str
    untracked_files: tuple[str, ...]
    untracked_bytes_sha256: str


@dataclass(frozen=True, slots=True)
class TargetBaseline:
    provider_root_existed: bool
    expected_root_presence: dict[str, bool]


@dataclass(frozen=True, slots=True)
class LiveAcceptanceSessionResult:
    schema_version: int
    status: str
    source_checkout: str
    external_root: str
    provider_root: str
    isolation_backend: str
    source_baseline: SourceIntegritySnapshot
    source_postflight: SourceIntegritySnapshot
    target_baseline: TargetBaseline
    target_postflight: dict[str, object]
    process_exit_code: int | None
    violations: tuple[str, ...]
    cleanup: dict[str, object]


def _run_git_bytes(source_checkout: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ("git", *args),
        cwd=source_checkout,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        if not detail:
            detail = completed.stdout.decode("utf-8", errors="replace").strip()
        raise LiveAcceptanceSessionError(
            f"Unable to capture live source integrity: {detail or 'unknown git error'}"
        )
    return completed.stdout


def _git_paths(source_checkout: Path, *args: str) -> tuple[str, ...]:
    output = _run_git_bytes(source_checkout, *args)
    decoded = output.decode("utf-8", errors="surrogateescape")
    return tuple(sorted(path for path in decoded.split("\0") if path))


def _hash_path(
    digest: _DigestWriter,
    *,
    source_checkout: Path,
    relative_path: str,
) -> None:
    path = source_checkout / relative_path
    resolved_source = source_checkout.resolve(strict=False)
    resolved_parent = path.parent.resolve(strict=False)
    if not resolved_parent.is_relative_to(resolved_source):
        raise LiveAcceptanceSessionError(
            f"Source integrity path escapes checkout: {relative_path}."
        )
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise LiveAcceptanceSessionError(
            f"Unable to inspect source integrity path {relative_path!r}: {exc}"
        ) from exc
    digest.update(relative_path.encode("utf-8", errors="surrogateescape"))
    digest.update(b"\0")
    digest.update(str(metadata.st_mode).encode("ascii"))
    digest.update(b"\0")
    if stat.S_ISLNK(metadata.st_mode):
        digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
    elif stat.S_ISREG(metadata.st_mode):
        try:
            with path.open("rb") as file_stream:
                while chunk := file_stream.read(1024 * 1024):
                    digest.update(chunk)
        except OSError as exc:
            raise LiveAcceptanceSessionError(
                f"Unable to read source integrity path {relative_path!r}: {exc}"
            ) from exc
    else:
        raise LiveAcceptanceSessionError(
            f"Unsupported source integrity file type: {relative_path}."
        )
    digest.update(b"\0")


def _paths_digest(source_checkout: Path, paths: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for relative_path in paths:
        _hash_path(digest, source_checkout=source_checkout, relative_path=relative_path)
    return digest.hexdigest()


def capture_source_integrity(source_checkout: Path) -> SourceIntegritySnapshot:
    source = source_checkout.resolve(strict=False)
    if not source.is_dir():
        raise LiveAcceptanceSessionError("AIDD source checkout must exist.")
    revision = _run_git_bytes(source, "rev-parse", "HEAD").decode().strip()
    tree = _run_git_bytes(source, "rev-parse", "HEAD^{tree}").decode().strip()
    tracked_paths = _git_paths(source, "ls-files", "-z")
    untracked_paths = _git_paths(
        source,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
    )
    tracked_status = _run_git_bytes(
        source,
        "status",
        "--porcelain",
        "--untracked-files=no",
    ).decode("utf-8", errors="replace").strip()
    return SourceIntegritySnapshot(
        revision=revision,
        tree=tree,
        tracked_file_count=len(tracked_paths),
        tracked_bytes_sha256=_paths_digest(source, tracked_paths),
        tracked_status=tracked_status,
        untracked_files=untracked_paths,
        untracked_bytes_sha256=_paths_digest(source, untracked_paths),
    )


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(path.expanduser()))


def _validate_preflight_roots(
    *,
    source_checkout: Path,
    external_root: Path,
    provider_root: Path,
) -> tuple[Path, Path, Path]:
    lexical_source = _absolute_lexical(source_checkout)
    lexical_external = _absolute_lexical(external_root)
    lexical_provider = _absolute_lexical(provider_root)
    source = lexical_source.resolve(strict=False)
    external = lexical_external.resolve(strict=False)
    if not source.is_dir():
        raise LiveAcceptanceSessionError("AIDD source checkout must exist.")
    if not external.is_dir():
        raise LiveAcceptanceSessionError("External live root must already exist.")
    if lexical_provider.is_symlink():
        raise LiveAcceptanceSessionError("Provider root must not be a symlink.")
    provider = lexical_provider.resolve(strict=False)
    if provider.parent != external:
        raise LiveAcceptanceSessionError(
            "Provider root must be exactly one component below the external live root."
        )
    if (
        source == external
        or source.is_relative_to(external)
        or external.is_relative_to(source)
    ):
        raise LiveAcceptanceSessionError(
            "Source checkout and external live root must not overlap."
        )
    return source, external, provider


def _target_baseline(provider_root: Path) -> TargetBaseline:
    return TargetBaseline(
        provider_root_existed=provider_root.exists(),
        expected_root_presence={
            name: (provider_root / name).exists() for name in _EXPECTED_PROVIDER_ROOTS
        },
    )


def _target_postflight(provider_root: Path) -> tuple[dict[str, object], tuple[str, ...]]:
    resolved_provider = provider_root.resolve(strict=False)
    provider_is_symlink = provider_root.is_symlink()
    provider_contained = resolved_provider == provider_root
    roots: dict[str, object] = {}
    violations: list[str] = []
    if provider_is_symlink or not provider_contained:
        violations.append("provider root escaped or became a symlink")
    for name in _EXPECTED_PROVIDER_ROOTS:
        path = provider_root / name
        exists = path.exists()
        is_symlink = path.is_symlink()
        resolved = path.resolve(strict=False)
        contained = resolved.is_relative_to(provider_root)
        roots[name] = {
            "path": path.as_posix(),
            "exists": exists,
            "is_symlink": is_symlink,
            "contained": contained,
        }
        if is_symlink or not contained:
            violations.append(f"provider target root `{name}` escaped or became a symlink")
    return {
        "provider_root": {
            "path": provider_root.as_posix(),
            "resolved_path": resolved_provider.as_posix(),
            "is_symlink": provider_is_symlink,
            "contained": provider_contained,
        },
        "expected_roots": roots,
    }, tuple(violations)


def _source_violations(
    baseline: SourceIntegritySnapshot,
    postflight: SourceIntegritySnapshot,
) -> tuple[str, ...]:
    violations: list[str] = []
    if baseline.revision != postflight.revision:
        violations.append("source revision changed")
    if baseline.tree != postflight.tree:
        violations.append("source tree changed")
    if baseline.tracked_file_count != postflight.tracked_file_count:
        violations.append("source tracked file count changed")
    if baseline.tracked_status != postflight.tracked_status:
        violations.append("source tracked status changed")
    if baseline.tracked_bytes_sha256 != postflight.tracked_bytes_sha256:
        violations.append("source tracked bytes changed")
    if baseline.untracked_files != postflight.untracked_files:
        violations.append("source untracked file set changed")
    if baseline.untracked_bytes_sha256 != postflight.untracked_bytes_sha256:
        violations.append("source untracked bytes changed")
    return tuple(violations)


def _write_result(path: Path, result: LiveAcceptanceSessionResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


class LiveAcceptanceSession:
    def __init__(
        self,
        *,
        source_checkout: Path,
        external_root: Path,
        provider_root: Path,
        allow_existing_provider: bool = False,
    ) -> None:
        self._source_input = source_checkout
        self._external_input = external_root
        self._provider_input = provider_root
        self._allow_existing_provider = allow_existing_provider
        self.source_checkout: Path | None = None
        self.external_root: Path | None = None
        self.provider_root: Path | None = None
        self.capability: LiveAcceptanceIsolationCapability | None = None
        self.source_baseline: SourceIntegritySnapshot | None = None
        self.target_baseline: TargetBaseline | None = None
        self.process_exit_code: int | None = None
        self.result: LiveAcceptanceSessionResult | None = None
        self._sentinel_path: Path | None = None

    @property
    def evidence_path(self) -> Path:
        if self.provider_root is None:
            raise LiveAcceptanceSessionError("Session has not passed preflight.")
        return self.provider_root / SESSION_INTEGRITY_FILENAME

    def record_process_exit(self, exit_code: int) -> None:
        self.process_exit_code = exit_code

    def __enter__(self) -> LiveAcceptanceSession:
        source, external, provider = _validate_preflight_roots(
            source_checkout=self._source_input,
            external_root=self._external_input,
            provider_root=self._provider_input,
        )
        source_baseline = capture_source_integrity(source)
        if source_baseline.tracked_status:
            raise LiveAcceptanceSessionError(
                "Live acceptance requires clean tracked source bytes before provider allocation."
            )
        target_baseline = _target_baseline(provider)
        if target_baseline.provider_root_existed and not self._allow_existing_provider:
            raise LiveAcceptanceSessionError(
                "Fresh live acceptance provider root is already allocated or contaminated."
            )
        try:
            capability = require_live_acceptance_isolation_capability()
        except LiveAcceptanceIsolationError as exc:
            raise LiveAcceptanceSessionError(str(exc)) from exc

        provider.mkdir(mode=0o700, exist_ok=self._allow_existing_provider)
        if not provider.is_dir() or provider.is_symlink():
            raise LiveAcceptanceSessionError("Provider root must remain a real directory.")
        sentinel = provider / _SESSION_SENTINEL_FILENAME
        try:
            with sentinel.open("x", encoding="utf-8", errors="strict") as stream:
                stream.write(json.dumps({"pid": os.getpid()}, sort_keys=True) + "\n")
        except FileExistsError as exc:
            raise LiveAcceptanceSessionError(
                "Provider root already has an active live-acceptance session."
            ) from exc
        self.source_checkout = source
        self.external_root = external
        self.provider_root = provider
        self.capability = capability
        self.source_baseline = source_baseline
        self.target_baseline = target_baseline
        self._sentinel_path = sentinel
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        del exc_type, traceback
        if (
            self.source_checkout is None
            or self.provider_root is None
            or self.capability is None
            or self.source_baseline is None
            or self.target_baseline is None
        ):
            return False

        violations: list[str] = []
        if (
            self.source_checkout.is_symlink()
            or self.source_checkout.resolve(strict=False) != self.source_checkout
        ):
            violations.append("source checkout root escaped or became a symlink")
        try:
            source_postflight = capture_source_integrity(self.source_checkout)
            violations.extend(
                _source_violations(self.source_baseline, source_postflight)
            )
        except LiveAcceptanceSessionError as postflight_error:
            source_postflight = self.source_baseline
            violations.append(f"source postflight failed: {postflight_error}")

        target_postflight, target_violations = _target_postflight(self.provider_root)
        violations.extend(target_violations)
        cleanup: dict[str, object] = {
            "sentinel_path": (
                None if self._sentinel_path is None else self._sentinel_path.as_posix()
            ),
            "sentinel_removed": False,
            "errors": [],
        }
        if self._sentinel_path is not None:
            try:
                self._sentinel_path.unlink()
                cleanup["sentinel_removed"] = not self._sentinel_path.exists()
            except OSError as cleanup_error:
                cast_errors = cleanup["errors"]
                if isinstance(cast_errors, list):
                    cast_errors.append(str(cleanup_error))
        if cleanup["sentinel_removed"] is not True:
            violations.append("session cleanup sentinel was not removed")

        status = "pass" if not violations else "fail"
        self.result = LiveAcceptanceSessionResult(
            schema_version=SESSION_SCHEMA_VERSION,
            status=status,
            source_checkout=self.source_checkout.as_posix(),
            external_root=(
                self.external_root.as_posix()
                if self.external_root is not None
                else self._external_input.as_posix()
            ),
            provider_root=self.provider_root.as_posix(),
            isolation_backend=self.capability.backend,
            source_baseline=self.source_baseline,
            source_postflight=source_postflight,
            target_baseline=self.target_baseline,
            target_postflight=target_postflight,
            process_exit_code=self.process_exit_code,
            violations=tuple(violations),
            cleanup=cleanup,
        )
        try:
            _write_result(self.evidence_path, self.result)
        except OSError as evidence_error:
            raise LiveAcceptanceSessionError(
                f"Unable to publish live session integrity evidence: {evidence_error}"
            ) from exc
        if violations:
            raise LiveAcceptanceSessionError(
                "Live acceptance session integrity failed: " + "; ".join(violations)
            ) from exc
        return False


__all__ = [
    "SESSION_INTEGRITY_FILENAME",
    "SESSION_SCHEMA_VERSION",
    "LiveAcceptanceSession",
    "LiveAcceptanceSessionError",
    "LiveAcceptanceSessionResult",
    "SourceIntegritySnapshot",
    "TargetBaseline",
    "capture_source_integrity",
]
