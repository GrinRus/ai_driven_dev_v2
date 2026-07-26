from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.harness.live_e2e_flow_state import find_resume_state

RUN_ID = "canonical-run"
SCENARIO_ID = "LIVE-FIXTURE"
RUNTIME_ID = "generic-runtime"
WORK_ITEM = "WI-FIXTURE"


def _identity(
    *,
    report_root: Path,
    work_root: Path,
    scenario_path: Path,
    run_id: str = RUN_ID,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "scenario_id": SCENARIO_ID,
        "scenario_path": scenario_path.resolve().as_posix(),
        "runtime_id": RUNTIME_ID,
        "work_item": WORK_ITEM,
        "report_root": report_root.resolve().as_posix(),
        "work_root": work_root.resolve().as_posix(),
        "run_work_root": (work_root.resolve() / run_id).as_posix(),
        "bundle_root": (report_root.resolve() / run_id).as_posix(),
    }


def _write_state(
    *,
    report_root: Path,
    work_root: Path,
    scenario_path: Path,
    run_id: str = RUN_ID,
    payload: dict[str, object] | None = None,
) -> Path:
    path = report_root / run_id / "flow-state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "schema_version": 2,
        "status": "pass",
        "next_action": "finish",
        "evaluator_pid": 99999999,
        **_identity(
            report_root=report_root,
            work_root=work_root,
            scenario_path=scenario_path,
            run_id=run_id,
        ),
        **(payload or {}),
    }
    path.write_text(json.dumps(state), encoding="utf-8")
    return path


def _find(
    *,
    report_root: Path,
    work_root: Path,
    scenario_path: Path,
    run_id: str | None = RUN_ID,
) -> Path | None:
    return find_resume_state(
        report_root=report_root,
        run_id=run_id,
        scenario_path=scenario_path,
        scenario_id=SCENARIO_ID,
        runtime_id=RUNTIME_ID,
        work_item=WORK_ITEM,
        work_root=work_root,
    )


def test_stale_running_reconstruction_is_idempotent(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    work_root = tmp_path / "work"
    scenario_path = tmp_path / "scenario.yaml"
    state_path = _write_state(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
        payload={
            "status": "running",
            "next_action": "run-stage",
        },
    )

    assert _find(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
    ) == state_path
    first_payload = state_path.read_bytes()
    assert _find(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
    ) == state_path

    assert state_path.read_bytes() == first_payload


def test_terminal_state_can_be_reloaded_without_rewriting(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    work_root = tmp_path / "work"
    scenario_path = tmp_path / "scenario.yaml"
    state_path = _write_state(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
    )
    original = state_path.read_bytes()

    assert _find(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
    ) == state_path
    assert _find(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
    ) == state_path
    assert state_path.read_bytes() == original


@pytest.mark.parametrize(
    "run_id",
    (
        "",
        " ",
        "/absolute",
        "nested/run",
        "nested\\run",
        "..",
        "../escape",
        "x" * 129,
    ),
)
def test_resume_rejects_unsafe_run_id_before_path_access(
    tmp_path: Path,
    run_id: str,
) -> None:
    report_root = tmp_path / "reports"

    with pytest.raises(ValueError, match="run_id must be one plain path component"):
        _find(
            report_root=report_root,
            work_root=tmp_path / "work",
            scenario_path=tmp_path / "scenario.yaml",
            run_id=run_id,
        )

    assert not report_root.exists()


def test_resume_rejects_run_root_symlink_escape(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    report_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (report_root / RUN_ID).symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="owning root must stay|resolve directly"):
        _find(
            report_root=report_root,
            work_root=tmp_path / "work",
            scenario_path=tmp_path / "scenario.yaml",
        )


def test_resume_rejects_flow_state_symlink(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    run_root = report_root / RUN_ID
    run_root.mkdir(parents=True)
    outside = tmp_path / "outside-state.json"
    outside.write_text("{}\n", encoding="utf-8")
    (run_root / "flow-state.json").symlink_to(outside)

    with pytest.raises(ValueError, match="flow-state filename|must not be a symlink"):
        _find(
            report_root=report_root,
            work_root=tmp_path / "work",
            scenario_path=tmp_path / "scenario.yaml",
        )


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    (
        ("run_id", "other-run"),
        ("scenario_id", "OTHER-SCENARIO"),
        ("runtime_id", "other-runtime"),
        ("work_item", "WI-OTHER"),
        ("scenario_path", "/tmp/other-scenario.yaml"),
        ("report_root", "/tmp/other-reports"),
        ("work_root", "/tmp/other-work"),
        ("run_work_root", "/tmp/other-run-work"),
        ("bundle_root", "/tmp/other-bundle"),
    ),
)
def test_resume_rejects_wrong_identity_without_mutating_stale_state(
    tmp_path: Path,
    field: str,
    wrong_value: str,
) -> None:
    report_root = tmp_path / "reports"
    work_root = tmp_path / "work"
    scenario_path = tmp_path / "scenario.yaml"
    state_path = _write_state(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
        payload={
            "status": "running",
            "next_action": "run-stage",
            field: wrong_value,
        },
    )
    original = state_path.read_bytes()

    with pytest.raises(ValueError, match=rf"`{field}` identity"):
        _find(
            report_root=report_root,
            work_root=work_root,
            scenario_path=scenario_path,
        )

    assert state_path.read_bytes() == original


def test_canonical_awaiting_review_resume_requires_contained_evidence(
    tmp_path: Path,
) -> None:
    report_root = tmp_path / "reports"
    work_root = tmp_path / "work"
    scenario_path = tmp_path / "scenario.yaml"
    required = report_root / RUN_ID / "stage-quality-audits" / "idea.md"
    required.parent.mkdir(parents=True)
    required.write_text("# Audit\n", encoding="utf-8")
    state_path = _write_state(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
        payload={
            "status": "awaiting-quality-review",
            "quality_review_required_path": required.as_posix(),
        },
    )

    assert _find(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
    ) == state_path


def test_awaiting_review_rejects_evidence_escape(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    work_root = tmp_path / "work"
    scenario_path = tmp_path / "scenario.yaml"
    outside = tmp_path / "outside-audit.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    _write_state(
        report_root=report_root,
        work_root=work_root,
        scenario_path=scenario_path,
        payload={
            "status": "awaiting-quality-review",
            "quality_review_required_path": outside.as_posix(),
        },
    )

    with pytest.raises(ValueError, match="must stay inside"):
        _find(
            report_root=report_root,
            work_root=work_root,
            scenario_path=scenario_path,
        )
