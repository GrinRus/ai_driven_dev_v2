from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from aidd.harness.live_acceptance_visibility import (
    VisibilityProbeTarget,
    run_live_acceptance_visibility_canary,
)
from aidd.harness.live_provider_auth_probe import probe_provider_auth_state
from aidd.harness.live_provider_auth_seed import (
    LiveProviderAuthSeedError,
    ProviderAuthRuntime,
    ProviderAuthSeedRequest,
    provider_auth_relative_destination,
    seed_provider_auth_state,
)

IsolationBackend = Literal["macos-seatbelt", "linux-bubblewrap"]

_SAFE_ENVIRONMENT_KEYS = frozenset(
    {
        "COLORTERM",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TERM",
        "TZ",
    }
)
_PRIVATE_ENVIRONMENT_PATHS = {
    "HOME": "home",
    "TMPDIR": "tmp",
    "TMP": "tmp",
    "TEMP": "tmp",
    "XDG_CONFIG_HOME": "config",
    "XDG_CACHE_HOME": "cache",
    "XDG_DATA_HOME": "data",
    "XDG_STATE_HOME": "state",
}
_ISOLATION_MARKER = "AIDD_LIVE_ISOLATION_ACTIVE"
_MACOS_DEVELOPER_ROOT_PARENTS = (
    Path("/Applications"),
    Path("/Library/Developer"),
)
_MACOS_DEVELOPER_ROOT_TIMEOUT_SECONDS = 5
_MACOS_SYSTEM_TLS_READ_ROOTS = (Path("/private/etc/ssl"),)


class LiveAcceptanceIsolationError(RuntimeError):
    """Raised when a live provider cannot be placed behind a proven boundary."""


@dataclass(frozen=True, slots=True)
class LiveAcceptanceIsolationBoundary:
    backend: IsolationBackend
    source_checkout: Path
    external_root: Path
    provider_root: Path
    private_root: Path
    operator_home: Path | None
    tool_read_roots: tuple[Path, ...]
    environment: dict[str, str]
    launch_prefix: tuple[str, ...]

    def wrap_command(self, command: Sequence[str]) -> tuple[str, ...]:
        if not command:
            raise LiveAcceptanceIsolationError("Isolated command must not be empty.")
        return (*self.launch_prefix, *command)


@dataclass(frozen=True, slots=True)
class LiveAcceptanceIsolationCapability:
    backend: IsolationBackend
    supported: bool
    detail: str


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _nested(left: Path, right: Path) -> bool:
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _validate_roots(
    *,
    source_checkout: Path,
    external_root: Path,
    provider_root: Path,
) -> tuple[Path, Path, Path]:
    source = _resolved(source_checkout)
    external = _resolved(external_root)
    lexical_provider = Path(os.path.abspath(provider_root.expanduser()))
    if lexical_provider.is_symlink():
        raise LiveAcceptanceIsolationError(
            "Provider root must be a real directory, not a symlink."
        )
    provider = _resolved(lexical_provider)
    if not source.is_dir():
        raise LiveAcceptanceIsolationError("AIDD source checkout must exist.")
    if not external.is_dir():
        raise LiveAcceptanceIsolationError("External live root must already exist.")
    if provider.parent != external:
        raise LiveAcceptanceIsolationError(
            "Provider root must be exactly one component below the external live root."
        )
    if _nested(source, external):
        raise LiveAcceptanceIsolationError(
            "AIDD source checkout and external live root must not overlap."
        )
    return source, external, provider


def _private_environment(
    *,
    inherited: Mapping[str, str],
    private_root: Path,
    credential_environment_keys: Sequence[str],
) -> dict[str, str]:
    credential_keys = tuple(credential_environment_keys)
    if len(set(credential_keys)) != len(credential_keys):
        raise LiveAcceptanceIsolationError(
            "Credential environment allowlist contains duplicate keys."
        )
    if any(not key or "=" in key or "\x00" in key for key in credential_keys):
        raise LiveAcceptanceIsolationError(
            "Credential environment allowlist contains an invalid key."
        )
    allowed_keys = _SAFE_ENVIRONMENT_KEYS.union(credential_keys)
    environment = {
        key: value
        for key, value in inherited.items()
        if key in allowed_keys and "\x00" not in value
    }
    for key, relative in _PRIVATE_ENVIRONMENT_PATHS.items():
        environment[key] = (private_root / relative).as_posix()
    environment[_ISOLATION_MARKER] = "1"
    return environment


