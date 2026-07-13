from __future__ import annotations

import json
import os
import shutil
import socket
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class RunMutationConflict(RuntimeError):
    """Raised when another process already owns a run mutation lease."""


@dataclass(frozen=True, slots=True)
class RunMutationLease:
    path: Path
    token: str
    operation: str


_PROCESS_LEASES_LOCK = threading.Lock()
_PROCESS_LEASES: dict[Path, tuple[int, RunMutationLease, int]] = {}


def _lease_payload(*, token: str, operation: str) -> dict[str, object]:
    return {
        "schema_version": 2,
        "token": token,
        "operation": operation,
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return True
    return True


def _read_owner(lease_path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads((lease_path / "owner.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _reclaim_dead_owner(lease_path: Path) -> bool:
    payload = _read_owner(lease_path)
    if payload is None or payload.get("hostname") != socket.gethostname():
        return False
    pid = payload.get("pid")
    if not isinstance(pid, int) or _pid_is_alive(pid):
        return False
    stale_path = lease_path.with_name(f"{lease_path.name}.stale-{uuid4().hex}")
    try:
        lease_path.rename(stale_path)
    except OSError:
        return False
    shutil.rmtree(stale_path, ignore_errors=True)
    return True


def _create_filesystem_lease(run_root: Path, *, operation: str) -> RunMutationLease:
    run_root.mkdir(parents=True, exist_ok=True)
    lease_path = run_root / ".mutation-lease"
    token = uuid4().hex
    for _ in range(2):
        try:
            lease_path.mkdir()
            break
        except FileExistsError as exc:
            if _reclaim_dead_owner(lease_path):
                continue
            payload = _read_owner(lease_path) or {}
            owner = str(payload.get("operation", "unknown"))
            raise RunMutationConflict(
                f"Run mutation conflict: operation '{owner}' already owns the run lease."
            ) from exc
    else:  # pragma: no cover - loop always returns or raises
        raise RunMutationConflict("Run mutation conflict: the run lease is unavailable.")
    owner_path = lease_path / "owner.json"
    try:
        owner_path.write_text(
            json.dumps(
                _lease_payload(token=token, operation=operation),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(lease_path, ignore_errors=True)
        raise
    return RunMutationLease(path=lease_path, token=token, operation=operation)


def acquire_run_mutation_lease_handle(
    run_root: Path,
    *,
    operation: str,
    allow_reentrant: bool = False,
) -> RunMutationLease:
    """Acquire a lease that may be transferred to a background worker."""

    normalized_operation = operation.strip()
    if not normalized_operation:
        raise ValueError("Run mutation operation must not be empty.")
    lease_path = run_root / ".mutation-lease"
    owner_thread = threading.get_ident()
    with _PROCESS_LEASES_LOCK:
        existing = _PROCESS_LEASES.get(lease_path)
        if existing is not None:
            thread_id, lease, depth = existing
            if thread_id != owner_thread or not allow_reentrant:
                raise RunMutationConflict(
                    f"Run mutation conflict: operation '{lease.operation}' already owns "
                    "the run lease."
                )
            _PROCESS_LEASES[lease_path] = (thread_id, lease, depth + 1)
            return lease
    lease = _create_filesystem_lease(run_root, operation=normalized_operation)
    with _PROCESS_LEASES_LOCK:
        _PROCESS_LEASES[lease.path] = (owner_thread, lease, 1)
    return lease


def transfer_run_mutation_lease(lease: RunMutationLease) -> None:
    """Transfer process-local ownership to the calling worker thread."""

    with _PROCESS_LEASES_LOCK:
        existing = _PROCESS_LEASES.get(lease.path)
        if existing is None or existing[1].token != lease.token:
            raise RunMutationConflict("Run mutation lease is no longer owned by this process.")
        _PROCESS_LEASES[lease.path] = (threading.get_ident(), lease, existing[2])


def release_run_mutation_lease(lease: RunMutationLease) -> None:
    remove_filesystem_lease = False
    with _PROCESS_LEASES_LOCK:
        existing = _PROCESS_LEASES.get(lease.path)
        if existing is None or existing[1].token != lease.token:
            return
        thread_id, current, depth = existing
        if depth > 1:
            _PROCESS_LEASES[lease.path] = (thread_id, current, depth - 1)
            return
        _PROCESS_LEASES.pop(lease.path, None)
        remove_filesystem_lease = True
    if not remove_filesystem_lease:
        return
    payload = _read_owner(lease.path) or {}
    if payload.get("token") == lease.token:
        shutil.rmtree(lease.path, ignore_errors=True)


@contextmanager
def use_transferred_run_mutation_lease(
    lease: RunMutationLease,
) -> Iterator[RunMutationLease]:
    transfer_run_mutation_lease(lease)
    try:
        yield lease
    finally:
        release_run_mutation_lease(lease)


@contextmanager
def acquire_run_mutation_lease(
    run_root: Path,
    *,
    operation: str,
) -> Iterator[RunMutationLease]:
    lease = acquire_run_mutation_lease_handle(
        run_root,
        operation=operation,
        allow_reentrant=True,
    )
    try:
        yield lease
    finally:
        release_run_mutation_lease(lease)


__all__ = [
    "RunMutationConflict",
    "RunMutationLease",
    "acquire_run_mutation_lease",
    "acquire_run_mutation_lease_handle",
    "release_run_mutation_lease",
    "transfer_run_mutation_lease",
    "use_transferred_run_mutation_lease",
]
