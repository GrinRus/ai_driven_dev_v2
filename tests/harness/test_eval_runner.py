from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from aidd.harness.eval_runner import run_eval_scenario


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


def _write_scenario_manifest(
    *,
    path: Path,
    repo_url: str,
    setup_commands: tuple[str, ...],
    verify_commands: tuple[str, ...],
    interview_required: bool,
    runtime_targets: tuple[str, ...] = ("opencode",),
    work_item: str = "WI-EVAL-RUNNER",
) -> None:
    payload = {
        "id": "AIDD-TEST-EVAL-RUNNER",
        "task": "exercise eval orchestration",
        "repo": {"url": repo_url},
        "setup": {"commands": list(setup_commands)},
        "verify": {"commands": list(verify_commands)},
        "interview": {"required": interview_required},
        "runtime_targets": list(runtime_targets),
        "aidd_invocation": {"work_item": work_item},
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _assert_bundle_basics(bundle_root: Path) -> None:
    assert (bundle_root / "harness-metadata.json").exists()
    assert (bundle_root / "setup-transcript.json").exists()
    assert (bundle_root / "run-transcript.json").exists()
    assert (bundle_root / "verify-transcript.json").exists()
    assert (bundle_root / "teardown-transcript.json").exists()
    assert (bundle_root / "runtime.log").exists()
    assert (bundle_root / "validator-report.md").exists()
    assert (bundle_root / "verdict.md").exists()
    assert (bundle_root / "summary.md").exists()
    assert (bundle_root / "log-analysis.md").exists()
    assert (bundle_root / "grader.json").exists()


def test_eval_runner_pass_status(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-pass.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-PASS",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "pass"
    assert result.first_failure_boundary.category == "none"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `pass`" in verdict_text


def test_eval_runner_fail_status_for_verification_non_zero(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-fail.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("exit 9",),
        interview_required=False,
        work_item="WI-EVAL-FAIL",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `fail`" in verdict_text


def test_eval_runner_blocked_status_when_answers_file_missing(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-blocked.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=(
            "test -f .aidd/workitems/WI-EVAL-BLOCKED/stages/idea/answers.md",
        ),
        interview_required=True,
        work_item="WI-EVAL-BLOCKED",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "blocked"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `blocked`" in verdict_text


def test_eval_runner_infra_fail_status_for_setup_error(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-infra.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("exit 7",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-INFRA",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "infra-fail"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `infra-fail`" in verdict_text