def _prepare_private_root(provider_root: Path) -> Path:
    private_root = provider_root / ".live-provider-private"
    if private_root.is_symlink():
        raise LiveAcceptanceIsolationError(
            "Provider-private root must not be a symlink."
        )
    private_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    for relative in set(_PRIVATE_ENVIRONMENT_PATHS.values()):
        path = private_root / relative
        if path.is_symlink():
            raise LiveAcceptanceIsolationError(
                "Provider-private environment directories must not be symlinks."
            )
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.chmod(0o700)
    return private_root


def _sbpl_string(value: Path) -> str:
    return value.as_posix().replace("\\", "\\\\").replace('"', '\\"')


def _macos_profile(
    *,
    source_checkout: Path,
    provider_root: Path,
    tool_read_roots: Sequence[Path],
) -> str:
    read_roots = tuple(dict.fromkeys((source_checkout, provider_root, *tool_read_roots)))
    read_filters = " ".join(
        f'(subpath "{_sbpl_string(root)}")' for root in read_roots
    )
    return " ".join(
        (
            "(version 1)",
            "(deny default)",
            '(import "system.sb")',
            "(allow process*)",
            "(allow signal (target same-sandbox))",
            "(allow network*)",
            "(allow sysctl-read)",
            "(allow mach-lookup mach-register)",
            "(allow ipc-posix*)",
            '(allow file-read-metadata file-test-existence (subpath "/"))',
            f"(allow file-read* file-map-executable {read_filters})",
            f'(allow file-write* (subpath "{_sbpl_string(provider_root)}"))',
        )
    )


def _directory_components(path: Path, *, below: Path) -> tuple[Path, ...]:
    relative = path.relative_to(below)
    current = below
    components: list[Path] = []
    for part in relative.parts:
        current /= part
        components.append(current)
    return tuple(components)


def _linux_prefix(
    *,
    executable: str,
    source_checkout: Path,
    external_root: Path,
    provider_root: Path,
    operator_home: Path | None,
    tool_read_roots: Sequence[Path],
) -> tuple[str, ...]:
    prefix: list[str] = [
        executable,
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        "--share-net",
        "--ro-bind",
        "/",
        "/",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
    ]
    hidden_roots = [external_root]
    if operator_home is not None and not _nested(operator_home, external_root):
        hidden_roots.append(operator_home)
    for hidden in hidden_roots:
        prefix.extend(("--tmpfs", hidden.as_posix()))

    restored_roots = tuple(
        dict.fromkeys((source_checkout, provider_root, *tool_read_roots))
    )
    for root in restored_roots:
        containing_hidden = next(
            (hidden for hidden in hidden_roots if root.is_relative_to(hidden)),
            None,
        )
        if containing_hidden is not None:
            for component in _directory_components(root, below=containing_hidden):
                prefix.extend(("--dir", component.as_posix()))
        bind_flag = "--bind" if root == provider_root else "--ro-bind"
        prefix.extend((bind_flag, root.as_posix(), root.as_posix()))
    return tuple(prefix)


