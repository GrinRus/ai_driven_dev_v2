from __future__ import annotations

import shutil

from aidd.adapters.base import CapabilityReport


def probe(command: str) -> CapabilityReport:
    return CapabilityReport(
        runtime_id="opencode",
        available=shutil.which(command) is not None,
        command=command,
        supports_structured_log_stream=False,
        supports_questions=False,
        supports_resume=False,
        supports_subagents=True,
    )
