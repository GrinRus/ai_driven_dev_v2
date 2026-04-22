from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.result_bundle import copy_or_link_run_artifacts, ensure_result_bundle_layout


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
