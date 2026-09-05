from __future__ import annotations

from pathlib import Path

import pytest

from aidd.adapters.native_prompt import build_native_prompt_text
from aidd.cli.support import _active_prompt_pack_paths
from aidd.core.repair import render_repair_brief
from aidd.core.stage_preparation import prepare_stage_bundle
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_prompt_pack_file_paths,
    resolve_stage_output_registry,
)
from aidd.core.stages import STAGES
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.reports import render_validator_report


def test_native_prompt_compiler_includes_attempt_bundle_and_contract(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd"
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True)
    stage_brief_path = stage_root / "stage-brief.md"
    input_bundle_path = stage_root / "attempts" / "attempt-0002" / "input-bundle.md"
    repair_brief_path = stage_root / "repair-brief.md"
    prompt_pack_path = repository_root / "prompt-packs" / "stages" / "plan" / "repair.md"
    input_bundle_path.parent.mkdir(parents=True)
    prompt_pack_path.parent.mkdir(parents=True)
    stage_brief_path.write_text("# Stage\n\nplan\n", encoding="utf-8")
    input_bundle_path.write_text("# Input bundle\n\n- upstream evidence\n", encoding="utf-8")
    repair_brief_path.write_text("# Failed checks\n\n- fix plan\n", encoding="utf-8")
    prompt_pack_path.write_text("# Repair prompt\n\nUse budget rules.\n", encoding="utf-8")

    prompt = build_native_prompt_text(
        runtime_id="codex",
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=stage_brief_path,
        prompt_pack_paths=(prompt_pack_path.relative_to(repository_root),),
        repository_root=repository_root,
        attempt_number=2,
        repair_mode=True,
        input_bundle_path=input_bundle_path,
        repair_brief_path=repair_brief_path,
        repair_context_markdown="Mode: `repair`\n\nAttempt number: `2`",
    )

    assert "- Runtime: codex" in prompt
    assert "- Stage: plan" in prompt
    assert "- Work item: WI-001" in prompt
    assert "- Run id: run-001" in prompt
    assert "- Attempt: 2" in prompt
    assert "- Attempt mode: repair" in prompt
    assert "## Input bundle" in prompt
    assert "upstream evidence" in prompt
    assert "## Repair context" in prompt
    assert "Mode: `repair`" in prompt
    assert "## Active prompt pack:" in prompt
    assert "# Repair prompt" in prompt
    assert "`repair-brief.md` is AIDD-owned read-only repair control evidence" in prompt
    assert "AIDD post-runtime validation is the final truth source" in prompt
    assert "do not inspect AIDD validator implementation" in prompt
    assert (
        "emit one brief final response that states the stage artifacts are complete or "
        "blocked, then stop immediately"
    ) in prompt
    assert "After the final required document write, do not read more files" in prompt
    assert "wait for additional instructions" in prompt
    assert "`answers.md` bullets must reuse the same question id" in prompt
    assert "Do not invent `A1`/`A2` answer ids" in prompt
    assert "When there are no questions, write `# Questions\\n\\n- none\\n`" in prompt
    assert "If an active prompt pack mentions a `contracts/...` path" in prompt
    assert "already included in this request as the accessible contract evidence" in prompt
    assert "`git stash`, `git reset`, `git checkout --`, or `git restore`" in prompt
    assert "using ASCII `-> pass`, `-> fail`, or `exit code N` wording" in prompt
    assert "exact path listed in the Stage brief" in prompt
    assert "Do not place required documents only under an `output/` subdirectory" in prompt


