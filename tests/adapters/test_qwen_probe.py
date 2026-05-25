from __future__ import annotations

import importlib


def test_probe_marks_qwen_dual_file_live_decisions(monkeypatch) -> None:
    probe_module = importlib.import_module("aidd.adapters.qwen.probe")
    monkeypatch.setattr(probe_module, "discover_command", lambda _: "/tmp/qwen")
    monkeypatch.setattr(probe_module, "discover_version", lambda _: "qwen 0.15.2")
    monkeypatch.setattr(
        probe_module,
        "discover_help_text",
        lambda _: "--approval-mode --output-format --json-file --input-file",
    )

    report = probe_module.probe("qwen")

    assert report.supports_live_decisions is True
    assert report.preferred_transport == "dual-jsonl"
