from __future__ import annotations

import subprocess
from pathlib import Path

import yaml
from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_source_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", path.as_posix()])
    _run(["git", "config", "user.email", "tests@example.com"], cwd=path)
    _run(["git", "config", "user.name", "AIDD Tests"], cwd=path)
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=path)
    _run(["git", "commit", "-m", "init"], cwd=path)


def _write_scenario_manifest(*, path: Path, repo_url: str) -> None:
    payload = {
        "id": "AIDD-TEST-EVAL-RUN-CLI",
        "task": "exercise eval cli command",
        "repo": {"url": repo_url},
        "setup": {"commands": ["printf 'setup\\n' > setup.log"]},
        "verify": {"commands": ["printf 'verify\\n' > verify.log"]},
        "runtime_targets": ["opencode"],
        "interview": {"required": False},
        "aidd_invocation": {"work_item": "WI-EVAL-CLI"},
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_eval_run_executes_harness_lifecycle_and_writes_bundle(
    tmp_path: Path, monkeypatch
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario.yaml"
    _write_scenario_manifest(path=scenario_path, repo_url=source_repo.as_uri())
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["eval", "run", str(scenario_path), "--runtime", "opencode"],
    )

    normalized_output = result.stdout.replace("\n", "")
    assert result.exit_code == 0
    assert "AIDD eval run: scenario=AIDD-TEST-EVAL-RUN-CLI runtime=opencode" in result.stdout
    assert "Status: pass" in result.stdout
    assert "Bundle root:" in result.stdout
    assert ".aidd/reports/evals/eval-test-eval-run-cli-opencode-" in normalized_output
    assert "Harness execution is not implemented yet." not in result.stdout
