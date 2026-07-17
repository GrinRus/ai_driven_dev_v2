from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from aidd.core.stages import STAGES
from aidd.harness.scenarios import ScenarioManifestError, load_scenario


@pytest.mark.parametrize("scenario_id", ("../escape", "nested/id", "nested\\id", "x" * 129))
def test_scenario_loader_rejects_unsafe_scenario_id(
    tmp_path: Path,
    scenario_id: str,
) -> None:
    source = Path("harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml")
    manifest = re.sub(
        r"^id:\s*.*$",
        f"id: {scenario_id!r}",
        source.read_text(encoding="utf-8"),
        count=1,
        flags=re.MULTILINE,
    )
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(manifest, encoding="utf-8")

    with pytest.raises(ScenarioManifestError, match="plain path component"):
        load_scenario(scenario_path)


def _assert_live_contract(scenario) -> None:
    assert scenario.is_live is True
    assert scenario.scenario_class in {"live-full-flow", "live-full-flow-interview"}
    assert scenario.feature_size in {"small", "medium", "large", "xlarge"}
    assert scenario.live_matrix_role in {"flow-regression", "product-evaluation"}
    if scenario.live_matrix_role == "flow-regression":
        assert scenario.feature_size == "small"
    else:
        assert scenario.feature_size in {"medium", "large", "xlarge"}
    assert scenario.automation_lane == "manual"
    assert scenario.canonical_runtime in scenario.runtime_targets
    assert scenario.repo.revision
    assert scenario.run.stage_start == STAGES[0]
    assert scenario.run.stage_end == STAGES[-1]
    assert scenario.run.timeout_minutes is not None
    assert scenario.run.timeout_minutes >= 240
    assert scenario.run.no_progress_timeout_minutes == 30
    assert scenario.feature_source is not None
    assert scenario.feature_source.mode == "authored-task-pool"
    assert scenario.feature_source.selection_policy == "first-listed"
    assert scenario.feature_source.tasks
    assert "quality" not in scenario.raw
    assert scenario.live_flow is not None
    assert scenario.live_flow.driver == "stepwise-black-box"
    assert scenario.live_flow.checkpoint_policy == "after-each-step"
    assert scenario.live_flow.answer_policy == "agent-decides"
    assert scenario.live_flow.frontend_checkpoints is True


def test_hono_non_error_live_scenario_preserves_public_type_contracts() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/hono-non-error-throw-handling.yaml"))

    _assert_live_contract(scenario)
    assert scenario.scenario_id == "AIDD-LIVE-007"
    assert scenario.feature_size == "medium"
    assert scenario.live_matrix_role == "product-evaluation"
    assert scenario.canonical_runtime == "codex"
    assert scenario.runtime_targets == ("codex", "claude-code", "qwen")
    task = scenario.feature_source.tasks[0]
    assert task.task_id == "TASK-LIVE-HONO-NON-ERROR-THROW"
    assert "without widening the public error handler" in task.target_change
    assert any(
        "Public error handler and context error types remain source-compatible"
        in criterion
        for criterion in task.acceptance_criteria
    )
    assert "preserves the existing public error type contracts" in task.quality_bar
    assert task.visible_request is not None
    assert task.audit_rubric is not None
    normalized_rubric = " ".join(task.audit_rubric.split())
    assert "immediate canonical stage order" in normalized_rubric
    assert "`research` must point to `plan`" in normalized_rubric
    assert "`plan` must point to `review-spec`" in normalized_rubric
    assert "`review-spec` must point to `tasklist`" in normalized_rubric
    assert "`tasklist` must point to `implement`" in normalized_rubric
    assert "`implement` must point to `review`, not directly to `qa`" in (
        normalized_rubric
    )
    assert task.complexity_axes == (
        "cross-module",
        "api-policy",
        "async-runtime",
        "type-compatibility",
    )
    focused_command = (
        "./node_modules/.bin/vitest --run --coverage.enabled=false "
        "src/hono.test.ts src/compose.test.ts"
    )
    assert task.verification == (
        focused_command,
        "./node_modules/.bin/tsc --noEmit",
    )
    assert scenario.verify.commands == (
        focused_command,
        "./node_modules/.bin/tsc --noEmit",
        "test -f .aidd/workitems/WI-LIVE-HONO-SMOKE/stages/qa/output/stage-result.md",
        "test -f .aidd/workitems/WI-LIVE-HONO-SMOKE/stages/qa/output/validator-report.md",
    )


