from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from aidd.harness.live_e2e_black_box_steps import (
    BlackBoxCommandResult,
    _run_black_box_command,
)

VISIBILITY_CANARY_SCHEMA_VERSION = 1
VISIBILITY_CANARY_LAUNCH_BOUNDARY = (
    "aidd.harness.live_e2e_black_box_steps._run_black_box_command"
)
_MAX_READ_BYTES = 64 * 1024
_LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_ENVIRONMENT_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ProbeStatus = Literal["allowed", "denied", "error"]


class LiveAcceptanceVisibilityError(ValueError):
    """Raised when the visibility canary request or result is not trustworthy."""


@dataclass(frozen=True, slots=True)
class VisibilityProbeTarget:
    label: str
    root: Path
    read_relative_path: str

    def __post_init__(self) -> None:
        if _LABEL_PATTERN.fullmatch(self.label) is None:
            raise LiveAcceptanceVisibilityError(
                "Visibility target label must use lowercase letters, digits, and hyphens."
            )
        relative_path = Path(self.read_relative_path)
        if (
            not self.read_relative_path
            or relative_path.is_absolute()
            or "\\" in self.read_relative_path
            or any(part in {"", ".", ".."} for part in relative_path.parts)
        ):
            raise LiveAcceptanceVisibilityError(
                "Visibility target read path must be a contained relative POSIX path."
            )
        object.__setattr__(self, "root", self.root.resolve(strict=False))

    def to_payload(self) -> dict[str, str]:
        return {
            "label": self.label,
            "root": self.root.as_posix(),
            "read_relative_path": self.read_relative_path,
        }


@dataclass(frozen=True, slots=True)
class LiveAcceptanceVisibilityResult:
    diagnostics: dict[str, object]
    command_result: BlackBoxCommandResult


def _operation_error(exc: OSError) -> dict[str, object]:
    status: ProbeStatus = "denied" if isinstance(exc, PermissionError) else "error"
    return {
        "status": status,
        "allowed": False,
        "error_type": exc.__class__.__name__,
        "error_number": exc.errno,
    }


def _probe_list(root: Path) -> dict[str, object]:
    try:
        entry_names = sorted(entry.name for entry in root.iterdir())
    except OSError as exc:
        return _operation_error(exc)
    digest = hashlib.sha256("\n".join(entry_names).encode("utf-8")).hexdigest()
    return {
        "status": "allowed",
        "allowed": True,
        "entry_count": len(entry_names),
        "entry_names_sha256": digest,
    }


def _contained_read_path(target: VisibilityProbeTarget) -> Path:
    candidate = (target.root / target.read_relative_path).resolve(strict=False)
    if not candidate.is_relative_to(target.root):
        raise LiveAcceptanceVisibilityError(
            f"Visibility target `{target.label}` read path escapes its root."
        )
    return candidate


def _probe_read(target: VisibilityProbeTarget) -> dict[str, object]:
    try:
        path = _contained_read_path(target)
        byte_size = path.stat().st_size
        with path.open("rb") as stream:
            observed = stream.read(_MAX_READ_BYTES)
    except OSError as exc:
        return _operation_error(exc)
    return {
        "status": "allowed",
        "allowed": True,
        "byte_size": byte_size,
        "observed_bytes": len(observed),
        "observed_sha256": hashlib.sha256(observed).hexdigest(),
        "truncated": byte_size > len(observed),
    }


def _probe_write(root: Path) -> dict[str, object]:
    candidate = root / f".aidd-visibility-canary-{os.getpid()}-{uuid.uuid4().hex}"
    content = b"aidd-live-acceptance-visibility-canary\n"
    try:
        with candidate.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        observed = candidate.read_bytes()
        if observed != content:
            return {
                "status": "error",
                "allowed": False,
                "error_type": "CanaryContentMismatch",
                "error_number": None,
            }
    except OSError as exc:
        return _operation_error(exc)
    finally:
        try:
            candidate.unlink(missing_ok=True)
        except OSError:
            pass
    if candidate.exists():
        return {
            "status": "error",
            "allowed": False,
            "error_type": "CanaryCleanupFailure",
            "error_number": None,
        }
    return {
        "status": "allowed",
        "allowed": True,
        "bytes_written": len(content),
        "cleaned_up": True,
    }


def _probe_target(target: VisibilityProbeTarget) -> dict[str, object]:
    return {
        "label": target.label,
        "root": target.root.as_posix(),
        "read_relative_path": target.read_relative_path,
        "operations": {
            "list": _probe_list(target.root),
            "read": _probe_read(target),
            "write": _probe_write(target.root),
        },
    }


