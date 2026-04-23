from __future__ import annotations

import json
from pathlib import Path

RUNTIME_EXIT_METADATA_FILENAME = "runtime-exit.json"


def write_runtime_exit_metadata(
    *,
    attempt_path: Path,
    exit_code: int,
    exit_classification: str,
    stdout_text: str,
    stderr_text: str,
    runtime_log_text: str,
) -> Path:
    attempt_path.mkdir(parents=True, exist_ok=True)
    runtime_exit_metadata_path = attempt_path / RUNTIME_EXIT_METADATA_FILENAME
    runtime_exit_metadata = {
        "schema_version": 1,
        "exit_code": exit_code,
        "exit_classification": exit_classification,
        "stdout_char_count": len(stdout_text),
        "stderr_char_count": len(stderr_text),
        "runtime_log_char_count": len(runtime_log_text),
    }
    runtime_exit_metadata_path.write_text(
        json.dumps(runtime_exit_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return runtime_exit_metadata_path