def test_all_live_scenarios_load_as_valid_full_flow_manifests() -> None:
    live_root = Path("harness/scenarios/live")
    scenario_files = sorted(live_root.glob("*.yaml"))
    assert scenario_files

    for scenario_file in scenario_files:
        scenario = load_scenario(scenario_file)
        assert scenario.scenario_id
        assert scenario.task
        _assert_live_contract(scenario)
        assert scenario.run.max_remediation_cycles == 3


def test_live_scenario_accepts_max_remediation_cycles_override(tmp_path: Path) -> None:
    source_path = Path("harness/scenarios/live/hono-non-error-throw-handling.yaml")
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    payload["limits"]["max_remediation_cycles"] = 5
    scenario_path = tmp_path / "harness" / "scenarios" / "live" / "hono-remediation-limit.yaml"
    scenario_path.parent.mkdir(parents=True)
    scenario_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    scenario = load_scenario(scenario_path)

    assert scenario.run.max_remediation_cycles == 5


def test_live_scenario_accepts_no_progress_timeout_override(tmp_path: Path) -> None:
    source_path = Path("harness/scenarios/live/hono-non-error-throw-handling.yaml")
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    payload["limits"]["no_progress_timeout_minutes"] = 45
    scenario_path = tmp_path / "harness" / "scenarios" / "live" / "hono-no-progress.yaml"
    scenario_path.parent.mkdir(parents=True)
    scenario_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    scenario = load_scenario(scenario_path)

    assert scenario.run.no_progress_timeout_minutes == 45


def test_live_scenario_rejects_invalid_no_progress_timeout(tmp_path: Path) -> None:
    source_path = Path("harness/scenarios/live/hono-non-error-throw-handling.yaml")
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    payload["limits"]["no_progress_timeout_minutes"] = 0
    scenario_path = tmp_path / "harness" / "scenarios" / "live" / "hono-invalid-no-progress.yaml"
    scenario_path.parent.mkdir(parents=True)
    scenario_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ScenarioManifestError, match="no_progress_timeout_minutes"):
        load_scenario(scenario_path)


def test_live_scenario_rejects_invalid_max_remediation_cycles(tmp_path: Path) -> None:
    source_path = Path("harness/scenarios/live/hono-non-error-throw-handling.yaml")
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    payload["limits"]["max_remediation_cycles"] = 0
    scenario_path = (
        tmp_path / "harness" / "scenarios" / "live" / "hono-invalid-remediation-limit.yaml"
    )
    scenario_path.parent.mkdir(parents=True)
    scenario_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ScenarioManifestError, match="max_remediation_cycles"):
        load_scenario(scenario_path)


def test_httpx_docs_sync_live_scenario_uses_docs_only_verification_gate() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/httpx-cli-docs-sync.yaml"))

    _assert_live_contract(scenario)
    assert scenario.scenario_id == "AIDD-LIVE-004"
    assert scenario.feature_size == "small"
    assert scenario.live_matrix_role == "flow-regression"
    assert scenario.canonical_runtime == "codex"
    assert scenario.repo.revision == "b5addb64f0161ff6bfe94c124ef76f6a1fba5254"
    assert scenario.runtime_targets == ("codex", "qwen")
    assert scenario.run.timeout_minutes == 240
    task = scenario.feature_source.tasks[0]
    assert "httpx https://httpbin.org/json" in task.intent
    assert "httpx https://httpbin.org/json" in task.target_change
    assert "httpx https://httpbin.org/json" in task.acceptance_criteria[0]
    verification_text = "\n".join(scenario.verify.commands)
    assert "git\", \"diff\", \"--name-only" in verification_text
    assert ".venv/bin/python" in verification_text
    assert "README.md" in verification_text
    assert "docs/index.md" in verification_text
    assert '"httpx " + "https:" + "//httpbin.org/json"' in verification_text
    assert "https://httpbin.org/json" not in verification_text
    assert "placeholder runnable example introduced" in verification_text
    assert "pytest -q" not in verification_text
    assert scenario.verify.commands[-2:] == (
        "test -f .aidd/workitems/WI-LIVE-HTTPX-DOCS-SYNC/stages/qa/output/stage-result.md",
        (
            "test -f .aidd/workitems/WI-LIVE-HTTPX-DOCS-SYNC/stages/qa/output/"
            "validator-report.md"
        ),
    )

