"""Read-only release preflight checks for AIDD package releases."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

PACKAGE_NAME = "ai-driven-dev-v2"
COMMAND_TIMEOUT_SECONDS = 30.0
NETWORK_TIMEOUT_SECONDS = 10.0
BROWSER_TIMEOUT_SECONDS = 1_800.0


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    failure_kind: str | None = None


@dataclass(frozen=True, slots=True)
class PreflightCheck:
    name: str
    status: str
    detail: str
    blocker_kind: str | None = None


@dataclass(frozen=True, slots=True)
class PreflightResult:
    version: str
    success: bool
    checks: tuple[PreflightCheck, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


CommandRunner = Callable[[Sequence[str], Path], CommandResult]
BrowserProbe = Callable[[Path], CommandResult]
BinaryResolver = Callable[[str], str | None]
PyPIProbeStatus = Literal["exists", "absent", "error"]


@dataclass(frozen=True, slots=True)
class PyPIProbeResult:
    status: PyPIProbeStatus
    detail: str
    blocker_kind: str | None = None


PyPIVersionProbe = Callable[[str], bool | PyPIProbeResult]


def run_preflight(
    *,
    project_root: Path,
    version: str | None = None,
    expected_branch: str | None = None,
    gh_binary: str | None = None,
    uv_binary: str | None = None,
    check_pypi: bool = True,
    command_runner: CommandRunner | None = None,
    binary_resolver: BinaryResolver | None = None,
    pypi_version_exists: PyPIVersionProbe | None = None,
    packaged_ui_browser_probe: BrowserProbe | None = None,
) -> PreflightResult:
    root = project_root.resolve()
    runner = command_runner or _run_command
    resolver = binary_resolver or shutil.which
    source_version = _source_version(root)
    candidate_version = version or source_version
    checks: list[PreflightCheck] = []

    checks.append(_binary_check("uv", explicit_path=uv_binary, resolver=resolver))
    checks.append(_binary_check("gh", explicit_path=gh_binary, resolver=resolver))
    checks.append(
        PreflightCheck(
            name="source-version",
            status="pass" if source_version == candidate_version else "fail",
            detail=(
                f"pyproject.toml project.version={source_version}; "
                f"candidate={candidate_version}"
            ),
        )
    )

    branch = _invoke_command(
        runner,
        ("git", "rev-parse", "--abbrev-ref", "HEAD"),
        root,
    )
    branch_name = branch.stdout.strip()
    expected = expected_branch or f"release/v{candidate_version}"
    checks.append(
        PreflightCheck(
            name="branch",
            status="pass" if branch.returncode == 0 and branch_name == expected else "fail",
            detail=branch_name or branch.stderr.strip() or f"expected {expected}",
            blocker_kind=branch.failure_kind,
        )
    )

    remote_tag = _invoke_command(
        runner,
        ("git", "ls-remote", "--tags", "origin", f"refs/tags/v{candidate_version}"),
        root,
    )
    tag_exists = bool(remote_tag.stdout.strip())
    checks.append(
        PreflightCheck(
            name="remote-tag-absence",
            status="pass" if remote_tag.returncode == 0 and not tag_exists else "fail",
            detail=(
                f"remote tag v{candidate_version} absent"
                if remote_tag.returncode == 0 and not tag_exists
                else remote_tag.stdout.strip()
                or remote_tag.stderr.strip()
                or f"remote tag v{candidate_version} exists"
            ),
            blocker_kind=remote_tag.failure_kind,
        )
    )

    if check_pypi:
        exists_probe = pypi_version_exists or _probe_pypi_version
        try:
            raw_probe = exists_probe(candidate_version)
        except Exception as exc:
            probe = _pypi_exception_result(exc)
        else:
            probe = (
                PyPIProbeResult(
                    status="exists" if raw_probe else "absent",
                    detail=(
                        f"PyPI version {candidate_version} already exists"
                        if raw_probe
                        else f"PyPI version {candidate_version} absent"
                    ),
                )
                if isinstance(raw_probe, bool)
                else raw_probe
            )
        checks.append(
            PreflightCheck(
                name="pypi-version-absence",
                status="pass" if probe.status == "absent" else "fail",
                detail=probe.detail,
                blocker_kind=probe.blocker_kind,
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="pypi-version-absence",
                status="skip",
                detail="PyPI version probe skipped by operator flag.",
            )
        )

    browser_probe = packaged_ui_browser_probe or _run_packaged_ui_browser
    checks.append(_packaged_ui_browser_check(root, probe=browser_probe))

    return PreflightResult(
        version=candidate_version,
        success=all(check.status in {"pass", "skip"} for check in checks),
        checks=tuple(checks),
    )


def _binary_check(
    name: str,
    *,
    explicit_path: str | None,
    resolver: BinaryResolver,
) -> PreflightCheck:
    resolved = explicit_path or resolver(name)
    return PreflightCheck(
        name=f"{name}-binary",
        status="pass" if resolved else "fail",
        detail=resolved or f"{name} not found in PATH; pass --{name}-binary if installed elsewhere",
    )


def _packaged_ui_browser_check(
    project_root: Path,
    *,
    probe: BrowserProbe,
) -> PreflightCheck:
    try:
        result = probe(project_root)
    except subprocess.TimeoutExpired as exc:
        result = CommandResult(
            returncode=124,
            stderr=f"packaged UI browser runner timed out: {exc}",
            failure_kind="timeout",
        )
    except OSError as exc:
        result = CommandResult(
            returncode=127,
            stderr=f"{type(exc).__name__}: {exc}",
            failure_kind="browser-infrastructure",
        )
    detail = result.stdout.strip() or result.stderr.strip()
    if result.returncode == 0:
        return PreflightCheck(
            name="packaged-ui-browser",
            status="pass",
            detail=detail or "All declared packaged UI browser journeys passed.",
        )
    return PreflightCheck(
        name="packaged-ui-browser",
        status="fail",
        detail=detail or f"Packaged UI browser runner exited {result.returncode}.",
        blocker_kind=result.failure_kind or "browser-journey",
    )


def _run_packaged_ui_browser(project_root: Path) -> CommandResult:
    runner_path = project_root / "scripts" / "run_packaged_ui_scenarios.py"
    if not runner_path.is_file():
        return CommandResult(
            returncode=127,
            stderr=f"Packaged UI browser runner is missing: {runner_path}",
            failure_kind="browser-infrastructure",
        )
    try:
        completed = subprocess.run(
            (sys.executable, runner_path.as_posix()),
            cwd=project_root,
            check=False,
            text=True,
            capture_output=True,
            timeout=BROWSER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            returncode=124,
            stderr=(
                "packaged UI browser runner timed out after "
                f"{BROWSER_TIMEOUT_SECONDS:.0f}s"
            ),
            failure_kind="timeout",
        )
    except OSError as exc:
        return CommandResult(
            returncode=127,
            stderr=f"{type(exc).__name__}: {exc}",
            failure_kind="browser-infrastructure",
        )
    combined = f"{completed.stdout}\n{completed.stderr}".lower()
    infrastructure_markers = (
        "executable doesn't exist",
        "playwright install chromium",
        "browser type launch",
    )
    blocker_kind = (
        "browser-infrastructure"
        if any(marker in combined for marker in infrastructure_markers)
        else "browser-preflight"
        if completed.returncode == 2
        else "browser-journey"
        if completed.returncode != 0
        else None
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        failure_kind=blocker_kind,
    )


def _source_version(project_root: Path) -> str:
    pyproject_path = project_root / "pyproject.toml"
    with pyproject_path.open("rb") as file_obj:
        payload = tomllib.load(file_obj)
    project = payload.get("project", {})
    version = project.get("version") if isinstance(project, dict) else None
    if not isinstance(version, str):
        raise ValueError("pyproject.toml must contain [project].version")
    return version


def _run_command(argv: Sequence[str], cwd: Path) -> CommandResult:
    try:
        completed = subprocess.run(
            tuple(argv),
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            returncode=124,
            stderr=f"command timed out after {COMMAND_TIMEOUT_SECONDS:.0f}s",
            failure_kind="timeout",
        )
    except OSError as exc:
        return CommandResult(
            returncode=127,
            stderr=f"{type(exc).__name__}: {exc}",
            failure_kind="transport",
        )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _invoke_command(
    runner: CommandRunner,
    argv: Sequence[str],
    cwd: Path,
) -> CommandResult:
    try:
        return runner(argv, cwd)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            returncode=124,
            stderr=f"command timed out: {exc}",
            failure_kind="timeout",
        )
    except OSError as exc:
        return CommandResult(
            returncode=127,
            stderr=f"{type(exc).__name__}: {exc}",
            failure_kind="transport",
        )


def _probe_pypi_version(version: str) -> PyPIProbeResult:
    url = f"https://pypi.org/pypi/{PACKAGE_NAME}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=NETWORK_TIMEOUT_SECONDS) as response:  # noqa: S310
            if response.status == 200:
                return PyPIProbeResult(
                    status="exists",
                    detail=f"PyPI version {version} already exists",
                )
            return PyPIProbeResult(
                status="error",
                detail=f"PyPI registry returned unexpected HTTP {response.status}",
                blocker_kind="server",
            )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return PyPIProbeResult(
                status="absent",
                detail=f"PyPI version {version} absent",
            )
        return PyPIProbeResult(
            status="error",
            detail=f"PyPI registry returned HTTP {exc.code}",
            blocker_kind="server",
        )
    except Exception as exc:
        return _pypi_exception_result(exc)


def _pypi_exception_result(exc: BaseException) -> PyPIProbeResult:
    if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)):
        blocker_kind = "timeout"
    elif isinstance(exc, urllib.error.HTTPError):
        blocker_kind = "server"
    elif isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        reason_text = str(reason).lower()
        blocker_kind = (
            "tls"
            if "ssl" in reason_text or "certificate" in reason_text
            else "dns"
            if "name resolution" in reason_text or "nodename" in reason_text
            else "transport"
        )
    else:
        blocker_kind = "transport"
    return PyPIProbeResult(
        status="error",
        detail=f"PyPI registry probe failed: {type(exc).__name__}: {exc}",
        blocker_kind=blocker_kind,
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--version", default=None)
    parser.add_argument("--expected-branch", default=None)
    parser.add_argument("--gh-binary", default=None)
    parser.add_argument("--uv-binary", default=None)
    parser.add_argument("--skip-pypi", action="store_true")
    return parser.parse_args(tuple(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = run_preflight(
            project_root=args.project_root,
            version=args.version,
            expected_branch=args.expected_branch,
            gh_binary=args.gh_binary,
            uv_binary=args.uv_binary,
            check_pypi=not args.skip_pypi,
        )
    except Exception as exc:
        result = PreflightResult(
            version=args.version or "unknown",
            success=False,
            checks=(
                PreflightCheck(
                    name="preflight-execution",
                    status="fail",
                    detail=f"{type(exc).__name__}: {exc}",
                    blocker_kind="preflight",
                ),
            ),
        )
    print(result.to_json())
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
