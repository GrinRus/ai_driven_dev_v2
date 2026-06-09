from __future__ import annotations

import json
from pathlib import Path

from aidd.core.run_comparison import resolve_run_comparison
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempt_root,
    run_manifest_path,
    write_attempt_artifact_index,
)


def _set_manifest_prompts(
    workspace_root: Path,
    *,
    run_id: str,
    prompt_hash: str | None,
) -> None:
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        run_id=run_id,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["prompt_pack_provenance"] = (
        []
        if prompt_hash is None
        else [{"path": "prompt-packs/stages/plan/run.md", "sha256": prompt_hash}]
    )
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _artifact_index_payload(workspace_root: Path, run_id: str) -> tuple[Path, dict[str, object]]:
    path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        run_id=run_id,
        stage="plan",
        attempt_number=1,
    )
    return path, json.loads(path.read_text(encoding="utf-8"))


def _write_run_artifact(
    workspace_root: Path,
    *,
    run_id: str,
    key: str,
    filename: str,
    text: str,
) -> None:
    relative_path = (
        Path("reports")
        / "runs"
        / "WI-CMP"
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / filename
    )
    path = workspace_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    index_path, payload = _artifact_index_payload(workspace_root, run_id)
    documents = payload.setdefault("documents", {})
    assert isinstance(documents, dict)
    documents[key] = relative_path.as_posix()
    index_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _prepare_comparison_run(
    workspace_root: Path,
    *,
    run_id: str,
    status: str,
    prompt_hash: str | None,
    input_bundle: str,
    validator_verdict: str,
) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "comparison-test"},
    )
    _set_manifest_prompts(workspace_root, run_id=run_id, prompt_hash=prompt_hash)
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        run_id=run_id,
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        run_id=run_id,
        stage="plan",
        status=status,
    )
    attempt_root = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        run_id=run_id,
        stage="plan",
        attempt_number=1,
    )
    attempt_root.joinpath("input-bundle.md").write_text(input_bundle, encoding="utf-8")
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        run_id=run_id,
        stage="plan",
        attempt_number=1,
    )
    attempt_root.joinpath("runtime.log").write_text(f"{run_id} runtime\n", encoding="utf-8")
    _write_run_artifact(
        workspace_root,
        run_id=run_id,
        key="validator_report",
        filename="validator-report.md",
        text=f"# Validator Report\n\n- Verdict: `{validator_verdict}`\n",
    )


def test_run_comparison_detects_prompt_stage_artifact_and_validator_drift(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_comparison_run(
        workspace_root,
        run_id="run-a",
        status="blocked",
        prompt_hash="a" * 64,
        input_bundle="baseline input\n",
        validator_verdict="fail",
    )
    _prepare_comparison_run(
        workspace_root,
        run_id="run-b",
        status="succeeded",
        prompt_hash="b" * 64,
        input_bundle="target input\n",
        validator_verdict="pass",
    )
    _write_run_artifact(
        workspace_root,
        run_id="run-a",
        key="baseline_only",
        filename="baseline-only.md",
        text="baseline only\n",
    )
    _write_run_artifact(
        workspace_root,
        run_id="run-b",
        key="target_only",
        filename="target-only.md",
        text="target only\n",
    )

    view = resolve_run_comparison(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        baseline_run_id="run-a",
        target_run_id="run-b",
    )

    assert view.baseline.run_id == "run-a"
    assert view.target.run_id == "run-b"
    prompt_delta = view.prompt_hash_deltas[0]
    assert prompt_delta.status == "changed"
    assert prompt_delta.baseline_sha256 == "a" * 64
    assert prompt_delta.target_sha256 == "b" * 64
    stage_delta = next(item for item in view.stage_status_deltas if item.stage == "plan")
    assert stage_delta.status == "changed"
    assert stage_delta.baseline_status == "blocked"
    assert stage_delta.target_status == "succeeded"
    artifact_statuses = {
        (item.stage, item.kind, item.key): item.status for item in view.artifact_hash_deltas
    }
    assert artifact_statuses[("plan", "document", "input_bundle")] == "changed"
    assert artifact_statuses[("plan", "document", "baseline_only")] == "removed"
    assert artifact_statuses[("plan", "document", "target_only")] == "added"
    validator_delta = next(
        item for item in view.validator_outcome_deltas if item.stage == "plan"
    )
    assert validator_delta.status == "changed"
    assert validator_delta.baseline_verdict == "fail"
    assert validator_delta.target_verdict == "pass"


def test_run_comparison_warns_for_missing_legacy_provenance_and_unsafe_artifact(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_comparison_run(
        workspace_root,
        run_id="run-a",
        status="succeeded",
        prompt_hash=None,
        input_bundle="baseline input\n",
        validator_verdict="pass",
    )
    _prepare_comparison_run(
        workspace_root,
        run_id="run-b",
        status="succeeded",
        prompt_hash="b" * 64,
        input_bundle="target input\n",
        validator_verdict="pass",
    )
    index_path, payload = _artifact_index_payload(workspace_root, "run-a")
    documents = payload.setdefault("documents", {})
    assert isinstance(documents, dict)
    documents["escape"] = "../outside.md"
    index_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    view = resolve_run_comparison(
        workspace_root=workspace_root,
        work_item="WI-CMP",
        baseline_run_id="run-a",
        target_run_id="run-b",
    )

    assert any("no prompt-pack provenance" in warning for warning in view.warnings)
    assert any("unsafe path" in warning for warning in view.warnings)