def test_sqlite_utils_canonical_live_scenario_declares_black_box_operator_contract() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml")
    )

    assert scenario.scenario_id == "AIDD-LIVE-005"
    assert scenario.feature_size == "small"
    assert scenario.live_matrix_role == "flow-regression"
    assert scenario.automation_lane == "manual"
    assert scenario.canonical_runtime == "codex"
    assert scenario.repo.url == "https://github.com/simonw/sqlite-utils"
    assert scenario.repo.default_branch == "main"
    assert scenario.repo.revision == "8d74ffc93292c604d5827e2b44fffedca0c28c19"
    _assert_live_contract(scenario)
    assert scenario.raw["operator_execution"] == {
        "install_channel": "uv-tool",
        "artifact_source": "local-wheel",
        "execution_cwd": "repository-root",
        "workspace_root": ".aidd",
        "resource_source": "packaged-assets",
    }
    assert scenario.runtime_targets == ("codex", "opencode", "claude-code")
    assert scenario.run.timeout_minutes == 240


def test_sqlite_utils_interview_scenario_forces_blocking_question_conditions() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/live/sqlite-utils-yielded-rows-interview.yaml")
    )

    _assert_live_contract(scenario)
    assert scenario.scenario_id == "AIDD-LIVE-006"
    assert scenario.scenario_class == "live-full-flow-interview"
    assert scenario.feature_size == "xlarge"
    assert scenario.live_matrix_role == "product-evaluation"
    assert scenario.canonical_runtime == "opencode"
    assert scenario.repo.revision == "8d74ffc93292c604d5827e2b44fffedca0c28c19"
    assert scenario.run.interview_required is True
    assert scenario.live_flow is not None
    assert scenario.live_flow.answer_policy == "agent-decides"
    assert scenario.raw["interview"]["must_ask_at_least_one"] is True
    assert scenario.feature_source.tasks[0].task_id == "TASK-LIVE-SQLITE-YIELDED-ROWS"
    assert scenario.feature_source.tasks[0].interview
    assert scenario.feature_source.tasks[0].visible_request is not None
    assert scenario.feature_source.tasks[0].audit_rubric is not None
    assert "security" in scenario.feature_source.tasks[0].complexity_axes
    assert scenario.raw["interview"]["blocking_question_topics"] == [
        "Execution trust boundary for user-provided Python code.",
        "Accepted input form (inline expression, file, or both).",
        "Required documentation updates and examples for the selected form.",
    ]
    assert (
        scenario.raw["interview"]["answer_flow"]["answers_file"]
        == ".aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/idea/answers.md"
    )
    assert scenario.verify.commands == (
        "aidd stage questions idea --work-item WI-LIVE-SQLITE-INTERVIEW",
        "test -f .aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/idea/answers.md",
        "uv run pytest -q",
        "test -f .aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/qa/output/stage-result.md",
        "test -f .aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/qa/output/validator-report.md",
    )


def test_hono_interview_scenario_forces_blocking_question_conditions() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/hono-router-double-star-parity.yaml"))

    _assert_live_contract(scenario)
    assert scenario.scenario_id == "AIDD-LIVE-008"
    assert scenario.scenario_class == "live-full-flow-interview"
    assert scenario.feature_size == "xlarge"
    assert scenario.live_matrix_role == "product-evaluation"
    assert scenario.canonical_runtime == "opencode"
    assert scenario.run.interview_required is True
    assert scenario.live_flow is not None
    assert scenario.live_flow.answer_policy == "agent-decides"
    assert scenario.feature_source.tasks[0].task_id == "TASK-LIVE-HONO-ROUTER-DOUBLE-STAR"
    assert scenario.feature_source.tasks[0].interview
    assert scenario.feature_source.tasks[0].visible_request is not None
    assert scenario.feature_source.tasks[0].audit_rubric is not None
    assert "api-policy" in scenario.feature_source.tasks[0].complexity_axes
    assert scenario.raw["interview"]["must_ask_at_least_one"] is True
    assert (
        scenario.raw["interview"]["answer_flow"]["answers_file"]
        == ".aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/idea/answers.md"
    )
    assert scenario.verify.commands == (
        "aidd stage questions idea --work-item WI-LIVE-HONO-INTERVIEW",
        "test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/idea/answers.md",
        "bunx vitest run src/router/ src/utils/url.test.ts",
        "bunx tsc --noEmit",
        "test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/qa/output/stage-result.md",
        "test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/qa/output/validator-report.md",
    )