def _validate_environment_keys(keys: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(keys)
    if len(set(normalized)) != len(normalized):
        raise LiveAcceptanceVisibilityError("Visibility environment keys must be unique.")
    for key in normalized:
        if _ENVIRONMENT_KEY_PATTERN.fullmatch(key) is None:
            raise LiveAcceptanceVisibilityError(
                f"Invalid visibility environment key: {key!r}."
            )
    return normalized


def _environment_diagnostics(
    environment: Mapping[str, str],
    keys: Sequence[str],
) -> list[dict[str, object]]:
    return [
        {
            "key": key,
            "present": key in environment,
            "non_empty": bool(environment.get(key)),
        }
        for key in keys
    ]


def collect_live_acceptance_visibility(
    *,
    targets: Sequence[VisibilityProbeTarget],
    environment_keys: Sequence[str],
    environment: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> dict[str, object]:
    labels = tuple(target.label for target in targets)
    if not targets:
        raise LiveAcceptanceVisibilityError("Visibility canary requires at least one target.")
    if len(set(labels)) != len(labels):
        raise LiveAcceptanceVisibilityError("Visibility target labels must be unique.")
    normalized_keys = _validate_environment_keys(environment_keys)
    observed_environment = os.environ if environment is None else environment
    process_cwd = (cwd or Path.cwd()).resolve(strict=False)
    return {
        "schema_version": VISIBILITY_CANARY_SCHEMA_VERSION,
        "launch_boundary": VISIBILITY_CANARY_LAUNCH_BOUNDARY,
        "cwd": process_cwd.as_posix(),
        "targets": [_probe_target(target) for target in targets],
        "environment": _environment_diagnostics(observed_environment, normalized_keys),
    }


def _parse_diagnostics(stdout_text: str) -> dict[str, object]:
    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError as exc:
        raise LiveAcceptanceVisibilityError(
            "Visibility canary did not emit one valid JSON diagnostics object."
        ) from exc
    if not isinstance(payload, dict):
        raise LiveAcceptanceVisibilityError(
            "Visibility canary diagnostics must be a JSON object."
        )
    if payload.get("schema_version") != VISIBILITY_CANARY_SCHEMA_VERSION:
        raise LiveAcceptanceVisibilityError(
            "Visibility canary diagnostics use an unsupported schema version."
        )
    if payload.get("launch_boundary") != VISIBILITY_CANARY_LAUNCH_BOUNDARY:
        raise LiveAcceptanceVisibilityError(
            "Visibility canary diagnostics do not name the live command boundary."
        )
    if not isinstance(payload.get("targets"), list) or not isinstance(
        payload.get("environment"), list
    ):
        raise LiveAcceptanceVisibilityError(
            "Visibility canary diagnostics are missing target or environment observations."
        )
    return cast(dict[str, object], payload)


def run_live_acceptance_visibility_canary(
    *,
    targets: Sequence[VisibilityProbeTarget],
    environment_keys: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: float = 15.0,
    launch_prefix: Sequence[str] = (),
) -> LiveAcceptanceVisibilityResult:
    if not targets:
        raise LiveAcceptanceVisibilityError("Visibility canary requires at least one target.")
    _validate_environment_keys(environment_keys)
    command: list[str] = [
        sys.executable,
        "-m",
        "aidd.harness.live_acceptance_visibility",
        "probe",
    ]
    for target in targets:
        command.extend(("--target", json.dumps(target.to_payload(), sort_keys=True)))
    for key in environment_keys:
        command.extend(("--environment-key", key))
    command_result = _run_black_box_command(
        command=tuple(command),
        launch_prefix=launch_prefix,
        cwd=cwd,
        environment=dict(environment),
        timeout_seconds=timeout_seconds,
    )
    if command_result.exit_code != 0:
        detail = command_result.stderr_text.strip() or "no diagnostic error output"
        raise LiveAcceptanceVisibilityError(
            f"Visibility canary process failed with exit {command_result.exit_code}: {detail}"
        )
    return LiveAcceptanceVisibilityResult(
        diagnostics=_parse_diagnostics(command_result.stdout_text),
        command_result=command_result,
    )


def _target_from_json(raw: str) -> VisibilityProbeTarget:
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LiveAcceptanceVisibilityError("Visibility target must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise LiveAcceptanceVisibilityError("Visibility target must be a JSON object.")
    label = payload.get("label")
    root = payload.get("root")
    read_relative_path = payload.get("read_relative_path")
    if not all(isinstance(value, str) for value in (label, root, read_relative_path)):
        raise LiveAcceptanceVisibilityError(
            "Visibility target requires string label, root, and read_relative_path fields."
        )
    return VisibilityProbeTarget(
        label=cast(str, label),
        root=Path(cast(str, root)),
        read_relative_path=cast(str, read_relative_path),
    )


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Characterize live-acceptance process filesystem and environment visibility."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    probe = subparsers.add_parser("probe")
    probe.add_argument("--target", action="append", default=[])
    probe.add_argument("--environment-key", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        targets = tuple(_target_from_json(raw) for raw in args.target)
        diagnostics = collect_live_acceptance_visibility(
            targets=targets,
            environment_keys=tuple(args.environment_key),
        )
    except LiveAcceptanceVisibilityError as exc:
        print(f"live acceptance visibility canary: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "LiveAcceptanceVisibilityError",
    "LiveAcceptanceVisibilityResult",
    "VISIBILITY_CANARY_LAUNCH_BOUNDARY",
    "VISIBILITY_CANARY_SCHEMA_VERSION",
    "VisibilityProbeTarget",
    "collect_live_acceptance_visibility",
    "run_live_acceptance_visibility_canary",
]
