from __future__ import annotations

import importlib.util
import re
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from typer.core import TyperGroup
from typer.main import get_command

from aidd.cli.main import app
from aidd.harness import live_runtime_config
from aidd.harness.deterministic_eval import validate_deterministic_scenario
from aidd.harness.live_e2e_black_box_orchestration import _parse_args
from aidd.harness.scenarios import load_scenario

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / ".agents" / "skills"
LIVE_COMMAND_PREFIX = ["uv", "run", "python", "-m", "aidd.harness.live_e2e_black_box"]


def _fenced_blocks(skill: str, language: str) -> list[str]:
    text = (SKILLS_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
    return re.findall(rf"^```{language}\n(.*?)^```", text, re.MULTILINE | re.DOTALL)


def _shell_commands(skill: str) -> list[list[str]]:
    return [
        shlex.split(line)
        for block in _fenced_blocks(skill, "bash")
        for line in block.replace("\\\n", " ").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_live_skill_launch_and_resume_preserve_harness_identity() -> None:
    commands = [
        command[len(LIVE_COMMAND_PREFIX) :]
        for command in _shell_commands("live-e2e")
        if command[: len(LIVE_COMMAND_PREFIX)] == LIVE_COMMAND_PREFIX
    ]
    assert commands, "The live workflow needs an executable launch example."
    parsed = [_parse_args(command) for command in commands]
    launches = [args for args in parsed if args.run_id is None]
    resumes = [args for args in parsed if args.run_id is not None]
    assert launches and resumes, "Document both fresh launch and explicit resume."

    identities = {
        (args.scenario, args.runtime, args.work_root, args.report_root) for args in launches
    }
    for command, args in zip(commands, parsed, strict=True):
        assert "--work-root" in command and "--report-root" in command
        scenario = load_scenario(REPO_ROOT / args.scenario, runtime_id=args.runtime)
        assert scenario.is_live
        assert args.runtime in scenario.runtime_targets
        if args.run_id is not None:
            assert "--run-id" in command
            assert (args.scenario, args.runtime, args.work_root, args.report_root) in identities


def test_live_skill_model_profile_matches_generated_native_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiles = [tomllib.loads(block) for block in _fenced_blocks("live-e2e", "toml")]
    documented = [profile["runtime"]["codex"] for profile in profiles]
    assert documented, "The measured live profile must be inspectable."
    command = next(
        command
        for command in _shell_commands("live-e2e")
        if command[: len(LIVE_COMMAND_PREFIX)] == LIVE_COMMAND_PREFIX
    )
    args = _parse_args(command[len(LIVE_COMMAND_PREFIX) :])
    scenario = load_scenario(REPO_ROOT / args.scenario, runtime_id=args.runtime)
    monkeypatch.setattr(
        live_runtime_config,
        "validate_live_runtime_command",
        lambda **_kwargs: None,
    )
    config_path = live_runtime_config.write_live_runtime_config(
        working_copy_path=tmp_path,
        runtime_id=args.runtime,
        scenario=scenario,
        environment={
            key: "" for key in live_runtime_config.LIVE_E2E_RUNTIME_COMMAND_ENV_VARS.values()
        },
    )
    actual = tomllib.loads(config_path.read_text(encoding="utf-8"))["runtime"]["codex"]
    for profile in documented:
        assert {key: actual[key] for key in profile} == profile
        assert {"model", "reasoning_effort"} <= profile.keys()


def test_deterministic_skill_examples_match_cli_and_admissible_fixture() -> None:
    root_command = get_command(app)
    assert isinstance(root_command, TyperGroup)
    eval_group = root_command.commands["eval"]
    assert isinstance(eval_group, TyperGroup)
    examples = [
        command[4:]
        for command in _shell_commands("aidd-eval")
        if command[:4] == ["uv", "run", "aidd", "eval"]
    ]
    assert {command[0] for command in examples} >= {"doctor", "execute", "summary"}
    params_by_command: dict[str, dict[str, object]] = {}
    for subcommand, *arguments in examples:
        with eval_group.commands[subcommand].make_context(subcommand, arguments) as context:
            params_by_command[subcommand] = context.params

    execution = params_by_command["execute"]
    scenario_path = REPO_ROOT / str(execution["scenario"])
    scenario = load_scenario(scenario_path, runtime_id="generic-cli")
    validate_deterministic_scenario(scenario_path=scenario_path, scenario=scenario)
    assert params_by_command["doctor"]["scenario"] == execution["scenario"]
    assert params_by_command["doctor"]["runtime"] == "generic-cli"
    assert params_by_command["summary"]["root"] == execution["root"]
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", str(execution["root"])],
        cwd=REPO_ROOT,
        check=False,
    )
    assert ignored.returncode == 0, "Keep generated eval evidence under an ignored root."


def test_release_skill_examples_use_current_helper_parsers_and_branch_version() -> None:
    version = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]["version"]
    commands = [
        [argument.replace("<project.version>", version) for argument in command]
        for command in _shell_commands("release-publish")
    ]
    branch = next(command[3] for command in commands if command[:3] == ["git", "switch", "-c"])
    parsed_helpers = {}
    for helper_name in ("preflight", "evidence_collector"):
        module_name = f"scripts.release.{helper_name}"
        examples = [
            command[3:] for command in commands if command[:3] == ["python", "-m", module_name]
        ]
        assert examples, f"The release workflow must route through {module_name}."
        path = REPO_ROOT / "scripts" / "release" / f"{helper_name}.py"
        test_module_name = f"agent_workflow_release_{helper_name}"
        spec = importlib.util.spec_from_file_location(test_module_name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[test_module_name] = module
        try:
            spec.loader.exec_module(module)
            parsed_helpers[helper_name] = [module._parse_args(arguments) for arguments in examples]
        finally:
            sys.modules.pop(test_module_name, None)

    for parsed in parsed_helpers["preflight"]:
        assert parsed.project_root.resolve() == REPO_ROOT
        assert parsed.version == version
        assert (parsed.expected_branch or f"release/v{parsed.version}") == branch
        assert parsed.skip_pypi is False
    for parsed in parsed_helpers["evidence_collector"]:
        assert Path(parsed.payload).suffix == ".json"
