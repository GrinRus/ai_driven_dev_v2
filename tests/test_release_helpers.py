from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import urllib.error
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
preflight_main = _PREFLIGHT.main
collect_release_evidence = _EVIDENCE.collect_release_evidence


def _passing_browser_probe(_root: Path) -> CommandResult:
    return CommandResult(
        returncode=0,
        stdout='{"discovered_ids": [], "executed_ids": [], "failed_ids": []}',
    )


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
        packaged_ui_browser_probe=_passing_browser_probe,
    )

    assert result.success is True
    assert [check.status for check in result.checks] == [
        "pass",
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
        packaged_ui_browser_probe=_passing_browser_probe,
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
        packaged_ui_browser_probe=_passing_browser_probe,
    )

    source_version = next(
        check for check in result.checks if check.name == "source-version"
    )
    assert result.success is False
    assert source_version.status == "fail"
    assert "0.1.0a9.dev0" in source_version.detail


def test_release_preflight_normalizes_command_timeout(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.1.0a9")

    def runner(argv: Sequence[str], _cwd: Path) -> CommandResult:
        raise subprocess.TimeoutExpired(argv, timeout=30)

    result = run_preflight(
        project_root=tmp_path,
        command_runner=runner,
        binary_resolver=lambda name: f"/usr/local/bin/{name}",
        pypi_version_exists=lambda _version: False,
        packaged_ui_browser_probe=_passing_browser_probe,
    )

    branch = next(check for check in result.checks if check.name == "branch")
    remote_tag = next(
        check for check in result.checks if check.name == "remote-tag-absence"
    )
    assert result.success is False
    assert branch.blocker_kind == "timeout"
    assert remote_tag.blocker_kind == "timeout"


def test_release_preflight_normalizes_registry_failures(
    tmp_path: Path,
) -> None:
    _write_pyproject(tmp_path, "0.1.0a9")

    def runner(argv: Sequence[str], _cwd: Path) -> CommandResult:
        if tuple(argv[:3]) == ("git", "rev-parse", "--abbrev-ref"):
            return CommandResult(returncode=0, stdout="release/v0.1.0a9\n")
        return CommandResult(returncode=0)

    failures = (
        TimeoutError("registry timeout"),
        urllib.error.URLError("temporary failure in name resolution"),
        urllib.error.URLError("certificate verify failed"),
        urllib.error.HTTPError(
            "https://pypi.org",
            503,
            "service unavailable",
            hdrs=None,
            fp=None,
        ),
    )
    expected_kinds = ("timeout", "dns", "tls", "server")
    for failure, expected_kind in zip(failures, expected_kinds, strict=True):
        def _probe(_version: str, *, error: Exception = failure) -> bool:
            raise error

        result = run_preflight(
            project_root=tmp_path,
            command_runner=runner,
            binary_resolver=lambda name: f"/usr/local/bin/{name}",
            pypi_version_exists=_probe,
            packaged_ui_browser_probe=_passing_browser_probe,
        )
        check = next(
            item for item in result.checks if item.name == "pypi-version-absence"
        )
        assert check.status == "fail"
        assert check.blocker_kind == expected_kind


def test_release_preflight_blocks_browser_journey_failure(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.1.0a9")

    def runner(argv: Sequence[str], _cwd: Path) -> CommandResult:
        if tuple(argv[:3]) == ("git", "rev-parse", "--abbrev-ref"):
            return CommandResult(returncode=0, stdout="release/v0.1.0a9\n")
        return CommandResult(returncode=0)

    result = run_preflight(
        project_root=tmp_path,
        command_runner=runner,
        binary_resolver=lambda name: f"/usr/local/bin/{name}",
        pypi_version_exists=lambda _version: False,
        packaged_ui_browser_probe=lambda _root: CommandResult(
            returncode=1,
            stdout='{"failed_ids": ["W36-E7-S1-T4"]}',
            failure_kind="browser-journey",
        ),
    )

    check = next(item for item in result.checks if item.name == "packaged-ui-browser")
    assert result.success is False
    assert check.status == "fail"
    assert check.blocker_kind == "browser-journey"


def test_release_preflight_blocks_missing_browser_infrastructure(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "0.1.0a9")

    def runner(argv: Sequence[str], _cwd: Path) -> CommandResult:
        if tuple(argv[:3]) == ("git", "rev-parse", "--abbrev-ref"):
            return CommandResult(returncode=0, stdout="release/v0.1.0a9\n")
        return CommandResult(returncode=0)

    result = run_preflight(
        project_root=tmp_path,
        command_runner=runner,
        binary_resolver=lambda name: f"/usr/local/bin/{name}",
        pypi_version_exists=lambda _version: False,
        packaged_ui_browser_probe=lambda _root: CommandResult(
            returncode=127,
            stderr="Chromium executable doesn't exist; run playwright install chromium",
            failure_kind="browser-infrastructure",
        ),
    )

    check = next(item for item in result.checks if item.name == "packaged-ui-browser")
    assert result.success is False
    assert check.status == "fail"
    assert check.blocker_kind == "browser-infrastructure"


def test_release_preflight_main_emits_json_for_invalid_project(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = preflight_main(("--project-root", tmp_path.as_posix(), "--skip-pypi"))

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["success"] is False
    assert payload["checks"][0]["blocker_kind"] == "preflight"


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
        pipx_version_exit_code=0,
        pipx_doctor_exit_code=0,
        uv_tool_version_exit_code=0,
        uv_tool_doctor_exit_code=0,
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
        pipx_version_exit_code=0,
        pipx_doctor_exit_code=0,
        uv_tool_version_exit_code=0,
        uv_tool_doctor_exit_code=0,
    )

    pipx_version = next(check for check in evidence.checks if check.name == "pipx-version")
    assert evidence.success is False
    assert pipx_version.status == "fail"


def test_release_evidence_rejects_ambiguous_urls_versions_and_exit_status() -> None:
    base = {
        "version": "0.1.0a9",
        "github_release_url": (
            "https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a9"
        ),
        "release_workflow_url": (
            "https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/123"
        ),
        "pypi_url": "https://pypi.org/project/ai-driven-dev-v2/0.1.0a9/",
        "pipx_version_output": "aidd 0.1.0a9",
        "pipx_doctor_output": "Version 0.1.0a9",
        "uv_tool_version_output": "aidd 0.1.0a9",
        "uv_tool_doctor_output": "Version 0.1.0a9",
        "pipx_version_exit_code": 0,
        "pipx_doctor_exit_code": 0,
        "uv_tool_version_exit_code": 0,
        "uv_tool_doctor_exit_code": 0,
    }
    mutations = (
        {"github_release_url": f"https://example.com/?next={base['github_release_url']}"},
        {"release_workflow_url": f"{base['release_workflow_url']}/attempts/1"},
        {"pypi_url": "https://pypi.org.evil.example/project/ai-driven-dev-v2/0.1.0a9/"},
        {"pipx_version_output": "aidd 0.1.0a90"},
        {
            "pipx_version_output": "aidd 0.1.0a9\nERROR installation failed",
            "pipx_version_exit_code": 1,
        },
        {"uv_tool_doctor_exit_code": None},
    )

    for mutation in mutations:
        evidence = collect_release_evidence(**{**base, **mutation})
        assert evidence.success is False, mutation


def test_release_evidence_payload_without_exit_codes_fails_closed() -> None:
    evidence = _EVIDENCE.collect_release_evidence_from_payload(
        {
            "version": "0.1.0a9",
            "github_release_url": (
                "https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a9"
            ),
            "release_workflow_url": (
                "https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/123"
            ),
            "pypi_url": "https://pypi.org/project/ai-driven-dev-v2/0.1.0a9/",
            "pipx_version_output": "aidd 0.1.0a9",
            "pipx_doctor_output": "Version 0.1.0a9",
            "uv_tool_version_output": "aidd 0.1.0a9",
            "uv_tool_doctor_output": "Version 0.1.0a9",
        }
    )

    assert evidence.success is False
    assert any(check.detail == "missing structured exit status" for check in evidence.checks)


def _write_pyproject(root: Path, version: str) -> None:
    (root / "pyproject.toml").write_text(
        f"[project]\nname = \"ai-driven-dev-v2\"\nversion = \"{version}\"\n",
        encoding="utf-8",
    )
