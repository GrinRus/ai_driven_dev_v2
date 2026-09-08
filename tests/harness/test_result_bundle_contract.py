from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.harness.result_bundle_contract import (
    BundleArtifactRequirement,
    ResultBundleArtifact,
    ResultBundleContractError,
    ResultBundleIdentity,
    ResultBundleInventory,
    dump_result_bundle_inventory,
    validate_result_bundle_inventory,
)


def _identity(*, product_run_id: str | None = "product-run-001") -> ResultBundleIdentity:
    return ResultBundleIdentity(
        evaluation_run_id="eval-run-001",
        product_run_id=product_run_id,
        scenario_id="AIDD-DETERMINISTIC-001",
        runtime_id="codex",
        work_item="WI-001",
    )


def _inventory(
    *, status: str = "pass", artifacts: tuple[ResultBundleArtifact, ...] = ()
) -> ResultBundleInventory:
    return ResultBundleInventory(
        identity=_identity(),
        status=status,  # type: ignore[arg-type]
        artifacts=artifacts,
        requirements=(
            BundleArtifactRequirement(
                path="verdict.md",
                required_for=frozenset({"pass"}),
            ),
        ),
    )


def test_identity_round_trip_keeps_eval_and_product_ids_distinct() -> None:
    identity = _identity().normalized()
    assert identity.eval_run_id == "eval-run-001"
    assert ResultBundleIdentity.from_dict(identity.to_dict()) == identity
    assert identity.to_dict()["product_run_id"] == "product-run-001"


def test_product_run_id_may_be_unknown_before_product_execution() -> None:
    identity = _identity(product_run_id=None).normalized()
    assert identity.product_run_id is None


def test_equal_eval_and_product_ids_are_ambiguous() -> None:
    with pytest.raises(ResultBundleContractError, match="remain distinct"):
        _identity(product_run_id="eval-run-001").normalized()


def test_legacy_identity_and_missing_product_id_are_rejected() -> None:
    with pytest.raises(ResultBundleContractError, match="legacy"):
        ResultBundleIdentity.from_dict({"run_id": "run-001"})
    legacy_extra = _identity().to_dict()
    legacy_extra["run_id"] = "run-001"
    with pytest.raises(ResultBundleContractError, match="legacy"):
        ResultBundleIdentity.from_dict(legacy_extra)
    payload = _identity().to_dict()
    payload.pop("product_run_id")
    with pytest.raises(ResultBundleContractError, match="missing required fields"):
        ResultBundleIdentity.from_dict(payload)


@pytest.mark.parametrize("path", ("/tmp/out.md", "../out.md", "nested\\out.md"))
def test_artifact_references_are_bundle_relative(path: str) -> None:
    with pytest.raises(ResultBundleContractError, match="bundle-relative|POSIX"):
        ResultBundleArtifact(path=path).normalized()


def test_valid_inventory_serializes_deterministically_and_validates(tmp_path: Path) -> None:
    (tmp_path / "verdict.md").write_text("# Verdict\n", encoding="utf-8")
    artifact = ResultBundleArtifact(path="verdict.md", size_bytes=10)
    inventory = _inventory(artifacts=(artifact,))

    validated = validate_result_bundle_inventory(
        inventory=inventory,
        bundle_root=tmp_path,
    )

    assert validated.identity.evaluation_run_id == "eval-run-001"
    assert json.loads(dump_result_bundle_inventory(validated))["status"] == "pass"


def test_dangling_artifact_reference_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ResultBundleContractError, match="dangling"):
        validate_result_bundle_inventory(
            inventory=_inventory(
                artifacts=(ResultBundleArtifact(path="missing.md"),),
            ),
            bundle_root=tmp_path,
        )


def test_required_artifact_is_checked_only_for_selected_status(tmp_path: Path) -> None:
    (tmp_path / "failure.md").write_text("failure\n", encoding="utf-8")
    inventory = ResultBundleInventory(
        identity=_identity(),
        status="fail",
        artifacts=(ResultBundleArtifact(path="failure.md"),),
        requirements=(
            BundleArtifactRequirement(
                path="verdict.md",
                required_for=frozenset({"pass"}),
            ),
            BundleArtifactRequirement(
                path="failure.md",
                required_for=frozenset({"fail"}),
                condition="fail",
            ),
        ),
    )
    validate_result_bundle_inventory(inventory=inventory, bundle_root=tmp_path)


def test_inactive_conditional_artifact_need_not_be_materialized(tmp_path: Path) -> None:
    inventory = ResultBundleInventory(
        identity=_identity(),
        status="pass",
        artifacts=(ResultBundleArtifact(path="failure.md", condition="fail"),),
    )
    validate_result_bundle_inventory(inventory=inventory, bundle_root=tmp_path)


def test_missing_required_artifact_and_duplicate_paths_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ResultBundleContractError, match="missing required"):
        validate_result_bundle_inventory(
            inventory=_inventory(),
            bundle_root=tmp_path,
        )
    with pytest.raises(ResultBundleContractError, match="duplicate"):
        _inventory(
            artifacts=(
                ResultBundleArtifact(path="verdict.md"),
                ResultBundleArtifact(path="verdict.md"),
            )
        ).normalized()


def test_legacy_inventory_payload_is_rejected() -> None:
    with pytest.raises(ResultBundleContractError, match="legacy"):
        ResultBundleInventory.from_dict({"run_id": "run-001", "status": "pass", "artifacts": []})


def test_orphaned_bundle_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "verdict.md").write_text("pass\n", encoding="utf-8")
    (tmp_path / "unexpected.txt").write_text("orphan\n", encoding="utf-8")
    inventory = _inventory(artifacts=(ResultBundleArtifact(path="verdict.md"),))
    with pytest.raises(ResultBundleContractError, match="orphaned"):
        validate_result_bundle_inventory(inventory=inventory, bundle_root=tmp_path)


def test_expected_identity_is_checked_at_validation_boundary(tmp_path: Path) -> None:
    (tmp_path / "verdict.md").write_text("pass\n", encoding="utf-8")
    inventory = _inventory(artifacts=(ResultBundleArtifact(path="verdict.md"),))
    with pytest.raises(ResultBundleContractError, match="identity"):
        validate_result_bundle_inventory(
            inventory=inventory,
            bundle_root=tmp_path,
            expected_identity=ResultBundleIdentity(
                evaluation_run_id="other-eval",
                product_run_id="product-run-001",
                scenario_id="AIDD-CONTRACT-TEST",
                runtime_id="generic-cli",
                work_item="WI-CONTRACT",
            ),
        )
