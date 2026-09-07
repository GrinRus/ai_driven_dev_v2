from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.harness.result_bundle import (
    SUMMARY_FILENAME,
    ensure_result_bundle_layout,
    seal_result_bundle,
)
from aidd.harness.result_bundle_contract import (
    ResultBundleContractError,
    ResultBundleIdentity,
    validate_result_bundle_inventory,
)


def _identity() -> ResultBundleIdentity:
    return ResultBundleIdentity(
        evaluation_run_id="eval-seal-001",
        product_run_id="product-seal-001",
        scenario_id="AIDD-SEAL-TEST",
        runtime_id="generic-cli",
        work_item="WI-SEAL",
    )


def _write_sealable_bundle(tmp_path: Path):
    layout = ensure_result_bundle_layout(workspace_root=tmp_path, run_id="eval-seal-001")
    identity = _identity()
    metadata = {
        "evaluation_run_id": identity.evaluation_run_id,
        "product_run_id": identity.product_run_id,
        "scenario_id": identity.scenario_id,
        "runtime_id": identity.runtime_id,
        "work_item": identity.work_item,
    }
    layout.harness_metadata_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")
    required_paths = (
        layout.install_transcript_path,
        layout.setup_transcript_path,
        layout.run_transcript_path,
        layout.verify_transcript_path,
        layout.teardown_transcript_path,
        layout.feature_selection_path,
        layout.runtime_log_path,
        layout.validator_report_path,
        layout.repair_history_path,
        layout.log_analysis_path,
        layout.stage_timing_json_path,
        layout.stage_timing_markdown_path,
        layout.self_repair_matrix_json_path,
        layout.self_repair_matrix_path,
        layout.grader_path,
        layout.verdict_path,
        layout.run_root / SUMMARY_FILENAME,
    )
    for path in required_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(path.name + "\n", encoding="utf-8")
    (layout.run_root / "canonical-evidence" / "work-item" / "stages").mkdir(
        parents=True
    )
    (layout.run_root / "canonical-evidence" / "task-run" / "run-manifest.json").parent.mkdir(
        parents=True
    )
    (layout.run_root / "canonical-evidence" / "work-item" / "stages" / "qa.md").write_text(
        "validator\n", encoding="utf-8"
    )
    (layout.run_root / "canonical-evidence" / "task-run" / "run-manifest.json").write_text(
        "{}\n", encoding="utf-8"
    )
    return layout, identity


def test_seal_publishes_inventory_as_final_commit_marker(tmp_path: Path) -> None:
    layout, identity = _write_sealable_bundle(tmp_path)
    inventory = seal_result_bundle(layout=layout, identity=identity, status="pass")

    assert layout.inventory_path.is_file()
    assert inventory.identity == identity
    payload = json.loads(layout.inventory_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    digest_payload = json.loads(layout.artifact_digests_path.read_text(encoding="utf-8"))
    assert digest_payload["schema_version"] == 2
    assert "canonical-evidence/task-run/run-manifest.json" in {
        item["path"] for item in digest_payload["artifacts"]
    }
    validate_result_bundle_inventory(
        inventory=inventory,
        bundle_root=layout.run_root,
        expected_identity=identity,
    )


def test_seal_allows_provider_free_pass_without_product_identity(tmp_path: Path) -> None:
    layout, identity = _write_sealable_bundle(tmp_path)
    provider_free_identity = ResultBundleIdentity(
        evaluation_run_id=identity.evaluation_run_id,
        product_run_id=None,
        scenario_id=identity.scenario_id,
        runtime_id=identity.runtime_id,
        work_item=identity.work_item,
    )
    metadata = json.loads(layout.harness_metadata_path.read_text(encoding="utf-8"))
    metadata["product_run_id"] = None
    layout.harness_metadata_path.write_text(
        json.dumps(metadata) + "\n", encoding="utf-8"
    )

    inventory = seal_result_bundle(
        layout=layout,
        identity=provider_free_identity,
        status="pass",
    )

    assert inventory.identity == provider_free_identity


def test_seal_rejects_missing_required_or_identity_evidence(tmp_path: Path) -> None:
    layout, identity = _write_sealable_bundle(tmp_path)
    layout.verdict_path.unlink()
    with pytest.raises(ResultBundleContractError, match="missing required"):
        seal_result_bundle(layout=layout, identity=identity, status="pass")
    assert not layout.inventory_path.exists()

    layout.verdict_path.write_text("verdict\n", encoding="utf-8")
    layout.harness_metadata_path.write_text(
        json.dumps({"evaluation_run_id": "wrong"}) + "\n", encoding="utf-8"
    )
    with pytest.raises(ResultBundleContractError, match="identity"):
        seal_result_bundle(layout=layout, identity=identity, status="pass")


def test_sealed_inventory_rejects_mutation_and_orphan(tmp_path: Path) -> None:
    layout, identity = _write_sealable_bundle(tmp_path)
    inventory = seal_result_bundle(layout=layout, identity=identity, status="pass")
    layout.verdict_path.write_text("mutated\n", encoding="utf-8")
    with pytest.raises(ResultBundleContractError, match="size|digest"):
        validate_result_bundle_inventory(inventory=inventory, bundle_root=layout.run_root)
    layout.verdict_path.write_text("verdict.md\n", encoding="utf-8")
    (layout.run_root / "orphan.txt").write_text("orphan\n", encoding="utf-8")
    with pytest.raises(ResultBundleContractError, match="orphaned"):
        validate_result_bundle_inventory(inventory=inventory, bundle_root=layout.run_root)