def _macos_developer_tool_root() -> Path | None:
    executable = Path("/usr/bin/xcode-select")
    if not executable.is_file():
        return None
    try:
        completed = subprocess.run(
            (executable.as_posix(), "--print-path"),
            capture_output=True,
            text=True,
            check=False,
            timeout=_MACOS_DEVELOPER_ROOT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    raw_path = completed.stdout.strip()
    if not raw_path or not Path(raw_path).is_absolute():
        return None
    selected = _resolved(Path(raw_path))
    trusted_parents = tuple(_resolved(path) for path in _MACOS_DEVELOPER_ROOT_PARENTS)
    if not selected.is_dir() or not any(
        selected.is_relative_to(parent) for parent in trusted_parents
    ):
        return None
    return selected


def _macos_system_tls_read_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    for candidate in _MACOS_SYSTEM_TLS_READ_ROOTS:
        if candidate.is_symlink():
            continue
        resolved = _resolved(candidate)
        if resolved == candidate and resolved.is_dir():
            roots.append(resolved)
    return tuple(roots)


def _default_tool_read_roots(*, system_name: str) -> tuple[Path, ...]:
    roots: list[Path] = []
    candidates: tuple[Path, ...] = (
        Path(sys.prefix),
        Path(sys.executable).resolve(strict=False).parents[3],
        Path(__file__).resolve(strict=False).parents[3],
        Path("/usr/local"),
        Path("/opt/homebrew"),
    )
    if system_name == "Darwin":
        developer_root = _macos_developer_tool_root()
        if developer_root is not None:
            candidates = (*candidates, developer_root)
        candidates = (*candidates, *_macos_system_tls_read_roots())
    for candidate in candidates:
        resolved = _resolved(candidate)
        if resolved.exists() and resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def prepare_live_acceptance_isolation(
    *,
    source_checkout: Path,
    external_root: Path,
    provider_root: Path,
    inherited_environment: Mapping[str, str] | None = None,
    credential_environment_keys: Sequence[str] = (),
    tool_read_roots: Sequence[Path] = (),
    system_name: str | None = None,
) -> LiveAcceptanceIsolationBoundary:
    source, external, provider = _validate_roots(
        source_checkout=source_checkout,
        external_root=external_root,
        provider_root=provider_root,
    )
    provider.mkdir(mode=0o700, exist_ok=True)
    if not provider.is_dir() or provider.is_symlink():
        raise LiveAcceptanceIsolationError(
            "Provider root must be a real directory, not a symlink."
        )
    private_root = _prepare_private_root(provider)
    inherited = os.environ if inherited_environment is None else inherited_environment
    operator_home_raw = inherited.get("HOME")
    operator_home = (
        _resolved(Path(operator_home_raw))
        if operator_home_raw and Path(operator_home_raw).is_absolute()
        else None
    )
    detected_system = system_name or platform.system()
    explicit_tool_roots = tuple(_resolved(path) for path in tool_read_roots)
    all_tool_roots = tuple(
        dict.fromkeys(
            (
                *_default_tool_read_roots(system_name=detected_system),
                *explicit_tool_roots,
            )
        )
    )
    for root in all_tool_roots:
        if not root.exists():
            raise LiveAcceptanceIsolationError(
                f"Authorized tool read root does not exist: {root.as_posix()}."
            )
        if _nested(root, external) and not root.is_relative_to(provider):
            raise LiveAcceptanceIsolationError(
                "Tool read roots cannot authorize a sibling provider subtree."
            )
    environment = _private_environment(
        inherited=inherited,
        private_root=private_root,
        credential_environment_keys=credential_environment_keys,
    )
    launch_prefix: tuple[str, ...]
    if detected_system == "Darwin":
        executable = shutil.which("sandbox-exec")
        if executable is None:
            raise LiveAcceptanceIsolationError(
                "macOS sandbox-exec is unavailable; live provider execution is blocked."
            )
        backend: IsolationBackend = "macos-seatbelt"
        launch_prefix = (
            executable,
            "-p",
            _macos_profile(
                source_checkout=source,
                provider_root=provider,
                tool_read_roots=all_tool_roots,
            ),
        )
    elif detected_system == "Linux":
        executable = shutil.which("bwrap")
        if executable is None:
            raise LiveAcceptanceIsolationError(
                "Linux bubblewrap is unavailable; live provider execution is blocked."
            )
        backend = "linux-bubblewrap"
        launch_prefix = _linux_prefix(
            executable=executable,
            source_checkout=source,
            external_root=external,
            provider_root=provider,
            operator_home=operator_home,
            tool_read_roots=all_tool_roots,
        )
    else:
        raise LiveAcceptanceIsolationError(
            f"No enforceable live provider isolation backend for {detected_system!r}."
        )
    return LiveAcceptanceIsolationBoundary(
        backend=backend,
        source_checkout=source,
        external_root=external,
        provider_root=provider,
        private_root=private_root,
        operator_home=operator_home,
        tool_read_roots=all_tool_roots,
        environment=environment,
        launch_prefix=launch_prefix,
    )


def probe_live_acceptance_isolation_capability(
    *,
    system_name: str | None = None,
) -> LiveAcceptanceIsolationCapability:
    detected_system = system_name or platform.system()
    backend: IsolationBackend = (
        "macos-seatbelt" if detected_system == "Darwin" else "linux-bubblewrap"
    )
    if detected_system not in {"Darwin", "Linux"}:
        raise LiveAcceptanceIsolationError(
            f"No enforceable live provider isolation backend for {detected_system!r}."
        )
    with tempfile.TemporaryDirectory(prefix="aidd-live-isolation-capability-") as raw:
        root = Path(raw).resolve()
        source = root / "source"
        external = root / "external"
        provider = external / "provider-a"
        sibling = external / "provider-b"
        source.mkdir()
        external.mkdir()
        sibling.mkdir()
        (source / "marker.txt").write_text("source\n", encoding="utf-8")
        (sibling / "marker.txt").write_text("sibling\n", encoding="utf-8")
        try:
            boundary = prepare_live_acceptance_isolation(
                source_checkout=source,
                external_root=external,
                provider_root=provider,
                inherited_environment={
                    "HOME": (root / "operator-home").as_posix(),
                    "PATH": os.environ.get("PATH", ""),
                    "AIDD_SIBLING_CREDENTIAL": "must-not-cross",
                },
                system_name=detected_system,
            )
            (provider / "marker.txt").write_text("provider\n", encoding="utf-8")
            result = run_live_acceptance_visibility_canary(
                targets=(
                    VisibilityProbeTarget("source", source, "marker.txt"),
                    VisibilityProbeTarget("own-provider", provider, "marker.txt"),
                    VisibilityProbeTarget("sibling-provider", sibling, "marker.txt"),
                ),
                environment_keys=("AIDD_SIBLING_CREDENTIAL", _ISOLATION_MARKER),
                cwd=provider,
                environment=boundary.environment,
                launch_prefix=boundary.launch_prefix,
            )
        except (LiveAcceptanceIsolationError, OSError, ValueError) as exc:
            return LiveAcceptanceIsolationCapability(
                backend=backend,
                supported=False,
                detail=str(exc),
            )
    target_items = cast(list[dict[str, Any]], result.diagnostics["targets"])
    environment_items = cast(
        list[dict[str, Any]],
        result.diagnostics["environment"],
    )
    targets = {
        str(item["label"]): item
        for item in target_items
    }
    environment = {
        str(item["key"]): item
        for item in environment_items
    }
    source_ops = targets["source"]["operations"]
    own_ops = targets["own-provider"]["operations"]
    sibling_ops = targets["sibling-provider"]["operations"]
    supported = bool(
        own_ops["list"]["allowed"]
        and own_ops["read"]["allowed"]
        and own_ops["write"]["allowed"]
        and source_ops["read"]["allowed"]
        and not source_ops["write"]["allowed"]
        and not sibling_ops["list"]["allowed"]
        and not sibling_ops["read"]["allowed"]
        and not sibling_ops["write"]["allowed"]
        and environment[_ISOLATION_MARKER]["present"]
        and not environment["AIDD_SIBLING_CREDENTIAL"]["present"]
    )
    return LiveAcceptanceIsolationCapability(
        backend=boundary.backend,
        supported=supported,
        detail=(
            "isolation canary passed"
            if supported
            else "isolation canary observed an unauthorized capability"
        ),
    )


def require_live_acceptance_isolation_capability() -> LiveAcceptanceIsolationCapability:
    capability = probe_live_acceptance_isolation_capability()
    if not capability.supported:
        raise LiveAcceptanceIsolationError(
            f"{capability.backend} cannot enforce the required boundary: {capability.detail}"
        )
    return capability


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a live evaluator behind a provider-private OS filesystem boundary."
    )
    parser.add_argument("--source-checkout", type=Path, required=True)
    parser.add_argument("--external-root", type=Path, required=True)
    parser.add_argument("--provider-root", type=Path, required=True)
    parser.add_argument(
        "--runtime",
        choices=("codex", "claude-code"),
        required=True,
    )
    parser.add_argument(
        "--seed-provider-auth-from-home",
        action="store_true",
        help="Copy only the runtime's allowlisted auth file into a fresh private HOME.",
    )
    parser.add_argument("--credential-environment-key", action="append", default=[])
    parser.add_argument("--tool-read-root", action="append", type=Path, default=[])
    parser.add_argument(
        "--resume-existing-provider",
        action="store_true",
        help="Allow an existing provider root only for an explicit guarded resume.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    from aidd.harness.live_acceptance_session import (
        LiveAcceptanceSession,
        LiveAcceptanceSessionError,
    )

    args = _parse_args(argv)
    command = tuple(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("live acceptance isolation: command is required", file=sys.stderr)
        return 2
    if args.seed_provider_auth_from_home and args.resume_existing_provider:
        print(
            "live acceptance isolation: --seed-provider-auth-from-home is "
            "incompatible with --resume-existing-provider",
            file=sys.stderr,
        )
        return 2
    if args.resume_existing_provider and not any(
        item == "--run-id" or item.startswith("--run-id=") for item in command
    ):
        print(
            "live acceptance isolation: --resume-existing-provider requires "
            "an explicit nested --run-id",
            file=sys.stderr,
        )
        return 2
    try:
        with LiveAcceptanceSession(
            source_checkout=args.source_checkout,
            external_root=args.external_root,
            provider_root=args.provider_root,
            allow_existing_provider=bool(args.resume_existing_provider),
        ) as session:
            boundary = prepare_live_acceptance_isolation(
                source_checkout=args.source_checkout,
                external_root=args.external_root,
                provider_root=args.provider_root,
                credential_environment_keys=tuple(args.credential_environment_key),
                tool_read_roots=tuple(args.tool_read_root),
            )
            runtime = cast(ProviderAuthRuntime, args.runtime)
            relative_destination = provider_auth_relative_destination(runtime)
            seed_mode: Literal[
                "none",
                "seeded-from-operator-home",
                "existing-private-home",
            ] = (
                "existing-private-home"
                if args.resume_existing_provider
                else (
                    "seeded-from-operator-home"
                    if args.seed_provider_auth_from_home
                    else "none"
                )
            )
            session.record_provider_auth(
                runtime=runtime,
                seed_mode=seed_mode,
                relative_destination=relative_destination,
                probe_status="pending",
            )
            if args.seed_provider_auth_from_home:
                if boundary.operator_home is None:
                    raise LiveProviderAuthSeedError(
                        "Provider auth seed requires an absolute operator HOME."
                    )
                seed_provider_auth_state(
                    ProviderAuthSeedRequest(
                        runtime=runtime,
                        operator_home=boundary.operator_home,
                        provider_private_home=Path(boundary.environment["HOME"]),
                    )
                )
            auth_probe = probe_provider_auth_state(
                runtime=runtime,
                boundary=boundary,
            )
            session.record_provider_auth(
                runtime=runtime,
                seed_mode=seed_mode,
                relative_destination=relative_destination,
                probe_status=auth_probe.status,
            )
            if auth_probe.status != "pass":
                completed_exit_code = 2
                session.record_process_exit(completed_exit_code)
            else:
                completed = subprocess.run(
                    boundary.wrap_command(command),
                    cwd=boundary.provider_root,
                    env=boundary.environment,
                    check=False,
                )
                completed_exit_code = completed.returncode
                session.record_process_exit(completed_exit_code)
    except (
        LiveAcceptanceIsolationError,
        LiveAcceptanceSessionError,
        LiveProviderAuthSeedError,
    ) as exc:
        print(f"live acceptance isolation: {exc}", file=sys.stderr)
        return 2
    if auth_probe.status != "pass":
        print(
            "live acceptance isolation: provider-auth blocker: "
            f"isolated {args.runtime} status probe {auth_probe.status}",
            file=sys.stderr,
        )
    return completed_exit_code


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "LiveAcceptanceIsolationBoundary",
    "LiveAcceptanceIsolationCapability",
    "LiveAcceptanceIsolationError",
    "prepare_live_acceptance_isolation",
    "probe_live_acceptance_isolation_capability",
    "require_live_acceptance_isolation_capability",
]
