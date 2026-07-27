from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from aidd.harness.live_bundle_manifest import (
    LIVE_BUNDLE_MANIFEST_FILENAME,
    LiveBundleManifestError,
    LiveBundleSealInputs,
    seal_live_bundle,
    validate_live_bundle_manifest,
)
from aidd.harness.live_result_bundle import (
    LiveResultBundleIdentity,
    materialize_live_result_bundle,
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _repository(root: Path, name: str) -> tuple[Path, str]:
    repository = root / name
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "test@example.invalid")
    _git(repository, "config", "user.name", "Test")
    (repository / "tracked.txt").write_text(f"{name}\n", encoding="utf-8")
    _git(repository, "add", "tracked.txt")
    _git(repository, "commit", "-qm", "baseline")
    return repository, _git(repository, "rev-parse", "HEAD")


def _identity() -> LiveResultBundleIdentity:
    return LiveResultBundleIdentity(
        scenario_id="AIDD-LIVE-007",
        runtime_id="codex",
        run_id="manifest-run",
        work_item="WI-MANIFEST",
    )


def _sealed_bundle(tmp_path: Path) -> tuple[Path, LiveBundleSealInputs]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source, source_commit = _repository(tmp_path, "source")
    target, target_revision = _repository(tmp_path, "target")
    stage = (
        target
        / ".aidd"
        / "workitems"
        / "WI-MANIFEST"
        / "stages"
        / "qa"
        / "output"
    )
    stage.mkdir(parents=True)
    (stage / "stage-result.md").write_text("# Result\n", encoding="utf-8")
    run_evidence = (
        target
        / ".aidd"
        / "reports"
        / "runs"
        / "WI-MANIFEST"
        / "manifest-run"
    )
    run_evidence.mkdir(parents=True)
    (run_evidence / "finalization.json").write_text("{}\n", encoding="utf-8")

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "verdict.md").write_text("# Pass\n", encoding="utf-8")
    browser = bundle / "manual-frontend-evidence"
    browser.mkdir()
    (browser / "1280x900.png").write_bytes(b"image")
    materialize_live_result_bundle(
        bundle_root=bundle,
        identity=_identity(),
        target_root=target,
    )
    wheel = tmp_path / "aidd_test.whl"
    wheel.write_bytes(b"wheel-bytes")
    inputs = LiveBundleSealInputs(
        identity=_identity(),
        source_repository_root=source,
        source_commit=source_commit,
        wheel_path=wheel,
        target_revision=target_revision,
    )
    seal_live_bundle(bundle_root=bundle, inputs=inputs)
    return bundle, inputs


def test_manifest_commits_source_wheel_all_artifacts_and_browser_identity(
    tmp_path: Path,
) -> None:
    bundle, inputs = _sealed_bundle(tmp_path)

    manifest = validate_live_bundle_manifest(
        bundle_root=bundle,
        expected_identity=_identity(),
    )

    assert manifest.source_commit == inputs.source_commit
    assert manifest.source_tree == _git(
        inputs.source_repository_root,
        "rev-parse",
        f"{inputs.source_commit}^{{tree}}",
    )
    assert manifest.target_revision == inputs.target_revision
    assert manifest.source_archive.path == "provenance/aidd-source.tar"
    assert manifest.wheel.path == "provenance/aidd_test.whl"
    assert manifest.source_archive in manifest.files
    assert manifest.wheel in manifest.files
    assert manifest.browser_artifacts[0].run_id == "manifest-run"
    assert manifest.browser_artifacts[0].viewport == "1280x900"
    assert not list(bundle.glob("*.tmp"))
    assert seal_live_bundle(bundle_root=bundle, inputs=inputs) == manifest
    assert not (bundle / "canonical-evidence" / "final" / "provenance").exists()
    shutil.rmtree(inputs.source_repository_root)
    inputs.wheel_path.unlink()
    assert validate_live_bundle_manifest(bundle_root=bundle) == manifest


def test_digest_mismatch_and_orphan_browser_file_fail_closed(tmp_path: Path) -> None:
    bundle, _ = _sealed_bundle(tmp_path)
    (bundle / "verdict.md").write_text("# Rewritten\n", encoding="utf-8")
    with pytest.raises(LiveBundleManifestError, match="digest or size mismatch"):
        validate_live_bundle_manifest(bundle_root=bundle)

    bundle, _ = _sealed_bundle(tmp_path / "orphan")
    browser = (
        bundle
        / "canonical-evidence"
        / "final"
        / "manual-frontend-evidence"
        / "375x812.png"
    )
    browser.write_bytes(b"orphan")
    with pytest.raises(LiveBundleManifestError, match="orphan file"):
        validate_live_bundle_manifest(bundle_root=bundle)


@pytest.mark.parametrize(
    ("field", "value"),
    (("run_id", "other-run"), ("viewport", "320x568")),
)
def test_wrong_browser_run_or_viewport_identity_blocks_readback(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    bundle, _ = _sealed_bundle(tmp_path)
    manifest_path = bundle / LIVE_BUNDLE_MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["browser_artifacts"][0][field] = value
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(LiveBundleManifestError, match="run or viewport"):
        validate_live_bundle_manifest(bundle_root=bundle)


def test_incomplete_materialization_and_wrong_run_identity_block_readback(
    tmp_path: Path,
) -> None:
    bundle, _ = _sealed_bundle(tmp_path)
    manifest_path = bundle / LIVE_BUNDLE_MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    removed = bundle / payload["files"][-1]["path"]
    removed.unlink()
    with pytest.raises(LiveBundleManifestError, match="incomplete materialization"):
        validate_live_bundle_manifest(bundle_root=bundle)

    bundle, _ = _sealed_bundle(tmp_path / "identity")
    with pytest.raises(LiveBundleManifestError, match="identity does not match"):
        validate_live_bundle_manifest(
            bundle_root=bundle,
            expected_identity=LiveResultBundleIdentity(
                scenario_id="AIDD-LIVE-007",
                runtime_id="claude",
                run_id="manifest-run",
                work_item="WI-MANIFEST",
            ),
        )
