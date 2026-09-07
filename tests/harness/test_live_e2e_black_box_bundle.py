from __future__ import annotations

from pathlib import Path

from aidd.harness import live_e2e_black_box_bundle as bundle


def test_write_run_transcript_preserves_projection_shape(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def write_json(path: Path, payload: dict[str, object]) -> Path:
        captured["path"] = path
        captured["payload"] = payload
        return path

    result = bundle.write_run_transcript(
        bundle_root=tmp_path,
        exit_code=1,
        runtime_id="codex",
        work_item="item-1",
        duration_seconds=1.25,
        timed_out=True,
        timeout_seconds=30.0,
        timeout_policy={"stage": "bounded"},
        process_segments=({"stage": "plan"},),
        commands=({"command": "aidd stage run"},),
        write_json=write_json,
    )

    assert result == tmp_path / "run-transcript.json"
    assert captured == {
        "path": tmp_path / "run-transcript.json",
        "payload": {
            "command_count": 1,
            "commands": [{"command": "aidd stage run"}],
            "duration_seconds": 1.25,
            "exit_code": 1,
            "process_segment_count": 1,
            "process_segments": [{"stage": "plan"}],
            "process_segment_duration_seconds": 1.25,
            "runtime_id": "codex",
            "step": "run",
            "timed_out": True,
            "timeout_seconds": 30.0,
            "timeout_policy": {"stage": "bounded"},
            "work_item": "item-1",
        },
    }


def test_materialize_canonical_live_result_seals_complete_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    materialized: list[dict[str, object]] = []
    sealed: list[object] = []
    monkeypatch.setattr(
        bundle,
        "materialize_live_result_bundle",
        lambda **kwargs: materialized.append(kwargs),
    )
    monkeypatch.setattr(bundle, "seal_live_bundle", lambda **kwargs: sealed.append(kwargs))

    source_root = tmp_path / "source"
    wheel_path = tmp_path / "aidd.whl"
    target_root = tmp_path / "target"
    bundle.materialize_canonical_live_result(
        bundle_root=tmp_path / "bundle",
        scenario_id="scenario-1",
        runtime_id="codex",
        run_id="run-1",
        work_item="item-1",
        target_root=target_root,
        target_revision="target-sha",
        source_repository_root=source_root,
        source_commit="source-sha",
        wheel_path=wheel_path,
    )

    assert materialized[0]["target_root"] == target_root
    identity = materialized[0]["identity"]
    assert identity.scenario_id == "scenario-1"
    assert identity.run_id == "run-1"
    assert len(sealed) == 1
    seal_inputs = sealed[0]["inputs"]
    assert seal_inputs.identity == identity
    assert seal_inputs.source_commit == "source-sha"
    assert seal_inputs.target_revision == "target-sha"
