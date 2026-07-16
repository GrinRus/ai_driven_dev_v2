from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from aidd.harness.result_bundle import (
    copy_or_link_run_artifacts,
    ensure_result_bundle_layout,
    read_artifact_digests,
)


def test_copy_or_link_run_artifacts_materializes_bundle_files(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    sources_root.mkdir(parents=True, exist_ok=True)
    runtime_log_path = sources_root / "runtime.log"
    validator_report_path = sources_root / "validator-report.md"
    verdict_path = sources_root / "verdict.md"
    runtime_jsonl_path = sources_root / "runtime.jsonl"
    events_jsonl_path = sources_root / "events.jsonl"
    runtime_log_path.write_text("runtime\n", encoding="utf-8")
    validator_report_path.write_text("# Validator report\n\n- Verdict: `pass`\n", encoding="utf-8")
    verdict_path.write_text("# Verdict\n\npass\n", encoding="utf-8")
    runtime_jsonl_path.write_text('{"event":"runtime"}\n', encoding="utf-8")
    events_jsonl_path.write_text('{"event":"normalized"}\n', encoding="utf-8")

    layout = ensure_result_bundle_layout(workspace_root=tmp_path, run_id="eval-run-202")
    copied = copy_or_link_run_artifacts(
        layout=layout,
        runtime_log_path=runtime_log_path,
        validator_report_path=validator_report_path,
        verdict_path=verdict_path,
        runtime_jsonl_path=runtime_jsonl_path,
        events_jsonl_path=events_jsonl_path,
    )

    assert copied["runtime_log"] == layout.runtime_log_path
    assert copied["validator_report"] == layout.validator_report_path
    assert copied["verdict"] == layout.verdict_path
    assert copied["runtime_jsonl"] == layout.runtime_jsonl_path
    assert copied["events_jsonl"] == layout.events_jsonl_path
    assert layout.runtime_log_path.read_text(encoding="utf-8") == "runtime\n"
    assert "# Validator report" in layout.validator_report_path.read_text(encoding="utf-8")
    assert "pass" in layout.verdict_path.read_text(encoding="utf-8")
    assert "runtime" in layout.runtime_jsonl_path.read_text(encoding="utf-8")
    assert "normalized" in layout.events_jsonl_path.read_text(encoding="utf-8")
    digest_payload = json.loads(
        layout.artifact_digests_path.read_text(encoding="utf-8")
    )
    assert digest_payload["schema_version"] == 1
    assert [item["path"] for item in digest_payload["artifacts"]] == sorted(
        (
            "events.jsonl",
            "runtime.jsonl",
            "runtime.log",
            "validator-report.md",
            "verdict.md",
        )
    )
    assert os.stat(runtime_log_path).st_ino != os.stat(layout.runtime_log_path).st_ino

    runtime_log_path.write_text("mutated source\n", encoding="utf-8")
    assert layout.runtime_log_path.read_text(encoding="utf-8") == "runtime\n"


def test_copy_or_link_run_artifacts_rejects_missing_source(tmp_path: Path) -> None:
    layout = ensure_result_bundle_layout(workspace_root=tmp_path, run_id="eval-run-203")
    validator_report_path = tmp_path / "validator-report.md"
    verdict_path = tmp_path / "verdict.md"
    validator_report_path.write_text("# Validator report\n", encoding="utf-8")
    verdict_path.write_text("# Verdict\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Artifact source file does not exist"):
        copy_or_link_run_artifacts(
            layout=layout,
            runtime_log_path=tmp_path / "missing-runtime.log",
            validator_report_path=validator_report_path,
            verdict_path=verdict_path,
        )


def test_copy_failure_does_not_publish_commit_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = ensure_result_bundle_layout(workspace_root=tmp_path, run_id="eval-run-204")
    sources = tmp_path / "sources"
    sources.mkdir()
    runtime_log = sources / "runtime.log"
    validator_report = sources / "validator-report.md"
    verdict = sources / "verdict.md"
    for path in (runtime_log, validator_report, verdict):
        path.write_text(path.name, encoding="utf-8")

    def _fail_copy(source: Path, destination: Path) -> str:
        raise OSError(f"injected copy failure: {source} -> {destination}")

    monkeypatch.setattr("aidd.harness.result_bundle.shutil.copyfile", _fail_copy)

    with pytest.raises(OSError, match="injected copy failure"):
        copy_or_link_run_artifacts(
            layout=layout,
            runtime_log_path=runtime_log,
            validator_report_path=validator_report,
            verdict_path=verdict,
        )

    assert not layout.artifact_digests_path.exists()
    assert not tuple(layout.run_root.glob(".artifact-materialization-*"))


def test_read_artifact_digests_warns_for_legacy_bundle(tmp_path: Path) -> None:
    layout = ensure_result_bundle_layout(workspace_root=tmp_path, run_id="legacy-run")

    with pytest.warns(UserWarning, match="legacy bundle"):
        assert read_artifact_digests(layout=layout) is None
