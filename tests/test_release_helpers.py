from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PREFLIGHT = _load_module(
    "release_preflight",
    _REPO_ROOT / "scripts" / "release" / "preflight.py",
)
_EVIDENCE = _load_module(
    "release_evidence_collector",
    _REPO_ROOT / "scripts" / "release" / "evidence_collector.py",
)

CommandResult = _PREFLIGHT.CommandResult
run_preflight = _PREFLIGHT.run_preflight
collect_release_evidence = _EVIDENCE.collect_release_evidence


def test_release_preflight_passes_for_unpublished_release_branch(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.1.0a9")

    def runner(argv: Sequence[str], _cwd: Path) -> CommandResult:
        if tuple(argv[:3]) == ("git", "rev-parse", "--abbrev-ref"):
            return CommandResult(returncode=0, stdout="release/v0.1.0a9\n")
        if tuple(argv[:3]) == ("git", "ls-remote", "--tags"):
            return CommandResult(returncode=0, stdout="")
        raise AssertionError(f"unexpected command: {argv}")

    result = run_preflight(
        project_root=tmp_path,
        command_runner=runner,
        binary_resolver=lambda name: f"/usr/local/bin/{name}",
        pypi_version_exists=lambda _version: False,
    )

    assert result.success is True
    assert [check.status for check in result.checks] == [
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    ]


def test_release_preflight_reports_missing_binaries_existing_tag_and_pypi(
    tmp_path: Path,
) -> None:
    _write_pyproject(tmp_path, "0.1.0a9")

    def runner(argv: Sequence[str], _cwd: Path) -> CommandResult:
        if tuple(argv[:3]) == ("git", "rev-parse", "--abbrev-ref"):
            return CommandResult(returncode=0, stdout="main\n")
        if tuple(argv[:3]) == ("git", "ls-remote", "--tags"):
            return CommandResult(
                returncode=0,
                stdout="deadbeef\trefs/tags/v0.1.0a9\n",
            )
        raise AssertionError(f"unexpected command: {argv}")

    result = run_preflight(
        project_root=tmp_path,
        command_runner=runner,
        binary_resolver=lambda _name: None,
        pypi_version_exists=lambda _version: True,
    )

    statuses = {check.name: check.status for check in result.checks}
    assert result.success is False
    assert statuses["uv-binary"] == "fail"
    assert statuses["gh-binary"] == "fail"
    assert statuses["branch"] == "fail"
    assert statuses["remote-tag-absence"] == "fail"
    assert statuses["pypi-version-absence"] == "fail"


def test_release_preflight_reports_mismatched_source_version(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.1.0a9.dev0")

    def runner(argv: Sequence[str], _cwd: Path) -> CommandResult:
        if tuple(argv[:3]) == ("git", "rev-parse", "--abbrev-ref"):
            return CommandResult(returncode=0, stdout="release/v0.1.0a9\n")
        if tuple(argv[:3]) == ("git", "ls-remote", "--tags"):
            return CommandResult(returncode=0, stdout="")
        raise AssertionError(f"unexpected command: {argv}")

    result = run_preflight(
        project_root=tmp_path,
        version="0.1.0a9",
        command_runner=runner,
        binary_resolver=lambda name: f"/usr/local/bin/{name}",
        pypi_version_exists=lambda _version: False,
    )

    source_version = next(
        check for check in result.checks if check.name == "source-version"
    )
    assert result.success is False
    assert source_version.status == "fail"
    assert "0.1.0a9.dev0" in source_version.detail


def test_release_evidence_collector_accepts_expected_links_and_outputs() -> None:
    evidence = collect_release_evidence(
        version="0.1.0a9",
        github_release_url="https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a9",
        release_workflow_url="https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/123",
        pypi_url="https://pypi.org/project/ai-driven-dev-v2/0.1.0a9/",
        pipx_version_output="aidd 0.1.0a9",
        pipx_doctor_output="Version 0.1.0a9\nRuntime readiness ok",
        uv_tool_version_output="aidd 0.1.0a9",
        uv_tool_doctor_output="Version 0.1.0a9\nRuntime readiness ok",
    )

    assert evidence.success is True
    assert "`github-release-url`: `pass`" in evidence.to_markdown()
    assert "v0.1.0a9" in evidence.to_json()


def test_release_evidence_collector_rejects_mismatched_output() -> None:
    evidence = collect_release_evidence(
        version="0.1.0a9",
        github_release_url="https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a9",
        release_workflow_url="https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/123",
        pypi_url="https://pypi.org/project/ai-driven-dev-v2/0.1.0a9/",
        pipx_version_output="aidd 0.1.0a8",
        pipx_doctor_output="Version 0.1.0a9",
        uv_tool_version_output="aidd 0.1.0a9",
        uv_tool_doctor_output="Version 0.1.0a9",
    )

    pipx_version = next(check for check in evidence.checks if check.name == "pipx-version")
    assert evidence.success is False
    assert pipx_version.status == "fail"


def _write_pyproject(root: Path, version: str) -> None:
    (root / "pyproject.toml").write_text(
        f"[project]\nname = \"ai-driven-dev-v2\"\nversion = \"{version}\"\n",
        encoding="utf-8",
    )
