from __future__ import annotations

from pathlib import Path

from aidd.core.stages import STAGES
from aidd.core.workspace import (
    DEFAULT_CONTRACT_REFERENCES_FILENAME,
    RESERVED_STAGE_FILENAMES,
    STAGE_INPUT_DIRNAME,
    STAGE_OUTPUT_DIRNAME,
    WORKITEM_CONTEXT_DIRNAME,
    WORKITEM_STAGES_DIRNAME,
    WORKSPACE_CONFIG_DIRNAME,
    WORKSPACE_REPORTS_DIRNAME,
    WORKSPACE_REPORTS_EVALS_DIRNAME,
    WORKSPACE_REPORTS_RUNS_DIRNAME,
    WORKSPACE_TRACES_DIRNAME,
    WORKSPACE_TRACES_REPLAYS_DIRNAME,
    WORKSPACE_TRACES_SESSIONS_DIRNAME,
    WORKSPACE_WORKITEMS_DIRNAME,
    create_workspace_tree,
    init_workspace,
    stage_input_root,
    stage_output_root,
    stage_root,
    work_item_context_root,
    work_item_root,
    work_item_stages_root,
    workspace_workitems_root,
)


def test_workspace_helpers_follow_canonical_layout(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"
    stage = "plan"

    expected_workitems_root = root / WORKSPACE_WORKITEMS_DIRNAME
    expected_work_item_root = expected_workitems_root / work_item
    expected_context_root = expected_work_item_root / WORKITEM_CONTEXT_DIRNAME
    expected_stages_root = expected_work_item_root / WORKITEM_STAGES_DIRNAME
    expected_stage_root = expected_stages_root / stage
    expected_input_root = expected_stage_root / STAGE_INPUT_DIRNAME
    expected_output_root = expected_stage_root / STAGE_OUTPUT_DIRNAME

    assert workspace_workitems_root(root) == expected_workitems_root
    assert work_item_root(root, work_item) == expected_work_item_root
    assert work_item_context_root(root, work_item) == expected_context_root
    assert work_item_stages_root(root, work_item) == expected_stages_root
    assert stage_root(root, work_item, stage) == expected_stage_root
    assert stage_input_root(root, work_item, stage) == expected_input_root
    assert stage_output_root(root, work_item, stage) == expected_output_root


def test_reserved_stage_filenames_are_seeded_by_init(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"

    item_root = init_workspace(root=root, work_item=work_item)
    plan_stage_root = item_root / WORKITEM_STAGES_DIRNAME / "plan"

    for filename in RESERVED_STAGE_FILENAMES:
        assert (plan_stage_root / filename).exists()


def test_init_workspace_seeds_default_contract_references(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"

    item_root = init_workspace(root=root, work_item=work_item)
    references_path = item_root / WORKITEM_CONTEXT_DIRNAME / DEFAULT_CONTRACT_REFERENCES_FILENAME

    assert references_path.exists()
    content = references_path.read_text(encoding="utf-8")
    assert "contracts/documents/stage-brief.md" in content
    assert "contracts/stages/plan.md" in content


def test_create_workspace_tree_builds_canonical_directories(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"

    item_root = create_workspace_tree(root=root, work_item=work_item)

    assert item_root == root / WORKSPACE_WORKITEMS_DIRNAME / work_item
    assert (root / WORKSPACE_CONFIG_DIRNAME).exists()
    assert (root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_RUNS_DIRNAME).exists()
    assert (root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_EVALS_DIRNAME).exists()
    assert (root / WORKSPACE_TRACES_DIRNAME / WORKSPACE_TRACES_SESSIONS_DIRNAME).exists()
    assert (root / WORKSPACE_TRACES_DIRNAME / WORKSPACE_TRACES_REPLAYS_DIRNAME).exists()
    assert (item_root / WORKITEM_CONTEXT_DIRNAME).exists()

    for stage in STAGES:
        assert (item_root / WORKITEM_STAGES_DIRNAME / stage / STAGE_INPUT_DIRNAME).exists()
        assert (item_root / WORKITEM_STAGES_DIRNAME / stage / STAGE_OUTPUT_DIRNAME).exists()
