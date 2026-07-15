from __future__ import annotations

import shutil
from pathlib import Path

from aidd.validators.cross_document import (
    ANSWER_WITHOUT_QUESTION_CODE,
    BLOCKING_UNANSWERED_CODE,
    DUPLICATE_ANSWER_ID_CODE,
    DUPLICATE_QUESTION_ID_CODE,
    PROJECT_SET_EVIDENCE_MISSING_CODE,
    REPAIR_BRIEF_NOT_REFERENCED_CODE,
    REPAIR_BUDGET_EXHAUSTED_CODE,
    REPAIR_MENTION_WITHOUT_BRIEF_CODE,
    TASKLIST_PLAN_DEPENDENCY_CODE,
    TASKLIST_PLAN_MILESTONE_CODE,
    TASKLIST_PLAN_VERIFICATION_CODE,
    validate_cross_document_consistency,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation


def _write_stage_contract(
    *,
    contracts_root: Path,
    required_inputs: tuple[str, ...],
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    (contracts_root / "review.md").write_text(
        "\n".join(
            [
                "# Stage Contract: `review`",
                "",
                "## Purpose",
                "",
                "Run review-stage document checks.",
                "",
                "## Primary output",
                "",
                *[f"- `{item}`" for item in required_outputs],
                "",
                "## Required inputs",
                "",
                *[f"- `{item}`" for item in required_inputs],
                "",
                "## Prompt pack",
                "",
                *[f"- `{item}`" for item in prompt_pack_paths],
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _touch_contract_references(
    *,
    repo_root: Path,
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    documents_root = repo_root / "contracts" / "documents"
    documents_root.mkdir(parents=True, exist_ok=True)
    for output in required_outputs:
        (documents_root / output).write_text("# Contract\n", encoding="utf-8")

    for prompt_path in prompt_pack_paths:
        prompt_file = repo_root / prompt_path
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text("# Prompt\n", encoding="utf-8")


def _stage_root(workspace_root: Path) -> Path:
    return workspace_root / "workitems" / "WI-001" / "stages" / "review"


def _write_project_set_context(workspace_root: Path) -> None:
    project_set_path = workspace_root / "workitems" / "WI-001" / "context" / "project-set.md"
    project_set_path.parent.mkdir(parents=True, exist_ok=True)
    project_set_path.write_text(
        "# Project set\n\n"
        "## Projects\n\n"
        "| Project id | Root | Role |\n"
        "| --- | --- | --- |\n"
        "| `api` | `services/api` | `primary` |\n"
        "| `web` | `apps/web` | `unspecified` |\n",
        encoding="utf-8",
    )


def _copy_example_bundle(
    *,
    example_root: Path,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> None:
    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    stage_root.mkdir(parents=True, exist_ok=True)
    for source_path in example_root.glob("*.md"):
        shutil.copy2(source_path, stage_root / source_path.name)


def _write_plan_tasklist_pair(
    workspace_root: Path,
    *,
    task_one_milestone: str = "M1",
    task_two_milestone: str = "M2",
    task_two_command: str = "uv run pytest -q tests/api",
) -> None:
    work_item_root = workspace_root / "workitems" / "WI-001" / "stages"
    plan_output = work_item_root / "plan" / "output"
    tasklist_root = work_item_root / "tasklist"
    plan_output.mkdir(parents=True)
    tasklist_root.mkdir(parents=True)
    plan_output.joinpath("plan.md").write_text(
        "# Plan\n\n"
        "## Milestones\n\n"
        "- M1: Add the model.\n"
        "- M2: Add the API.\n\n"
        "## Dependencies\n\n"
        "- M2 depends on M1.\n\n"
        "## Verification notes\n\n"
        "- M1: run `uv run pytest -q tests/model`.\n"
        "- M2: run `uv run pytest -q tests/api`.\n",
        encoding="utf-8",
    )
    tasklist_root.joinpath("tasklist.md").write_text(
        "# Tasklist\n\n"
        "## Ordered tasks\n\n"
        "### T1 — Add model\n\n"
        f"- Outcome: Complete {task_one_milestone}.\n"
        "- Dominant deliverable: `src/model.py`.\n"
        "- In scope: `src/model.py`.\n"
        "- Acceptance criteria:\n"
        "  - T1-AC1: The model behavior required by the milestone is covered.\n\n"
        "### T2 — Add API\n\n"
        f"- Outcome: Complete {task_two_milestone}.\n"
        "- Dominant deliverable: `src/api.py`.\n"
        "- In scope: `src/api.py`.\n"
        "- Acceptance criteria:\n"
        "  - T2-AC1: The API behavior required by the milestone is covered.\n\n"
        "## Dependencies\n\n"
        "- T1: none\n"
        "- T2: T1\n\n"
        "## Verification notes\n\n"
        f"- T1: {task_one_milestone} `uv run pytest -q tests/model`\n"
        f"- T2: M2 `{task_two_command}`\n",
        encoding="utf-8",
    )


def test_tasklist_plan_cross_validation_accepts_exact_milestone_bindings(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_tasklist_pair(workspace_root)

    findings = validate_cross_document_consistency(
        stage="tasklist",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_tasklist_plan_cross_validation_reports_unknown_and_uncovered_milestones(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_tasklist_pair(workspace_root, task_one_milestone="M9")

    findings = validate_cross_document_consistency(
        stage="tasklist",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    milestone_findings = [item for item in findings if item.code == TASKLIST_PLAN_MILESTONE_CODE]
    assert len(milestone_findings) == 2
    assert any("unknown M9" in item.message for item in milestone_findings)
    assert any("`M1` is not covered" in item.message for item in milestone_findings)


def test_tasklist_plan_cross_validation_reports_inverted_dependency_mapping(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_tasklist_pair(
        workspace_root,
        task_one_milestone="M2",
        task_two_milestone="M1",
    )

    findings = validate_cross_document_consistency(
        stage="tasklist",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    assert any(item.code == TASKLIST_PLAN_DEPENDENCY_CODE for item in findings)


def test_tasklist_plan_cross_validation_preserves_exact_authored_command(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_tasklist_pair(
        workspace_root,
        task_two_command="uv run pytest tests/api",
    )

    findings = validate_cross_document_consistency(
        stage="tasklist",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    assert [item.code for item in findings] == [TASKLIST_PLAN_VERIFICATION_CODE]
    assert "uv run pytest -q tests/api" in findings[0].message


def test_validate_cross_document_consistency_passes_for_consistent_bundle(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n- `Q1` `[blocking]` Confirm risk acceptance owner.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n- `Q1` `[resolved]` Release manager owns final risk sign-off.\n",
        encoding="utf-8",
    )
    (stage_root / "stage-result.md").write_text(
        "# Stage\n\nreview\n\n# Attempt history\n\n- Attempt `1` (`initial`) -> succeeded.\n",
        encoding="utf-8",
    )

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == ()


def test_validate_cross_document_consistency_passes_for_project_set_evidence(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    _write_project_set_context(workspace_root)
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-result.md").write_text(
        "# Stage\n\nreview\n\n"
        "## Attempt history\n\n- Attempt `1` (`initial`) -> succeeded.\n\n"
        "## Project-set evidence\n\n"
        "- Context: `workitems/WI-001/context/project-set.md`\n"
        "- `api` at `services/api` retained review evidence.\n"
        "- `web` at `apps/web` was unaffected by this review stage.\n",
        encoding="utf-8",
    )

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == ()


def test_validate_cross_document_consistency_requires_project_set_evidence(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    _write_project_set_context(workspace_root)
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-result.md").write_text(
        "# Stage\n\nreview\n\n## Attempt history\n\n- Attempt `1` (`initial`) -> succeeded.\n",
        encoding="utf-8",
    )

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert [finding.code for finding in findings] == [
        PROJECT_SET_EVIDENCE_MISSING_CODE,
        PROJECT_SET_EVIDENCE_MISSING_CODE,
        PROJECT_SET_EVIDENCE_MISSING_CODE,
        PROJECT_SET_EVIDENCE_MISSING_CODE,
    ]
    assert "Project-set evidence" in findings[0].message
    assert "project-set context path" in findings[1].message
    assert "project id `api` and project root `services/api`" in findings[2].message
    assert "project id `web` and project root `apps/web`" in findings[3].message


def test_validate_cross_document_consistency_reports_answer_without_question(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n- `Q1` `[non-blocking]` Confirm scope.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n- `Q9` `[resolved]` Scope is confirmed.\n",
        encoding="utf-8",
    )
    (stage_root / "stage-result.md").write_text("# Stage\n\nreview\n", encoding="utf-8")

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=ANSWER_WITHOUT_QUESTION_CODE,
            message=(
                "Answer references `Q9` but no matching question exists in questions.md."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/review/answers.md",
                line_number=3,
            ),
        ),
    )


def test_validate_cross_document_consistency_reports_duplicate_ids(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        (
            "# Questions\n\n"
            "- `Q1` `[blocking]` Confirm scope.\n"
            "- `Q1` `[non-blocking]` Confirm rollout.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        (
            "# Answers\n\n"
            "- `Q1` `[resolved]` Scope is confirmed.\n"
            "- `Q1` `[partial]` Rollout pending.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "stage-result.md").write_text("# Stage\n\nreview\n", encoding="utf-8")

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=DUPLICATE_QUESTION_ID_CODE,
            message="Duplicate question id `Q1` in questions.md.",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/review/questions.md",
                line_number=4,
            ),
        ),
        ValidationFinding(
            code=DUPLICATE_ANSWER_ID_CODE,
            message="Duplicate answer id `Q1` in answers.md.",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/review/answers.md",
                line_number=4,
            ),
        ),
    )


def test_validate_cross_document_consistency_ignores_inline_answer_references(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n- `Q1` `[non-blocking]` Confirm scope.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        (
            "# Answers\n\n"
            "- `Q1` `[resolved]` Scope is confirmed.\n"
            "  The prior plan-stage `Q1 [resolved]` answer remains "
            "the source of truth.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "stage-result.md").write_text("# Stage\n\nreview\n", encoding="utf-8")

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == ()


def test_validate_cross_document_consistency_reports_repair_mismatch_cases(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-result.md").write_text(
        (
            "# Stage\n\nreview\n\n"
            "# Attempt history\n\n"
            "- Attempt `1` (`initial`) -> failed validation.\n"
            "- Attempt `2` (`repair`) -> succeeded.\n"
        ),
        encoding="utf-8",
    )

    findings_without_brief = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    assert findings_without_brief == (
        ValidationFinding(
            code=REPAIR_MENTION_WITHOUT_BRIEF_CODE,
            message="Stage result records a repair attempt but `repair-brief.md` is missing.",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/review/stage-result.md",
            ),
        ),
    )

    (stage_root / "repair-brief.md").write_text("# Failed checks\n\n- none\n", encoding="utf-8")
    findings_without_reference = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    assert findings_without_reference == (
        ValidationFinding(
            code=REPAIR_BRIEF_NOT_REFERENCED_CODE,
            message=(
                "`repair-brief.md` exists but stage-result.md does not reference it for "
                "repair traceability."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/review/stage-result.md",
            ),
        ),
    )


def test_validate_cross_document_consistency_reports_unresolved_blocking_question(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n- `Q1` `[blocking]` Confirm scope.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n- `Q1` `[partial]` Scope details are pending legal review.\n",
        encoding="utf-8",
    )
    (stage_root / "stage-result.md").write_text(
        "# Stage\n\nreview\n\n## Status\n\n- `succeeded`\n",
        encoding="utf-8",
    )

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=BLOCKING_UNANSWERED_CODE,
            message=(
                "`Q1` is marked `[blocking]` and has no matching `[resolved]` answer in "
                "`answers.md`. Stage status must not be `succeeded` while blocking questions "
                "remain."
            ),
            severity="critical",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/review/questions.md",
                line_number=3,
            ),
        ),
    )


def test_validate_cross_document_consistency_reports_exhausted_repair_budget(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-result.md").write_text(
        (
            "# Stage\n\nreview\n\n"
            "## Status\n\n"
            "- `blocked`\n\n"
            "## Terminal state notes\n\n"
            "- See `repair-brief.md` for the final exhausted-budget decision context.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "repair-brief.md").write_text(
        "# Failed checks\n\n"
        "- `SEM-PLACEHOLDER-CONTENT` (`high`) in `workitems/WI-001/stages/review/plan.md`.\n\n"
        "## Required corrections\n\n"
        "- Remove placeholder text and rerun checks.\n\n"
        "## Relevant upstream docs\n\n"
        "- `questions.md`\n\n"
        "repair-budget-exhausted\n",
        encoding="utf-8",
    )

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=REPAIR_BUDGET_EXHAUSTED_CODE,
            message=(
                "`repair-brief.md` declares `repair-budget-exhausted`; stage-result.md status "
                "must be `failed`."
            ),
            severity="critical",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/review/stage-result.md",
                line_number=7,
            ),
        ),
    )


def test_validate_cross_document_consistency_allows_failed_exhausted_repair_budget(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=("prompt-packs/stages/review/system.md",),
    )

    workspace_root = tmp_path / ".aidd"
    stage_root = _stage_root(workspace_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-result.md").write_text(
        (
            "# Stage\n\nreview\n\n"
            "## Status\n\n"
            "- `failed`\n\n"
            "## Terminal state notes\n\n"
            "- Repair budget status: `repair-budget-exhausted`; see `repair-brief.md`.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "repair-brief.md").write_text(
        "# Failed checks\n\n"
        "- `SEM-PLACEHOLDER-CONTENT` (`high`) in `workitems/WI-001/stages/review/plan.md`.\n\n"
        "## Required corrections\n\n"
        "- Remove placeholder text and rerun checks.\n\n"
        "## Relevant upstream docs\n\n"
        "- `questions.md`\n\n"
        "repair-budget-exhausted\n",
        encoding="utf-8",
    )

    findings = validate_cross_document_consistency(
        stage="review",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == tuple()


def test_validate_cross_document_consistency_avoids_false_positive_on_answered_bundle(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _copy_example_bundle(
        example_root=Path("contracts/examples/research/answered"),
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="research",
    )

    findings = validate_cross_document_consistency(
        stage="research",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_cross_document_consistency_avoids_false_negative_on_unresolved_bundle(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _copy_example_bundle(
        example_root=Path("contracts/examples/research/unresolved"),
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="research",
    )

    findings = validate_cross_document_consistency(
        stage="research",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=BLOCKING_UNANSWERED_CODE,
            message=(
                "`Q1` is marked `[blocking]` and has no matching `[resolved]` answer in "
                "`answers.md`."
            ),
            severity="critical",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/research/questions.md",
                line_number=5,
            ),
        ),
    )
