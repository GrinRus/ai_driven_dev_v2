from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from aidd.harness.live_result_bundle import (
    LIVE_RESULT_INDEX_FILENAME,
    LiveResultBundleError,
    LiveResultBundleIdentity,
    materialize_live_result_bundle,
    resolve_live_result_reference,
    validate_live_result_bundle,
)


def _git(target_root: Path, *args: str) -> None:
    subprocess.run(
        ("git", *args),
        cwd=target_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _identity() -> LiveResultBundleIdentity:
    return LiveResultBundleIdentity(
        scenario_id="AIDD-LIVE-007",
        runtime_id="codex",
        run_id="run-007",
        work_item="WI-007",
    )


def _prepare_target(root: Path) -> Path:
    target = root / "target"
    target.mkdir()
    _git(target, "init", "-q")
    _git(target, "config", "user.email", "test@example.invalid")
    _git(target, "config", "user.name", "Test")
    (target / "product.txt").write_text("before\n", encoding="utf-8")
    _git(target, "add", "product.txt")
    _git(target, "commit", "-qm", "baseline")
    (target / "product.txt").write_text("after\n", encoding="utf-8")
    (target / "new-product.txt").write_text("new\n", encoding="utf-8")

    stage_root = (
        target
        / ".aidd"
        / "workitems"
        / "WI-007"
        / "stages"
        / "implement"
        / "output"
    )
    stage_root.mkdir(parents=True)
    (stage_root / "implementation-report.md").write_text(
        "# Implementation\n", encoding="utf-8"
    )
    (stage_root / "stage-result.md").write_text("# Result\n", encoding="utf-8")
    (stage_root / "validator-report.md").write_text(
        "# Validator\n", encoding="utf-8"
    )

    attempt_root = (
        target
        / ".aidd"
        / "reports"
        / "runs"
        / "WI-007"
        / "run-007"
        / "stages"
        / "implement"
        / "attempts"
        / "attempt-0001"
    )
    attempt_root.mkdir(parents=True)
    (attempt_root / "task-evidence.json").write_text(
        '{"status":"succeeded"}\n', encoding="utf-8"
    )
    (attempt_root.parent.parent / "stage-metadata.json").write_text(
        '{"status":"succeeded"}\n', encoding="utf-8"
    )
    return target


def _prepare_bundle(root: Path) -> Path:
    bundle = root / "reports" / "run-007"
    bundle.mkdir(parents=True)
    (bundle / "verdict.md").write_text("# Verdict\n", encoding="utf-8")
    (bundle / "grader.json").write_text('{"status":"pass"}\n', encoding="utf-8")
    (bundle / "verification.json").write_text(
        '{"exit_code":0}\n', encoding="utf-8"
    )
    (bundle / "stage-audits").mkdir()
    (bundle / "stage-audits" / "implement.json").write_text(
        '{"stage":"implement"}\n', encoding="utf-8"
    )
    (bundle / "remediation-actions").mkdir()
    (bundle / "remediation-actions" / "action.json").write_text(
        '{"status":"completed"}\n', encoding="utf-8"
    )
    (bundle / "manual-frontend-evidence").mkdir()
    (bundle / "manual-frontend-evidence" / "desktop.png").write_bytes(b"png")
    return bundle


def test_materialized_bundle_survives_mutable_root_deletion(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    work_root = tmp_path / "work"
    source_root.mkdir()
    work_root.mkdir()
    (source_root / "source.whl").write_bytes(b"wheel")
    target = _prepare_target(work_root)
    bundle = _prepare_bundle(tmp_path)

    result = materialize_live_result_bundle(
        bundle_root=bundle,
        identity=_identity(),
        target_root=target,
    )

    shutil.rmtree(source_root)
    shutil.rmtree(work_root)
    verified = validate_live_result_bundle(
        bundle_root=bundle,
        expected_identity=_identity(),
    )
    paths = {artifact.path for artifact in verified.artifacts}
    assert result == verified
    assert (
        "canonical-evidence/work-item/stages/implement/output/stage-result.md"
        in paths
    )
    assert (
        "canonical-evidence/work-item/stages/implement/output/validator-report.md"
        in paths
    )
    assert (
        "canonical-evidence/task-run/stages/implement/attempts/"
        "attempt-0001/task-evidence.json"
    ) in paths
    assert "canonical-evidence/target/target.patch" in paths
    assert "canonical-evidence/final/verdict.md" in paths
    assert (
        "canonical-evidence/final/manual-frontend-evidence/desktop.png" in paths
    )
    patch_path, mode = resolve_live_result_reference(
        bundle_root=bundle,
        reference="canonical-evidence/target/target.patch",
    )
    assert mode == "bundle-relative"
    assert b"-before" in patch_path.read_bytes()
    assert b"+after" in patch_path.read_bytes()
    assert b"new-product.txt" in patch_path.read_bytes()
    assert b"implementation-report.md" not in patch_path.read_bytes()


def test_validation_fails_closed_for_dangling_tampered_and_wrong_identity(
    tmp_path: Path,
) -> None:
    target = _prepare_target(tmp_path)
    bundle = _prepare_bundle(tmp_path)
    materialize_live_result_bundle(
        bundle_root=bundle,
        identity=_identity(),
        target_root=target,
    )
    index_path = bundle / LIVE_RESULT_INDEX_FILENAME
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    artifact_path = bundle / payload["artifacts"][0]["path"]
    artifact_path.unlink()

    with pytest.raises(LiveResultBundleError, match="dangling"):
        validate_live_result_bundle(bundle_root=bundle)

    materialize_live_result_bundle(
        bundle_root=bundle,
        identity=_identity(),
        target_root=target,
    )
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    artifact_path = bundle / payload["artifacts"][0]["path"]
    artifact_path.write_bytes(artifact_path.read_bytes() + b"tampered")
    with pytest.raises(LiveResultBundleError, match="does not match"):
        validate_live_result_bundle(bundle_root=bundle)

    with pytest.raises(LiveResultBundleError, match="identity does not match"):
        validate_live_result_bundle(
            bundle_root=bundle,
            expected_identity=LiveResultBundleIdentity(
                scenario_id="AIDD-LIVE-007",
                runtime_id="claude",
                run_id="run-007",
                work_item="WI-007",
            ),
        )


def test_absolute_reference_requires_explicit_legacy_degraded_mode(
    tmp_path: Path,
) -> None:
    bundle = _prepare_bundle(tmp_path)
    legacy = tmp_path / "legacy.md"
    legacy.write_text("# Legacy\n", encoding="utf-8")

    with pytest.raises(LiveResultBundleError, match="legacy evidence"):
        resolve_live_result_reference(
            bundle_root=bundle,
            reference=legacy.as_posix(),
        )

    path, mode = resolve_live_result_reference(
        bundle_root=bundle,
        reference=legacy.as_posix(),
        allow_legacy_absolute=True,
    )
    assert path == legacy
    assert mode == "legacy-degraded"


def test_materialization_rejects_symlinked_target_evidence(tmp_path: Path) -> None:
    target = _prepare_target(tmp_path)
    bundle = _prepare_bundle(tmp_path)
    external = tmp_path / "external.md"
    external.write_text("secret\n", encoding="utf-8")
    stage_root = target / ".aidd" / "workitems" / "WI-007"
    (stage_root / "escape.md").symlink_to(external)

    with pytest.raises(LiveResultBundleError, match="Symlink"):
        materialize_live_result_bundle(
            bundle_root=bundle,
            identity=_identity(),
            target_root=target,
        )
