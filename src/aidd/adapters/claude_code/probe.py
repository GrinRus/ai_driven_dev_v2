from __future__ import annotations

import shutil

from aidd.adapters.base import CapabilityReport


def probe(command: str) -> CapabilityReport:
    return CapabilityReport(
        runtime_id="claude-code",
        available=shutil.which(command) is not None,
        command=command,
        supports_structured_log_stream=True,
        supports_questions=True,
        supports_resume=True,
        supports_subagents=True,
    )
