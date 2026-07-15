from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.stages import STAGES
from aidd.core.workspace import (
    DEFAULT_CONTRACT_REFERENCES_FILENAME,
    REQUEST_CONTEXT_FILENAMES,
    RESERVED_STAGE_FILENAMES,
    STAGE_INPUT_DIRNAME,
    STAGE_OUTPUT_DIRNAME,
    WORKITEM_CONTEXT_DIRNAME,
    WORKITEM_METADATA_FILENAME,
    WORKITEM_STAGES_DIRNAME,
    WORKSPACE_CONFIG_DIRNAME,
    WORKSPACE_REPORTS_DIRNAME,
    WORKSPACE_REPORTS_EVALS_DIRNAME,
    WORKSPACE_REPORTS_RUNS_DIRNAME,
    WORKSPACE_TRACES_DIRNAME,
    WORKSPACE_TRACES_REPLAYS_DIRNAME,
    WORKSPACE_TRACES_SESSIONS_DIRNAME,
    WORKSPACE_WORKITEMS_DIRNAME,
    WorkspaceBootstrapService,
    create_workspace_tree,
    init_workspace,
    seed_work_item_context,
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


@pytest.mark.parametrize(
    "work_item",
    (
        "",
        " ",
        ".",
        "..",
        "../WI-1",
        "WI/1",
        "WI\\1",
        "/WI-1",
        "bad$id",
        "X" * 129,
    ),
)
def test_workspace_rejects_unsafe_work_item_before_any_write(
    tmp_path: Path,
    work_item: str,
) -> None:
    root = tmp_path / ".aidd"

    with pytest.raises(ValueError, match="work_item"):
        create_workspace_tree(root=root, work_item=work_item)

    assert not root.exists()


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="symlinks unavailable")
def test_workspace_rejects_workitems_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / WORKSPACE_WORKITEMS_DIRNAME).symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="resolve directly below"):
        create_workspace_tree(root=root, work_item="WI-1")

    assert tuple(outside.iterdir()) == ()


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="symlinks unavailable")
def test_workspace_rejects_work_item_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    outside = tmp_path / "outside"
    workitems = root / WORKSPACE_WORKITEMS_DIRNAME
    workitems.mkdir(parents=True)
    outside.mkdir()
    (workitems / "WI-1").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="resolve directly below"):
        create_workspace_tree(root=root, work_item="WI-1")

    assert tuple(outside.iterdir()) == ()