def test_complex_live_candidate_manifests_are_bounded_and_pinned() -> None:
    openapi = load_scenario(
        Path("harness/scenarios/live/openapi-typescript-discriminator-composition.yaml")
    )
    pytest_scenario = load_scenario(
        Path("harness/scenarios/live/pytest-collection-error-summary.yaml")
    )
    starlette = load_scenario(
        Path("harness/scenarios/live/starlette-streaming-error-boundary.yaml")
    )

    for scenario in (openapi, pytest_scenario, starlette):
        _assert_live_contract(scenario)
        assert scenario.repo.revision
        assert scenario.run.patch_budget_files is not None
        assert scenario.run.timeout_minutes is not None
        assert scenario.run.timeout_minutes >= 240
        assert scenario.live_matrix_role == "product-evaluation"
        assert scenario.feature_source is not None
        assert scenario.feature_source.tasks[0].visible_request is not None
        assert scenario.feature_source.tasks[0].audit_rubric is not None
        assert scenario.feature_source.tasks[0].complexity_axes
        assert "generic-cli" not in scenario.runtime_targets

    assert openapi.scenario_id == "AIDD-LIVE-010"
    assert openapi.scenario_class == "live-full-flow-interview"
    assert openapi.feature_size == "large"
    assert openapi.canonical_runtime == "opencode"
    assert openapi.run.interview_required is True
    assert openapi.repo.url == "https://github.com/openapi-ts/openapi-typescript"
    assert openapi.repo.revision == "0cc7ee77d28359c7901d9cd3b5733b70a050ea49"
    assert (
        "pnpm --filter openapi-typescript exec vitest run test/discriminators.test.ts "
        "test/node-api.test.ts"
        in openapi.verify.commands
    )
    assert (
        "aidd stage questions idea --work-item WI-LIVE-OPENAPI-DISCRIMINATOR"
        in openapi.verify.commands
    )
    assert "pnpm --filter openapi-typescript lint:ts" in openapi.verify.commands

    assert pytest_scenario.scenario_id == "AIDD-LIVE-011"
    assert pytest_scenario.scenario_class == "live-full-flow-interview"
    assert pytest_scenario.feature_size == "xlarge"
    assert pytest_scenario.canonical_runtime == "opencode"
    assert pytest_scenario.run.interview_required is True
    assert pytest_scenario.repo.url == "https://github.com/pytest-dev/pytest"
    assert pytest_scenario.repo.revision == "0a465c8a716f37aca0ce456eb34614699ecd701f"
    assert pytest_scenario.setup.commands == (
        "uv venv --python 3.12",
        'uv pip install -e ".[dev]"',
    )
    assert (
        ".venv/bin/python -m pytest -q testing/test_collection.py testing/test_terminal.py "
        "testing/test_main.py"
        in pytest_scenario.verify.commands
    )
    assert (
        "aidd stage questions idea --work-item WI-LIVE-PYTEST-COLLECTION"
        in pytest_scenario.verify.commands
    )

    assert starlette.scenario_id == "AIDD-LIVE-012"
    assert starlette.scenario_class == "live-full-flow"
    assert starlette.feature_size == "large"
    assert starlette.canonical_runtime == "codex"
    assert starlette.run.interview_required is False
    assert starlette.repo.url == "https://github.com/Kludex/starlette"
    assert starlette.repo.revision == "e636c77b15d903ab3ff3968cd43aee1887dd1e48"
    assert (
        "uv run --frozen pytest -q tests/middleware/test_base.py tests/middleware/test_errors.py "
        "tests/test_responses.py"
        in starlette.verify.commands
    )
    assert (
        "uv run --frozen ruff check starlette tests/middleware/test_base.py "
        "tests/middleware/test_errors.py tests/test_responses.py"
        in starlette.verify.commands
    )


def test_live_interview_manifests_use_installed_aidd_for_aidd_self_checks() -> None:
    manifest_paths = sorted(Path("harness/scenarios/live").glob("*.yaml"))
    offenders: list[str] = []

    for manifest_path in manifest_paths:
        scenario = load_scenario(manifest_path)
        commands = list(scenario.verify.commands)
        for task in (scenario.feature_source.tasks if scenario.feature_source else ()):
            commands.extend(task.verification)
        answer_flow = scenario.raw.get("interview", {}).get("answer_flow", {})
        commands.extend(
            " ".join(answer_flow.get(key, ()))
            for key in ("question_check_command", "resume_command")
        )
        for command in commands:
            if command.startswith("uv run aidd "):
                offenders.append(f"{manifest_path}: {command}")

    assert offenders == []


