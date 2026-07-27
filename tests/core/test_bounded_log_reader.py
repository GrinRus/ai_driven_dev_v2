from __future__ import annotations

from pathlib import Path

from aidd.core.bounded_log_reader import MAX_LOG_READ_BYTES, read_bounded_log


def test_sparse_log_tail_reads_only_requested_range(tmp_path: Path) -> None:
    path = tmp_path / "runtime.log"
    with path.open("wb") as stream:
        stream.seek(64 * 1024 * 1024)
        stream.write(b"tail-marker\n")

    result = read_bounded_log(path, mode="tail", requested_bytes=4096)

    assert result.byte_size == 64 * 1024 * 1024 + len(b"tail-marker\n")
    assert result.retained_bytes == 4096
    assert result.end_byte == result.byte_size
    assert result.start_byte == result.byte_size - 4096
    assert result.text.endswith("tail-marker\n")
    assert result.truncated_head is True
    assert result.truncated_tail is False


def test_oversized_single_line_retains_bounded_head_and_tail(tmp_path: Path) -> None:
    path = tmp_path / "runtime.log"
    path.write_bytes(b"x" * (MAX_LOG_READ_BYTES * 2))

    head = read_bounded_log(
        path,
        mode="head",
        requested_bytes=MAX_LOG_READ_BYTES * 4,
    )
    tail = read_bounded_log(
        path,
        mode="tail",
        requested_bytes=MAX_LOG_READ_BYTES * 4,
    )

    assert head.retained_bytes == MAX_LOG_READ_BYTES
    assert head.requested_bytes == MAX_LOG_READ_BYTES
    assert head.partial_tail_line is True
    assert head.oversized_line is True
    assert tail.retained_bytes == MAX_LOG_READ_BYTES
    assert tail.partial_head_line is True
    assert tail.oversized_line is True
    assert len(head.text.encode()) == MAX_LOG_READ_BYTES
    assert len(tail.text.encode()) == MAX_LOG_READ_BYTES


def test_bounded_reader_reports_head_and_tail_metadata(tmp_path: Path) -> None:
    path = tmp_path / "runtime.log"
    path.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    head = read_bounded_log(path, mode="head", requested_bytes=7)
    tail = read_bounded_log(path, mode="tail", requested_bytes=7)

    assert head.text == "alpha\nb"
    assert head.start_byte == 0
    assert head.end_byte == 7
    assert head.partial_tail_line is True
    assert tail.text == "\ngamma\n"
    assert tail.start_byte == path.stat().st_size - 7
    assert tail.end_byte == path.stat().st_size
    assert tail.partial_head_line is False