def test_init_workspace_seeds_non_control_stage_files(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"

    item_root = init_workspace(root=root, work_item=work_item)
    plan_stage_root = item_root / WORKITEM_STAGES_DIRNAME / "plan"

    for filename in RESERVED_STAGE_FILENAMES:
        if filename == "repair-brief.md":
            continue
        assert (plan_stage_root / filename).exists()
    assert not (plan_stage_root / "repair-brief.md").exists()


def test_init_workspace_seeds_default_contract_references(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"

    item_root = init_workspace(root=root, work_item=work_item)
    references_path = item_root / WORKITEM_CONTEXT_DIRNAME / DEFAULT_CONTRACT_REFERENCES_FILENAME

    assert references_path.exists()
    content = references_path.read_text(encoding="utf-8")
    assert "contracts/documents/stage-brief.md" in content
    assert "contracts/stages/plan.md" in content


def test_init_workspace_seeds_stable_work_item_metadata(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"

    item_root = init_workspace(root=root, work_item=work_item)
    metadata_path = item_root / WORKITEM_METADATA_FILENAME

    assert metadata_path.exists()
    first_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert first_payload["work_item_id"] == work_item
    assert first_payload["schema_version"] == 1
    assert first_payload["stage_order"] == list(STAGES)

    init_workspace(root=root, work_item=work_item)
    second_payload = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert second_payload == first_payload


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


def test_workspace_bootstrap_service_bootstraps_work_item(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    service = WorkspaceBootstrapService(root=root)

    item_root = service.bootstrap_work_item(work_item="WI-001")

    assert item_root == root / WORKSPACE_WORKITEMS_DIRNAME / "WI-001"
    assert (item_root / WORKITEM_METADATA_FILENAME).exists()


def test_init_workspace_bootstraps_fresh_root(tmp_path: Path) -> None:
    root = tmp_path / "fresh-root"
    work_item = "WI-NEW"

    assert root.exists() is False
    item_root = init_workspace(root=root, work_item=work_item)

    assert item_root == root / WORKSPACE_WORKITEMS_DIRNAME / work_item
    assert (item_root / WORKITEM_CONTEXT_DIRNAME).exists()
    assert (item_root / WORKITEM_STAGES_DIRNAME / "plan" / STAGE_INPUT_DIRNAME).exists()
    assert (item_root / WORKITEM_STAGES_DIRNAME / "plan" / STAGE_OUTPUT_DIRNAME).exists()


def test_init_workspace_is_idempotent_for_existing_directories(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"

    first = init_workspace(root=root, work_item=work_item)
    second = init_workspace(root=root, work_item=work_item)

    assert first == second
    assert (second / WORKITEM_METADATA_FILENAME).exists()


def test_init_workspace_recovers_partially_initialized_workspace(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-001"
    partial_stage_root = (
        root / WORKSPACE_WORKITEMS_DIRNAME / work_item / WORKITEM_STAGES_DIRNAME / "plan"
    )
    (partial_stage_root / STAGE_INPUT_DIRNAME).mkdir(parents=True)
    existing_stage_result = partial_stage_root / "stage-result.md"
    existing_stage_result.write_text("# Stage result\n\npre-existing\n", encoding="utf-8")

    init_workspace(root=root, work_item=work_item)

    assert (partial_stage_root / STAGE_OUTPUT_DIRNAME).exists()
    assert (partial_stage_root / "stage-brief.md").exists()
    assert existing_stage_result.read_text(encoding="utf-8") == "# Stage result\n\npre-existing\n"


def test_seed_work_item_context_writes_request_documents(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-REQ"
    init_workspace(root=root, work_item=work_item)

    result = seed_work_item_context(
        root=root,
        work_item=work_item,
        request_text="Implement CSV import validation.",
        project_root=tmp_path,
    )

    context_root = work_item_context_root(root=root, work_item=work_item)
    assert result.paths == tuple(context_root / filename for filename in REQUEST_CONTEXT_FILENAMES)
    assert result.overwritten is False
    assert "Implement CSV import validation." in result.intake_path.read_text(encoding="utf-8")
    assert "Implement CSV import validation." in result.user_request_path.read_text(
        encoding="utf-8"
    )
    assert tmp_path.as_posix() in result.repository_state_path.read_text(encoding="utf-8")


def test_seed_work_item_context_preserves_existing_docs_without_force(
    tmp_path: Path,
) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-REQ"
    init_workspace(root=root, work_item=work_item)
    context_root = work_item_context_root(root=root, work_item=work_item)
    intake_path = context_root / "intake.md"
    intake_path.write_text("# Intake\n\nExisting.\n", encoding="utf-8")

    try:
        seed_work_item_context(
            root=root,
            work_item=work_item,
            request_text="Replace existing intake.",
        )
    except FileExistsError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected FileExistsError for existing context docs.")

    assert "Use --force-context" in message
    assert intake_path.read_text(encoding="utf-8") == "# Intake\n\nExisting.\n"


def test_seed_work_item_context_overwrites_existing_docs_with_force(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    work_item = "WI-REQ"
    init_workspace(root=root, work_item=work_item)
    intake_path = work_item_context_root(root=root, work_item=work_item) / "intake.md"
    intake_path.write_text("# Intake\n\nExisting.\n", encoding="utf-8")

    result = seed_work_item_context(
        root=root,
        work_item=work_item,
        request_text="Replace existing intake.",
        force=True,
    )

    assert result.overwritten is True
    assert "Replace existing intake." in intake_path.read_text(encoding="utf-8")