def test_native_prompt_compiler_includes_operator_request_context(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd"
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True)
    stage_brief_path = stage_root / "stage-brief.md"
    input_bundle_path = stage_root / "attempts" / "attempt-0002" / "input-bundle.md"
    operator_request_path = stage_root / "operator-requests" / "request-0001.md"
    prompt_pack_path = (
        repository_root / "prompt-packs" / "stages" / "plan" / "intervention.md"
    )
    input_bundle_path.parent.mkdir(parents=True)
    operator_request_path.parent.mkdir(parents=True)
    prompt_pack_path.parent.mkdir(parents=True)
    stage_brief_path.write_text("# Stage\n\nplan\n", encoding="utf-8")
    input_bundle_path.write_text("# Input bundle\n\n- existing plan\n", encoding="utf-8")
    operator_request_path.write_text(
        "# Operator Request\n\n## Request\n\nAdd migration rollback risks.\n",
        encoding="utf-8",
    )
    prompt_pack_path.write_text("# Operator intervention prompt\n", encoding="utf-8")

    prompt = build_native_prompt_text(
        runtime_id="codex",
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=stage_brief_path,
        prompt_pack_paths=(prompt_pack_path.relative_to(repository_root),),
        repository_root=repository_root,
        attempt_number=2,
        repair_mode=False,
        attempt_mode="intervention",
        input_bundle_path=input_bundle_path,
        operator_request_path=operator_request_path,
    )

    assert "- Attempt mode: intervention" in prompt
    assert "## Operator request context" in prompt
    assert "Add migration rollback risks." in prompt
    assert "# Operator intervention prompt" in prompt
    assert "Apply only the requested stage-scoped delta" in prompt


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("attempt_mode", ("initial", "repair", "intervention"))
def test_composed_stage_request_respects_runtime_write_authority(
    tmp_path: Path, stage: str, attempt_mode: str
) -> None:
    """Exercise real contract, brief, active-pack selection, and final native guidance together."""
    repository_root = DEFAULT_STAGE_CONTRACTS_ROOT.parent.parent
    workspace_root = tmp_path / "target-repository" / ".aidd"
    work_item = "WI-OWNERSHIP"
    bundle = prepare_stage_bundle(
        workspace_root=workspace_root, work_item=work_item, stage=stage
    )
    stage_brief_path = tmp_path / "stage-brief.md"
    stage_brief_path.write_text(bundle.stage_brief_markdown, encoding="utf-8")
    registry = resolve_stage_output_registry(
        workspace_root=workspace_root, work_item=work_item, stage=stage
    )
    repair_mode = attempt_mode == "repair"
    active_paths = _active_prompt_pack_paths(
        prompt_pack_paths=resolve_prompt_pack_file_paths(stage=stage),
        repair_mode=repair_mode,
        intervention_mode=attempt_mode == "intervention",
    )
    expected_names = {
        "initial": {"system.md", "run.md", "interview.md"},
        "repair": {"system.md", "run.md", "repair.md", "interview.md"},
        "intervention": {"system.md", "intervention.md"},
    }
    assert {path.name for path in active_paths} == expected_names[attempt_mode]
    input_bundle_path = tmp_path / "input-bundle.md"
    input_bundle_path.write_text(
        "# Input bundle\n\nRetained upstream evidence.\n", encoding="utf-8"
    )
    runtime_output = registry.runtime_authored[0].relative_to(workspace_root).as_posix()
    generated_output = f"workitems/{work_item}/stages/{stage}/stage-result.md"
    repair_context = render_repair_brief(
        validator_report_markdown=render_validator_report(findings=(
            ValidationFinding(
                code="SEM-INCOMPLETE-SECTION", severity="high",
                message="Correct the located substantive-output finding.",
                location=ValidationIssueLocation(workspace_relative_path=runtime_output),
            ),
            ValidationFinding(
                code="SEM-INCOMPLETE-SECTION", severity="high",
                message="Stage must name exactly the canonical current stage.",
                location=ValidationIssueLocation(workspace_relative_path=generated_output),
            ),
        )),
        validator_report_path=f"workitems/{work_item}/stages/{stage}/validator-report.md",
        prior_stage_artifacts=(),
        stage_attempt_count=1,
        max_repair_attempts=2,
    ) if repair_mode else None
    operator_request = "Preserve evidence and clarify the current stage recommendation."
    prompt = build_native_prompt_text(
        runtime_id="codex",
        stage=stage,
        work_item=work_item,
        run_id="run-ownership",
        workspace_root=workspace_root,
        stage_brief_path=stage_brief_path,
        prompt_pack_paths=active_paths,
        repository_root=repository_root,
        attempt_number=1 if attempt_mode == "initial" else 2,
        repair_mode=repair_mode,
        attempt_mode=attempt_mode,
        input_bundle_path=input_bundle_path,
        repair_context_markdown=repair_context,
        operator_request_markdown=operator_request if attempt_mode == "intervention" else None,
    )

    write_targets = prompt.split("# Runtime write targets\n", maxsplit=1)[1].split(
        "\n# ", maxsplit=1
    )[0]
    for path in registry.runtime_authored:
        assert path.relative_to(workspace_root).as_posix() in write_targets
    for path in registry.aidd_generated:
        assert path.name not in write_targets
        assert f"## `{path.name}`" not in bundle.stage_brief_markdown
    for path in active_paths:
        assert path.read_text(encoding="utf-8").strip() in prompt
    assert "Retained upstream evidence." in prompt
    assert f"- Attempt mode: {attempt_mode}" in prompt
    if attempt_mode == "intervention":
        assert operator_request in prompt
    if repair_mode:
        assert "Correct the located substantive-output finding." in prompt
        assert f"AIDD must reconcile `{generated_output}`" in prompt
        assert f"Update `{generated_output}`" not in prompt
        assert f"Update `{runtime_output}`" in prompt

    execution_contract = prompt.rsplit("## Execution contract", maxsplit=1)[1]
    assert "`Runtime write targets` section" in execution_contract
    assert "`Expected output documents` section" not in execution_contract
    assert "Do not write `stage-result.md` or `validator-report.md`" in execution_contract
    assert "If a blocker prevents completion, submit a `[blocking]` question" in execution_contract
    assert "Substantive blocker prose alone does not pause AIDD." in execution_contract
    if attempt_mode in {"repair", "intervention"}:
        mode_prompt = next(path for path in active_paths if path.stem == attempt_mode)
        assert "submit a `[blocking]` question" in mode_prompt.read_text(encoding="utf-8")
    normalized = " ".join(prompt.split())
    # Retained regression signatures are positive mutation instructions from the old composed
    # request, not references to read-only records or legacy evidence.
    forbidden_instructions = (
        "runtime-authored summary draft",
        "When repairing a draft `validator-report.md`",
        "set `stage-result.md`",
        "update `stage-result.md` truthfully",
        "record the outcome truthfully in `stage-result.md`",
        "any repair summary in `stage-result.md`",
        "Re-copy the `stage-result.md` and `validator-report.md` skeleton",
        "create or replace `tasklist.md`, `stage-result.md`",
        "If `stage-result.md` retained the bootstrap placeholder, replace",
        "align `stage-result.md` blockers/next actions",
    )
    for instruction in forbidden_instructions:
        assert instruction not in normalized, (stage, attempt_mode, instruction)
