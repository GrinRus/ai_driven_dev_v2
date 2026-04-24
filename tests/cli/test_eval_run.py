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


def _write_fake_aidd(path: Path, *, exit_code: int, write_plan_outputs: bool = False) -> None:
    del write_plan_outputs
    write_outputs_lines: tuple[str, ...] = tuple()
    write_outputs_lines = (
        "output_root=\".aidd/workitems/$AIDD_HARNESS_WORK_ITEM/stages/plan/output\"",
        "mkdir -p \"$output_root\"",
        (
            "printf '# Stage result\\n\\n- status: succeeded\\n' "
            "> \"$output_root/stage-result.md\""
        ),
        (
            "printf '# Validator report\\n\\n## Result\\n\\n- Verdict: `pass`\\n' "
            "> \"$output_root/validator-report.md\""
        ),
        "printf '# Plan\\n\\n- generated\\n' > \"$output_root/plan.md\"",
    )
    path.write_text(
        "\n".join(
            (
                "#!/bin/sh",
                "printf 'fake aidd\\n'",
                *write_outputs_lines,
                f"exit {exit_code}",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_scenario_manifest(
    *,
    path: Path,
    repo_url: str,
    aidd_command: tuple[str, ...] | None = None,
) -> None:
    aidd_invocation: dict[str, object] = {"work_item": "WI-EVAL-CLI"}
    if aidd_command is not None:
        aidd_invocation["command"] = list(aidd_command)
    payload = {
        "id": "AIDD-TEST-EVAL-RUN-CLI",
        "scenario_class": "deterministic-stage",
        "feature_size": "small",
        "automation_lane": "ci",
        "canonical_runtime": "opencode",
        "task": "exercise eval cli command",
        "repo": {"url": repo_url},
        "setup": {"commands": ["printf 'setup\\n' > setup.log"]},
        "verify": {"commands": ["printf 'verify\\n' > verify.log"]},
        "stage_scope": {"start": "plan", "end": "plan"},
        "runtime_targets": ["opencode"],
        "interview": {"required": False},
        "aidd_invocation": aidd_invocation,
        "feature_source": {
            "mode": "fixture-seed",
            "selection_policy": "fixture-owned",
            "fixture_path": "harness/fixtures/minimal-python",
            "seed_id": "eval-run-cli-fixture",
            "summary": "Use a deterministic local fixture seed for eval CLI tests.",
        },
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_eval_run_executes_harness_lifecycle_and_writes_bundle(
    tmp_path: Path, monkeypatch
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=0, write_plan_outputs=True)
    scenario_path = tmp_path / "scenario.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        aidd_command=(fake_aidd.as_posix(),),
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["eval", "run", str(scenario_path), "--runtime", "opencode"],
    )

    normalized_output = result.stdout.replace("\n", "")
    assert result.exit_code == 0
    assert "AIDD eval run: scenario=AIDD-TEST-EVAL-RUN-CLI runtime=opencode" in result.stdout
    assert "Status: pass" in result.stdout
    assert "Quality gate: none" in result.stdout
    assert "Bundle root:" in result.stdout
    assert ".aidd/reports/evals/eval-test-eval-run-cli-opencode-" in normalized_output
    assert "Harness execution is not implemented yet." not in result.stdout


def test_eval_run_reports_fail_for_unsupported_runtime_real_invocation(
    tmp_path: Path, monkeypatch
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-real-run.yaml"
    _write_scenario_manifest(path=scenario_path, repo_url=source_repo.as_uri())
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["eval", "run", str(scenario_path), "--runtime", "opencode"],
    )

    assert result.exit_code == 0
    assert "AIDD eval run: scenario=AIDD-TEST-EVAL-RUN-CLI runtime=opencode" in result.stdout
    assert "Status: fail" in result.stdout
    assert "Quality gate: none" in result.stdout
