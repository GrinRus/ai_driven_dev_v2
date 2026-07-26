from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LiveProductAcceptance:
    execution_pass: bool
    quality_reviewed: bool
    counted_clean: bool
    manual_quality_stop: bool
    legacy_degraded: bool
    not_clean_reasons: tuple[str, ...]


_COUNTED_CLEAN_PATTERN = re.compile(
    r"^\s*-\s*(?:deliverable quality decision|overall decision|final decision):"
    r"\s*`?counted-clean`?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def derive_live_product_acceptance(
    *,
    flow_status: str | None,
    verdict_status: str | None,
    grader_status: str | None,
    stage_quality_audit_paths: tuple[Path, ...],
    final_report_paths: tuple[Path, ...],
    quality_report_path: Path,
    legacy_degraded: bool,
) -> LiveProductAcceptance:
    manual_quality_stop = flow_status == "manual-quality-stop"
    execution_pass = (
        flow_status == "pass"
        and verdict_status == "pass"
        and grader_status == "pass"
    )
    quality_reviewed = (
        bool(stage_quality_audit_paths)
        and all(path.is_file() for path in stage_quality_audit_paths)
        and bool(final_report_paths)
        and all(path.is_file() for path in final_report_paths)
    )
    quality_text = (
        quality_report_path.read_text(encoding="utf-8", errors="replace")
        if quality_report_path.is_file()
        else ""
    )
    manual_counted_clean = _COUNTED_CLEAN_PATTERN.search(quality_text) is not None
    counted_clean = (
        execution_pass
        and quality_reviewed
        and manual_counted_clean
        and not manual_quality_stop
        and not legacy_degraded
    )
    reasons: list[str] = []
    if not execution_pass:
        reasons.append("execution did not pass consistently")
    if not quality_reviewed:
        reasons.append("manual quality evidence is incomplete")
    elif not manual_counted_clean:
        reasons.append("quality-report.md does not record counted-clean")
    if manual_quality_stop:
        reasons.append("manual quality review stopped the run")
    if legacy_degraded:
        reasons.append("bundle uses legacy degraded evidence")
    return LiveProductAcceptance(
        execution_pass=execution_pass,
        quality_reviewed=quality_reviewed,
        counted_clean=counted_clean,
        manual_quality_stop=manual_quality_stop,
        legacy_degraded=legacy_degraded,
        not_clean_reasons=tuple(reasons),
    )


__all__ = ["LiveProductAcceptance", "derive_live_product_acceptance"]
