from __future__ import annotations

import json
import shlex
from dataclasses import replace
from pathlib import Path

import pytest

from aidd.harness.deterministic_eval import (
    DeterministicEvalRequest,
    execute_deterministic_eval,
)
from aidd.harness.eval_models import EvalRunPreparation, EvalScenarioRunResult
from aidd.harness.eval_preparation import prepare_eval_run
from aidd.harness.scenarios import ScenarioCommandSteps

SMOKE_SCENARIO = (
    Path(__file__).resolve().parents[2]
    / "harness/scenarios/smoke/plan-stage-minimal-fixture.yaml"
)


def _execute_lifecycle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    setup_exit: int = 0,
    run_exit: int = 0,
    verify_exit: int = 0,
    teardown_exit: int = 0,
) -> tuple[EvalScenarioRunResult, Path]:
    fake_aidd = tmp_path / "fake-aidd"
    fake_aidd.write_text(
        "#!/bin/sh\nprintf 'run\\n' >> lifecycle.log\n"
        f"printf 'fake aidd\\n'\nexit {run_exit}\n",
        encoding="utf-8",
    )
    fake_aidd.chmod(0o755)
    working_copy_marker = tmp_path / "working-copy-path"

    def _prepare(
        *, scenario_path: Path, runtime_id: str, workspace_root: Path
    ) -> EvalRunPreparation:
        prep = prepare_eval_run(
            scenario_path=scenario_path,
            runtime_id=runtime_id,
            workspace_root=workspace_root,
        )
        scenario = replace(
            prep.scenario,
            scenario_class="deterministic-workflow",
            setup=ScenarioCommandSteps(
                commands=(
                    f"pwd > {shlex.quote(str(working_copy_marker))}",
                    "printf '# fixture config\\n' > aidd.example.toml",
                    f"printf 'setup\\n' >> lifecycle.log; exit {setup_exit}",
                ),
            ),
            verify=ScenarioCommandSteps(
                commands=(f"printf 'verify\\n' >> lifecycle.log; exit {verify_exit}",),
            ),
        )
        return replace(
            prep,
            scenario=scenario,
            aidd_command=(fake_aidd.as_posix(),),
            teardown_commands=(
                f"printf 'teardown\\n' >> lifecycle.log; exit {teardown_exit}",
            ),
        )

    monkeypatch.setattr("aidd.harness.deterministic_eval.prepare_eval_run", _prepare)
    result = execute_deterministic_eval(
        DeterministicEvalRequest(
            scenario_path=SMOKE_SCENARIO,
            workspace_root=tmp_path / ".aidd",
        )
    )
    working_copy = Path(working_copy_marker.read_text(encoding="utf-8").strip())
    return result, working_copy


@pytest.mark.parametrize(
    ("setup_exit", "run_exit", "verify_exit", "status", "steps", "error"),
    (
        (0, 0, 0, "pass", ["setup", "run", "verify", "teardown"], None),
        (4, 0, 0, "infra-fail", ["setup", "teardown"], "Setup command failed"),
        (0, 3, 0, "fail", ["setup", "run", "verify", "teardown"], "AIDD execution failed"),
        (0, 0, 9, "fail", ["setup", "run", "verify", "teardown"], "Verification command failed"),
    ),
)
def test_deterministic_lifecycle_always_runs_teardown_and_persists_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    setup_exit: int,
    run_exit: int,
    verify_exit: int,
    status: str,
    steps: list[str],
    error: str | None,
) -> None:
    result, working_copy = _execute_lifecycle(
        tmp_path,
        monkeypatch,
        setup_exit=setup_exit,
        run_exit=run_exit,
        verify_exit=verify_exit,
    )

    assert result.status == status
    assert (working_copy / "lifecycle.log").read_text(encoding="utf-8").splitlines() == steps
    verdict = result.verdict_path.read_text(encoding="utf-8")
    assert f"- Status: `{status}`" in verdict
    if error is not None:
        assert error in verdict
    teardown = json.loads((result.bundle_root / "teardown-transcript.json").read_text())
    assert teardown["command_count"] == 1
    assert teardown["commands"][0]["exit_code"] == 0
    assert "teardown" in teardown["commands"][0]["command"]


@pytest.mark.parametrize("error_type", (RuntimeError, KeyboardInterrupt))
@pytest.mark.parametrize("teardown_exit", (0, 5))
def test_deterministic_lifecycle_retains_execution_and_teardown_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[BaseException],
    teardown_exit: int,
) -> None:
    def _fail_runtime_invocation(**_kwargs: object) -> None:
        raise error_type("injected runtime interruption")

    monkeypatch.setattr(
        "aidd.harness.deterministic_eval.invoke_aidd_run",
        _fail_runtime_invocation,
    )
    result, working_copy = _execute_lifecycle(
        tmp_path,
        monkeypatch,
        teardown_exit=teardown_exit,
    )

    assert result.status == "infra-fail"
    assert (working_copy / "lifecycle.log").read_text(encoding="utf-8") == "setup\nteardown\n"
    assert "injected runtime interruption" in result.verdict_path.read_text(encoding="utf-8")
    runtime_log = (result.bundle_root / "runtime.log").read_text(encoding="utf-8")
    assert "error=injected runtime interruption" in runtime_log
    if teardown_exit:
        assert "error=Teardown command failed with non-zero exit (5)" in runtime_log
    else:
        assert "teardown_commands=1" in runtime_log
