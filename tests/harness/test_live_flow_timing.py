from __future__ import annotations

from aidd.harness.live_flow_timing import (
    cumulative_process_duration_seconds,
    finish_stale_owner_segment,
    process_segments_payload,
    update_process_segments,
)


def test_process_segments_accumulate_across_two_resumes() -> None:
    segments = update_process_segments(
        [],
        owner_pid=101,
        observed_at_utc="2026-07-26T10:00:00Z",
        status="running",
    )
    segments = update_process_segments(
        process_segments_payload(segments),
        owner_pid=101,
        observed_at_utc="2026-07-26T10:00:05Z",
        status="awaiting-quality-review",
    )
    segments = update_process_segments(
        process_segments_payload(segments),
        owner_pid=202,
        observed_at_utc="2026-07-26T10:01:00Z",
        status="running",
    )
    segments = update_process_segments(
        process_segments_payload(segments),
        owner_pid=202,
        observed_at_utc="2026-07-26T10:01:07Z",
        status="blocked",
    )
    segments = update_process_segments(
        process_segments_payload(segments),
        owner_pid=303,
        observed_at_utc="2026-07-26T10:02:00Z",
        status="running",
    )
    segments = update_process_segments(
        process_segments_payload(segments),
        owner_pid=303,
        observed_at_utc="2026-07-26T10:02:11Z",
        status="pass",
    )

    assert [segment.segment_id for segment in segments] == [
        "segment-0001",
        "segment-0002",
        "segment-0003",
    ]
    assert [segment.duration_seconds for segment in segments] == [5.0, 7.0, 11.0]
    assert [segment.termination_reason for segment in segments] == [
        "awaiting-quality-review",
        "blocked",
        "pass",
    ]
    assert cumulative_process_duration_seconds(process_segments_payload(segments)) == 23.0


def test_stale_owner_closes_existing_segment_without_stage_verdict() -> None:
    active = update_process_segments(
        [],
        owner_pid=101,
        observed_at_utc="2026-07-26T10:00:00Z",
        status="running",
    )

    finished = finish_stale_owner_segment(
        process_segments_payload(active),
        owner_pid=101,
        finished_at_utc="2026-07-26T10:00:09Z",
    )

    assert len(finished) == 1
    assert finished[0].duration_seconds == 9.0
    assert finished[0].termination_reason == "stale-owner"
