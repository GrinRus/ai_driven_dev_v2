from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.remediation import (
    clear_stale_stages,
    create_remediation_request,
    latest_remediation_input_documents,
    list_remediation_requests,
    load_remediation_status,
    mark_downstream_stale,
)
from aidd.core.run_store import create_run_manifest


def _create_run(workspace_root: Path) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "remediation-test"},
        workflow_stage_start="idea",
        workflow_stage_end="qa",
    )


def test_create_remediation_request_writes_durable_implement_input(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _create_run(workspace_root)

    request = create_remediation_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        source_stage="review",
        source_ids=("RV-1",),
        operator_note="Fix rejected review finding.",
    )

    text = request.request_path.read_text(encoding="utf-8")
    listed = list_remediation_requests(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
    )
    latest = latest_remediation_input_documents(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        target_stage="implement",
    )
    assert request.request_id == "request-0001"
    assert "Source stage: `review`" in text
    assert "`RV-1`" in text
    assert "Fix rejected review finding." in text
    assert listed == (request,)
    assert latest == (request.request_path,)


def test_remediation_request_rejects_invalid_source_and_target(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _create_run(workspace_root)

    with pytest.raises(ValueError, match="source_stage must be review or qa"):
        create_remediation_request(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            source_stage="plan",
            source_ids=("RV-1",),
            operator_note="Fix it.",
        )

    with pytest.raises(ValueError, match="target_stage must be implement"):
        create_remediation_request(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            source_stage="qa",
            source_ids=("QA-1",),
            operator_note="Fix it.",
            target_stage="review",
        )


def test_mark_downstream_stale_and_clear_preserves_request_list(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _create_run(workspace_root)
    request = create_remediation_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        source_stage="qa",
        source_ids=("risk-1",),
        operator_note="Fix QA risk.",
    )

    status = mark_downstream_stale(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        invalidated_by=request.request_id,
    )
    assert [item.stage for item in status.stale_stages] == ["review", "qa"]
    assert all(item.invalidated_by == request.request_id for item in status.stale_stages)
    assert load_remediation_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
    ).requests == (request,)

    cleared = clear_stale_stages(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stages=("review",),
    )
    assert [item.stage for item in cleared.stale_stages] == ["qa"]
    assert cleared.requests == (request,)


@pytest.mark.parametrize(
    "run_id",
    ("", ".", "..", "../run", "run/child", r"run\child", "/absolute"),
)
def test_remediation_rejects_invalid_run_ids_without_partial_state(
    tmp_path: Path,
    run_id: str,
) -> None:
    workspace_root = tmp_path / ".aidd"

    with pytest.raises(ValueError):
        create_remediation_request(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            source_stage="review",
            source_ids=("RV-1",),
            operator_note="Fix it.",
        )

    assert not (workspace_root / "workitems").exists()


def test_remediation_rejects_symlinked_overlay_escape(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _create_run(workspace_root)
    work_item_root = workspace_root / "workitems" / "WI-UI"
    work_item_root.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside-remediations"
    outside.mkdir()
    (work_item_root / "remediations").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="owning root|storage boundary"):
        create_remediation_request(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            source_stage="review",
            source_ids=("RV-1",),
            operator_note="Fix it.",
        )

    assert list(outside.iterdir()) == []
