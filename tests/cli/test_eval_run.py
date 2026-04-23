from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def _run_git(args: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return
    stderr = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
    raise RuntimeError(stderr)


def _init_local_git_repo(repo_path: Path) -> None:
    repo_path.mkdir(parents=True, exist_ok=True)
    _run_git(["init", "--initial-branch", "main"], cwd=repo_path)
    (repo_path / "README.md").write_text("# Test repo\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=repo_path)
    _run_git(
        [
            "-c",
            "user.name=AIDD Test",
            "-c",
            "user.email=aidd-test@example.com",
            "commit",
            "-m",
            "init",
        ],
        cwd=repo_path,
    )


def _write_fake_aidd(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "#!/bin/sh",
                "printf '%s\\n' \"$@\" > invoked-args.txt",
                "printf 'fake aidd stdout\\n'",
                "printf 'fake aidd stderr\\n' 1>&2",
                "exit 0",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_scenario(path: Path, *, repo_url: str) -> None:
    path.write_text(
        "\n".join(
            (
                "id: AIDD-TEST-EVAL-CLI",
                "task: Validate eval run command wiring",
                "repo:",
                f"  url: \"{repo_url}\"",
                "  default_branch: \"main\"",
                "setup:",
                "  commands:",
                "    - \"echo setup > setup.log\"",
                "run:",
                "  stage_scope:",
                "    start: idea",
                "    end: idea",
                "  limits:",
                "    patch_budget_files: 1",
                "    timeout_minutes: 5",
                "  interview:",
                "    required: false",
                "runtime_targets:",
                "  - generic-cli",
                "verify:",
                "  commands:",
                "    - \"test -f invoked-args.txt\"",
                "",
            )
        ),
        encoding="utf-8",
    )


def test_eval_run_executes_scenario_and_writes_reports(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    _init_local_git_repo(repo_path)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd)
    scenario_path = tmp_path / "scenario.yaml"
    _write_scenario(scenario_path, repo_url=repo_path.as_posix())
    workspace_root = tmp_path / ".aidd"

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            str(scenario_path),
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--aidd-command",
            fake_aidd.as_posix(),
        ],
    )

    assert result.exit_code == 0
    assert "AIDD eval run: scenario=AIDD-TEST-EVAL-CLI runtime=generic-cli" in result.stdout
    assert "status=pass" in result.stdout

    eval_reports_root = workspace_root / "reports" / "evals"
    summary_paths = sorted(eval_reports_root.glob("*/summary.md"))
    verdict_paths = sorted(eval_reports_root.glob("*/verdict.md"))
    grader_paths = sorted(eval_reports_root.glob("*/grader.json"))
    assert summary_paths
    assert verdict_paths
    assert grader_paths
    assert "# Eval Summary" in summary_paths[-1].read_text(encoding="utf-8")
    assert "- Status: `pass`" in verdict_paths[-1].read_text(encoding="utf-8")
    grader_payload = json.loads(grader_paths[-1].read_text(encoding="utf-8"))
    assert grader_payload["overall_status"] == "pass"
    assert grader_payload["contract_compliance"]["status"] == "pass"
    assert grader_payload["process_compliance"]["status"] == "pass"
    assert grader_payload["task_outcome"]["status"] == "pass"