def test_smoke_plan_stagepack_scenario_declares_cross_runtime_output_checks() -> None:
    scenario = load_scenario(Path("harness/scenarios/smoke/plan-stagepack-smoke.yaml"))

    assert scenario.is_live is False
    assert scenario.scenario_id == "AIDD-STAGEPACK-PLAN-SMOKE-001"
    assert scenario.scenario_class == "deterministic-stage"
    assert scenario.feature_size == "medium"
    assert scenario.automation_lane == "ci"
    assert scenario.canonical_runtime == "opencode"
    assert "command" not in scenario.raw["aidd_invocation"]
    assert scenario.run.stage_start == "plan"
    assert scenario.run.stage_end == "plan"
    assert scenario.feature_source is not None
    assert scenario.feature_source.mode == "fixture-seed"
    assert scenario.feature_source.selection_policy == "fixture-owned"
    assert scenario.feature_source.fixture_path == "harness/fixtures/minimal-python"
    assert scenario.runtime_targets == (
        "generic-cli",
        "claude-code",
        "codex",
        "opencode",
    )
    assert scenario.verify.commands == (
        "test -f .aidd/workitems/WI-STAGE-PLAN-SMOKE/stages/plan/output/plan.md",
        "test -f .aidd/workitems/WI-STAGE-PLAN-SMOKE/stages/plan/output/stage-result.md",
        "test -f .aidd/workitems/WI-STAGE-PLAN-SMOKE/stages/plan/output/validator-report.md",
    )


def test_minimal_fixture_smoke_scenario_declares_small_ci_fixture_seed() -> None:
    scenario = load_scenario(Path("harness/scenarios/smoke/plan-stage-minimal-fixture.yaml"))

    assert scenario.is_live is False
    assert scenario.scenario_class == "deterministic-stage"
    assert scenario.feature_size == "small"
    assert scenario.automation_lane == "ci"
    assert scenario.canonical_runtime == "generic-cli"
    assert scenario.feature_source is not None
    assert scenario.feature_source.mode == "fixture-seed"
    assert scenario.feature_source.seed_id == "minimal-python-plan-stage"
    assert scenario.run.stage_start == "plan"
    assert scenario.run.stage_end == "plan"


def test_installed_local_project_smoke_scenario_uses_source_install_and_local_fixture() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/smoke/installed-local-project-fixture.yaml")
    )

    assert scenario.scenario_id == "AIDD-INSTALLED-LOCAL-001"
    assert scenario.is_live is False
    assert scenario.scenario_class == "deterministic-workflow"
    assert scenario.feature_size == "small"
    assert scenario.automation_lane == "manual"
    assert scenario.canonical_runtime == "generic-cli"
    assert scenario.repo.url == "harness/fixtures/minimal-python"
    assert scenario.run.stage_start == "idea"
    assert scenario.run.stage_end == "plan"
    assert scenario.feature_source is not None
    assert scenario.feature_source.mode == "fixture-seed"
    assert scenario.feature_source.fixture_path == "harness/fixtures/minimal-python"
    assert scenario.raw["operator_execution"] == {
        "install_channel": "uv-tool-run",
        "artifact_source": "source-checkout",
        "source_checkout_path": "/path/to/ai_driven_dev_v2",
        "execution_cwd": "local-fixture-root",
        "workspace_root": ".aidd",
        "github_issue_intake": False,
    }
    assert scenario.raw["aidd_invocation"]["command"] == [
        "uv",
        "tool",
        "run",
        "--from",
        "/path/to/ai_driven_dev_v2",
        "aidd",
        "run",
    ]
    setup_commands = "\n".join(scenario.setup.commands)
    verify_commands = "\n".join(scenario.verify.commands)
    assert 'command = "python ../aidd_fixture_runtime.py"' in setup_commands
    assert "aidd doctor --config aidd.example.toml" in setup_commands
    assert "aidd init --work-item WI-INSTALLED-LOCAL-SMOKE" in setup_commands
    assert "--request" in setup_commands
    assert "--root .aidd" in setup_commands
    assert "aidd run show --work-item WI-INSTALLED-LOCAL-SMOKE --root .aidd" in (
        verify_commands
    )
    assert "aidd run logs --work-item WI-INSTALLED-LOCAL-SMOKE --stage plan" in (
        verify_commands
    )
    assert "aidd run artifacts --work-item WI-INSTALLED-LOCAL-SMOKE --stage plan" in (
        verify_commands
    )
    assert "aidd stage questions plan --work-item WI-INSTALLED-LOCAL-SMOKE" in (
        verify_commands
    )
    assert "answers.md" in verify_commands


