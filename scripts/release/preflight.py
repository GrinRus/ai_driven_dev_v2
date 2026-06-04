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

PACKAGE_NAME = "ai-driven-dev-v2"


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True, slots=True)
class PreflightCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class PreflightResult:
    version: str
    success: bool
    checks: tuple[PreflightCheck, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


CommandRunner = Callable[[Sequence[str], Path], CommandResult]
BinaryResolver = Callable[[str], str | None]
PyPIVersionProbe = Callable[[str], bool]


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

    branch = runner(("git", "rev-parse", "--abbrev-ref", "HEAD"), root)
    branch_name = branch.stdout.strip()
    expected = expected_branch or f"release/v{candidate_version}"
    checks.append(
        PreflightCheck(
            name="branch",
            status="pass" if branch.returncode == 0 and branch_name == expected else "fail",
            detail=branch_name or branch.stderr.strip() or f"expected {expected}",
        )
    )

    remote_tag = runner(
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
        )
    )

    if check_pypi:
        exists_probe = pypi_version_exists or _pypi_version_exists
        exists = exists_probe(candidate_version)
        checks.append(
            PreflightCheck(
                name="pypi-version-absence",
                status="pass" if not exists else "fail",
                detail=(
                    f"PyPI version {candidate_version} absent"
                    if not exists
                    else f"PyPI version {candidate_version} already exists"
                ),
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


def _source_version(project_root: Path) -> str:
    pyproject_path = project_root / "pyproject.toml"
    with pyproject_path.open("rb") as file_obj:
        payload = tomllib.load(file_obj)
    project = payload.get("project", {})
    if not isinstance(project, dict) or not isinstance(project.get("version"), str):
        raise ValueError("pyproject.toml must contain [project].version")
    return project["version"]


def _run_command(argv: Sequence[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(
        tuple(argv),
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _pypi_version_exists(version: str) -> bool:
    url = f"https://pypi.org/pypi/{PACKAGE_NAME}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310
            return response.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


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
    result = run_preflight(
        project_root=args.project_root,
        version=args.version,
        expected_branch=args.expected_branch,
        gh_binary=args.gh_binary,
        uv_binary=args.uv_binary,
        check_pypi=not args.skip_pypi,
    )
    print(result.to_json())
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
