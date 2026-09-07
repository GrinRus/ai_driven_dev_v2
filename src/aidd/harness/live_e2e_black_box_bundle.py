from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from aidd.harness.live_bundle_manifest import LiveBundleSealInputs, seal_live_bundle
from aidd.harness.live_result_bundle import LiveResultBundleIdentity, materialize_live_result_bundle


def materialize_canonical_live_result(
    *,
    bundle_root: Path,
    scenario_id: str,
    runtime_id: str,
    run_id: str,
    work_item: str,
    target_root: Path | None,
    target_revision: str | None,
    source_repository_root: Path | None,
    source_commit: str | None,
    wheel_path: Path | None,
) -> None:
    """Materialize and seal the canonical live result without owning orchestration state."""
    identity = LiveResultBundleIdentity(
        scenario_id=scenario_id,
        runtime_id=runtime_id,
        run_id=run_id,
        work_item=work_item,
    )
    materialize_live_result_bundle(
        bundle_root=bundle_root,
        identity=identity,
        target_root=target_root,
    )
    if (
        source_repository_root is not None
        and source_commit is not None
        and wheel_path is not None
        and target_root is not None
        and target_revision is not None
    ):
        seal_live_bundle(
            bundle_root=bundle_root,
            inputs=LiveBundleSealInputs(
                identity=identity,
                source_repository_root=source_repository_root,
                source_commit=source_commit,
                wheel_path=wheel_path,
                target_revision=target_revision,
            ),
        )


def write_run_transcript(
    *,
    bundle_root: Path,
    exit_code: int,
    runtime_id: str,
    work_item: str,
    duration_seconds: float,
    timed_out: bool,
    timeout_seconds: float | None,
    timeout_policy: Mapping[str, object],
    process_segments: Sequence[Mapping[str, object]],
    commands: Sequence[Mapping[str, object]],
    write_json: Callable[[Path, dict[str, object]], Path],
) -> Path:
    """Write the stable run transcript projection used by live result bundles."""
    return write_json(
        bundle_root / "run-transcript.json",
        {
            "command_count": len(commands),
            "commands": [dict(command) for command in commands],
            "duration_seconds": duration_seconds,
            "exit_code": exit_code,
            "process_segment_count": len(process_segments),
            "process_segments": [dict(segment) for segment in process_segments],
            "process_segment_duration_seconds": duration_seconds,
            "runtime_id": runtime_id,
            "step": "run",
            "timed_out": timed_out,
            "timeout_seconds": timeout_seconds,
            "timeout_policy": dict(timeout_policy),
            "work_item": work_item,
        },
    )


__all__ = ["materialize_canonical_live_result", "write_run_transcript"]