def test_local_fixture_workflow_scenarios_use_workspace_relative_runtime_path() -> None:
    scenario_paths = (
        (
            Path("harness/scenarios/deterministic/project-set-plan-context.yaml"),
            'command = "python3 ../aidd_fixture_runtime.py"',
        ),
        (
            Path("harness/scenarios/smoke/installed-local-project-fixture.yaml"),
            'command = "python ../aidd_fixture_runtime.py"',
        ),
    )

    for scenario_path, expected_command in scenario_paths:
        scenario = load_scenario(scenario_path)
        setup_commands = "\n".join(scenario.setup.commands)
        assert expected_command in setup_commands


def test_deterministic_workflow_scenarios_cover_medium_ci_and_large_manual_buckets() -> None:
    medium_ci = load_scenario(
        Path("harness/scenarios/deterministic/minimal-python-bounded-workflow.yaml")
    )
    large_manual = load_scenario(
        Path("harness/scenarios/deterministic/minimal-python-full-workflow.yaml")
    )

    assert medium_ci.is_live is False
    assert medium_ci.scenario_class == "deterministic-workflow"
    assert medium_ci.feature_size == "medium"
    assert medium_ci.automation_lane == "ci"
    assert medium_ci.canonical_runtime == "opencode"
    assert medium_ci.feature_source is not None
    assert medium_ci.feature_source.mode == "fixture-seed"
    assert medium_ci.feature_source.selection_policy == "fixture-owned"
    assert medium_ci.feature_source.fixture_path == "harness/fixtures/minimal-python"
    assert medium_ci.run.stage_start == "idea"
    assert medium_ci.run.stage_end == "tasklist"

    assert large_manual.is_live is False
    assert large_manual.scenario_class == "deterministic-workflow"
    assert large_manual.feature_size == "large"
    assert large_manual.automation_lane == "manual"
    assert large_manual.canonical_runtime == "generic-cli"
    assert large_manual.feature_source is not None
    assert large_manual.feature_source.mode == "fixture-seed"
    assert large_manual.run.stage_start == "idea"
    assert large_manual.run.stage_end == "qa"


def test_task_execution_scenario_declares_incremental_full_flow_evidence() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/deterministic/minimal-python-task-execution.yaml")
    )

    assert scenario.scenario_id == "AIDD-DETERMINISTIC-004"
    assert scenario.scenario_class == "deterministic-workflow"
    assert scenario.feature_size == "medium"
    assert scenario.automation_lane == "ci"
    assert scenario.canonical_runtime == "generic-cli"
    assert scenario.run.stage_start == "idea"
    assert scenario.run.stage_end == "qa"
    assert scenario.run.interview_required is True
    assert scenario.feature_source is not None
    assert scenario.feature_source.seed_id == "minimal-python-task-execution"
    verification = "\n".join(scenario.verify.commands)
    assert "task-ledger.json" in verification
    assert "implementation-report.md" in verification
    assert "qa-report.md" in verification
    assert "finalization/attempts/attempt-0001" in verification
    assert "tasks/TL-2/attempts/attempt-0001/task-diff.json" in verification
    assert "tasks/TL-3/attempts/attempt-0001/attempt-state.json" in verification
    manifest = Path(
        "harness/scenarios/deterministic/minimal-python-task-execution.yaml"
    ).read_text(encoding="utf-8")
    assert "aggregate finalization succeed" in manifest


def test_project_set_deterministic_scenario_declares_two_root_context_checks() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/deterministic/project-set-plan-context.yaml")
    )

    assert scenario.scenario_id == "AIDD-DETERMINISTIC-003"
    assert scenario.is_live is False
    assert scenario.scenario_class == "deterministic-workflow"
    assert scenario.feature_source is not None
    assert scenario.feature_source.seed_id == "minimal-python-project-set-plan-context"
    assert scenario.run.stage_start == "idea"
    assert scenario.run.stage_end == "plan"
    assert any("[[project_set.projects]]" in command for command in scenario.setup.commands)
    assert any("`api`" in command for command in scenario.verify.commands)
    assert any("`web`" in command for command in scenario.verify.commands)
    assert any("artifact-index.json" in command for command in scenario.verify.commands)
    assert any("input-bundle.md" in command for command in scenario.verify.commands)
